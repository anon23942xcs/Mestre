"""Modelo independente da Wiki canônica do mundo."""
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


TipoFicha = Literal[
    "personagem", "local", "raca", "item", "organizacao", "evento",
    "criatura", "divindade", "conceito",
]


class FichaMundo(BaseModel):
    id: str
    tipo: TipoFicha
    titulo: str
    resumo: str = ""
    conteudo: str = ""
    campos: Dict[str, Any] = Field(default_factory=dict)
    imagem: str = ""
    tags: List[str] = Field(default_factory=list)
    # Relações são referências, nunca cópias: {"contem_itens": ["ficha_id"]}.
    relacoes: Dict[str, List[str]] = Field(default_factory=dict)
