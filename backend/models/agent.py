"""Agent-related models"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    calendly_api_token: Optional[str] = None
    calendly_event_type_uri: Optional[str] = None
    is_active: bool = True
    max_daily_calls: int = 50
    assigned_leads: int = 0
    booked_meetings: int = 0
    use_case: str = "sales_cold_calling"
    system_prompt: Optional[str] = None
    voice_type: str = "preset"
    preset_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    cloned_voice_id: Optional[str] = None
    cloned_voice_name: Optional[str] = None
    voice_settings: Optional[Dict[str, Any]] = None
    # Multi-language support
    language: str = "en"  # ISO language code
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    calendly_api_token: Optional[str] = None
    max_daily_calls: int = 50
    use_case: str = "sales_cold_calling"
    system_prompt: Optional[str] = None
    voice_type: str = "preset"
    preset_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    voice_settings: Optional[Dict[str, Any]] = None
    language: str = "en"
