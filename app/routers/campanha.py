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

from app.models.estado import EstadoCompleto, Jogador
from app.models.requests import AcaoRequest, CriarPersonagemRequest, RespostaAcao
from app.services import pipeline
from app.services.estado_inicial import criar_estado_inicial
from app.services.ia_client import ErroIA
from app.storage import repositorio

router = APIRouter(prefix="/campanhas", tags=["campanhas"])


@router.get("")
async def listar_campanhas():
    return repositorio.listar()


@router.post("", response_model=EstadoCompleto)
async def criar_campanha(dados: CriarPersonagemRequest):
    campanha_id = repositorio.novo_id()
    estado = criar_estado_inicial(
        campanha_id,
        Jogador(
            nome=dados.nome.strip(),
            idade=dados.idade,
            genero=dados.genero.strip(),
            aparencia=dados.aparencia.strip(),
            historico=dados.historico.strip(),
            ficha_completa=dados.ficha_completa.strip(),
        ),
    )
    repositorio.salvar(estado)
    return estado


@router.post("/{campanha_id}/acao", response_model=RespostaAcao)
async def processar_acao(campanha_id: str, requisicao: AcaoRequest):
    mensagem = requisicao.mensagem.strip()
    if not mensagem:
        raise HTTPException(status_code=400, detail="Mensagem obrigatória")

    try:
        with repositorio.bloqueio(campanha_id):
            estado = repositorio.carregar(campanha_id)
            if not estado:
                raise HTTPException(status_code=404, detail="Campanha não encontrada")

            try:
                resultado = pipeline.processar_turno(estado, mensagem)
            except ErroIA as e:
                raise HTTPException(status_code=502, detail=f"Erro ao falar com a IA: {e}")

            repositorio.salvar(resultado.estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")

    return RespostaAcao(
        resposta=resultado.resposta,
        estado=resultado.estado,
        erro=resultado.erro,
        teste=resultado.teste,
    )


@router.get("/{campanha_id}", response_model=EstadoCompleto)
async def obter_campanha(campanha_id: str):
    try:
        estado = repositorio.carregar(campanha_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")
    if not estado:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return estado


@router.delete("/{campanha_id}")
async def apagar_campanha(campanha_id: str):
    try:
        apagado = repositorio.deletar(campanha_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")
    if not apagado:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return {"mensagem": "Campanha apagada"}
