from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

TaskStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "overdue",
]

class TaskBase(BaseModel):
    lead_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: TaskStatus = "pending"
    assigned_to: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    assigned_to: Optional[str] = None

class Task(TaskBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
