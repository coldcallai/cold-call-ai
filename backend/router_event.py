from fastapi import APIRouter, HTTPException, status
from crud_event import event_crud
from models.event import Event

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/", response_model=Event)
def create_event(payload: dict):
    return event_crud.create(payload)

@router.get("/", response_model=list[Event])
def list_events():
    return event_crud.list()

@router.get("/{event_id}", response_model=Event)
def get_event(event_id: str):
    event = event_crud.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=Event)
def update_event(event_id: str, payload: dict):
    updated = event_crud.update(event_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str):
    deleted = event_crud.delete(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return None
