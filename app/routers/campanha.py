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

from app.models.estado import EstadoCompleto, Jogador, MensagemChat
from app.models.requests import (
    AcaoRequest,
    CriarPersonagemRequest,
    EditarMensagemRequest,
    EditarNarracaoRequest,
    PresencaNPCRequest,
    RespostaAcao,
)
from app.services import pipeline
from app.services.estado_inicial import criar_estado_inicial
from app.services.fichas_jogador import organizar_ficha_markdown
from app.services.ia_client import ErroIA
from app.storage import ficha_repositorio, mundo_repositorio, personagem_repositorio, repositorio
from app.systems.sistema_d10 import construir_ficha

router = APIRouter(prefix="/campanhas", tags=["campanhas"])


@router.get("")
async def listar_campanhas():
    return repositorio.listar()


@router.post("", response_model=EstadoCompleto)
async def criar_campanha(dados: CriarPersonagemRequest):
    campanha_id = repositorio.novo_id()
    mundo = mundo_repositorio.carregar(dados.mundo_id)
    if not mundo:
        raise HTTPException(status_code=404, detail="Mundo não encontrado")
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
                construir_ficha(mundo.configuracao.d10_pontos_atributos, dados.d10_atributos_jogador)
                if mundo.configuracao.sistema_rpg and mundo.configuracao.sistema_id == "d10" else {}
            ),
        ),
        mundo.configuracao.model_copy(deep=True),
        mundo_id=mundo.id,
        mundo_nome=mundo.nome,
    )
    ficha_repositorio.copiar_fichas(f"mundo_{mundo.id}", f"campanha_{campanha_id}")
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

    if not estado.historico_chat:
        nome_jogador = estado.jogador.nome if estado.jogador and estado.jogador.nome else "Jogador"
        nome_mestre = "Mestre"
        if estado.configuracao_mundo.primeira_mensagem:
            primeira = estado.configuracao_mundo.primeira_mensagem.replace("{{user}}", nome_jogador)
            estado.historico_chat.append(MensagemChat(autor="mestre", nome=nome_mestre, conteudo=primeira))
        if estado.ultima_narracao and estado.ultima_narracao != estado.configuracao_mundo.primeira_mensagem:
            estado.historico_chat.append(MensagemChat(autor="mestre", nome=nome_mestre, conteudo=estado.ultima_narracao))
        repositorio.salvar(estado)

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
    ficha_repositorio.deletar_escopo(f"campanha_{campanha_id}")
    return {"mensagem": "Campanha apagada"}


