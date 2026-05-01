from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

InteractionType = Literal[
    "note",
    "call",
    "task",
    "status_change",
    "ai_action",
    "human_action",
]

class InteractionBase(BaseModel):
    lead_id: str
    interaction_type: InteractionType
    description: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[dict] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    description: Optional[str] = None
    metadata: Optional[dict] = None

class Interaction(InteractionBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
