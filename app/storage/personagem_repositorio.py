"""Persistência dos personagens do jogador, separada das campanhas."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.models.personagem import Personagem


def _id_seguro(valor: str) -> str:
    if not valor or not valor.replace("_", "").isalnum():
        raise ValueError("id inválido")
    return valor


def _pasta() -> Path:
    pasta = DATA_DIR / "personagens"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _caminho(personagem_id: str) -> Path:
    return _pasta() / f"{_id_seguro(personagem_id)}.json"


def novo_id() -> str:
    return f"personagem_{uuid.uuid4().hex[:12]}"


def listar() -> list[Personagem]:
    personagens = []
    for caminho in _pasta().glob("*.json"):
        try:
            personagens.append(Personagem.model_validate_json(caminho.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(personagens, key=lambda personagem: personagem.nome.lower())


def carregar(personagem_id: str) -> Optional[Personagem]:
    caminho = _caminho(personagem_id)
    if not caminho.exists():
        return None
    return Personagem.model_validate_json(caminho.read_text(encoding="utf-8"))


def salvar(personagem: Personagem) -> None:
    personagem.ultima_atualizacao = datetime.now().isoformat()
    caminho = _caminho(personagem.id)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(personagem.model_dump_json(indent=2), encoding="utf-8")
    temporario.replace(caminho)


def deletar(personagem_id: str) -> bool:
    caminho = _caminho(personagem_id)
    if not caminho.exists():
        return False
    caminho.unlink()
    return True
