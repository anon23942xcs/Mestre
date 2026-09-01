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

from app.models.estado import ConfiguracaoMundo, EstadoCompleto, Jogador
from app.models.requests import (
    AcaoRequest,
    CriarPersonagemRequest,
    PresencaNPCRequest,
    RespostaAcao,
)
from app.services import pipeline
from app.services.estado_inicial import criar_estado_inicial
from app.services.fichas_jogador import organizar_ficha_markdown
from app.services.ia_client import ErroIA
from app.storage import personagem_repositorio, repositorio
from app.systems.sistema_d10 import construir_ficha

router = APIRouter(prefix="/campanhas", tags=["campanhas"])


@router.get("")
async def listar_campanhas():
    return repositorio.listar()


@router.post("", response_model=EstadoCompleto)
async def criar_campanha(dados: CriarPersonagemRequest):
    campanha_id = repositorio.novo_id()
    personagem = None
    if dados.personagem_id:
        personagem = personagem_repositorio.carregar(dados.personagem_id)
        if not personagem:
            raise HTTPException(status_code=404, detail="Personagem não encontrado")
    estado = criar_estado_inicial(
        campanha_id,
        Jogador(
            personagem_id=personagem.id if personagem else None,
            nome=(personagem.nome if personagem else dados.nome).strip(),
            idade=personagem.idade if personagem else dados.idade,
            genero=(personagem.genero if personagem else dados.genero).strip(),
            aparencia=(personagem.aparencia if personagem else dados.aparencia).strip(),
            historico=(personagem.historico if personagem else dados.historico).strip(),
            ficha_completa=(personagem.ficha_completa if personagem else dados.ficha_completa).strip(),
            ficha_estruturada=organizar_ficha_markdown(personagem.ficha_completa if personagem else dados.ficha_completa),
            ficha_sistema=(
                construir_ficha(dados.d10_pontos_atributos, dados.d10_atributos_jogador)
                if dados.sistema_rpg and dados.sistema_id.strip() == "d10" else {}
            ),
        ),
        ConfiguracaoMundo(
            sistema_rpg=dados.sistema_rpg,
            sistema_id=dados.sistema_id.strip() if dados.sistema_rpg else "nenhum",
            d10_limiar_sucesso=dados.d10_limiar_sucesso,
            d10_pontos_atributos=dados.d10_pontos_atributos,
            cenario=dados.cenario.strip() or ConfiguracaoMundo().cenario,
            personalidade=dados.personalidade_mestre.strip() or ConfiguracaoMundo().personalidade,
            primeira_mensagem=dados.primeira_mensagem.strip() or ConfiguracaoMundo().primeira_mensagem,
            dialogos_exemplo=dados.dialogos_exemplo.strip() or ConfiguracaoMundo().dialogos_exemplo,
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


@router.post("/{campanha_id}/npcs/{npc_id}/sair", response_model=EstadoCompleto)
async def npc_sair_de_cena(campanha_id: str, npc_id: str, dados: PresencaNPCRequest):
    with repositorio.bloqueio(campanha_id):
        estado = repositorio.carregar(campanha_id)
        if not estado:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
        npc = next((n for n in estado.estado.npc_ativos if n.id == npc_id), None)
        if not npc:
            raise HTTPException(status_code=404, detail="NPC presente não encontrado")
        estado.estado.npc_ativos.remove(npc)
        npc.presente = False
        npc.local_ausente = dados.local_ausente
        estado.estado.npc_ausentes.append(npc)
        repositorio.salvar(estado)
    return estado


@router.post("/{campanha_id}/npcs/{npc_id}/voltar", response_model=EstadoCompleto)
async def npc_voltar_a_cena(campanha_id: str, npc_id: str):
    with repositorio.bloqueio(campanha_id):
        estado = repositorio.carregar(campanha_id)
        if not estado:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
        npc = next((n for n in estado.estado.npc_ausentes if n.id == npc_id), None)
        if not npc:
            raise HTTPException(status_code=404, detail="NPC ausente não encontrado")
        estado.estado.npc_ausentes.remove(npc)
        npc.presente = True
        npc.local_ausente = ""
        estado.estado.npc_ativos.append(npc)
        repositorio.salvar(estado)
    return estado


@router.delete("/{campanha_id}")
async def apagar_campanha(campanha_id: str):
    try:
        apagado = repositorio.deletar(campanha_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")
    if not apagado:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    from app.storage import ficha_repositorio
    ficha_repositorio.deletar_da_campanha(campanha_id)
    return {"mensagem": "Campanha apagada"}
