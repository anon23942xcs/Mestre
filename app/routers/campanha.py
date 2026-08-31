"""
Rotas de campanha.

Diferença principal em relação ao main.py original: /acao não recebe mais
o estado no corpo da requisição. O cliente manda só a mensagem, o servidor
carrega o estado a partir do campanha_id salvo no disco. Isso remove a
possibilidade de o jogador adulterar pv/atributos/inventário editando o
JavaScript no navegador antes de reenviar, já que o navegador não é mais
a fonte de verdade.

Também dá suporte a várias campanhas simultâneas, uma por campanha_id, em
vez do antigo arquivo global único.
"""
from fastapi import APIRouter, HTTPException

from app.models.estado import EstadoCompleto, Jogador, Estado, Campanha
from app.models.requests import CriarPersonagemRequest, AcaoRequest, RespostaAcao
from app.storage import repositorio
from app.services import pipeline
from app.services.ia_client import ErroIA

router = APIRouter(prefix="/campanhas", tags=["campanhas"])


@router.post("", response_model=EstadoCompleto)
async def criar_campanha(dados: CriarPersonagemRequest):
    campanha_id = repositorio.novo_id()
    estado = EstadoCompleto(
        campanha_id=campanha_id,
        jogador=Jogador(
            nome=dados.nome,
            idade=dados.idade,
            genero=dados.genero,
            aparencia=dados.aparencia,
            historico=dados.historico,
        ),
        estado=Estado(
            local="Taverna do Cão Caído - Alderan",
            clima="nublado",
            npc_ativos=[
                {
                    "id": "npc_001",
                    "nome": "Estalajadeira",
                    "raca": "humano",
                    "aparencia": "mulher robusta, avental manchado, cabelo preso",
                    "humor": "indiferente",
                    "relacao": 0,
                    "segredos": [],
                    "ultima_interacao": "observa o novo cliente",
                }
            ],
        ),
        campanha=Campanha(arco_principal="Em busca de vingança"),
    )
    repositorio.salvar(estado)
    return estado


@router.post("/{campanha_id}/acao", response_model=RespostaAcao)
async def processar_acao(campanha_id: str, requisicao: AcaoRequest):
    if not requisicao.mensagem.strip():
        raise HTTPException(status_code=400, detail="Mensagem obrigatória")

    estado = repositorio.carregar(campanha_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    try:
        resultado = pipeline.processar_turno(estado, requisicao.mensagem)
    except ErroIA as e:
        raise HTTPException(status_code=502, detail=f"Erro ao falar com a IA: {e}")

    repositorio.salvar(resultado.estado)

    return RespostaAcao(
        resposta=resultado.resposta,
        estado=resultado.estado,
        erro=resultado.erro,
        teste=resultado.teste,
    )


@router.get("/{campanha_id}", response_model=EstadoCompleto)
async def obter_campanha(campanha_id: str):
    estado = repositorio.carregar(campanha_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return estado


@router.delete("/{campanha_id}")
async def apagar_campanha(campanha_id: str):
    apagado = repositorio.deletar(campanha_id)
    if not apagado:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return {"mensagem": "Campanha apagada"}
