from pydantic import BaseModel


class ResultadoTeste(BaseModel):
    """Resultado de 1d20 + atributo contra uma CD. Decidido em Python, não pela IA."""

    rolagem: int
    atributo: int
    total: int
    dificuldade: int
    sucesso: bool
    critico_sucesso: bool
    critico_falha: bool
