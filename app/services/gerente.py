"""
Passo 2: Gerente.

Este é o passo que estava totalmente ausente antes. A função
atualizar_estado() original só fazia um pop/append manual em
memorias_recentes, nenhuma IA participava disso, e por isso NPCs nunca
mudavam de humor ou relação, eventos nunca eram criados, e o progresso da
campanha nunca avançava. O "estado vivo" prometido na especificação não
acontecia de fato.

Em vez de deixar a IA reescrever o estado inteiro livremente (caro, e
arriscado porque um JSON malformado quebraria o campanha inteira), a IA
gera um PATCH pequeno e estruturado, e este módulo aplica esse patch nos
objetos Pydantic já validados. Isso mantém o custo baixo (~poucas centenas
de tokens) e a integridade do estado garantida pelo Pydantic.
"""
from typing import Optional

from app.config import LIMITE_MEMORIAS_IMPORTANTES, LIMITE_MEMORIAS_RECENTES
from app.models.estado import EstadoCompleto, NPC
from app.models.teste import ResultadoTeste
from app.prompts.preencher import preencher
from app.services.formatadores import formatar_npcs_resumo, formatar_teste_gerente
from app.services.ia_client import gerar_json, ErroIA, ErroFormatoIA
from app.services.wiki_gerente import aplicar_patch_wiki

PROMPT = """Você é o Gerente de estado de um RPG. Sua função é decidir como o mundo reage à ação do jogador, NÃO narrar em prosa.

Responda APENAS com um JSON válido, sem texto antes ou depois, sem cercas de código markdown, no formato:
{
  "npc_atualizados": [
    {"id": "id do npc existente", "humor": "novo humor ou null para manter", "relacao_delta": número inteiro pequeno (-3 a 3) ou 0, "novo_segredo": "texto ou null", "ultima_interacao": "resumo curto ou null", "memoria_relacao": "resumo canônico da relação ou null"}
  ],
  "npcs_saem_de_cena": [{"id": "id do NPC presente", "local_ausente": "onde foi parar"}],
  "npcs_entram_em_cena": ["id de NPC ausente que volta a ser relevante"],
  "npc_novo": {"id": "id_curto_unico", "nome": "...", "raca": "...", "aparencia": "...", "humor": "...", "relacao": 0} ou null se nenhum NPC novo apareceu,
  "eventos_novos": ["lista de novos eventos ativos, vazio se nenhum"],
  "eventos_removidos": ["eventos que deixaram de ser ativos, vazio se nenhum"],
  "memoria_importante_nova": "um fato canônico que deve ser lembrado a longo prazo, ou null",
  "progresso_delta": número inteiro entre -5 e 10 representando avanço no arco principal, 0 se nada mudou,
  "local_novo": "novo local ou null se não mudou",
  "hora_nova": "novo horário ou null se não mudou",
  "patch_wiki": {
    "fichas_atualizadas": [{"id": "id da ficha", "campos": {"chave": "valor"}, "conteudo_append": "texto ou null"}],
    "ficha_nova": {"tipo": "tipo válido", "titulo": "..."} ou null,
    "relacao_adicionada": [{"origem": "id", "tipo_relacao": "...", "destino": "id"}],
    "relacao_removida": [{"origem": "id", "tipo_relacao": "...", "destino": "id"}]
  } ou {} se nenhum fato canônico da Wiki mudou
}

Só inclua mudanças que façam sentido causadas pela ação do jogador. Não invente eventos grandes sem motivo.
Quando uma ficha mudar, use patch_wiki. Relações sempre usam IDs; remover uma
relação NÃO apaga a ficha de destino. Não crie patch_wiki para diálogo comum.

[ESTADO ATUAL]
Local: {local} - {hora}
NPCs: {npcs}
Eventos ativos: {eventos}
Progresso da campanha: {progresso}%

[INTERPRETAÇÃO DA AÇÃO DO JOGADOR]
Intenção: {intencao}
Alvo: {alvo}
Tom: {tom}
{resultado_teste}

[MENSAGEM ORIGINAL DO JOGADOR]
"{mensagem}"
"""


def atualizar_estado(
    estado: EstadoCompleto,
    mensagem: str,
    interpretacao: dict,
    resultado_teste: Optional[ResultadoTeste] = None,
) -> EstadoCompleto:
    prompt = preencher(
        PROMPT,
        local=estado.estado.local,
        hora=estado.estado.hora,
        npcs=formatar_npcs_resumo(estado),
        eventos=", ".join(estado.estado.eventos_ativos) or "nenhum",
        progresso=estado.campanha.progresso,
        intencao=interpretacao.get("intencao", ""),
        alvo=interpretacao.get("alvo") or "nenhum",
        tom=interpretacao.get("tom", "neutro"),
        resultado_teste=formatar_teste_gerente(resultado_teste),
        mensagem=mensagem,
    )

    try:
        patch = gerar_json(prompt)
    except (ErroIA, ErroFormatoIA):
        # Se o Gerente falhar, o turno continua sem atualizar NPCs/eventos
        # desta vez, em vez de derrubar a requisição inteira.
        _registrar_memoria_recente(estado, f"Jogador: {mensagem}")
        return estado

    aplicar_patch(estado, patch)
    _registrar_memoria_recente(estado, f"Jogador: {mensagem}")
    return estado


