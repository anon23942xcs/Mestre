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

AVISO DE ESCALABILIDADE:
- Com ~100+ campanhas simultâneas, I/O em disco por turno vira gargalo.
- Com >10 usuários salvando/carregando em paralelo, considere:
  1. Cache (Redis) para estado recente
  2. Banco de dados (Postgres) para persistência
  3. Índice em campanha_id para queries rápidas
"""
import json
import threading
import uuid
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from app.config import DATA_DIR
from app.models.estado import EstadoCompleto

_locks_por_id: dict[str, threading.Lock] = defaultdict(threading.Lock)
_locks_meta = threading.Lock()


def novo_id() -> str:
    return uuid.uuid4().hex[:12]


def _id_seguro(campanha_id: str) -> str:
    if not campanha_id or not campanha_id.isalnum():
        raise ValueError("campanha_id inválido")
    return campanha_id


def _caminho(campanha_id: str) -> Path:
    return DATA_DIR / f"{_id_seguro(campanha_id)}.json"


@contextmanager
def bloqueio(campanha_id: str) -> Iterator[None]:
    """Evita dois turnos da mesma campanha gravando o arquivo ao mesmo tempo."""
    chave = _id_seguro(campanha_id)
    with _locks_meta:
        lock = _locks_por_id[chave]
    with lock:
        yield


def carregar(campanha_id: str) -> Optional[EstadoCompleto]:
    caminho = _caminho(campanha_id)
    if not caminho.exists():
        return None
    with caminho.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    return EstadoCompleto.model_validate(dados)


def salvar(estado: EstadoCompleto) -> None:
    caminho = _caminho(estado.campanha_id)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(estado.model_dump_json(indent=2), encoding="utf-8")
    temporario.replace(caminho)


def deletar(campanha_id: str) -> bool:
    caminho = _caminho(campanha_id)
    if caminho.exists():
        caminho.unlink()
        return True
    return False


def existe(campanha_id: str) -> bool:
    return _caminho(campanha_id).exists()


def listar() -> list[dict]:
    """
    Lista um resumo de todas as campanhas salvas em disco, mais recente
    primeiro. Usada para o jogador poder escolher qual campanha retomar,
    em vez de só a última guardada no localStorage do navegador.
    """
    resumos = []
    for caminho in DATA_DIR.glob("*.json"):
        try:
            with caminho.open("r", encoding="utf-8") as f:
                dados = json.load(f)
            resumos.append({
                "campanha_id": dados.get("campanha_id", caminho.stem),
                "mundo_id": dados.get("mundo_id"),
                "mundo": dados.get("mundo", "Mundo não identificado"),
                "personagem_id": dados.get("jogador", {}).get("personagem_id"),
                "nome_jogador": dados.get("jogador", {}).get("nome", "?"),
                "local": dados.get("estado", {}).get("local", "?"),
                "turno": dados.get("turno", 0),
                "ultima_atualizacao": dados.get("ultima_atualizacao", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue  # arquivo corrompido ou ilegível, ignora em vez de quebrar a lista inteira
    resumos.sort(key=lambda r: r["ultima_atualizacao"], reverse=True)
    return resumos
