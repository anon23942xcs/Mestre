"""Perfis de personagem reutilizáveis entre campanhas."""
from datetime import datetime

from pydantic import BaseModel, Field


class Personagem(BaseModel):
    id: str
    nome: str
    idade: int
    genero: str
    aparencia: str
    historico: str = ""
    ficha_completa: str = ""
    imagem: str = ""
    data_criacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    ultima_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())
