from app.prompts.preencher import preencher
from app.services.ia_client import extrair_json


def test_preencher_nao_quebra_com_chaves_do_jogador():
    texto = preencher("Diga: {mensagem}", mensagem="uso {pv} e {local}")
    assert texto == "Diga: uso {pv} e {local}"


def test_extrair_json_de_cerca_markdown():
    bruto = "claro\n```json\n{\"ok\": true}\n```\n"
    assert extrair_json(bruto) == '{"ok": true}'


def test_extrair_json_solto():
    assert extrair_json("prefixo {\"a\": 1} sufixo") == '{"a": 1}'
