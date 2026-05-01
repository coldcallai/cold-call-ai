from fastapi import APIRouter, HTTPException, status
from crud_script import script_crud
from models.script import Script

router = APIRouter(prefix="/scripts", tags=["scripts"])

@router.post("/", response_model=Script)
def create_script(payload: dict):
    return script_crud.create(payload)

@router.get("/", response_model=list[Script])
def list_scripts():
    return script_crud.list()

@router.get("/{script_id}", response_model=Script)
def get_script(script_id: str):
    script = script_crud.get(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.put("/{script_id}", response_model=Script)
def update_script(script_id: str, payload: dict):
    updated = script_crud.update(script_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Script not found")
    return updated

@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_script(script_id: str):
    deleted = script_crud.delete(script_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Script not found")
    return None
