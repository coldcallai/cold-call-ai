from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

EventType = Literal[
    "call",
    "meeting",
    "follow_up",
    "task_deadline",
    "reminder",
]

class EventBase(BaseModel):
    lead_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_type: EventType = "follow_up"
    scheduled_for: datetime
    created_by: Optional[str] = None
    completed: bool = False

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    scheduled_for: Optional[datetime] = None
    completed: Optional[bool] = None

class Event(EventBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
