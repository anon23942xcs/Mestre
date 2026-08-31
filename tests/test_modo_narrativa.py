from app.models.estado import Jogador
from app.services.estado_inicial import criar_estado_inicial


def test_modo_narrativa_nao_rola_teste(monkeypatch):
    from app.services import dados, gerente, interprete, narrador
    from app.services.pipeline import processar_turno

    estado = criar_estado_inicial("narrativa", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))
    estado.configuracao_mundo.sistema_rpg = False
    monkeypatch.setattr(interprete, "interpretar", lambda _mensagem: {"requer_teste": True, "tipo_acao": "combate", "dificuldade_sugerida": 12})
    monkeypatch.setattr(gerente, "atualizar_estado", lambda estado, *_args: estado)
    monkeypatch.setattr(gerente, "registrar_resposta_mestre", lambda *_args: None)
    monkeypatch.setattr(narrador, "narrar", lambda *_args: "narrativa")
    monkeypatch.setattr(dados, "resolver_teste", lambda *_args: (_ for _ in ()).throw(AssertionError("não deveria rolar")))

    resultado = processar_turno(estado, "Ataco")
    assert resultado.teste is None


def test_prompt_narrativo_omite_pv_e_testes(monkeypatch):
    from app.services import narrador

    estado = criar_estado_inicial("narrativa", Jogador(nome="Lia", idade=22, genero="F", aparencia="curta", historico="viajante"))
    estado.configuracao_mundo.sistema_rpg = False
    capturado = {}
    monkeypatch.setattr(narrador, "gerar_texto", lambda prompt: capturado.setdefault("prompt", prompt) or "ok")

    narrador.narrar(estado, "Observo a sala")
    assert "PV:" not in capturado["prompt"]
    assert "[RESULTADO DE TESTE DE DADOS]" not in capturado["prompt"]
