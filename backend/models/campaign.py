"""Campaign-related models"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from .enums import CampaignStatus


class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    ai_script: str
    qualification_criteria: Dict[str, Any] = {}
    status: CampaignStatus = CampaignStatus.DRAFT
    calls_per_day: int = 100
    total_calls: int = 0
    successful_calls: int = 0
    qualified_leads: int = 0
    booked_meetings: int = 0
    voicemail_enabled: bool = True
    voicemail_message: Optional[str] = None
    response_wait_seconds: int = 4
    company_name: Optional[str] = None
    icp_config: Optional[Dict[str, Any]] = None
    min_icp_score: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ai_script: str
    qualification_criteria: Dict[str, Any] = {}
    calls_per_day: int = 100
    voicemail_enabled: bool = True
    voicemail_message: Optional[str] = None
    response_wait_seconds: int = 4
    company_name: Optional[str] = None
    icp_config: Optional[Dict[str, Any]] = None
    min_icp_score: int = 0