def aplicar_patch(estado: EstadoCompleto, patch: dict) -> None:
    npcs_por_id = {n.id: n for n in estado.estado.npc_ativos + estado.estado.npc_ausentes}

    for atualizacao in patch.get("npc_atualizados") or []:
        if not isinstance(atualizacao, dict):
            continue
        npc = npcs_por_id.get(atualizacao.get("id"))
        if not npc:
            continue
        if atualizacao.get("humor"):
            npc.humor = str(atualizacao["humor"])
        delta = atualizacao.get("relacao_delta") or 0
        if isinstance(delta, (int, float)):
            npc.relacao = max(-10, min(10, npc.relacao + int(delta)))
        if atualizacao.get("novo_segredo"):
            npc.segredos.append(str(atualizacao["novo_segredo"]))
        if atualizacao.get("ultima_interacao"):
            npc.ultima_interacao = str(atualizacao["ultima_interacao"])
        if atualizacao.get("memoria_relacao"):
            npc.memoria_relacao = str(atualizacao["memoria_relacao"])

    npc_novo = patch.get("npc_novo")
    if isinstance(npc_novo, dict) and npc_novo.get("id") not in npcs_por_id:
        try:
            estado.estado.npc_ativos.append(NPC(**npc_novo))
        except Exception:
            pass  # patch malformado para o novo NPC, ignora em vez de travar

    # A presença é uma mudança de estado explícita: o NPC não é apagado ao
    # deixar a cena e, por estar em ``npc_ausentes``, não entra no prompt.
    for saida in patch.get("npcs_saem_de_cena") or []:
        if not isinstance(saida, dict):
            continue
        npc = next((n for n in estado.estado.npc_ativos if n.id == saida.get("id")), None)
        if npc:
            estado.estado.npc_ativos.remove(npc)
            npc.presente = False
            npc.local_ausente = str(saida.get("local_ausente") or "desconhecido")
            estado.estado.npc_ausentes.append(npc)

    for npc_id in patch.get("npcs_entram_em_cena") or []:
        npc = next((n for n in estado.estado.npc_ausentes if n.id == str(npc_id)), None)
        if npc:
            estado.estado.npc_ausentes.remove(npc)
            npc.presente = True
            npc.local_ausente = ""
            estado.estado.npc_ativos.append(npc)

    for evento in patch.get("eventos_novos") or []:
        evento = str(evento)
        if evento and evento not in estado.estado.eventos_ativos:
            estado.estado.eventos_ativos.append(evento)

    for evento in patch.get("eventos_removidos") or []:
        evento = str(evento)
        if evento in estado.estado.eventos_ativos:
            estado.estado.eventos_ativos.remove(evento)

    memoria_nova = patch.get("memoria_importante_nova")
    if memoria_nova:
        estado.estado.memorias_importantes.append(str(memoria_nova))
        estado.estado.memorias_importantes = estado.estado.memorias_importantes[-LIMITE_MEMORIAS_IMPORTANTES:]

    progresso_delta = patch.get("progresso_delta") or 0
    if isinstance(progresso_delta, (int, float)):
        estado.campanha.progresso = max(0, min(100, estado.campanha.progresso + int(progresso_delta)))

    if patch.get("local_novo"):
        estado.estado.local = str(patch["local_novo"])
    if patch.get("hora_nova"):
        estado.estado.hora = str(patch["hora_nova"])

    # A Wiki compartilha o JSON do Gerente, mas mantém modelo e persistência
    # próprios. Um patch malformado é ignorado sem comprometer o turno.
    aplicar_patch_wiki(estado, patch.get("patch_wiki"))


def _registrar_memoria_recente(estado: EstadoCompleto, texto: str) -> None:
    if len(estado.estado.memorias_recentes) >= LIMITE_MEMORIAS_RECENTES:
        estado.estado.memorias_recentes.pop(0)
    resumo = texto if len(texto) <= 120 else texto[:120] + "..."
    estado.estado.memorias_recentes.append(resumo)


def registrar_resposta_mestre(estado: EstadoCompleto, narracao: str) -> None:
    _registrar_memoria_recente(estado, f"Mestre: {narracao}")
