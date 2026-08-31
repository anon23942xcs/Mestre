"""
Orquestrador do pipeline de um turno.

Este módulo é o que faltava para a especificação (seção 3.2, o pipeline de
3 passos + Compilador) virar realidade em vez de só existir no documento.
A ordem é:

1. Intérprete: entende a intenção da mensagem.
2. Se a ação exigir teste, o sistema (não a IA) rola os dados.
3. Gerente: decide como o mundo reage (NPCs, eventos, progresso) via patch.
4. Narrador: escreve a prosa em cima do que os passos 1-3 decidiram.
5. A cada TURNOS_POR_COMPILACAO turnos, o Compilador destila memórias.

Cada passo tem fallback: se um passo de IA falhar, o pipeline não trava o
turno inteiro, ele degrada (por exemplo, sem atualizar NPCs desta vez) e
ainda assim devolve uma resposta ao jogador.

AVISO DE ESCALABILIDADE:
Se adicionar mais de 2-3 novos passos além destes 5, considere refatorar
para factory pattern ou chain of responsibility em vez de continuar
adicionando ifs/imports. Hoje é linear e simples. Com >7-8 passos fica
complexo manter.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.config import TURNOS_POR_COMPILACAO
from app.models.estado import EstadoCompleto
from app.models.teste import ResultadoTeste
from app.services import compilador, dados, gerente, interprete, narrador
from app.services.ia_client import ErroIA


@dataclass
class ResultadoTurno:
    resposta: str
    estado: EstadoCompleto
    erro: Optional[str]
    teste: Optional[ResultadoTeste]


def processar_turno(estado: EstadoCompleto, mensagem: str) -> ResultadoTurno:
    erro: Optional[str] = None

    # Passo 1: Intérprete
    interpretacao = interprete.interpretar(mensagem)

    # Teste de dados, decidido por código, não pela IA
    resultado_teste = None
    if interpretacao.get("requer_teste"):
        atributo_nome = dados.atributo_para_tipo(interpretacao.get("tipo_acao", "outro"))
        valor_atributo = getattr(estado.jogador.atributos, atributo_nome, 5)
        dificuldade = interpretacao.get("dificuldade_sugerida") or 12
        resultado_teste = dados.resolver_teste(valor_atributo, int(dificuldade))

    # Passo 2: Gerente atualiza o estado (NPCs, eventos, progresso)
    estado = gerente.atualizar_estado(estado, mensagem, interpretacao, resultado_teste)

    # Passo 3: Narrador escreve a prosa
    try:
        resposta = narrador.narrar(estado, mensagem, resultado_teste)
    except ErroIA as e:
        resposta = "O Mestre hesita por um momento, tentando organizar os pensamentos... (não foi possível gerar a narração desta vez)"
        erro = str(e)

    gerente.registrar_resposta_mestre(estado, resposta)
    estado.ultima_narracao = resposta
    estado.turno += 1
    estado.ultima_atualizacao = datetime.now().isoformat()

    # Passo 0 (a cada N turnos): Compilador
    if estado.turno % TURNOS_POR_COMPILACAO == 0:
        estado = compilador.compilar(estado)

    return ResultadoTurno(resposta=resposta, estado=estado, erro=erro, teste=resultado_teste)
