from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

UserRole = Literal["owner", "admin", "manager", "sales", "viewer"]

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    role: UserRole = "sales"
    team_id: Optional[str] = None
    active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    team_id: Optional[str] = None
    active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
