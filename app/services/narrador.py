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
from app.systems.base import ResultadoTesteGenerico
from app.prompts.preencher import preencher
from app.services.formatadores import (
    formatar_memorias,
    formatar_npcs_narrativa,
)
from app.services.ia_client import gerar_texto
from app.services.fichas_jogador import formatar_ficha_estruturada

PROMPT = """[INSTRUÇÕES DO MESTRE]
- Você é o Mestre de RPG. Narra a história, controla os NPCs e o mundo.
- NUNCA controle o personagem do jogador nem decida as ações dele.
- NPCs têm personalidades próprias e podem discordar ou negar pedidos.
{instrucao_teste}
- Introduza conflitos quando a história estiver muito parada.
- Limite a resposta a no máximo 4 parágrafos.
- Seja descritivo, mostre emoções através de ações e diálogos, não apenas afirme.
- FORMATAÇÃO OBRIGATÓRIA: toda ação, gesto ou descrição física fica entre asteriscos, e toda fala fica entre aspas. NUNCA coloque uma fala (texto entre aspas) dentro de asteriscos — são marcações separadas, nunca aninhadas. Exemplo de formato CORRETO:
  *A estalajadeira cruza os braços, encarando você com desconfiança.* "A taverna só abre mais tarde," ela resmunga, batendo o pé no chão. *Ela força um sorriso amarelo.* "Mas se quiser esperar, sente-se ali."
  Exemplo ERRADO (não faça isso): *"A taverna só abre mais tarde,"* ela resmunga.
- Use SEMPRE essa mistura de asteriscos e aspas, nunca escreva a cena inteira em um único parágrafo de prosa corrida sem essas marcações.
- Respeite a ficha completa do personagem abaixo (se houver): habilidades, limitações, regras próprias e tom descrito nela têm prioridade sobre suposições genéricas de RPG de fantasia.
- Continue a partir da cena anterior e das memórias recentes. Não reinicie a cena do zero.

[ESTADO DO MUNDO]
Mundo: {mundo}
Cenário: {cenario}
Personalidade do Mestre: {personalidade_mestre}
Diálogos de referência: {dialogos_exemplo}

[JOGADOR]
Nome: {nome}
Aparência: {aparencia}
Histórico: {historico}
Inventário: {inventario}
{bloco_pv}

[FICHA COMPLETA DO PERSONAGEM]
{ficha_completa}

[LOCAL]
{local} - {hora}, clima {clima}

[NPCs PRESENTES]
{npcs}

[EVENTOS ATIVOS]
{eventos}

[MEMÓRIAS IMPORTANTES]
{memorias_importantes}

[TURNOS RECENTES]
{memorias_recentes}

[CENA ANTERIOR]
{cena_anterior}

{bloco_teste}

[MENSAGEM DO JOGADOR]
"{mensagem}"

[RESPOSTA DO MESTRE]
Escreva a narração em prosa, mantendo a imersão e a coerência. Não controle o jogador.
"""


def narrar(estado: EstadoCompleto, mensagem: str, resultado_teste: Optional[ResultadoTesteGenerico] = None) -> str:
    sistema_rpg = estado.configuracao_mundo.sistema_rpg
    prompt = preencher(
        PROMPT,
        mundo=estado.mundo,
        nome=estado.jogador.nome,
        aparencia=estado.jogador.aparencia,
        historico=estado.jogador.historico,
        ficha_completa=formatar_ficha_estruturada(estado.jogador.ficha_estruturada, estado.jogador.ficha_completa),
        cenario=estado.configuracao_mundo.cenario,
        personalidade_mestre=estado.configuracao_mundo.personalidade,
        dialogos_exemplo=estado.configuracao_mundo.dialogos_exemplo,
        inventario=", ".join(estado.jogador.inventario) or "nenhum",
        instrucao_teste=(
            "- Se houver um resultado de teste de dados abaixo, a narrativa DEVE refletir esse resultado exatamente (sucesso ou falha), você não decide isso, o sistema já decidiu."
            if sistema_rpg else
            "- Esta é uma narrativa pura: nunca mencione PV, HP, dados, rolagens, CDs ou testes."
        ),
        bloco_pv=f"PV: {estado.jogador.pv}/{estado.jogador.pv_max}" if sistema_rpg else "",
        local=estado.estado.local,
        hora=estado.estado.hora,
        clima=estado.estado.clima,
        npcs=formatar_npcs_narrativa(estado),
        eventos=", ".join(estado.estado.eventos_ativos) or "nenhum evento ativo",
        memorias_importantes=formatar_memorias(estado.estado.memorias_importantes, "nenhuma ainda"),
        memorias_recentes=formatar_memorias(estado.estado.memorias_recentes, "nenhum turno recente"),
        cena_anterior=estado.ultima_narracao or "início da campanha",
        bloco_teste=(
            f"[RESULTADO DO SISTEMA DE REGRAS]\n{resultado_teste.resumo_narrador}"
            if sistema_rpg and resultado_teste and resultado_teste.houve_teste else ""
        ),
        mensagem=mensagem,
    )
    texto = gerar_texto(prompt)
    if "```" in texto:
        texto = texto.split("```")[0].strip()
    return texto
