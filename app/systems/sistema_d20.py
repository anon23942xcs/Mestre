"""Plugin que encapsula as regras d20 já existentes, sem alterá-las."""
from app.services import dados
from app.systems.base import ResultadoTesteGenerico


class SistemaD20:
    id = "d20"
    nome = "d20 clássico"

    def resolver(self, estado, interpretacao: dict) -> ResultadoTesteGenerico:
        atributo_nome = dados.atributo_para_tipo(interpretacao.get("tipo_acao", "outro"))
        valor_atributo = getattr(estado.jogador.atributos, atributo_nome, 5)
        dificuldade = int(interpretacao.get("dificuldade_sugerida") or 12)
        resultado = dados.resolver_teste(valor_atributo, dificuldade)
        if resultado.critico_sucesso:
            resumo = "Sucesso crítico! A ação deu muito mais certo do que o esperado."
        elif resultado.critico_falha:
            resumo = "Falha crítica! Algo deu muito errado, além do esperado."
        else:
            status = "SUCESSO" if resultado.sucesso else "FALHA"
            resumo = (
                f"{status} (rolagem {resultado.rolagem} + atributo {resultado.atributo} "
                f"= {resultado.total}, contra dificuldade {resultado.dificuldade})"
            )
        return ResultadoTesteGenerico(
            sistema=self.id,
            houve_teste=True,
            sucesso=resultado.sucesso,
            resumo_narrador=resumo,
            detalhes=resultado.model_dump(),
        )

    def formatar_para_narrador(self, resultado: ResultadoTesteGenerico) -> str:
        return resultado.resumo_narrador

    def ficha_padrao(self) -> dict:
        return {"forca": 5, "destreza": 5, "inteligencia": 5, "carisma": 5, "pv": 20, "pv_max": 20}
