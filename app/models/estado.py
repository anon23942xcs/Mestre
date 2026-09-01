"""
Modelos de dados do estado do jogo.

Mesma ideia do models.py original, mas com dois campos novos importantes:
- EstadoCompleto.campanha_id: identifica a campanha, permite várias
  campanhas/jogadores simultâneos em vez de um único arquivo global.
- EstadoCompleto.turno: contador usado para saber quando rodar o Compilador
  a cada N turnos.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import uuid



class Atributos(BaseModel):
    forca: int = 5
    destreza: int = 5
    inteligencia: int = 5
    carisma: int = 5


class Jogador(BaseModel):
    # Referência opcional ao perfil reutilizável de origem. A campanha mantém
    # uma cópia para que PV, inventário e evolução não vazem para outra mesa.
    personagem_id: Optional[str] = None
    nome: str
    idade: int
    genero: str
    aparencia: str
    historico: str
    # Ficha de personagem completa e livre (habilidades, regras próprias,
    # lore, etc.). Fica separada de "historico" porque pode ser bem mais
    # longa; é injetada inteira no prompt do Narrador a cada turno.
    ficha_completa: str = ""
    # Texto fonte preservado acima; esta cópia por seções é a que o Narrador
    # consome, para que regras extensas não virem uma única string opaca.
    ficha_estruturada: Dict[str, str] = Field(default_factory=dict)
    # Espaço de ficha próprio de cada plugin; o d20 ainda usa Atributos
    # durante a transição, mas sistemas novos não precisarão mudar o núcleo.
    ficha_sistema: Dict[str, object] = Field(default_factory=dict)
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
    # Um NPC ausente continua persistido, mas não é incluído no prompt.
    presente: bool = True
    local_ausente: str = ""
    ficha_catalogo_id: Optional[str] = None
    memoria_relacao: str = ""
    # Espaço reservado para regras específicas do sistema ativo. Mantido
    # opcional para campanhas já salvas antes da existência das fichas de NPC.
    ficha_sistema: Dict[str, object] = Field(default_factory=dict)




class Estado(BaseModel):
    local: str
    regiao: str = "Reino de Valdris"
    hora: str = "manhã"
    clima: str = "normal"
    eventos_ativos: List[str] = Field(default_factory=list)
    # ``npc_ativos`` contém exclusivamente quem está na cena atual.
    npc_ativos: List[NPC] = Field(default_factory=list)
    npc_ausentes: List[NPC] = Field(default_factory=list)
    memorias_recentes: List[str] = Field(default_factory=list)
    memorias_importantes: List[str] = Field(default_factory=list)


class Campanha(BaseModel):
    arco_principal: str = "Em aberto"
    progresso: int = 0
    vilao: Dict[str, str] = Field(default_factory=dict)
    proximos_eventos: List[str] = Field(default_factory=list)


class ConfiguracaoMundo(BaseModel):
    # Mantém compatibilidade com campanhas existentes: RPG é o padrão.
    sistema_rpg: bool = True
    sistema_id: str = "d20"
    d10_limiar_sucesso: int = 6
    d10_pontos_atributos: List[int] = Field(default_factory=lambda: [4, 3, 2])
    cenario: str = "Um mundo à espera de uma história."
    personalidade: str = "Um Mestre imparcial, descritivo e atento às escolhas do jogador."
    primeira_mensagem: str = "A aventura começa. O que você deseja fazer?"
    dialogos_exemplo: str = "*O mundo responde às escolhas do personagem.*"


class MensagemChat(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    autor: str  # "jogador" ou "mestre"
    nome: str
    conteudo: str
    data: str = Field(default_factory=lambda: datetime.now().isoformat())


class EstadoCompleto(BaseModel):
    campanha_id: str
    mundo_id: Optional[str] = None
    mundo: str = "Mundo sem título"
    configuracao_mundo: ConfiguracaoMundo = Field(default_factory=ConfiguracaoMundo)
    jogador: Jogador
    estado: Estado
    campanha: Campanha = Field(default_factory=Campanha)
    turno: int = 0
    # Última prosa do Narrador. Serve para retomar a cena ao recarregar a
    # página e como contexto imediato no turno seguinte.
    ultima_narracao: str = ""
    # Histórico persistente e sequencial de todas as mensagens do chat
    historico_chat: List[MensagemChat] = Field(default_factory=list)
    data_criacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    ultima_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())

