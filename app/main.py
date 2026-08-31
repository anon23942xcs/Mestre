"""
Ponto de entrada da aplicação.

Antes, este arquivo tinha ~400 linhas: modelos, lógica de IA, HTML embutido
e as rotas, tudo junto. Agora ele só monta o app e registra as peças que
vivem em app/models, app/services, app/storage e app/routers.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import campanha

app = FastAPI(title="Mestre", version="2.0")

app.include_router(campanha.router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def raiz():
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    print("Mestre - Servidor iniciado em http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
