"""
Sistema de dados.

Este módulo não existia antes. A especificação original promete
"consequências reais" e testes de dados como diferencial do Modo Mestre,
mas nada no código impedia a IA de simplesmente narrar sucesso sempre,
igual ao Modo Janitor que o projeto quer evitar. A diferença entre "a IA
decide narrativamente" e "o sistema decide por regra e a IA só narra o
resultado" é o que dá substância a essa promessa.

A rolagem é feita em Python com random, fora do alcance do modelo de
linguagem. A IA (no Narrador) recebe o resultado já decidido e escreve em
cima dele, não o contrário.
"""
import random
from typing import Literal

TipoAcao = Literal["combate", "social", "exploracao", "outro"]

# Mapa de qual atributo do jogador é testado para cada tipo de ação.
ATRIBUTO_POR_TIPO = {
    "combate": "forca",
    "social": "carisma",
    "exploracao": "destreza",
    "outro": "inteligencia",
}


def rolar_d20() -> int:
    return random.randint(1, 20)


def resolver_teste(valor_atributo: int, dificuldade: int = 12) -> dict:
    """
    Rola 1d20 + atributo contra uma dificuldade (CD).

    Retorna um dicionário serializável em JSON, usado tanto para decidir o
    que aconteceu quanto para mostrar ao jogador o que foi rolado.
    """
    rolagem = rolar_d20()
    total = rolagem + valor_atributo
    critico_sucesso = rolagem == 20
    critico_falha = rolagem == 1
    sucesso = critico_sucesso or (not critico_falha and total >= dificuldade)
    return {
        "rolagem": rolagem,
        "atributo": valor_atributo,
        "total": total,
        "dificuldade": dificuldade,
        "sucesso": sucesso,
        "critico_sucesso": critico_sucesso,
        "critico_falha": critico_falha,
    }


def atributo_para_tipo(tipo_acao: str) -> str:
    return ATRIBUTO_POR_TIPO.get(tipo_acao, "inteligencia")
