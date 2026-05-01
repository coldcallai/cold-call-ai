from fastapi import APIRouter, HTTPException, status
from crud_note import note_crud
from models.note import Note

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/", response_model=Note)
def create_note(payload: dict):
    return note_crud.create(payload)

@router.get("/", response_model=list[Note])
def list_notes():
    return note_crud.list()

@router.get("/{note_id}", response_model=Note)
def get_note(note_id: str):
    note = note_crud.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/{note_id}", response_model=Note)
def update_note(note_id: str, payload: dict):
    updated = note_crud.update(note_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found")
    return updated

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str):
    deleted = note_crud.delete(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return None
