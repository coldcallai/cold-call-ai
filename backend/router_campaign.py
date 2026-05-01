from fastapi import APIRouter, HTTPException, status
from crud_campaign import campaign_crud
from models.campaign import Campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

@router.post("/", response_model=Campaign)
def create_campaign(payload: dict):
    return campaign_crud.create(payload)

@router.get("/", response_model=list[Campaign])
def list_campaigns():
    return campaign_crud.list()

@router.get("/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: str):
    campaign = campaign_crud.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.put("/{campaign_id}", response_model=Campaign)
def update_campaign(campaign_id: str, payload: dict):
    updated = campaign_crud.update(campaign_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: str):
    deleted = campaign_crud.delete(campaign_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return None
