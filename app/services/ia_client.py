"""
Cliente único de chamadas à IA.

Antes, main.py e ia_service.py cada um configurava o genai e montava prompts
quase idênticos, de forma duplicada e sem nenhum ponto único de manutenção.
Agora só existe esse módulo falando com o Gemini.

Mudanças nesta versão:
- system_instruction fixo (app/prompts/sistema.py) com regras de formatação
  e o enquadramento de ficção interativa, para reduzir recusas em cenas de
  combate e deixar a formatação (aspas/asteriscos) consistente.
- generation_config explícito (temperatura mais alta = respostas menos secas).
- safety_settings ajustados para as categorias de harassment/dangerous
  content, que são as que mais tendem a disparar em cenas de luta ficcional.
  Conteúdo sexual e discurso de ódio continuam no padrão da API.
"""
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.prompts.sistema import SISTEMA


class ErroIA(Exception):
    """Erro técnico ao chamar a IA (rede, cota, chave ausente, etc.)."""


class ErroFormatoIA(Exception):
    """A IA respondeu, mas não em um formato utilizável (ex: JSON malformado)."""


_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

_GENERATION_CONFIG = {
    "temperature": 1.0,
    "top_p": 0.95,
}

_modelo = None


def _obter_modelo():
    global _modelo
    if _modelo is not None:
        return _modelo
    if not GEMINI_API_KEY:
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    _modelo = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=SISTEMA,
        generation_config=_GENERATION_CONFIG,
        safety_settings=_SAFETY_SETTINGS,
    )
    return _modelo


def disponivel() -> bool:
    return _obter_modelo() is not None


def gerar_texto(prompt: str) -> str:
    """Chama a IA e devolve o texto puro da resposta."""
    modelo = _obter_modelo()
    if modelo is None:
        raise ErroIA("GEMINI_API_KEY não configurada. Defina-a no arquivo .env.")
    try:
        resposta = modelo.generate_content(prompt)
        try:
            texto = resposta.text
        except ValueError as e:
            raise ErroIA(f"A IA devolveu resposta vazia ou bloqueada: {e}") from e
        if not texto or not texto.strip():
            raise ErroIA("A IA devolveu resposta vazia.")
        return texto.strip()
    except ErroIA:
        raise
    except Exception as e:
        raise ErroIA(f"Falha ao chamar a IA: {e}") from e


def gerar_json(prompt: str) -> dict:
    """
    Chama a IA pedindo uma resposta em JSON e faz o parse.

    Modelos de linguagem costumam envolver o JSON em blocos de código
    markdown (```json ... ```) mesmo quando instruídos a não fazer isso,
    então extraímos o bloco antes de tentar o parse.
    """
    texto = gerar_texto(prompt)
    texto_limpo = extrair_json(texto)
    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError as e:
        raise ErroFormatoIA(f"A IA não devolveu um JSON válido: {e}. Resposta bruta: {texto[:200]}") from e


def extrair_json(texto: str) -> str:
    # Remove cercas de código markdown, se existirem.
    match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", texto, re.DOTALL)
    if match:
        return match.group(1)
    # Se não tem cerca, tenta achar o primeiro { ... } ou [ ... ] do texto.
    match = re.search(r"(\{.*\}|\[.*\])", texto, re.DOTALL)
    if match:
        return match.group(1)
    return texto
