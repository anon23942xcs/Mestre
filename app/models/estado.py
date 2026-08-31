"""
Modelos de dados do estado do jogo.

Mesma ideia do models.py original, mas com dois campos novos importantes:
- EstadoCompleto.campanha_id: identifica a campanha, permite várias
  campanhas/jogadores simultâneos em vez de um único arquivo global.
- EstadoCompleto.turno: contador usado para saber quando rodar o Compilador
  a cada N turnos.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class Atributos(BaseModel):
    forca: int = 5
    destreza: int = 5
    inteligencia: int = 5
    carisma: int = 5


class Jogador(BaseModel):
    nome: str
    idade: int
    genero: str
    aparencia: str
    historico: str
    # Ficha de personagem completa e livre (habilidades, regras próprias,
    # lore, etc.). Fica separada de "historico" porque pode ser bem mais
    # longa; é injetada inteira no prompt do Narrador a cada turno.
    ficha_completa: str = ""
    atributos: Atributos = Field(default_factory=Atributos)
    inventario: List[str] = Field(default_factory=lambda: ["roupas rasgadas"])
    pv: int = 20
    pv_max: int = 20


class NPC(BaseModel):
    id: str
    nome: str
    raca: str
    aparencia: str
    humor: str
    relacao: int = 0
    segredos: List[str] = Field(default_factory=list)
    ultima_interacao: str = ""


class Estado(BaseModel):
    local: str
    regiao: str = "Reino de Valdris"
    hora: str = "manhã"
    clima: str = "normal"
    eventos_ativos: List[str] = Field(default_factory=list)
    npc_ativos: List[NPC] = Field(default_factory=list)
    memorias_recentes: List[str] = Field(default_factory=list)
    memorias_importantes: List[str] = Field(default_factory=list)


class Campanha(BaseModel):
    arco_principal: str = "Em aberto"
    progresso: int = 0
    vilao: Dict[str, str] = Field(default_factory=dict)
    proximos_eventos: List[str] = Field(default_factory=list)


class EstadoCompleto(BaseModel):
    campanha_id: str
    mundo: str = "Fantasia Medieval - Alderan, Reino de Valdris"
    jogador: Jogador
    estado: Estado
    campanha: Campanha = Field(default_factory=Campanha)
    turno: int = 0
    data_criacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    ultima_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())