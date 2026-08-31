"""Substituição segura de placeholders em prompts.

str.format() quebra se a mensagem do jogador contém chaves `{` `}`, e
também interpreta `{{`/`}}` do JSON de exemplo. Aqui só substituímos
chaves conhecidas, uma vez cada, sem avaliar o restante do texto.
"""


def preencher(template: str, **valores: object) -> str:
    resultado = template
    for chave, valor in valores.items():
        resultado = resultado.replace("{" + chave + "}", "" if valor is None else str(valor))
    return resultado