@router.put("/{campanha_id}/narracao", response_model=EstadoCompleto)
async def editar_ultima_narracao(campanha_id: str, dados: EditarNarracaoRequest):
    nova_narracao = dados.narracao.strip()
    if not nova_narracao:
        raise HTTPException(status_code=400, detail="Narração não pode ser vazia")

    try:
        with repositorio.bloqueio(campanha_id):
            estado = repositorio.carregar(campanha_id)
            if not estado:
                raise HTTPException(status_code=404, detail="Campanha não encontrada")
            estado.ultima_narracao = nova_narracao
            # Atualiza o resumo da última resposta do Mestre na memória de curto prazo se existir
            if estado.estado.memorias_recentes:
                for i in range(len(estado.estado.memorias_recentes) - 1, -1, -1):
                    if estado.estado.memorias_recentes[i].startswith("Mestre:"):
                        estado.estado.memorias_recentes[i] = f"Mestre: {nova_narracao[:180]}"
                        break
            # Também atualiza no historico_chat a última mensagem do mestre se houver
            if estado.historico_chat:
                for i in range(len(estado.historico_chat) - 1, -1, -1):
                    if estado.historico_chat[i].autor == "mestre":
                        estado.historico_chat[i].conteudo = nova_narracao
                        break
            repositorio.salvar(estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")

    return estado


@router.put("/{campanha_id}/mensagens/{mensagem_id}", response_model=EstadoCompleto)
async def editar_mensagem(campanha_id: str, mensagem_id: str, dados: EditarMensagemRequest):
    novo_conteudo = dados.conteudo.strip()
    if not novo_conteudo:
        raise HTTPException(status_code=400, detail="Conteúdo não pode ser vazio")

    try:
        with repositorio.bloqueio(campanha_id):
            estado = repositorio.carregar(campanha_id)
            if not estado:
                raise HTTPException(status_code=404, detail="Campanha não encontrada")

            msg_encontrada = None
            for msg in estado.historico_chat:
                if msg.id == mensagem_id:
                    msg.conteudo = novo_conteudo
                    msg_encontrada = msg
                    break

            if not msg_encontrada:
                raise HTTPException(status_code=404, detail="Mensagem não encontrada")

            # Se for a última mensagem do mestre, atualiza ultima_narracao
            if estado.historico_chat and estado.historico_chat[-1].id == mensagem_id and msg_encontrada.autor == "mestre":
                estado.ultima_narracao = novo_conteudo

            repositorio.salvar(estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")

    return estado


@router.delete("/{campanha_id}/mensagens/{mensagem_id}", response_model=EstadoCompleto)
async def apagar_mensagem_e_subsequentes(campanha_id: str, mensagem_id: str):
    """Apaga a mensagem especificada e TODAS as mensagens que vierem abaixo dela na conversa."""
    try:
        with repositorio.bloqueio(campanha_id):
            estado = repositorio.carregar(campanha_id)
            if not estado:
                raise HTTPException(status_code=404, detail="Campanha não encontrada")

            indice = None
            for i, msg in enumerate(estado.historico_chat):
                if msg.id == mensagem_id:
                    indice = i
                    break

            if indice is None:
                raise HTTPException(status_code=404, detail="Mensagem não encontrada")

            # Trunca o histórico até o ponto anterior à mensagem
            estado.historico_chat = estado.historico_chat[:indice]

            # Recalcula ultima_narracao com base na última mensagem do mestre restante
            ultima_ia = next((m.conteudo for m in reversed(estado.historico_chat) if m.autor == "mestre"), None)
            if ultima_ia:
                estado.ultima_narracao = ultima_ia
            elif estado.configuracao_mundo and estado.configuracao_mundo.primeira_mensagem:
                nome_jog = estado.jogador.nome if estado.jogador and estado.jogador.nome else "Jogador"
                estado.ultima_narracao = estado.configuracao_mundo.primeira_mensagem.replace("{{user}}", nome_jog)
            else:
                estado.ultima_narracao = ""

            # Recalcula turnos pelo número de ações do jogador
            estado.turno = sum(1 for m in estado.historico_chat if m.autor == "jogador")
            repositorio.salvar(estado)
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")

    return estado


@router.post("/{campanha_id}/regenerar", response_model=RespostaAcao)
async def regenerar_ultimo_turno(campanha_id: str):
    """Regenera a resposta do Mestre para a última ação do jogador."""
    try:
        with repositorio.bloqueio(campanha_id):
            estado = repositorio.carregar(campanha_id)
            if not estado:
                raise HTTPException(status_code=404, detail="Campanha não encontrada")

            # Se a última mensagem for do Mestre, remove-a
            if estado.historico_chat and estado.historico_chat[-1].autor == "mestre":
                estado.historico_chat.pop()

            # Encontra a última mensagem do jogador
            if not estado.historico_chat or estado.historico_chat[-1].autor != "jogador":
                raise HTTPException(status_code=400, detail="Nenhuma ação do jogador para regenerar")

            ultimo_jogador = estado.historico_chat.pop()
            msg_acao = ultimo_jogador.conteudo

            # Reverte o contador de turno para que processar_turno incremente corretamente
            if estado.turno > 0:
                estado.turno -= 1

            try:
                resultado = pipeline.processar_turno(estado, msg_acao)
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


@router.post("/{campanha_id}/sincronizar_wiki")
async def sincronizar_wiki_endpoint(campanha_id: str):
    """Analisa acontecimentos recentes e sincroniza imediatamente fichas da Wiki, jogador e memórias."""
    try:
        with repositorio.bloqueio(campanha_id):
            estado = repositorio.carregar(campanha_id)
            if not estado:
                raise HTTPException(status_code=404, detail="Campanha não encontrada")

            from app.services.compilador import compilar_e_sincronizar_wiki
            resultado = compilar_e_sincronizar_wiki(estado)
            repositorio.salvar(resultado["estado"])
    except ValueError:
        raise HTTPException(status_code=400, detail="campanha_id inválido")

    return resultado



