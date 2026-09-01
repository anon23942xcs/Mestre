"""
Compilador de memórias e sincronizador canônico da Wiki e do Estado.
"""
from typing import Dict, Any
from app.config import LIMITE_MEMORIAS_IMPORTANTES
from app.models.estado import EstadoCompleto
from app.models.ficha import FichaMundo
from app.prompts.preencher import preencher
from app.services.ia_client import gerar_json, ErroIA, ErroFormatoIA
from app.storage import ficha_repositorio

PROMPT_SINCRONIZAR = """Você é o Cronista e Compilador Canônico do RPG. Sua missão é consolidar os acontecimentos recentes da história, atualizando as fichas da Wiki do mundo, a ficha do jogador e as memórias de longo prazo.

IMPORTANTE:
- Se personagens morreram, foram devorados ou derrotados (exemplo: Olive foi devorada ou morta por Mike), atualize a ficha correspondente em "fichas_atualizadas" alterando os campos (ex: "status": "Morta / Devorada", "rank": "Poderes absorvidos") e inserindo o relato no "conteudo_append".
- Se o jogador evoluiu, despertou habilidades, absorveu poderes ou subiu de rank (ex: Mike absorveu a Cura Rank S de Olive ou subiu andares da torre), registre em "jogador_atualizado" e se apropriado crie uma ficha nova de habilidade em "fichas_novas".
- Atualize locais ou facções se foram afetados (ex: andares da torre desbravados, monstros destruídos).
- Gere até {limite} memórias importantes canônicas resumidas de longo prazo.

Responda APENAS com JSON no formato:
{{
  "memorias_importantes": ["fato canônico 1", "fato canônico 2", ...],
  "fichas_atualizadas": [
    {{
      "id": "id_da_ficha",
      "campos": {{"status": "Morta / Devorada", "rank": "..."}},
      "conteudo_append": "relato canônico do que aconteceu com esta entidade"
    }}
  ],
  "fichas_novas": [
    {{
      "tipo": "personagem",
      "titulo": "Nome",
      "resumo": "Resumo curto",
      "conteudo": "Descrição completa",
      "campos": {{"chave": "valor"}}
    }}
  ],
  "jogador_atualizado": {{
    "novos_poderes": "descrição dos poderes recém absorvidos ou descobertos, ou null",
    "novo_status_rank": "novo rank ou status, ex: Devorador Desperto, ou null",
    "novos_itens": ["item1"],
    "itens_removidos": []
  }},
  "resumo_alteracoes": "Frase curta em português resumindo o que mudou na Wiki e no mundo"
}}

[FICHAS DA WIKI DA CAMPANHA ATUAL]
{fichas_wiki}

[JOGADOR ATUAL]
Nome: {jogador_nome}
Aparência: {jogador_aparencia}
Histórico: {jogador_historico}
Inventário: {jogador_inventario}

[MEMÓRIAS IMPORTANTES ANTERIORES]
{existentes}

[HISTÓRICO RECENTE DE AÇÕES E NARRATIVAS]
{recentes}
"""


