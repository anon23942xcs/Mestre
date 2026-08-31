"""Contrato estável entre o núcleo narrativo e um sistema de RPG."""
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ResultadoTesteGenerico(BaseModel):
    sistema: str
    houve_teste: bool
    sucesso: bool
    resumo_narrador: str
    detalhes: dict = Field(default_factory=dict)


class SistemaRPG(Protocol):
    id: str
    nome: str

    def resolver(self, estado: Any, interpretacao: dict) -> ResultadoTesteGenerico: ...
    def formatar_para_narrador(self, resultado: ResultadoTesteGenerico) -> str: ...
    def ficha_padrao(self) -> dict: ...
