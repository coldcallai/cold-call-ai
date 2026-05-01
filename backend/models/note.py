from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class NoteBase(BaseModel):
    lead_id: str
    content: str
    created_by: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    content: Optional[str] = None

class Note(NoteBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
