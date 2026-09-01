from app.models.estado import Campanha, ConfiguracaoMundo, Estado, EstadoCompleto, Jogador


def criar_estado_inicial(campanha_id: str, jogador: Jogador, configuracao_mundo: ConfiguracaoMundo | None = None, mundo_id: str | None = None, mundo_nome: str = "") -> EstadoCompleto:
    """Estado padrão da primeira cena. Isolado do router para poder testar e trocar o gancho depois."""
    configuracao = configuracao_mundo or ConfiguracaoMundo()
    if not jogador.ficha_sistema:
        from app.systems.registro import obter_sistema
        if configuracao.sistema_id == "d10":
            from app.systems.sistema_d10 import construir_ficha
            jogador.ficha_sistema = construir_ficha(configuracao.d10_pontos_atributos, {})
        else:
            jogador.ficha_sistema = obter_sistema(configuracao.sistema_id).ficha_padrao()
    return EstadoCompleto(
        campanha_id=campanha_id,
        mundo_id=mundo_id,
        mundo=mundo_nome or "Mundo sem título",
        jogador=jogador,
        configuracao_mundo=configuracao,
        estado=Estado(
            local=configuracao.cenario or "Cena inicial",
        ),
        campanha=Campanha(),
    )
