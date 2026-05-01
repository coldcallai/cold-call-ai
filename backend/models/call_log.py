from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

CallDirection = Literal["outbound", "inbound"]
CallStatus = Literal[
    "initiated",
    "ringing",
    "answered",
    "completed",
    "failed",
    "no_answer",
    "busy",
]

class CallLogBase(BaseModel):
    lead_id: Optional[str] = None
    agent_id: Optional[str] = None
    direction: CallDirection = "outbound"
    status: CallStatus = "initiated"
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_sentiment: Optional[str] = None
    duration_seconds: Optional[int] = None
    qualification_score: Optional[int] = None
    icp_score: Optional[int] = None

class CallLogCreate(CallLogBase):
    pass

class CallLogUpdate(BaseModel):
    status: Optional[CallStatus] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_sentiment: Optional[str] = None
    duration_seconds: Optional[int] = None
    qualification_score: Optional[int] = None
    icp_score: Optional[int] = None

class CallLog(CallLogBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
