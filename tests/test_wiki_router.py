import asyncio
import json
import pytest

from app.main import app
from app.models.estado import Jogador
from app.models.ficha import FichaMundo
from app.services.estado_inicial import criar_estado_inicial
from app.storage import ficha_repositorio, repositorio


@pytest.fixture(autouse=True)
def pasta_dados(tmp_path, monkeypatch):
    monkeypatch.setattr(repositorio, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ficha_repositorio, "DATA_DIR", tmp_path)


async def requisicao_get(caminho: str) -> tuple[int, dict]:
    mensagens = []

    async def receber():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def enviar(mensagem):
        mensagens.append(mensagem)

    await app({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "GET", "scheme": "http", "path": caminho,
        "raw_path": caminho.encode(), "query_string": b"", "headers": [],
        "client": ("testclient", 50000), "server": ("testserver", 80),
    }, receber, enviar)
    status = next(mensagem["status"] for mensagem in mensagens if mensagem["type"] == "http.response.start")
    corpo = b"".join(mensagem.get("body", b"") for mensagem in mensagens if mensagem["type"] == "http.response.body")
    return status, json.loads(corpo)


def test_obter_ficha_existente_retorna_200():
    campanha_id = "campanha123"
    repositorio.salvar(criar_estado_inicial(
        campanha_id,
        Jogador(nome="Kael", idade=30, genero="M", aparencia="cicatriz", historico="ex-soldado"),
    ))
    ficha_repositorio.salvar(campanha_id, FichaMundo(
        id="ficha_kael", tipo="personagem", titulo="Kael", resumo="Aventureiro",
    ))

    status, resposta = asyncio.run(requisicao_get(f"/campanhas/{campanha_id}/catalogo/ficha_kael"))

    assert status == 200
    assert resposta["id"] == "ficha_kael"
    assert resposta["titulo"] == "Kael"


def test_obter_ficha_inexistente_retorna_404():
    campanha_id = "campanha123"
    repositorio.salvar(criar_estado_inicial(
        campanha_id,
        Jogador(nome="Kael", idade=30, genero="M", aparencia="cicatriz", historico="ex-soldado"),
    ))

    status, resposta = asyncio.run(requisicao_get(f"/campanhas/{campanha_id}/catalogo/ficha_inexistente"))

    assert status == 404
    assert resposta["detail"] == "Ficha não encontrada"
