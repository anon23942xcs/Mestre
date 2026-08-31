import pytest

from app.models.estado import Jogador
from app.services.estado_inicial import criar_estado_inicial
from app.storage import repositorio


@pytest.fixture(autouse=True)
def pasta_dados(tmp_path, monkeypatch):
    monkeypatch.setattr(repositorio, "DATA_DIR", tmp_path)
    return tmp_path


def test_salvar_carregar_e_listar():
    estado = criar_estado_inicial(
        repositorio.novo_id(),
        Jogador(nome="Kael", idade=30, genero="M", aparencia="cicatriz", historico="ex-soldado"),
    )
    repositorio.salvar(estado)
    carregado = repositorio.carregar(estado.campanha_id)
    assert carregado is not None
    assert carregado.jogador.nome == "Kael"
    lista = repositorio.listar()
    assert lista[0]["nome_jogador"] == "Kael"


def test_path_traversal_e_rejeitado():
    with pytest.raises(ValueError):
        repositorio.carregar("../../etc/passwd")


def test_deletar():
    estado = criar_estado_inicial(
        "deadbeef",
        Jogador(nome="A", idade=18, genero="X", aparencia="a", historico="b"),
    )
    repositorio.salvar(estado)
    assert repositorio.deletar("deadbeef") is True
    assert repositorio.carregar("deadbeef") is None
