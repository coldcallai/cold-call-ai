from fastapi import APIRouter, HTTPException, status
from crud_agent import agent_crud
from models.agent import Agent

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/", response_model=Agent)
def create_agent(payload: dict):
    return agent_crud.create(payload)

@router.get("/", response_model=list[Agent])
def list_agents():
    return agent_crud.list()

@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    agent = agent_crud.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=Agent)
def update_agent(agent_id: str, payload: dict):
    updated = agent_crud.update(agent_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return updated

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str):
    deleted = agent_crud.delete(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None
