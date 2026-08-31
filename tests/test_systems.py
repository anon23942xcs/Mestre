from app.models.estado import Jogador
from app.services.estado_inicial import criar_estado_inicial
from app.systems.registro import obter_sistema


def test_registro_obtem_d20_e_fallback_seguro():
    assert obter_sistema("d20").id == "d20"
    assert obter_sistema("nao-existe").id == "d20"
    assert obter_sistema("d10").id == "d10"


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


def _estado_d10(limiar=6):
    estado = criar_estado_inicial("d10teste", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))
    estado.configuracao_mundo.sistema_id = "d10"
    estado.configuracao_mundo.d10_limiar_sucesso = limiar
    estado.jogador.ficha_sistema = {"pools": {"combate": 2, "social": 2, "exploracao": 2, "outro": 2}}
    return estado


def test_d10_jogador_com_mais_sucessos(monkeypatch):
    from app.services import dados
    sequencia = iter([[6, 8], [5]])
    monkeypatch.setattr(dados, "rolar_pool", lambda _n: next(sequencia))
    resultado = obter_sistema("d10").resolver(_estado_d10(), {"tipo_acao": "combate", "dificuldade_sugerida": 8})
    assert resultado.sucesso is True
    assert resultado.detalhes["sucessos_jogador"] == 2
    assert resultado.detalhes["sucessos_oposicao"] == 0


def test_d10_oposicao_vence_empate(monkeypatch):
    from app.services import dados
    sequencia = iter([[6, 2], [6]])
    monkeypatch.setattr(dados, "rolar_pool", lambda _n: next(sequencia))
    resultado = obter_sistema("d10").resolver(_estado_d10(), {"tipo_acao": "combate", "dificuldade_sugerida": 8})
    assert resultado.sucesso is False
    assert resultado.detalhes["sucessos_jogador"] == resultado.detalhes["sucessos_oposicao"] == 1


def test_d10_oposicao_com_mais_sucessos_falha(monkeypatch):
    from app.services import dados
    sequencia = iter([[2, 3], [6, 7]])
    monkeypatch.setattr(dados, "rolar_pool", lambda _n: next(sequencia))
    resultado = obter_sistema("d10").resolver(_estado_d10(), {"tipo_acao": "combate", "dificuldade_sugerida": 10})
    assert resultado.sucesso is False
    assert resultado.detalhes["sucessos_jogador"] == 0
    assert resultado.detalhes["sucessos_oposicao"] == 2


def test_d10_limiar_configuravel_muda_contagem(monkeypatch):
    from app.services import dados
    dados_fixos = [[5, 6], [6]]
    monkeypatch.setattr(dados, "rolar_pool", lambda _n: list(dados_fixos.pop(0)))
    facil = obter_sistema("d10").resolver(_estado_d10(5), {"tipo_acao": "combate", "dificuldade_sugerida": 8})
    dados_fixos[:] = [[5, 6], [6]]
    dificil = obter_sistema("d10").resolver(_estado_d10(7), {"tipo_acao": "combate", "dificuldade_sugerida": 8})
    assert facil.detalhes["sucessos_jogador"] == 2
    assert dificil.detalhes["sucessos_jogador"] == 0
    assert facil.sucesso is True and dificil.sucesso is False
