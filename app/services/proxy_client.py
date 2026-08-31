"""
Cliente de proxy para IA - permite usar API key do usuário em vez da do servidor.

Funciona como o sistema do Janitor AI: o usuário fornece sua própria chave de API
e prompt personalizado, e o servidor atua apenas como proxy para as chamadas.
"""
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import Optional
from dataclasses import dataclass

from app.config import GEMINI_MODEL
from app.prompts.sistema import SISTEMA
from app.services.ia_client import extrair_json


@dataclass
class ProxyConfig:
    """Configuração do proxy fornecida pelo usuário."""
    api_key: str
    custom_prompt: str = ""
    model: str = GEMINI_MODEL
    temperature: float = 1.0
    top_p: float = 0.95


class ErroProxy(Exception):
    """Erro técnico ao chamar a IA via proxy."""


class ErroFormatoProxy(Exception):
    """A IA respondeu, mas não em um formato utilizável."""


_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}


def _criar_modelo_proxy(config: ProxyConfig):
    """Cria um modelo Gemini configurado com as credenciais do usuário."""
    genai.configure(api_key=config.api_key)
    
    # Combina o prompt de sistema padrão com o prompt personalizado do usuário
    system_instruction = SISTEMA
    if config.custom_prompt and config.custom_prompt.strip():
        system_instruction += f"\n\n--- PROMPT PERSONALIZADO DO USUÁRIO ---\n{config.custom_prompt.strip()}"
    
    return genai.GenerativeModel(
        config.model,
        system_instruction=system_instruction,
        generation_config={
            "temperature": config.temperature,
            "top_p": config.top_p,
        },
        safety_settings=_SAFETY_SETTINGS,
    )


def gerar_texto_proxy(config: ProxyConfig, prompt: str) -> str:
    """
    Chama a IA via proxy com a configuração do usuário e devolve o texto puro.
    """
    try:
        modelo = _criar_modelo_proxy(config)
        resposta = modelo.generate_content(prompt)
        try:
            texto = resposta.text
        except ValueError as e:
            raise ErroProxy(f"A IA devolveu resposta vazia ou bloqueada: {e}") from e
        if not texto or not texto.strip():
            raise ErroProxy("A IA devolveu resposta vazia.")
        return texto.strip()
    except ErroProxy:
        raise
    except Exception as e:
        raise ErroProxy(f"Falha ao chamar a IA via proxy: {e}") from e


def gerar_json_proxy(config: ProxyConfig, prompt: str) -> dict:
    """
    Chama a IA via proxy pedindo uma resposta em JSON e faz o parse.
    """
    texto = gerar_texto_proxy(config, prompt)
    texto_limpo = extrair_json(texto)
    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError as e:
        raise ErroFormatoProxy(f"A IA não devolveu um JSON válido: {e}. Resposta bruta: {texto[:200]}") from e


def validar_chave_api(api_key: str) -> bool:
    """
    Valida se uma chave de API do Gemini é válida fazendo uma chamada de teste.
    """
    try:
        genai.configure(api_key=api_key)
        modelo = genai.GenerativeModel(GEMINI_MODEL)
        # Teste simples - apenas verifica se a chave funciona
        resposta = modelo.generate_content("Responda apenas 'OK'")
        return "OK" in (resposta.text or "").upper()
    except Exception:
        return False