"""Registro central de plugins de regras disponíveis."""
from app.systems.base import SistemaRPG
from app.systems.sistema_d20 import SistemaD20
from app.systems.sistema_nenhum import SistemaNenhum

SISTEMAS: dict[str, SistemaRPG] = {
    "d20": SistemaD20(),
    "nenhum": SistemaNenhum(),
}


def obter_sistema(sistema_id: str) -> SistemaRPG:
    """Retorna d20 como fallback seguro para campanhas/ids desconhecidos."""
    return SISTEMAS.get(sistema_id, SISTEMAS["d20"])
