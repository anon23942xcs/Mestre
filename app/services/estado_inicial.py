from app.models.estado import Campanha, ConfiguracaoMundo, Estado, EstadoCompleto, Jogador, NPC


def criar_estado_inicial(campanha_id: str, jogador: Jogador, configuracao_mundo: ConfiguracaoMundo | None = None) -> EstadoCompleto:
    """Estado padrão da primeira cena. Isolado do router para poder testar e trocar o gancho depois."""
    configuracao = configuracao_mundo or ConfiguracaoMundo()
    if not jogador.ficha_sistema:
        from app.systems.registro import obter_sistema
        if configuracao.sistema_id == "d10":
            from app.systems.sistema_d10 import construir_ficha
            jogador.ficha_sistema = construir_ficha(configuracao.d10_pontos_atributos, {})
        else:
            jogador.ficha_sistema = obter_sistema(configuracao.sistema_id).ficha_padrao()
    ficha_npc = {}
    if configuracao.sistema_id == "d10":
        from app.systems.sistema_d10 import construir_ficha
        ficha_npc = construir_ficha(configuracao.d10_pontos_atributos, {})
    return EstadoCompleto(
        campanha_id=campanha_id,
        jogador=jogador,
        configuracao_mundo=configuracao,
        estado=Estado(
            local="Taverna do Cão Caído - Alderan",
            clima="nublado",
            npc_ativos=[
                NPC(
                    id="npc_001",
                    nome="Estalajadeira",
                    raca="humano",
                    aparencia="mulher robusta, avental manchado, cabelo preso",
                    humor="indiferente",
                    relacao=0,
                    segredos=[],
                    ultima_interacao="observa o novo cliente",
                    ficha_catalogo_id="ficha_estalajadeira",
                    ficha_sistema=ficha_npc,
                )
            ],
        ),
        campanha=Campanha(arco_principal="Em busca de vingança"),
    )
