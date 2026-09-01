"""Persistência atômica dos moldes de mundo."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.models.mundo import Mundo


def _id_seguro(valor: str) -> str:
    if not valor or not valor.replace("_", "").isalnum():
        raise ValueError("id inválido")
    return valor


def _pasta() -> Path:
    pasta = DATA_DIR / "mundos"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def novo_id() -> str:
    return f"mundo_{uuid.uuid4().hex[:12]}"


def _caminho(mundo_id: str) -> Path:
    return _pasta() / f"{_id_seguro(mundo_id)}.json"


def listar() -> list[Mundo]:
    mundos = []
    for caminho in _pasta().glob("*.json"):
        try:
            mundos.append(Mundo.model_validate_json(caminho.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(mundos, key=lambda mundo: mundo.nome.lower())


def carregar(mundo_id: str) -> Optional[Mundo]:
    caminho = _caminho(mundo_id)
    if not caminho.exists():
        return None
    return Mundo.model_validate_json(caminho.read_text(encoding="utf-8"))


def salvar(mundo: Mundo) -> None:
    mundo.ultima_atualizacao = datetime.now().isoformat()
    caminho = _caminho(mundo.id)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(mundo.model_dump_json(indent=2), encoding="utf-8")
    temporario.replace(caminho)


def deletar(mundo_id: str) -> bool:
    caminho = _caminho(mundo_id)
    if not caminho.exists():
        return False
    caminho.unlink()
    return True
