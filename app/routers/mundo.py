"""CRUD dos mundos canônicos e de suas fichas-base."""
from fastapi import APIRouter, HTTPException

from app.models.ficha import FichaMundo
from app.models.mundo import Mundo
from app.models.requests import FichaMundoRequest, MundoRequest
from app.storage import ficha_repositorio, mundo_repositorio

router = APIRouter(prefix="/api/mundos", tags=["mundos"])


def _exigir_mundo(mundo_id: str) -> Mundo:
    mundo = mundo_repositorio.carregar(mundo_id)
    if not mundo:
        raise HTTPException(status_code=404, detail="Mundo não encontrado")
    return mundo


def _escopo(mundo_id: str) -> str:
    return f"mundo_{mundo_id}"


@router.get("", response_model=list[Mundo])
async def listar_mundos():
    return mundo_repositorio.listar()


@router.post("", response_model=Mundo, status_code=201)
async def criar_mundo(dados: MundoRequest):
    mundo = Mundo(id=mundo_repositorio.novo_id(), **dados.model_dump())
    mundo_repositorio.salvar(mundo)
    return mundo


@router.get("/{mundo_id}", response_model=Mundo)
async def obter_mundo(mundo_id: str):
    return _exigir_mundo(mundo_id)


@router.put("/{mundo_id}", response_model=Mundo)
async def editar_mundo(mundo_id: str, dados: MundoRequest):
    mundo = _exigir_mundo(mundo_id)
    for campo, valor in dados.model_dump().items():
        setattr(mundo, campo, valor)
    mundo_repositorio.salvar(mundo)
    return mundo


@router.delete("/{mundo_id}")
async def apagar_mundo(mundo_id: str):
    _exigir_mundo(mundo_id)
    mundo_repositorio.deletar(mundo_id)
    ficha_repositorio.deletar_escopo(_escopo(mundo_id))
    return {"mensagem": "Mundo apagado"}


@router.get("/{mundo_id}/fichas", response_model=list[FichaMundo])
async def listar_fichas(mundo_id: str):
    _exigir_mundo(mundo_id)
    return ficha_repositorio.listar(_escopo(mundo_id))


@router.post("/{mundo_id}/fichas", response_model=FichaMundo, status_code=201)
async def criar_ficha(mundo_id: str, dados: FichaMundoRequest):
    _exigir_mundo(mundo_id)
    ficha = FichaMundo(id=ficha_repositorio.novo_id(), **dados.model_dump())
    ficha_repositorio.salvar(_escopo(mundo_id), ficha)
    return ficha


@router.get("/{mundo_id}/fichas/{ficha_id}", response_model=FichaMundo)
async def obter_ficha(mundo_id: str, ficha_id: str):
    _exigir_mundo(mundo_id)
    ficha = ficha_repositorio.carregar(_escopo(mundo_id), ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha não encontrada")
    return ficha


@router.put("/{mundo_id}/fichas/{ficha_id}", response_model=FichaMundo)
async def editar_ficha(mundo_id: str, ficha_id: str, dados: FichaMundoRequest):
    _exigir_mundo(mundo_id)
    ficha = ficha_repositorio.carregar(_escopo(mundo_id), ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha não encontrada")
    for campo, valor in dados.model_dump().items():
        setattr(ficha, campo, valor)
    ficha_repositorio.salvar(_escopo(mundo_id), ficha)
    return ficha


@router.delete("/{mundo_id}/fichas/{ficha_id}")
async def apagar_ficha(mundo_id: str, ficha_id: str):
    _exigir_mundo(mundo_id)
    if not ficha_repositorio.deletar(_escopo(mundo_id), ficha_id):
        raise HTTPException(status_code=404, detail="Ficha não encontrada")
    return {"mensagem": "Ficha apagada"}
