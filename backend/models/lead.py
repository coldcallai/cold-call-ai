from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

LeadStatus = Literal[
    "new",
    "contacted",
    "qualified",
    "booked",
    "closed_won",
    "closed_lost",
    "not_qualified",
]

class LeadBase(BaseModel):
    business_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    status: LeadStatus = "new"
    qualification_score: int = 0
    icp_score: int = 0
    campaign_id: Optional[str] = None
    agent_id: Optional[str] = None
    source: Optional[str] = "manual"

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    business_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[LeadStatus] = None
    qualification_score: Optional[int] = None
    icp_score: Optional[int] = None
    campaign_id: Optional[str] = None
    agent_id: Optional[str] = None

class Lead(LeadBase):
    id: str = Field(alias="_id")
    notes_count: int = 0
    tasks_count: int = 0
    last_contacted_at: Optional[datetime] = None
    next_action_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
