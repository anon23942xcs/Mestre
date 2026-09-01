from app.models.estado import Jogador
from app.services.estado_inicial import criar_estado_inicial
from app.storage import repositorio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_editar_ultima_narracao():
    cid = repositorio.novo_id()
    estado = criar_estado_inicial(cid, Jogador(nome='Mike', idade=18, genero='M', aparencia='alto', historico='viajante'))
    estado.ultima_narracao = 'Texto antigo do Mestre'
    repositorio.salvar(estado)

    resp = client.put(f'/campanhas/{estado.campanha_id}/narracao', json={'narracao': 'Texto editado pelo jogador'})
    assert resp.status_code == 200
    dados = resp.json()
    assert dados['ultima_narracao'] == 'Texto editado pelo jogador'

    carregado = repositorio.carregar(estado.campanha_id)
    assert carregado.ultima_narracao == 'Texto editado pelo jogador'

    repositorio.deletar(estado.campanha_id)


def test_editar_e_deletar_mensagem_cascata():
    from app.models.estado import MensagemChat
    cid = repositorio.novo_id()
    estado = criar_estado_inicial(cid, Jogador(nome='Mike', idade=18, genero='M', aparencia='alto', historico='viajante'))
    msg1 = MensagemChat(id="msg_1", autor="mestre", nome="Olive", conteudo="Primeira cena")
    msg2 = MensagemChat(id="msg_2", autor="jogador", nome="Mike", conteudo="Minha primeira ação")
    msg3 = MensagemChat(id="msg_3", autor="mestre", nome="Olive", conteudo="Resposta da Olive")
    msg4 = MensagemChat(id="msg_4", autor="jogador", nome="Mike", conteudo="Minha segunda ação")
    msg5 = MensagemChat(id="msg_5", autor="mestre", nome="Olive", conteudo="Resposta dois")
    estado.historico_chat = [msg1, msg2, msg3, msg4, msg5]
    estado.ultima_narracao = msg5.conteudo
    estado.turno = 2
    repositorio.salvar(estado)

    # 1. Testar edição de mensagem
    resp_edit = client.put(f"/campanhas/{cid}/mensagens/msg_2", json={"conteudo": "Ação editada"})
    assert resp_edit.status_code == 200
    dados = resp_edit.json()
    assert dados["historico_chat"][1]["conteudo"] == "Ação editada"

    # 2. Testar deleção com remoção de todas as mensagens abaixo
    # Se deletar msg_4 (segunda ação do jogador), msg_4 e msg_5 devem sumir
    resp_del = client.delete(f"/campanhas/{cid}/mensagens/msg_4")
    assert resp_del.status_code == 200
    dados_del = resp_del.json()
    ids_restantes = [m["id"] for m in dados_del["historico_chat"]]
    assert ids_restantes == ["msg_1", "msg_2", "msg_3"]
    assert dados_del["ultima_narracao"] == "Resposta da Olive"
    assert dados_del["turno"] == 1

    repositorio.deletar(cid)

