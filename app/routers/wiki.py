"""Rotas independentes do catálogo canônico da Wiki."""
from fastapi import APIRouter, HTTPException

from app.models.ficha import FichaMundo
from app.models.requests import FichaMundoRequest
from app.storage import ficha_repositorio, repositorio

router = APIRouter(prefix="/campanhas/{campanha_id}/catalogo", tags=["wiki"])


def _exigir_campanha(campanha_id: str) -> None:
    if not repositorio.existe(campanha_id):
        raise HTTPException(status_code=404, detail="Campanha não encontrada")


@router.get("", response_model=list[FichaMundo])
async def listar_fichas(campanha_id: str):
    _exigir_campanha(campanha_id)
    return ficha_repositorio.listar(campanha_id)


@router.post("", response_model=FichaMundo, status_code=201)
async def criar_ficha(campanha_id: str, dados: FichaMundoRequest):
    _exigir_campanha(campanha_id)
    ficha = FichaMundo(id=ficha_repositorio.novo_id(), **dados.model_dump())
    ficha_repositorio.salvar(campanha_id, ficha)
    return ficha


@router.put("/{ficha_id}", response_model=FichaMundo)
async def editar_ficha(campanha_id: str, ficha_id: str, dados: FichaMundoRequest):
    _exigir_campanha(campanha_id)
    ficha = ficha_repositorio.carregar(campanha_id, ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha não encontrada")
    for campo, valor in dados.model_dump().items():
        setattr(ficha, campo, valor)
    ficha_repositorio.salvar(campanha_id, ficha)
    return ficha


@router.delete("/{ficha_id}")
async def apagar_ficha(campanha_id: str, ficha_id: str):
    _exigir_campanha(campanha_id)
    if not ficha_repositorio.deletar(campanha_id, ficha_id):
        raise HTTPException(status_code=404, detail="Ficha não encontrada")
    return {"mensagem": "Ficha apagada"}
