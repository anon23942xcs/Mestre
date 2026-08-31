"""Plugin de narrativa pura: não há rolagens nem regras mecânicas."""
from app.systems.base import ResultadoTesteGenerico


class SistemaNenhum:
    id = "nenhum"
    nome = "Narrativa pura"

    def resolver(self, estado, interpretacao: dict) -> ResultadoTesteGenerico:
        return ResultadoTesteGenerico(sistema=self.id, houve_teste=False, sucesso=True, resumo_narrador="")

    def formatar_para_narrador(self, resultado: ResultadoTesteGenerico) -> str:
        return ""

    def ficha_padrao(self) -> dict:
        return {}
