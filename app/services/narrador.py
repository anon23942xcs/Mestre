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
from app.models.teste import ResultadoTeste
from app.prompts.preencher import preencher
from app.services.formatadores import (
    formatar_memorias,
    formatar_npcs_narrativa,
    formatar_teste_narrador,
)
from app.services.ia_client import gerar_texto
from app.services.fichas_jogador import formatar_ficha_estruturada

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
PV: {pv}/{pv_max}

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

[RESULTADO DE TESTE DE DADOS]
{resultado_teste}

[MENSAGEM DO JOGADOR]
"{mensagem}"

[RESPOSTA DO MESTRE]
Escreva a narração em prosa, mantendo a imersão e a coerência. Não controle o jogador.
"""


def narrar(estado: EstadoCompleto, mensagem: str, resultado_teste: Optional[ResultadoTeste] = None) -> str:
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
        pv=estado.jogador.pv,
        pv_max=estado.jogador.pv_max,
        local=estado.estado.local,
        hora=estado.estado.hora,
        clima=estado.estado.clima,
        npcs=formatar_npcs_narrativa(estado),
        eventos=", ".join(estado.estado.eventos_ativos) or "nenhum evento ativo",
        memorias_importantes=formatar_memorias(estado.estado.memorias_importantes, "nenhuma ainda"),
        memorias_recentes=formatar_memorias(estado.estado.memorias_recentes, "nenhum turno recente"),
        cena_anterior=estado.ultima_narracao or "início da campanha",
        resultado_teste=formatar_teste_narrador(resultado_teste),
        mensagem=mensagem,
    )
    texto = gerar_texto(prompt)
    if "```" in texto:
        texto = texto.split("```")[0].strip()
    return texto
