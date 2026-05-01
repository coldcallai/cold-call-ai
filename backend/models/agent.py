from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

AgentType = Literal["ai", "human"]

class AgentBase(BaseModel):
    name: str
    agent_type: AgentType = "ai"
    phone_number: Optional[str] = None
    email: Optional[str] = None
    active: bool = True
    voice_id: Optional[str] = None
    personality_profile: Optional[str] = None

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    agent_type: Optional[AgentType] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None
    voice_id: Optional[str] = None
    personality_profile: Optional[str] = None

class Agent(AgentBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
