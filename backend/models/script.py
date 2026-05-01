from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class ScriptBase(BaseModel):
    name: str
    description: Optional[str] = None
    opening_line: Optional[str] = None
    fallback_line: Optional[str] = None
    objection_handlers: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None
    steps: Optional[List[str]] = None
    active: bool = True

class ScriptCreate(ScriptBase):
    pass

class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    opening_line: Optional[str] = None
    fallback_line: Optional[str] = None
    objection_handlers: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None
    steps: Optional[List[str]] = None
    active: Optional[bool] = None

class Script(ScriptBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
