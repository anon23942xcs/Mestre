from typing import Optional

from app.models.estado import EstadoCompleto
from app.models.teste import ResultadoTeste
from app.systems.base import ResultadoTesteGenerico


def formatar_npcs_resumo(estado: EstadoCompleto) -> str:
    if not estado.estado.npc_ativos:
        return "nenhum"
    return "; ".join(
        f"{n.id}:{n.nome} (humor: {n.humor}, relação: {n.relacao})"
        for n in estado.estado.npc_ativos
    )


def formatar_npcs_narrativa(estado: EstadoCompleto) -> str:
    if not estado.estado.npc_ativos:
        return "nenhum"
    return "\n".join(
        f"- {n.nome} ({n.raca}): {n.aparencia} - humor: {n.humor}, relação: {n.relacao}/10"
        + (f". Memória da relação: {n.memoria_relacao}" if n.memoria_relacao else "")
        for n in estado.estado.npc_ativos
    )


def formatar_teste_gerente(resultado: Optional[ResultadoTesteGenerico]) -> str:
    if not resultado:
        return ""
    return resultado.resumo_narrador if resultado.houve_teste else ""


def formatar_teste_narrador(resultado: Optional[ResultadoTeste]) -> str:
    if not resultado:
        return "Nenhum teste foi necessário para esta ação."
    if resultado.critico_sucesso:
        return "Sucesso crítico! A ação deu muito mais certo do que o esperado."
    if resultado.critico_falha:
        return "Falha crítica! Algo deu muito errado, além do esperado."
    status = "SUCESSO" if resultado.sucesso else "FALHA"
    return (
        f"{status} (rolagem {resultado.rolagem} + atributo {resultado.atributo} "
        f"= {resultado.total}, contra dificuldade {resultado.dificuldade})"
    )


def formatar_memorias(itens: list[str], vazio: str) -> str:
    return "\n".join(f"- {m}" for m in itens) if itens else vazio
