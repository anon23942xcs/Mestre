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

    Otimização: lê apenas os primeiros ~4 KB de cada arquivo para extrair
    os campos de resumo sem parsear o JSON inteiro (que pode passar de 50 KB
    em campanhas longas).
    """
    import re

    _RE_CAMPO = {
        "campanha_id": re.compile(r'"campanha_id"\s*:\s*"([^"]*)"'),
        "mundo_id": re.compile(r'"mundo_id"\s*:\s*"([^"]*)"'),
        "mundo": re.compile(r'"mundo"\s*:\s*"([^"]*)"'),
        "turno": re.compile(r'"turno"\s*:\s*(\d+)'),
        "ultima_atualizacao": re.compile(r'"ultima_atualizacao"\s*:\s*"([^"]*)"'),
    }

    resumos = []
    for caminho in DATA_DIR.glob("*.json"):
        try:
            with caminho.open("r", encoding="utf-8") as f:
                cabecalho = f.read(4096)

            resumo = {
                "campanha_id": caminho.stem,
                "mundo_id": None,
                "mundo": "Mundo não identificado",
                "personagem_id": None,
                "nome_jogador": "?",
                "local": "?",
                "turno": 0,
                "ultima_atualizacao": "",
            }

            for campo, regex in _RE_CAMPO.items():
                m = regex.search(cabecalho)
                if m:
                    resumo[campo] = int(m.group(1)) if campo == "turno" else m.group(1)

            # jogador.nome e jogador.personagem_id estão aninhados; regex simples
            m_nome = re.search(r'"jogador"\s*:\s*\{[^}]*"nome"\s*:\s*"([^"]*)"', cabecalho, re.DOTALL)
            if m_nome:
                resumo["nome_jogador"] = m_nome.group(1)
            m_pid = re.search(r'"jogador"\s*:\s*\{[^}]*"personagem_id"\s*:\s*"([^"]*)"', cabecalho, re.DOTALL)
            if m_pid:
                resumo["personagem_id"] = m_pid.group(1)

            # estado.local também aninhado
            m_local = re.search(r'"estado"\s*:\s*\{[^}]*"local"\s*:\s*"([^"]*)"', cabecalho, re.DOTALL)
            if m_local:
                resumo["local"] = m_local.group(1)

            resumos.append(resumo)
        except OSError:
            continue
    resumos.sort(key=lambda r: r["ultima_atualizacao"], reverse=True)
    return resumos
