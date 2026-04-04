"""Call-related models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from .enums import CallStatus


class Call(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    lead_id: str
    campaign_id: str
    agent_id: Optional[str] = None
    status: CallStatus = CallStatus.PENDING
    duration_seconds: int = 0
    transcript: List[Dict[str, str]] = []
    qualification_result: Optional[Dict[str, Any]] = None
    answered_by: Optional[str] = None
    voicemail_dropped: bool = False
    amd_status: Optional[str] = None
    recording_url: Optional[str] = None
    recording_sid: Optional[str] = None
    recording_duration_seconds: Optional[int] = None
    full_transcript: Optional[str] = None
    transcript_segments: Optional[List[Dict[str, Any]]] = None
    transcription_status: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QualificationResult(BaseModel):
    is_qualified: bool
    is_decision_maker: bool
    interest_level: int
    score: int
    notes: List[str]
