from app.models.estado import Campanha, ConfiguracaoMundo, Estado, EstadoCompleto, Jogador, NPC


def criar_estado_inicial(campanha_id: str, jogador: Jogador, configuracao_mundo: ConfiguracaoMundo | None = None) -> EstadoCompleto:
    """Estado padrão da primeira cena. Isolado do router para poder testar e trocar o gancho depois."""
    return EstadoCompleto(
        campanha_id=campanha_id,
        jogador=jogador,
        configuracao_mundo=configuracao_mundo or ConfiguracaoMundo(),
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
                )
            ],
        ),
        campanha=Campanha(arco_principal="Em busca de vingança"),
    )
