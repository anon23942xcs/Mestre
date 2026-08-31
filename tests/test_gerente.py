import pytest

from app.models.estado import Jogador
from app.services.estado_inicial import criar_estado_inicial
from app.services.gerente import aplicar_patch


@pytest.fixture
def estado():
    return criar_estado_inicial("abc123", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))


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
