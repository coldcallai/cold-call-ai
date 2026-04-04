"""CRM Integration models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

from .enums import CRMProvider


class CRMCredentials(BaseModel):
    provider: CRMProvider
    api_key: Optional[str] = None
    instance_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    is_connected: bool = False
    connected_at: Optional[str] = None
    last_sync_at: Optional[str] = None
    sync_enabled: bool = True
    sync_leads: bool = True
    sync_calls: bool = True
    sync_bookings: bool = True
    field_mapping: dict = {}


class CRMLeadPushLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lead_id: str
    provider: CRMProvider
    crm_record_id: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None
    pushed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CRMConnectionRequest(BaseModel):
    provider: CRMProvider
    api_key: Optional[str] = None
    instance_url: Optional[str] = None


class WebhookConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    url: str
    events: list = []
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebhookConfigCreate(BaseModel):
    name: str
    url: str
    events: list = []
