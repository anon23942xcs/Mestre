"""API dos personagens reutilizáveis do jogador."""
from fastapi import APIRouter, HTTPException

from app.models.personagem import Personagem
from app.models.requests import PersonagemRequest
from app.storage import personagem_repositorio

router = APIRouter(prefix="/api/personagens", tags=["personagens"])


@router.get("", response_model=list[Personagem])
async def listar_personagens():
    return personagem_repositorio.listar()


@router.get("/{personagem_id}", response_model=Personagem)
async def obter_personagem(personagem_id: str):
    personagem = personagem_repositorio.carregar(personagem_id)
    if not personagem:
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    return personagem


@router.post("", response_model=Personagem, status_code=201)
async def criar_personagem(dados: PersonagemRequest):
    personagem = Personagem(id=personagem_repositorio.novo_id(), **dados.model_dump())
    personagem_repositorio.salvar(personagem)
    return personagem


@router.put("/{personagem_id}", response_model=Personagem)
async def editar_personagem(personagem_id: str, dados: PersonagemRequest):
    personagem = personagem_repositorio.carregar(personagem_id)
    if not personagem:
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    for campo, valor in dados.model_dump().items():
        setattr(personagem, campo, valor)
    personagem_repositorio.salvar(personagem)
    return personagem


@router.delete("/{personagem_id}")
async def apagar_personagem(personagem_id: str):
    if not personagem_repositorio.deletar(personagem_id):
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    return {"mensagem": "Personagem apagado"}