def compilar_e_sincronizar_wiki(estado: EstadoCompleto) -> Dict[str, Any]:
    """Analisa o histórico recente e sincroniza fichas da Wiki, jogador e memórias."""
    escopo = f"campanha_{estado.campanha_id}"
    fichas = ficha_repositorio.listar(escopo)
    
    if not fichas and estado.mundo_id:
        ficha_repositorio.copiar_fichas(f"mundo_{estado.mundo_id}", escopo)
        fichas = ficha_repositorio.listar(escopo)

    fichas_formatadas = "\n".join(
        f"- ID: {f.id} | Título: {f.titulo} | Tipo: {f.tipo}\n  Resumo: {f.resumo}\n  Campos: {f.campos}"
        for f in fichas
    ) or "Nenhuma ficha cadastrada na wiki."

    if estado.historico_chat:
        ultimas_msgs = estado.historico_chat[-12:]
        recentes = "\n".join(f"{m.nome} ({m.autor}): {m.conteudo}" for m in ultimas_msgs)
    elif estado.estado.memorias_recentes:
        recentes = "\n".join(estado.estado.memorias_recentes)
    else:
        recentes = estado.ultima_narracao or "Início da campanha."

    prompt = preencher(
        PROMPT_SINCRONIZAR,
        limite=LIMITE_MEMORIAS_IMPORTANTES,
        fichas_wiki=fichas_formatadas,
        jogador_nome=estado.jogador.nome,
        jogador_aparencia=estado.jogador.aparencia,
        jogador_historico=estado.jogador.historico,
        jogador_inventario=", ".join(estado.jogador.inventario) or "nenhum",
        existentes="\n".join(estado.estado.memorias_importantes) or "nenhuma ainda",
        recentes=recentes,
    )

    try:
        resultado = gerar_json(prompt)
    except (ErroIA, ErroFormatoIA) as e:
        return {
            "sucesso": False,
            "resumo_alteracoes": f"Não foi possível sincronizar no momento: {e}",
            "fichas_atualizadas": [],
            "fichas_novas": [],
            "estado": estado
        }

    # 1. Atualizar memórias importantes
    novas_memorias = resultado.get("memorias_importantes")
    if isinstance(novas_memorias, list) and novas_memorias:
        estado.estado.memorias_importantes = [str(m) for m in novas_memorias][:LIMITE_MEMORIAS_IMPORTANTES]

    # 2. Atualizar fichas da Wiki existentes
    fichas_map = {f.id: f for f in fichas}
    fichas_atualizadas_nomes = []

    for at in resultado.get("fichas_atualizadas") or []:
        if not isinstance(at, dict) or not at.get("id"):
            continue
        fid = str(at["id"])
        ficha = fichas_map.get(fid)
        if not ficha:
            continue
        if isinstance(at.get("campos"), dict):
            ficha.campos.update({str(k): v for k, v in at["campos"].items()})
        append = at.get("conteudo_append")
        if isinstance(append, str) and append.strip():
            ficha.conteudo = (ficha.conteudo + "\n\n[ATUALIZAÇÃO CANÔNICA]: " + append.strip()).strip()
        ficha_repositorio.salvar(escopo, ficha)
        fichas_atualizadas_nomes.append(ficha.titulo)

    # 3. Criar novas fichas na Wiki
    fichas_novas_nomes = []
    for nova in resultado.get("fichas_novas") or []:
        if not isinstance(nova, dict) or not nova.get("titulo"):
            continue
        try:
            dados = dict(nova)
            dados["id"] = ficha_repositorio.novo_id()
            ficha_obj = FichaMundo(**dados)
            ficha_repositorio.salvar(escopo, ficha_obj)
            fichas_novas_nomes.append(ficha_obj.titulo)
        except Exception:
            pass

    # 4. Atualizar ficha do jogador (estado.jogador)
    jog_up = resultado.get("jogador_atualizado")
    if isinstance(jog_up, dict):
        if jog_up.get("novos_poderes"):
            poderes = str(jog_up["novos_poderes"])
            if poderes not in estado.jogador.historico:
                estado.jogador.historico += f"\n[Poderes Absorvidos/Despertos]: {poderes}"
                estado.jogador.ficha_completa += f"\n\n### PODERES ADQUIRIDOS / ABSORVIDOS\n- {poderes}"
        if jog_up.get("novo_status_rank"):
            status = str(jog_up["novo_status_rank"])
            if status not in estado.jogador.aparencia:
                estado.jogador.aparencia += f" | {status}"
        for item in jog_up.get("novos_itens") or []:
            if str(item) not in estado.jogador.inventario:
                estado.jogador.inventario.append(str(item))
        for item in jog_up.get("itens_removidos") or []:
            if str(item) in estado.jogador.inventario:
                estado.jogador.inventario.remove(str(item))

    resumo = str(resultado.get("resumo_alteracoes") or "Wiki e memórias sincronizadas com sucesso.")

    estado.estado.memorias_recentes = []

    return {
        "sucesso": True,
        "resumo_alteracoes": resumo,
        "fichas_atualizadas": fichas_atualizadas_nomes,
        "fichas_novas": fichas_novas_nomes,
        "estado": estado
    }


def compilar(estado: EstadoCompleto) -> EstadoCompleto:
    """Passo 0 periódico de compilação."""
    resultado = compilar_e_sincronizar_wiki(estado)
    return resultado["estado"] if "estado" in resultado else estado