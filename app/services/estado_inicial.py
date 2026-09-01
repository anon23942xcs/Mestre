from app.models.estado import Campanha, ConfiguracaoMundo, Estado, EstadoCompleto, Jogador, MensagemChat


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

    if not configuracao.cenario or configuracao.cenario == "Um mundo à espera de uma história.":
        local_inicial = "Cena inicial"
    elif len(configuracao.cenario) <= 60 and "\n" not in configuracao.cenario:
        local_inicial = configuracao.cenario
    else:
        primeira_linha = configuracao.cenario.strip().split("\n")[0]
        local_inicial = primeira_linha[:60] if len(primeira_linha) > 60 else primeira_linha

    primeira_msg = configuracao.primeira_mensagem.replace("{{user}}", jogador.nome) if configuracao.primeira_mensagem else ""
    historico = []
    if primeira_msg:
        historico.append(MensagemChat(autor="mestre", nome="Mestre", conteudo=primeira_msg))


    return EstadoCompleto(
        campanha_id=campanha_id,
        mundo_id=mundo_id,
        mundo=mundo_nome or "Mundo sem título",
        jogador=jogador,
        configuracao_mundo=configuracao,
        estado=Estado(
            local=local_inicial,
        ),
        campanha=Campanha(),
        ultima_narracao=primeira_msg,
        historico_chat=historico,
    )
