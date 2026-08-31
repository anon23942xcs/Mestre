from app.services.fichas_jogador import formatar_ficha_estruturada, organizar_ficha_markdown


def test_organizar_ficha_preserva_secoes_markdown():
    texto = "# Mike\n\n## Identidade\n- Nome: Mike\n\n## Regras\n- Não controlar o jogador"
    secoes = organizar_ficha_markdown(texto)
    assert secoes["mike"] == ""
    assert "Nome: Mike" in secoes["identidade"]
    assert "Não controlar" in formatar_ficha_estruturada(secoes, "")


def test_organizar_ficha_sem_cabecalho_preserva_texto():
    assert organizar_ficha_markdown("texto livre") == {"ficha_completa": "texto livre"}
