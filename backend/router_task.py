from fastapi import APIRouter, HTTPException, status
from crud_task import task_crud
from models.task import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=Task)
def create_task(payload: dict):
    return task_crud.create(payload)

@router.get("/", response_model=list[Task])
def list_tasks():
    return task_crud.list()

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = task_crud.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=Task)
def update_task(task_id: str, payload: dict):
    updated = task_crud.update(task_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    deleted = task_crud.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
