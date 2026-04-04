"""Booking-related models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

from .enums import BookingStatus


class Booking(BaseModel):
    """Track scheduled meetings between leads and agents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    lead_id: str
    agent_id: str
    campaign_id: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    booking_link: str
    scheduled_time: Optional[str] = None
    calendly_event_uri: Optional[str] = None
    lead_name: str
    lead_phone: Optional[str] = None
    lead_email: Optional[str] = None
    agent_name: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BookingRequest(BaseModel):
    lead_id: str
    agent_id: str
    preferred_time: Optional[str] = None
