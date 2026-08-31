"""
Passo 3: Narrador.

Parecido com o gerar_resposta() original, mas com duas diferenças:
1. Recebe o resultado do teste de dados (quando houve) já decidido pelo
   módulo services/dados.py, e é instruído a narrar em cima desse resultado,
   não a decidir sozinho se o jogador teve sucesso. Isso fecha a brecha de
   "a IA nunca diz não" que a especificação queria evitar no Modo Mestre.
2. Não mistura mais texto de erro técnico com narrativa: erros de IA sobem
   como exceção e quem decide o que mostrar ao jogador é o pipeline/router,
   não este módulo.
"""
from typing import Optional

from app.models.estado import EstadoCompleto
from app.services.ia_client import gerar_texto

PROMPT = """[INSTRUÇÕES DO MESTRE]
- Você é o Mestre de RPG. Narra a história, controla os NPCs e o mundo.
- NUNCA controle o personagem do jogador nem decida as ações dele.
- NPCs têm personalidades próprias e podem discordar ou negar pedidos.
- Se houver um resultado de teste de dados abaixo, a narrativa DEVE refletir esse resultado exatamente (sucesso ou falha), você não decide isso, o sistema já decidiu.
- Introduza conflitos quando a história estiver muito parada.
- Limite a resposta a no máximo 4 parágrafos.
- Seja descritivo, mostre emoções através de ações e diálogos, não apenas afirme.
- FORMATAÇÃO OBRIGATÓRIA: toda ação, gesto ou descrição física fica entre asteriscos, e toda fala fica entre aspas. NUNCA coloque uma fala (texto entre aspas) dentro de asteriscos — são marcações separadas, nunca aninhadas. Exemplo de formato CORRETO:
  *A estalajadeira cruza os braços, encarando você com desconfiança.* "A taverna só abre mais tarde," ela resmunga, batendo o pé no chão. *Ela força um sorriso amarelo.* "Mas se quiser esperar, sente-se ali."
  Exemplo ERRADO (não faça isso): *"A taverna só abre mais tarde,"* ela resmunga.
- Use SEMPRE essa mistura de asteriscos e aspas, nunca escreva a cena inteira em um único parágrafo de prosa corrida sem essas marcações.
- Respeite a ficha completa do personagem abaixo (se houver): habilidades, limitações, regras próprias e tom descrito nela têm prioridade sobre suposições genéricas de RPG de fantasia.

[ESTADO DO MUNDO]
Mundo: {mundo}

[JOGADOR]
Nome: {nome}
Aparência: {aparencia}
Histórico: {historico}
Ficha completa do personagem: {ficha_completa}
Inventário: {inventario}
PV: {pv}/{pv_max}

[LOCAL]
{local} - {hora}, clima {clima}

[NPCs PRESENTES]
{npcs}

[EVENTOS ATIVOS]
{eventos}

[MEMÓRIAS IMPORTANTES]
{memorias_importantes}

[RESULTADO DE TESTE DE DADOS]
{resultado_teste}

[MENSAGEM DO JOGADOR]
"{mensagem}"

[RESPOSTA DO MESTRE]
Escreva a narração em prosa, mantendo a imersão e a coerência. Não controle o jogador.
"""


def _formatar_npcs(estado: EstadoCompleto) -> str:
    if not estado.estado.npc_ativos:
        return "nenhum"
    linhas = [
        f"- {n.nome} ({n.raca}): {n.aparencia} - humor: {n.humor}, relação: {n.relacao}/10"
        for n in estado.estado.npc_ativos
    ]
    return "\n".join(linhas)


def _formatar_resultado_teste(resultado_teste: Optional[dict]) -> str:
    if not resultado_teste:
        return "Nenhum teste foi necessário para esta ação."
    if resultado_teste["critico_sucesso"]:
        return "Sucesso crítico! A ação deu muito mais certo do que o esperado."
    if resultado_teste["critico_falha"]:
        return "Falha crítica! Algo deu muito errado, além do esperado."
    status = "SUCESSO" if resultado_teste["sucesso"] else "FALHA"
    return f"{status} (rolagem {resultado_teste['rolagem']} + atributo {resultado_teste['atributo']} = {resultado_teste['total']}, contra dificuldade {resultado_teste['dificuldade']})"


def narrar(estado: EstadoCompleto, mensagem: str, resultado_teste: Optional[dict] = None) -> str:
    prompt = PROMPT.format(
        mundo=estado.mundo,
        nome=estado.jogador.nome,
        aparencia=estado.jogador.aparencia,
        historico=estado.jogador.historico,
        ficha_completa=estado.jogador.ficha_completa or "nenhuma ficha adicional além do histórico acima",
        inventario=", ".join(estado.jogador.inventario) or "nenhum",
        pv=estado.jogador.pv,
        pv_max=estado.jogador.pv_max,
        local=estado.estado.local,
        hora=estado.estado.hora,
        clima=estado.estado.clima,
        npcs=_formatar_npcs(estado),
        eventos=", ".join(estado.estado.eventos_ativos) or "nenhum evento ativo",
        memorias_importantes=", ".join(estado.estado.memorias_importantes) or "nenhuma ainda",
        resultado_teste=_formatar_resultado_teste(resultado_teste),
        mensagem=mensagem,
    )
    texto = gerar_texto(prompt)
    if "```" in texto:
        texto = texto.split("```")[0].strip()
    return texto