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
    atributos: Atributos = Atributos()
    inventario: List[str] = []
    pv: int = 20
    pv_max: int = 20

class NPC(BaseModel):
    id: str
    nome: str
    raca: str
    aparencia: str
    humor: str
    relacao: int = 0
    segredos: List[str] = []
    ultima_interacao: str = ""

class Estado(BaseModel):
    local: str
    regiao: str = "Reino de Valdris"
    hora: str = "manhã"
    clima: str = "normal"
    eventos_ativos: List[str] = []
    npc_ativos: List[NPC] = []
    memorias_recentes: List[str] = []
    memorias_importantes: List[str] = []

class Campanha(BaseModel):
    arco_principal: str = "Em aberto"
    progresso: int = 0
    vilao: Dict[str, str] = {}
    proximos_eventos: List[str] = []

class EstadoCompleto(BaseModel):
    mundo: str = "Fantasia Medieval - Alderan, Reino de Valdris"
    jogador: Jogador
    estado: Estado
    campanha: Campanha = Campanha()
    data_criacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    ultima_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())