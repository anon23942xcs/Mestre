"""
Passo 1: Intérprete.

Extrai da mensagem livre do jogador uma intenção estruturada, incluindo se
a ação exige um teste de dados e qual o tipo. Isso não existia no código
anterior: só havia o Narrador. Sem essa etapa, não dá pra saber
programaticamente quando rolar dados ou o que passar ao Gerente.
"""
from app.services.ia_client import gerar_json, ErroIA, ErroFormatoIA

PROMPT = """Você analisa a mensagem de um jogador de RPG e extrai a intenção dela.

Responda APENAS com um JSON válido, sem texto antes ou depois, sem cercas de código markdown, no formato:
{{
  "intencao": "resumo curto da intenção do jogador",
  "alvo": "quem ou o que a ação envolve, ou null se não houver alvo claro",
  "tom": "um de: agressivo, amigável, cauteloso, neutro, cômico",
  "tipo_acao": "um de: combate, social, exploracao, outro",
  "requer_teste": true ou false (true se o resultado é incerto e deveria depender de sorte/habilidade),
  "dificuldade_sugerida": um número entre 8 e 20 representando o quão difícil é a ação (10 é fácil, 15 é médio, 20 é muito difícil)
}}

Mensagem do jogador: "{mensagem}"
"""

_PADRAO = {
    "intencao": "ação não especificada",
    "alvo": None,
    "tom": "neutro",
    "tipo_acao": "outro",
    "requer_teste": False,
    "dificuldade_sugerida": 12,
}


def interpretar(mensagem: str) -> dict:
    """
    Devolve a interpretação estruturada da mensagem. Se a IA falhar ou
    devolver algo ilegível, cai para um padrão neutro em vez de travar o
    turno inteiro — o jogo continua, só sem a camada extra de nuance.
    """
    try:
        resultado = gerar_json(PROMPT.format(mensagem=mensagem))
    except (ErroIA, ErroFormatoIA):
        return dict(_PADRAO)

    interpretacao = dict(_PADRAO)
    interpretacao.update({k: v for k, v in resultado.items() if k in _PADRAO})
    return interpretacao
