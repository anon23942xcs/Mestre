"""Molde canônico de mundo, independente das campanhas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.estado import ConfiguracaoMundo


class Mundo(BaseModel):
    id: str
    nome: str
    descricao: str = ""
    configuracao: ConfiguracaoMundo = Field(default_factory=ConfiguracaoMundo)
    data_criacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    ultima_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())
