from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    agent_id: Optional[str] = None
    script_id: Optional[str] = None
    active: bool = True
    lead_sources: Optional[List[str]] = None
    daily_call_limit: Optional[int] = None
    timezone: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_id: Optional[str] = None
    script_id: Optional[str] = None
    active: Optional[bool] = None
    lead_sources: Optional[List[str]] = None
    daily_call_limit: Optional[int] = None
    timezone: Optional[str] = None

class Campaign(CampaignBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
