"""
Ponto de entrada da aplicação.

Antes, este arquivo tinha ~400 linhas: modelos, lógica de IA, HTML embutido
e as rotas, tudo junto. Agora ele só monta o app e registra as peças que
vivem em app/models, app/services, app/storage e app/routers.
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import campanha, wiki

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Mestre", version="2.2.0")

app.include_router(campanha.router)
app.include_router(wiki.router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def raiz():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/saude")
async def saude():
    from app.services.ia_client import disponivel

    return {"ok": True, "ia_configurada": disponivel()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
