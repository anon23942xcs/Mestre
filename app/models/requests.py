"""
Modelos de requisição e resposta da API.

Diferença importante em relação à versão anterior: AcaoRequest não recebe
mais o estado inteiro do cliente. O cliente manda só a mensagem e o
campanha_id; o servidor carrega o estado do disco, que é a única fonte de
verdade. Isso fecha a brecha de um jogador editar pv/atributos/inventário
direto no JavaScript do navegador antes de reenviar.
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.models.estado import EstadoCompleto
from app.models.ficha import TipoFicha
from app.systems.base import ResultadoTesteGenerico


class CriarPersonagemRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    idade: int = Field(ge=1, le=200)
    genero: str = Field(min_length=1, max_length=40)
    aparencia: str = Field(min_length=1, max_length=500)
    historico: str = Field(default="", max_length=4000)
    # Campo livre para colar uma ficha de personagem inteira (habilidades,
    # regras próprias, histórico detalhado, etc.), diferente de "historico"
    # que é pensado para um resumo curto. Vai inteiro para o prompt do
    # Narrador em todo turno, então o personagem não "some" depois da
    # criação.
    ficha_completa: str = Field(default="", max_length=20000)
    cenario: str = Field(default="", max_length=12000)
    personalidade_mestre: str = Field(default="", max_length=8000)
    primeira_mensagem: str = Field(default="", max_length=4000)
    dialogos_exemplo: str = Field(default="", max_length=12000)
    sistema_rpg: bool = True
    sistema_id: str = Field(default="d20", max_length=40)
    d10_limiar_sucesso: int = Field(default=6, ge=2, le=10)


class AcaoRequest(BaseModel):
    mensagem: str = Field(min_length=1, max_length=4000)


class RespostaAcao(BaseModel):
    resposta: str
    estado: EstadoCompleto
    # Erros técnicos (falha de chamada à IA, JSON malformado etc.) ficam
    # aqui, separados do texto narrativo que o jogador lê. Antes, um erro
    # de API virava texto de narração misturado com a ficção.
    erro: Optional[str] = None
    # Contrato agnóstico ao sistema de regras ativo.
    teste: Optional[ResultadoTesteGenerico] = None


class FichaMundoRequest(BaseModel):
    tipo: TipoFicha
    titulo: str = Field(min_length=1, max_length=160)
    resumo: str = Field(default="", max_length=1000)
    conteudo: str = Field(default="", max_length=30000)
    campos: dict = Field(default_factory=dict)
    imagem: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=30)


class PresencaNPCRequest(BaseModel):
    local_ausente: str = Field(default="", max_length=300)
