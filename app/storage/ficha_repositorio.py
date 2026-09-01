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


def _pasta(escopo_id: str) -> Path:
    escopo_id = _id_seguro(escopo_id)
    # Campanhas anteriores à separação usavam somente o id como pasta.
    legado = escopo_id.removeprefix("campanha_") if escopo_id.startswith("campanha_") else ""
    pasta_legada = DATA_DIR / "wiki" / legado if legado else None
    pasta = pasta_legada if pasta_legada and pasta_legada.exists() else DATA_DIR / "wiki" / escopo_id
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _caminho(escopo_id: str, ficha_id: str) -> Path:
    return _pasta(escopo_id) / f"{_id_seguro(ficha_id)}.json"


def novo_id() -> str:
    return f"ficha_{uuid.uuid4().hex[:12]}"


def listar(escopo_id: str) -> list[FichaMundo]:
    fichas = []
    for caminho in _pasta(escopo_id).glob("*.json"):
        try:
            fichas.append(FichaMundo.model_validate_json(caminho.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(fichas, key=lambda ficha: (ficha.tipo, ficha.titulo.lower()))


def carregar(escopo_id: str, ficha_id: str) -> Optional[FichaMundo]:
    caminho = _caminho(escopo_id, ficha_id)
    if not caminho.exists():
        return None
    return FichaMundo.model_validate_json(caminho.read_text(encoding="utf-8"))


def salvar(escopo_id: str, ficha: FichaMundo) -> None:
    caminho = _caminho(escopo_id, ficha.id)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(ficha.model_dump_json(indent=2), encoding="utf-8")
    temporario.replace(caminho)


def deletar(escopo_id: str, ficha_id: str) -> bool:
    caminho = _caminho(escopo_id, ficha_id)
    if not caminho.exists():
        return False
    caminho.unlink()
    return True


def deletar_escopo(escopo_id: str) -> None:
    """Remove todas as fichas de um escopo, incluindo pasta legada de campanha."""
    escopo_id = _id_seguro(escopo_id)
    pastas = [DATA_DIR / "wiki" / escopo_id]
    if escopo_id.startswith("campanha_"):
        pastas.append(DATA_DIR / "wiki" / escopo_id.removeprefix("campanha_"))
    for pasta in pastas:
        if pasta.exists():
            shutil.rmtree(pasta)


def deletar_da_campanha(campanha_id: str) -> None:
    deletar_escopo(f"campanha_{campanha_id}")


def copiar_fichas(escopo_origem: str, escopo_destino: str) -> None:
    """Cria arquivos independentes, preservando ids e ignorando fichas ruins."""
    for ficha in listar(escopo_origem):
        salvar(escopo_destino, ficha.model_copy(deep=True))
