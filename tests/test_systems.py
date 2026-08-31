from app.models.estado import Jogador
from app.services.estado_inicial import criar_estado_inicial
from app.systems.registro import obter_sistema


def test_registro_obtem_d20_e_fallback_seguro():
    assert obter_sistema("d20").id == "d20"
    assert obter_sistema("nao-existe").id == "d20"


def test_sistema_nenhum_nunca_rola():
    resultado = obter_sistema("nenhum").resolver(None, {"requer_teste": True})
    assert resultado.sistema == "nenhum"
    assert resultado.houve_teste is False
    assert resultado.sucesso is True
    assert resultado.resumo_narrador == ""


def test_sistema_d20_mantem_regra_atual(monkeypatch):
    from app.services import dados

    estado = criar_estado_inicial("d20teste", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))
    monkeypatch.setattr(dados, "rolar_d20", lambda: 20)
    resultado = obter_sistema("d20").resolver(estado, {"tipo_acao": "combate", "dificuldade_sugerida": 99})
    assert resultado.sistema == "d20"
    assert resultado.houve_teste is True
    assert resultado.sucesso is True
    assert resultado.detalhes["rolagem"] == 20
    assert resultado.detalhes["critico_sucesso"] is True


def test_ficha_sistema_recebe_padrao_do_plugin():
    estado = criar_estado_inicial("ficha", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))
    assert estado.configuracao_mundo.sistema_id == "d20"
    assert estado.jogador.ficha_sistema["forca"] == 5
