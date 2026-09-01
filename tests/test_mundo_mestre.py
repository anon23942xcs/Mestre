from app.models.estado import ConfiguracaoMundo, Jogador
from app.models.mundo import Mundo
from app.models.personagem import Personagem
from app.models.requests import CriarPersonagemRequest
from app.routers.campanha import criar_campanha
from app.services import pipeline
from app.storage import mundo_repositorio, personagem_repositorio, repositorio, ficha_repositorio
import pytest


@pytest.mark.anyio
async def test_mundo_propaga_nome_e_imagem_do_mestre_para_campanha(monkeypatch, tmp_path):
    data_dir = tmp_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    mundos_dir = tmp_path / 'mundos'
    mundos_dir.mkdir(parents=True, exist_ok=True)
    pers_dir = tmp_path / 'personagens'
    pers_dir.mkdir(parents=True, exist_ok=True)
    wiki_dir = tmp_path / 'wiki'
    wiki_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(repositorio, 'DATA_DIR', data_dir)
    monkeypatch.setattr(mundo_repositorio, 'DATA_DIR', mundos_dir)
    monkeypatch.setattr(personagem_repositorio, 'DATA_DIR', pers_dir)
    monkeypatch.setattr(ficha_repositorio, 'DATA_DIR', wiki_dir)

    mid = mundo_repositorio.novo_id()
    config = ConfiguracaoMundo(
        nome_mestre='O Cronista Sombrio',
        imagem_mestre='https://exemplo.com/mestre_foto.png',
        cenario='Ruínas ancestrais cobertas de névoa.',
        primeira_mensagem='Vocês chegam diante dos portões de ferro.',
    )
    mundo = Mundo(id=mid, nome='Reino Sombrio', descricao='Mundo gótico', configuracao=config)
    mundo_repositorio.salvar(mundo)

    pid = personagem_repositorio.novo_id()
    personagem = Personagem(
        id=pid,
        nome='Valerius',
        idade=28,
        genero='M',
        aparencia='Guerreiro de armadura negra',
        historico='Exilado de sua terra natal',
        ficha_completa='# Valerius\n\n## Perícias\n- Luta com espada',
        imagem='https://exemplo.com/valerius.png',
    )
    personagem_repositorio.salvar(personagem)

    req = CriarPersonagemRequest(
        mundo_id=mid,
        personagem_id=pid,
    )
    estado = await criar_campanha(req)

    assert estado.jogador.imagem == 'https://exemplo.com/valerius.png'
    assert estado.configuracao_mundo.nome_mestre == 'O Cronista Sombrio'
    assert estado.configuracao_mundo.imagem_mestre == 'https://exemplo.com/mestre_foto.png'
    assert len(estado.historico_chat) >= 1
    assert estado.historico_chat[0].autor == 'mestre'
    assert estado.historico_chat[0].nome == 'O Cronista Sombrio'

    monkeypatch.setattr('app.services.narrador.narrar', lambda *args, **kwargs: 'O vento uiva entre as árvores.')
    monkeypatch.setattr('app.services.interprete.interpretar', lambda *args, **kwargs: {'requer_teste': False})
    monkeypatch.setattr('app.services.gerente.atualizar_estado', lambda estado, *args, **kwargs: estado)

    resultado = pipeline.processar_turno(estado, 'Eu observo ao redor.')
    assert resultado.estado.historico_chat[-1].autor == 'mestre'
    assert resultado.estado.historico_chat[-1].nome == 'O Cronista Sombrio'
