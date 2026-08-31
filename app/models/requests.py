"""
Modelos de requisição e resposta da API.

Diferença importante em relação à versão anterior: AcaoRequest não recebe
mais o estado inteiro do cliente. O cliente manda só a mensagem e o
campanha_id; o servidor carrega o estado do disco, que é a única fonte de
verdade. Isso fecha a brecha de um jogador editar pv/atributos/inventário
direto no JavaScript do navegador antes de reenviar.
"""
from pydantic import BaseModel
from typing import Optional
from app.models.estado import EstadoCompleto


class CriarPersonagemRequest(BaseModel):
    nome: str
    idade: int
    genero: str
    aparencia: str
    historico: str


class AcaoRequest(BaseModel):
    mensagem: str


class RespostaAcao(BaseModel):
    resposta: str
    estado: EstadoCompleto
    # Erros técnicos (falha de chamada à IA, JSON malformado etc.) ficam
    # aqui, separados do texto narrativo que o jogador lê. Antes, um erro
    # de API virava texto de narração misturado com a ficção.
    erro: Optional[str] = None
    # Resultado do teste de dados, quando a ação exigiu um (ver services/dados.py).
    teste: Optional[dict] = None
