"""Persistência atômica e independente para as fichas da Wiki."""
import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.models.ficha import FichaMundo


def _id_seguro(valor: str) -> str:
    if not valor or not valor.replace("_", "").isalnum():
        raise ValueError("id inválido")
    return valor


def _pasta(campanha_id: str) -> Path:
    pasta = DATA_DIR / "wiki" / _id_seguro(campanha_id)
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _caminho(campanha_id: str, ficha_id: str) -> Path:
    return _pasta(campanha_id) / f"{_id_seguro(ficha_id)}.json"


def novo_id() -> str:
    return f"ficha_{uuid.uuid4().hex[:12]}"


def listar(campanha_id: str) -> list[FichaMundo]:
    fichas = []
    for caminho in _pasta(campanha_id).glob("*.json"):
        try:
            fichas.append(FichaMundo.model_validate_json(caminho.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(fichas, key=lambda ficha: (ficha.tipo, ficha.titulo.lower()))


def carregar(campanha_id: str, ficha_id: str) -> Optional[FichaMundo]:
    caminho = _caminho(campanha_id, ficha_id)
    if not caminho.exists():
        return None
    return FichaMundo.model_validate_json(caminho.read_text(encoding="utf-8"))


def salvar(campanha_id: str, ficha: FichaMundo) -> None:
    caminho = _caminho(campanha_id, ficha.id)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(ficha.model_dump_json(indent=2), encoding="utf-8")
    temporario.replace(caminho)


def deletar(campanha_id: str, ficha_id: str) -> bool:
    caminho = _caminho(campanha_id, ficha_id)
    if not caminho.exists():
        return False
    caminho.unlink()
    return True


def deletar_da_campanha(campanha_id: str) -> None:
    """Remove a Wiki junto da campanha, evitando fichas órfãs."""
    pasta = DATA_DIR / "wiki" / _id_seguro(campanha_id)
    if pasta.exists():
        shutil.rmtree(pasta)
