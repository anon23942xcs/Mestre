"""
Camada de persistência.

Antes existia um único arquivo global (estado_salvo.json), então duas
campanhas simultâneas se sobrescreviam. Agora cada campanha vira um arquivo
próprio em data/{campanha_id}.json, identificado por um UUID.

Isso ainda é armazenamento em arquivo, não um banco de dados de verdade.
Para uma dezena de jogadores testando, é suficiente. Para produção com
usuários reais e pagamento (Modo Mestre premium), o passo natural depois
é trocar esta camada por um banco (Postgres/SQLite) sem precisar mexer no
resto do sistema, já que todo o resto do código só conhece as funções
carregar/salvar/deletar abaixo, não o formato de armazenamento em si.
"""
import json
import uuid
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.models.estado import EstadoCompleto


def novo_id() -> str:
    return uuid.uuid4().hex[:12]


def _caminho(campanha_id: str) -> Path:
    # Sanitização simples do id para não permitir path traversal
    # (ex: campanha_id="../../etc/passwd").
    id_seguro = "".join(c for c in campanha_id if c.isalnum())
    if not id_seguro:
        raise ValueError("campanha_id inválido")
    return DATA_DIR / f"{id_seguro}.json"


def carregar(campanha_id: str) -> Optional[EstadoCompleto]:
    caminho = _caminho(campanha_id)
    if not caminho.exists():
        return None
    with caminho.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    return EstadoCompleto.model_validate(dados)


def salvar(estado: EstadoCompleto) -> None:
    caminho = _caminho(estado.campanha_id)
    with caminho.open("w", encoding="utf-8") as f:
        f.write(estado.model_dump_json(indent=2))


def deletar(campanha_id: str) -> bool:
    caminho = _caminho(campanha_id)
    if caminho.exists():
        caminho.unlink()
        return True
    return False


def existe(campanha_id: str) -> bool:
    return _caminho(campanha_id).exists()
