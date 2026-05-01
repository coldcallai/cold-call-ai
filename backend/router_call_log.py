from fastapi import APIRouter, HTTPException, status
from crud_call_log import call_log_crud
from models.call_log import CallLog

router = APIRouter(prefix="/call_logs", tags=["call_logs"])

@router.post("/", response_model=CallLog)
def create_call_log(payload: dict):
    return call_log_crud.create(payload)

@router.get("/", response_model=list[CallLog])
def list_call_logs():
    return call_log_crud.list()

@router.get("/{log_id}", response_model=CallLog)
def get_call_log(log_id: str):
    log = call_log_crud.get(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Call log not found")
    return log

@router.put("/{log_id}", response_model=CallLog)
def update_call_log(log_id: str, payload: dict):
    updated = call_log_crud.update(log_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Call log not found")
    return updated

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call_log(log_id: str):
    deleted = call_log_crud.delete(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Call log not found")
    return None
