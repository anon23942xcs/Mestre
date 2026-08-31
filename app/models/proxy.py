from pydantic import BaseModel, Field, field_validator


class ConfiguracaoProxy(BaseModel):
    """Credenciais e prompt do proxy, enviados pelo cliente. Nunca persistidos no servidor."""

    nome: str = Field(default="Padrão", max_length=80)
    url: str = Field(min_length=8, max_length=500)
    chave: str = Field(min_length=1, max_length=800)
    modelo: str = Field(min_length=1, max_length=120)
    prompt_personalizado: str = Field(default="", max_length=50000)

    @field_validator("url")
    @classmethod
    def validar_url(cls, valor: str) -> str:
        # Valida que a URL tem formato básico correto
        valor_limpo = valor.strip()
        if not valor_limpo.startswith(("http://", "https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        if "/" not in valor_limpo[8:]:  # Verifica se há / após http:// ou https://
            raise ValueError("URL inválida")
        return valor_limpo

    @field_validator("chave", "modelo")
    @classmethod
    def tira_espaco(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("campo obrigatório")
        return texto

    @field_validator("nome")
    @classmethod
    def nome_ok(cls, valor: str) -> str:
        return valor.strip() or "Padrão"
