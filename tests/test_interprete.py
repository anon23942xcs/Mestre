from app.services.interprete import interpretar


def test_interpretar_cai_no_padrao_quando_ia_falha(monkeypatch):
    from app.services import interprete
    from app.services.ia_client import ErroIA

    def falhar(_prompt):
        raise ErroIA("sem chave")

    monkeypatch.setattr(interprete, "gerar_json", falhar)
    resultado = interpretar("eu ataco o orc {com} fúria")
    assert resultado["tom"] == "neutro"
    assert resultado["requer_teste"] is False
    assert resultado["dificuldade_sugerida"] == 12


def test_interpretar_normaliza_valores_invalidos(monkeypatch):
    from app.services import interprete

    monkeypatch.setattr(
        interprete,
        "gerar_json",
        lambda _p: {
            "intencao": "saltar",
            "tom": "xyz",
            "tipo_acao": "voar",
            "requer_teste": 1,
            "dificuldade_sugerida": 99,
        },
    )
    resultado = interpretar("salto")
    assert resultado["tom"] == "neutro"
    assert resultado["tipo_acao"] == "outro"
    assert resultado["requer_teste"] is True
    assert resultado["dificuldade_sugerida"] == 20
