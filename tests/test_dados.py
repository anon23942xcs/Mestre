from app.services.dados import atributo_para_tipo, resolver_teste


def test_atributo_por_tipo():
    assert atributo_para_tipo("combate") == "forca"
    assert atributo_para_tipo("social") == "carisma"
    assert atributo_para_tipo("exploracao") == "destreza"
    assert atributo_para_tipo("desconhecido") == "inteligencia"


def test_resolver_teste_limites(monkeypatch):
    monkeypatch.setattr("app.services.dados.rolar_d20", lambda: 15)
    resultado = resolver_teste(5, 12)
    assert resultado.rolagem == 15
    assert resultado.total == 20
    assert resultado.sucesso is True
    assert resultado.critico_sucesso is False
    assert resultado.critico_falha is False


def test_critico_sucesso_mesmo_abaixo_da_cd(monkeypatch):
    monkeypatch.setattr("app.services.dados.rolar_d20", lambda: 20)
    resultado = resolver_teste(0, 30)
    assert resultado.sucesso is True
    assert resultado.critico_sucesso is True


def test_critico_falha_mesmo_acima_da_cd(monkeypatch):
    monkeypatch.setattr("app.services.dados.rolar_d20", lambda: 1)
    resultado = resolver_teste(20, 5)
    assert resultado.sucesso is False
    assert resultado.critico_falha is True
