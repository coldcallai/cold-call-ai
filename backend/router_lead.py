from fastapi import APIRouter, HTTPException, status
from crud_lead import lead_crud
from models.lead import Lead

router = APIRouter(prefix="/leads", tags=["leads"])

@router.post("/", response_model=Lead)
def create_lead(payload: dict):
    return lead_crud.create(payload)

@router.get("/", response_model=list[Lead])
def list_leads():
    return lead_crud.list()

@router.get("/{lead_id}", response_model=Lead)
def get_lead(lead_id: str):
    lead = lead_crud.get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=Lead)
def update_lead(lead_id: str, payload: dict):
    updated = lead_crud.update(lead_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return updated

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: str):
    deleted = lead_crud.delete(lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead not found")
    return None
