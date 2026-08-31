"""Plugin d10 de pools opostos."""
from app.services import dados
from app.systems.base import ResultadoTesteGenerico

POOL_PADRAO = 2
LIMIAR_PADRAO = 6
OPOSICAO_MINIMA = 1
OPOSICAO_MAXIMA = 7
# Empate é vitória da oposição. Mude para True para inverter essa convenção.
EMPATE_FAVORECE_OPOSICAO = True
CATEGORIAS = ["fisico", "social", "mental"]
TIPO_ACAO_PARA_CATEGORIA = {
    "combate": "fisico",
    "exploracao": "fisico",
    "social": "social",
    "outro": "mental",
}


def _pontos_seguros(pontos) -> list[int]:
    """Normaliza o orçamento do mundo sem deixar dados legados quebrarem o jogo."""
    if not isinstance(pontos, list) or len(pontos) != len(CATEGORIAS):
        return [4, 3, 2]
    if any(isinstance(ponto, bool) for ponto in pontos):
        return [4, 3, 2]
    try:
        valores = [int(ponto) for ponto in pontos]
    except (TypeError, ValueError):
        return [4, 3, 2]
    return valores if all(1 <= valor <= 20 for valor in valores) else [4, 3, 2]


def construir_ficha(pontos: list[int], escolha: dict) -> dict:
    """Monta a ficha d10, aceitando apenas uma permutação do orçamento."""
    valores = _pontos_seguros(pontos)
    padrao = dict(zip(CATEGORIAS, valores))
    if not isinstance(escolha, dict) or set(escolha) != set(CATEGORIAS):
        return {"atributos": padrao}
    if any(isinstance(escolha[categoria], bool) for categoria in CATEGORIAS):
        return {"atributos": padrao}
    try:
        atributos = {categoria: int(escolha[categoria]) for categoria in CATEGORIAS}
    except (TypeError, ValueError):
        return {"atributos": padrao}
    if sorted(atributos.values()) != sorted(valores):
        return {"atributos": padrao}
    return {"atributos": atributos}


def _inteiro_seguro(valor, padrao: int, minimo: int, maximo: int) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, numero))


class SistemaD10:
    id = "d10"
    nome = "d10 (pool oposto)"

    def resolver(self, estado, interpretacao: dict) -> ResultadoTesteGenerico:
        ficha = getattr(getattr(estado, "jogador", None), "ficha_sistema", {})
        tipo = interpretacao.get("tipo_acao", "outro") if isinstance(interpretacao, dict) else "outro"
        categoria = TIPO_ACAO_PARA_CATEGORIA.get(tipo, "mental")
        atributos = ficha.get("atributos", {}) if isinstance(ficha, dict) else {}
        # Fichas anteriores guardavam pools; as incompletas usam o mesmo
        # fallback seguro para que uma campanha persistida nunca pare no turno.
        pool_jogador = _inteiro_seguro(
            atributos.get(categoria) if isinstance(atributos, dict) else None,
            POOL_PADRAO,
            1,
            20,
        )

        # Converte CD 8..20 em 1..7 dados: max(1, (CD - 6) // 2).
        dificuldade = _inteiro_seguro(
            interpretacao.get("dificuldade_sugerida") if isinstance(interpretacao, dict) else None,
            12, 8, 20,
        )
        pool_oposicao = max(OPOSICAO_MINIMA, min(OPOSICAO_MAXIMA, (dificuldade - 6) // 2))
        configuracao = getattr(estado, "configuracao_mundo", None)
        limiar = _inteiro_seguro(getattr(configuracao, "d10_limiar_sucesso", LIMIAR_PADRAO), LIMIAR_PADRAO, 2, 10)

        rolagens_jogador = dados.rolar_pool(pool_jogador)
        rolagens_oposicao = dados.rolar_pool(pool_oposicao)
        sucessos_jogador = sum(dado >= limiar for dado in rolagens_jogador)
        sucessos_oposicao = sum(dado >= limiar for dado in rolagens_oposicao)
        sucesso = sucessos_jogador > sucessos_oposicao if EMPATE_FAVORECE_OPOSICAO else sucessos_jogador >= sucessos_oposicao
        status = "SUCESSO" if sucesso else "FALHA"
        resumo = f"{status} — {sucessos_jogador} sucessos do jogador contra {sucessos_oposicao} da oposição (limiar {limiar}+)"
        return ResultadoTesteGenerico(
            sistema=self.id,
            houve_teste=True,
            sucesso=sucesso,
            resumo_narrador=resumo,
            detalhes={
                "rolagens_jogador": rolagens_jogador,
                "rolagens_oposicao": rolagens_oposicao,
                "sucessos_jogador": sucessos_jogador,
                "sucessos_oposicao": sucessos_oposicao,
                "limiar": limiar,
                "pool_jogador": pool_jogador,
                "pool_oposicao": pool_oposicao,
            },
        )

    def formatar_para_narrador(self, resultado: ResultadoTesteGenerico) -> str:
        return resultado.resumo_narrador

    def ficha_padrao(self) -> dict:
        return construir_ficha([4, 3, 2], {})
