from fastapi import APIRouter, HTTPException, status
from crud_interaction import interaction_crud
from models.interaction import Interaction

router = APIRouter(prefix="/interactions", tags=["interactions"])

@router.post("/", response_model=Interaction)
def create_interaction(payload: dict):
    return interaction_crud.create(payload)

@router.get("/", response_model=list[Interaction])
def list_interactions():
    return interaction_crud.list()

@router.get("/{interaction_id}", response_model=Interaction)
def get_interaction(interaction_id: str):
    interaction = interaction_crud.get(interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@router.put("/{interaction_id}", response_model=Interaction)
def update_interaction(interaction_id: str, payload: dict):
    updated = interaction_crud.update(interaction_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return updated

@router.delete("/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interaction(interaction_id: str):
    deleted = interaction_crud.delete(interaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return None
