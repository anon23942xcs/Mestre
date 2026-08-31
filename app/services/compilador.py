"""
Compilador de memórias (Passo 0, a cada N turnos).

Não existia nenhuma versão disso no código anterior, mesmo sendo citado na
especificação como diferencial ("Memória Compilada"). memorias_recentes
crescia com um FIFO simples que só descartava, sem nunca resumir o que
importava para memorias_importantes. Esta função fecha essa lacuna.
"""
from app.config import LIMITE_MEMORIAS_IMPORTANTES
from app.models.estado import EstadoCompleto
from app.prompts.preencher import preencher
from app.services.ia_client import gerar_json, ErroIA, ErroFormatoIA

PROMPT = """Você resume o progresso recente de uma campanha de RPG em fatos canônicos de longo prazo.

Responda APENAS com um JSON válido, sem texto antes ou depois, sem cercas de código markdown, no formato:
{"memorias_importantes": ["fato canônico 1", "fato canônico 2", ...]}

Regras:
- No máximo {limite} memórias importantes no total.
- Descarte detalhes triviais (conversas pequenas, deslocamentos sem consequência).
- Mantenha apenas o que muda o rumo da história: decisões do jogador, mortes, traições, segredos revelados, alianças formadas.
- Combine as memórias importantes já existentes com o que aconteceu nos últimos turnos, sem duplicar.

[MEMÓRIAS IMPORTANTES JÁ EXISTENTES]
{existentes}

[ÚLTIMOS TURNOS]
{recentes}
"""


def compilar(estado: EstadoCompleto) -> EstadoCompleto:
    if not estado.estado.memorias_recentes:
        return estado

    prompt = preencher(
        PROMPT,
        limite=LIMITE_MEMORIAS_IMPORTANTES,
        existentes="\n".join(estado.estado.memorias_importantes) or "nenhuma ainda",
        recentes="\n".join(estado.estado.memorias_recentes),
    )

    try:
        resultado = gerar_json(prompt)
        novas = resultado.get("memorias_importantes")
        if isinstance(novas, list) and novas:
            estado.estado.memorias_importantes = [str(m) for m in novas][:LIMITE_MEMORIAS_IMPORTANTES]
    except (ErroIA, ErroFormatoIA):
        # Se a compilação falhar, mantém as memórias importantes como
        # estavam, só não trava o turno por causa disso.
        pass

    # As memórias recentes já foram digeridas (ou tentamos digerir),
    # esvazia para começar a próxima janela de turnos.
    estado.estado.memorias_recentes = []
    return estado
