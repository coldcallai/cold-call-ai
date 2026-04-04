"""Follow-up related models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from .enums import FollowUpReason, FollowUpStatus


class FollowUp(BaseModel):
    """Scheduled follow-up calls for leads"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lead_id: str
    campaign_id: str
    agent_id: Optional[str] = None
    scheduled_at: str
    reason: FollowUpReason = FollowUpReason.NO_ANSWER
    status: FollowUpStatus = FollowUpStatus.SCHEDULED
    attempt_number: int = 1
    max_attempts: int = 3
    original_call_id: Optional[str] = None
    notes: Optional[str] = None
    callback_time_preference: Optional[str] = None
    result_call_id: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FollowUpCreate(BaseModel):
    lead_id: str
    campaign_id: str
    scheduled_at: str
    reason: FollowUpReason = FollowUpReason.NO_ANSWER
    notes: Optional[str] = None
    callback_time_preference: Optional[str] = None
    max_attempts: int = 3


class FollowUpSequence(BaseModel):
    """Multi-touch follow-up sequence template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    steps: List[Dict[str, Any]] = []
    max_attempts_per_step: int = 2
    stop_on_connect: bool = True
    stop_on_booking: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CampaignFollowUpSettings(BaseModel):
    """Follow-up settings for a campaign"""
    enabled: bool = True
    no_answer_retry_enabled: bool = True
    no_answer_retry_count: int = 3
    no_answer_retry_delay_hours: int = 24
    voicemail_followup_enabled: bool = True
    voicemail_followup_delay_hours: int = 48
    callback_buffer_minutes: int = 15
    sequence_id: Optional[str] = None
