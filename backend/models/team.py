from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

RoleType = Literal["owner", "admin", "manager", "sales"]

class TeamMember(BaseModel):
    user_id: str
    role: RoleType = "sales"
    active: bool = True

class TeamBase(BaseModel):
    name: str
    company_domain: Optional[str] = None
    members: List[TeamMember] = []
    active: bool = True
    call_transfer_number: Optional[str] = None
    default_agent_id: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    company_domain: Optional[str] = None
    members: Optional[List[TeamMember]] = None
    active: Optional[bool] = None
    call_transfer_number: Optional[str] = None
    default_agent_id: Optional[str] = None

class Team(TeamBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
