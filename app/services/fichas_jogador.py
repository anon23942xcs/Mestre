"""Organização determinística de fichas Markdown, sem chamar uma IA."""
import re

_CABECALHO = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def organizar_ficha_markdown(texto: str) -> dict[str, str]:
    """Separa uma ficha por títulos Markdown sem perder conteúdo algum."""
    texto = texto.strip()
    if not texto:
        return {}
    encontrados = list(_CABECALHO.finditer(texto))
    if not encontrados:
        return {"ficha_completa": texto}
    secoes: dict[str, str] = {}
    introducao = texto[:encontrados[0].start()].strip()
    if introducao:
        secoes["visao_geral"] = introducao
    for indice, encontrado in enumerate(encontrados):
        titulo = encontrado.group(1).strip().lower()
        fim = encontrados[indice + 1].start() if indice + 1 < len(encontrados) else len(texto)
        conteudo = texto[encontrado.end():fim].strip()
        # Títulos repetidos recebem um sufixo, sem sobrescrever informação.
        chave = titulo
        contador = 2
        while chave in secoes:
            chave = f"{titulo} ({contador})"
            contador += 1
        secoes[chave] = conteudo
    return secoes


def formatar_ficha_estruturada(secoes: dict[str, str], fallback: str) -> str:
    if not secoes:
        return fallback or "nenhuma ficha adicional"
    return "\n\n".join(
        f"[{titulo.upper()}]\n{conteudo}" for titulo, conteudo in secoes.items()
    )
