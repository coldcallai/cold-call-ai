from fastapi import APIRouter, HTTPException, status
from crud_team import team_crud
from models.team import Team

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=Team)
def create_team(payload: dict):
    return team_crud.create(payload)

@router.get("/", response_model=list[Team])
def list_teams():
    return team_crud.list()

@router.get("/{team_id}", response_model=Team)
def get_team(team_id: str):
    team = team_crud.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.put("/{team_id}", response_model=Team)
def update_team(team_id: str, payload: dict):
    updated = team_crud.update(team_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Team not found")
    return updated

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: str):
    deleted = team_crud.delete(team_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team not found")
    return None
