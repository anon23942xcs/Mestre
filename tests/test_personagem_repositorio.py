import asyncio

import pytest

from app.models.personagem import Personagem
from app.models.requests import CriarPersonagemRequest
from app.routers.campanha import criar_campanha
from app.storage import ficha_repositorio, personagem_repositorio, repositorio


@pytest.fixture(autouse=True)
def pasta_dados(tmp_path, monkeypatch):
    monkeypatch.setattr(repositorio, "DATA_DIR", tmp_path)
    monkeypatch.setattr(personagem_repositorio, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ficha_repositorio, "DATA_DIR", tmp_path)


def test_personagem_e_reutilizado_sem_criar_ficha_padrao():
    personagem = Personagem(
        id="personagem_lia", nome="Lia", idade=22, genero="F", aparencia="cabelo curto",
        historico="Viajante", ficha_completa="## HABILIDADES\nObservadora",
    )
    personagem_repositorio.salvar(personagem)

    estado = asyncio.run(criar_campanha(CriarPersonagemRequest(personagem_id=personagem.id)))

    assert estado.jogador.personagem_id == personagem.id
    assert estado.jogador.nome == "Lia"
    assert estado.jogador.ficha_estruturada["habilidades"] == "Observadora"
    assert ficha_repositorio.listar(estado.campanha_id) == []
