import pytest

from app.models.estado import Jogador, NPC
from app.services.estado_inicial import criar_estado_inicial
from app.services.gerente import aplicar_patch
from app.services.wiki_gerente import aplicar_patch_wiki
from app.models.ficha import FichaMundo
from app.storage import ficha_repositorio


@pytest.fixture
def estado():
    estado = criar_estado_inicial("abc123", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))
    estado.estado.npc_ativos.append(NPC(id="npc_001", nome="Guia", raca="humano", aparencia="curta", humor="indiferente"))
    return estado


def test_aplicar_patch_atualiza_npc_e_local(estado):
    aplicar_patch(estado, {
        "npc_atualizados": [{"id": "npc_001", "humor": "desconfiada", "relacao_delta": 2, "novo_segredo": None}],
        "npc_novo": None,
        "eventos_novos": ["barulho na despensa"],
        "eventos_removidos": [],
        "memoria_importante_nova": "Lia chegou à taverna",
        "progresso_delta": 3,
        "local_novo": "Porão da taverna",
        "hora_nova": "noite",
    })
    npc = estado.estado.npc_ativos[0]
    assert npc.humor == "desconfiada"
    assert npc.relacao == 2
    assert "barulho na despensa" in estado.estado.eventos_ativos
    assert estado.estado.local == "Porão da taverna"
    assert estado.estado.hora == "noite"
    assert estado.campanha.progresso == 3
    assert "Lia chegou à taverna" in estado.estado.memorias_importantes


def test_aplicar_patch_ignora_npc_inexistente(estado):
    aplicar_patch(estado, {"npc_atualizados": [{"id": "nao_existe", "humor": "furioso"}]})
    assert estado.estado.npc_ativos[0].humor == "indiferente"


def test_aplicar_patch_ignora_npc_novo_malformado(estado):
    aplicar_patch(estado, {"npc_novo": {"id": "x"}})
    assert len(estado.estado.npc_ativos) == 1


def test_aplicar_patch_preserva_npc_ausente_fora_do_contexto(estado):
    aplicar_patch(estado, {
        "npcs_saem_de_cena": [{"id": "npc_001", "local_ausente": "mercado"}],
    })
    assert estado.estado.npc_ativos == []
    assert estado.estado.npc_ausentes[0].nome == "Guia"
    assert estado.estado.npc_ausentes[0].presente is False
    assert estado.estado.npc_ausentes[0].local_ausente == "mercado"

    aplicar_patch(estado, {"npcs_entram_em_cena": ["npc_001"]})
    assert estado.estado.npc_ausentes == []
    assert estado.estado.npc_ativos[0].presente is True


def test_patch_wiki_atualiza_e_move_relacao(estado, tmp_path, monkeypatch):
    monkeypatch.setattr(ficha_repositorio, "DATA_DIR", tmp_path)
    loja = FichaMundo(id="local_loja", tipo="local", titulo="Loja", relacoes={"contem_itens": ["item_espada"]})
    espada = FichaMundo(id="item_espada", tipo="item", titulo="Espada rara")
    ficha_repositorio.salvar(estado.campanha_id, loja)
    ficha_repositorio.salvar(estado.campanha_id, espada)

    aplicar_patch_wiki(estado, {
        "fichas_atualizadas": [{"id": "item_espada", "campos": {"dono": "ladrao"}, "conteudo_append": "Foi roubada."}],
        "relacao_removida": [{"origem": "local_loja", "tipo_relacao": "contem_itens", "destino": "item_espada"}],
    })
    assert ficha_repositorio.carregar(estado.campanha_id, "item_espada").campos["dono"] == "ladrao"
    assert "Foi roubada." in ficha_repositorio.carregar(estado.campanha_id, "item_espada").conteudo
    assert ficha_repositorio.carregar(estado.campanha_id, "local_loja").relacoes == {}


def test_patch_wiki_adiciona_ficha_e_relacao(estado, tmp_path, monkeypatch):
    monkeypatch.setattr(ficha_repositorio, "DATA_DIR", tmp_path)
    ficha_repositorio.salvar(estado.campanha_id, FichaMundo(id="local_loja", tipo="local", titulo="Loja"))
    aplicar_patch_wiki(estado, {
        "ficha_nova": {"tipo": "item", "titulo": "Poção"},
        "relacao_adicionada": [{"origem": "local_loja", "tipo_relacao": "contem_itens", "destino": "item_pocao"}],
    })
    # A relação por ID é válida mesmo se a ficha de destino for criada em
    # outro patch/turno; o destino jamais é copiado para a ficha origem.
    assert ficha_repositorio.carregar(estado.campanha_id, "local_loja").relacoes == {"contem_itens": ["item_pocao"]}
