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

from app.config import LIMITE_HISTORICO_CHAT, TURNOS_POR_COMPILACAO
from app.models.estado import EstadoCompleto, MensagemChat
from app.services import compilador, gerente, interprete, narrador
from app.services.ia_client import ErroIA
from app.systems.base import ResultadoTesteGenerico
from app.systems.registro import obter_sistema


@dataclass
class ResultadoTurno:
    resposta: str
    estado: EstadoCompleto
    erro: Optional[str]
    teste: Optional[ResultadoTesteGenerico]
    # As mensagens adicionadas neste turno (jogador + mestre), para que o
    # front-end possa appendá-las sem re-parsear o histórico inteiro.
    mensagens_novas: list[MensagemChat] = None


def processar_turno(estado: EstadoCompleto, mensagem: str) -> ResultadoTurno:
    erro: Optional[str] = None

    # Passo 1: Intérprete
    interpretacao = interprete.interpretar(mensagem)

    # O pipeline só conhece o contrato do plugin, nunca regras/atributos d20.
    resultado_teste = None
    if estado.configuracao_mundo.sistema_rpg and interpretacao.get("requer_teste"):
        sistema = obter_sistema(estado.configuracao_mundo.sistema_id)
        resultado_teste = sistema.resolver(estado, interpretacao)

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

    # Histórico persistente de mensagens da conversa
    nome_jogador = estado.jogador.nome if estado.jogador and estado.jogador.nome else "Jogador"
    nome_mestre = (getattr(estado.configuracao_mundo, "nome_mestre", "") or "Mestre").strip() or "Mestre"
    
    if not estado.historico_chat and estado.configuracao_mundo and estado.configuracao_mundo.primeira_mensagem:
        primeira = estado.configuracao_mundo.primeira_mensagem.replace("{{user}}", nome_jogador)
        estado.historico_chat.append(MensagemChat(autor="mestre", nome=nome_mestre, conteudo=primeira))

    estado.historico_chat.append(MensagemChat(autor="jogador", nome=nome_jogador, conteudo=mensagem))
    msg_mestre = MensagemChat(autor="mestre", nome=nome_mestre, conteudo=resposta)
    estado.historico_chat.append(msg_mestre)
    novas = [estado.historico_chat[-2], msg_mestre]

    # Poda mensagens antigas para manter o JSON leve. A primeira mensagem
    # (abertura do mundo) é sempre preservada.
    if len(estado.historico_chat) > LIMITE_HISTORICO_CHAT:
        primeira = estado.historico_chat[0]
        estado.historico_chat = [primeira] + estado.historico_chat[-(LIMITE_HISTORICO_CHAT - 1):]

    # Passo 0 (a cada N turnos): Compilador
    if estado.turno % TURNOS_POR_COMPILACAO == 0:
        estado = compilador.compilar(estado)

    return ResultadoTurno(resposta=resposta, estado=estado, erro=erro, teste=resultado_teste, mensagens_novas=novas)
