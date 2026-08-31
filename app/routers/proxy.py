from fastapi import APIRouter, HTTPException

from app.models.proxy import ConfiguracaoProxy
from app.prompts.sistema import SISTEMA
from app.services.ia_client import ErroIA
from app.services.proxy_client import gerar_texto_proxy, ProxyConfig

router = APIRouter(prefix="/proxy", tags=["proxy"])


@router.get("/prompt-global")
async def prompt_global():
    return {"prompt": SISTEMA}


@router.post("/testar")
async def testar_proxy(config: ConfiguracaoProxy):
    try:
        # Converte ConfiguracaoProxy para ProxyConfig
        proxy_config = ProxyConfig(
            api_key=config.chave,
            custom_prompt=config.prompt_personalizado,
            model=config.modelo,
        )
        texto = gerar_texto_proxy(proxy_config, "Responda com exatamente esta palavra: ok")
    except ErroIA as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True, "trecho": texto[:240]}
