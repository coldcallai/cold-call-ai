"""Lead-related models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from .enums import LeadStatus


class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    business_name: str
    contact_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: str = "manual"
    intent_signals: List[str] = []
    status: LeadStatus = LeadStatus.NEW
    qualification_score: Optional[int] = None
    is_decision_maker: Optional[bool] = None
    interest_level: Optional[int] = None
    line_type: Optional[str] = None
    carrier: Optional[str] = None
    phone_verified: bool = False
    icp_score: Optional[int] = None
    icp_breakdown: Optional[Dict[str, Any]] = None
    dial_priority: Optional[int] = None
    notes: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LeadCreate(BaseModel):
    business_name: str
    contact_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: str = "manual"
    intent_signals: List[str] = []


class LeadDiscoveryRequest(BaseModel):
    search_query: str = "credit card processing"
    location: Optional[str] = None
    industry: Optional[str] = None
    max_results: int = 10
