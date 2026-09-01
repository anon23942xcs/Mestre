import asyncio

import pytest

from app.models.ficha import FichaMundo
from app.models.mundo import Mundo
from app.models.personagem import Personagem
from app.models.requests import CriarPersonagemRequest
from app.routers.campanha import apagar_campanha, criar_campanha
from app.storage import ficha_repositorio, mundo_repositorio, personagem_repositorio, repositorio


@pytest.fixture(autouse=True)
def pasta_dados(tmp_path, monkeypatch):
    for modulo in (repositorio, ficha_repositorio, mundo_repositorio, personagem_repositorio):
        monkeypatch.setattr(modulo, "DATA_DIR", tmp_path)


def test_copiar_fichas_preserva_origem_e_isola_destino():
    origem = "mundo_molde"
    destino = "campanha_abc123"
    ficha_repositorio.salvar(origem, FichaMundo(id="local_porto", tipo="local", titulo="Porto", campos={"perigo": 2}))

    ficha_repositorio.copiar_fichas(origem, destino)
    copia = ficha_repositorio.carregar(destino, "local_porto")
    copia.campos["perigo"] = 9
    ficha_repositorio.salvar(destino, copia)

    assert ficha_repositorio.carregar(origem, "local_porto").campos["perigo"] == 2
    assert ficha_repositorio.carregar(destino, "local_porto").campos["perigo"] == 9


def test_campanha_copia_mundo_e_apaga_so_a_propria_wiki():
    mundo = Mundo(id="mundo_ilhas", nome="Ilhas", descricao="Mar aberto")
    personagem = Personagem(id="personagem_lia", nome="Lia", idade=22, genero="F", aparencia="curta")
    mundo_repositorio.salvar(mundo)
    personagem_repositorio.salvar(personagem)
    ficha_repositorio.salvar("mundo_mundo_ilhas", FichaMundo(id="item_bussola", tipo="item", titulo="Bússola"))

    estado = asyncio.run(criar_campanha(CriarPersonagemRequest(personagem_id=personagem.id, mundo_id=mundo.id)))
    escopo_campanha = f"campanha_{estado.campanha_id}"

    assert estado.mundo_id == mundo.id
    assert estado.mundo == "Ilhas"
    assert ficha_repositorio.carregar(escopo_campanha, "item_bussola") is not None
    assert estado.estado.npc_ativos == []

    asyncio.run(apagar_campanha(estado.campanha_id))

    assert ficha_repositorio.carregar("mundo_mundo_ilhas", "item_bussola") is not None
    assert ficha_repositorio.listar(escopo_campanha) == []
