from app.models.estado import Jogador
from app.models.personagem import Personagem
from app.models.requests import EditarJogadorCampanhaRequest
from app.routers.campanha import editar_jogador_campanha
from app.services.estado_inicial import criar_estado_inicial
from app.storage import personagem_repositorio, repositorio
import pytest


@pytest.mark.anyio
async def test_editar_jogador_campanha_preserva_isolamento_com_perfil(monkeypatch, tmp_path):
    data_dir = tmp_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    pers_dir = tmp_path / 'personagens'
    pers_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(repositorio, 'DATA_DIR', data_dir)
    monkeypatch.setattr(personagem_repositorio, 'DATA_DIR', pers_dir)

    # 1. Salva personagem reutilizável
    pid = personagem_repositorio.novo_id()
    original = Personagem(
        id=pid,
        nome='Aventureiro Original',
        idade=20,
        genero='M',
        aparencia='Simples',
        historico='Histórico original',
        ficha_completa='# Ficha Original',
        imagem='https://exemplo.com/orig.png',
    )
    personagem_repositorio.salvar(original)

    # 2. Cria campanha com cópia do jogador
    cid = repositorio.novo_id()
    estado = criar_estado_inicial(
        cid,
        Jogador(
            personagem_id=pid,
            nome=original.nome,
            idade=original.idade,
            genero=original.genero,
            aparencia=original.aparencia,
            historico=original.historico,
            ficha_completa=original.ficha_completa,
            imagem=original.imagem,
            pv=20,
            pv_max=20,
        )
    )
    repositorio.salvar(estado)

    # 3. Edita jogador dentro da campanha
    req = EditarJogadorCampanhaRequest(
        nome='Aventureiro Evoluído',
        idade=21,
        pv=15,
        pv_max=25,
        imagem='https://exemplo.com/evolucao.png',
        ficha_completa='# Aventureiro\n\n## Perícias\n- Furtividade rank S',
        inventario=['espada mágica', 'poção de cura'],
        atributos={'forca': 8, 'destreza': 7}
    )
    atualizado = await editar_jogador_campanha(cid, req)

    # 4. Verifica se a campanha foi alterada
    assert atualizado.jogador.nome == 'Aventureiro Evoluído'
    assert atualizado.jogador.idade == 21
    assert atualizado.jogador.pv == 15
    assert atualizado.jogador.pv_max == 25
    assert atualizado.jogador.imagem == 'https://exemplo.com/evolucao.png'
    assert 'espada mágica' in atualizado.jogador.inventario
    assert atualizado.jogador.atributos.forca == 8
    assert atualizado.jogador.atributos.destreza == 7
    assert 'furtividade rank s' in str(atualizado.jogador.ficha_estruturada).lower()

    # 5. GARANTIA CRÍTICA DE ISOLAMENTO:
    # O perfil original em personagem_repositorio NÃO pode ter sido alterado!
    perfil_no_banco = personagem_repositorio.carregar(pid)
    assert perfil_no_banco.nome == 'Aventureiro Original'
    assert perfil_no_banco.idade == 20
    assert perfil_no_banco.imagem == 'https://exemplo.com/orig.png'
    assert perfil_no_banco.ficha_completa == '# Ficha Original'
