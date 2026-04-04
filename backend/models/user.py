"""User-related models"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .enums import UserRole, SubscriptionTier


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    phone_number: Optional[str] = None
    phone_verified: bool = False
    picture: Optional[str] = None
    role: UserRole = UserRole.USER
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: str = "inactive"
    lead_credits_remaining: int = 0
    call_credits_remaining: int = 0
    monthly_lead_allowance: int = 0
    monthly_call_allowance: int = 0
    team_seat_count: int = 1
    saved_keywords: List[str] = []
    onboarding_completed: bool = False
    trial_minutes_total: float = 15.0
    trial_seconds_used: float = 0.0
    trial_expired: bool = False
    compliance_acknowledged: bool = False
    compliance_acknowledged_at: Optional[str] = None
    compliance_acknowledged_version: Optional[str] = None
    ftc_san: Optional[str] = None
    calling_mode: str = "b2b"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone_number: str
    verification_code: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PhoneVerificationRequest(BaseModel):
    phone_number: str
    email: EmailStr


class PhoneVerificationConfirm(BaseModel):
    phone_number: str
    code: str


class PasswordUser(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    password_hash: str
    role: UserRole = UserRole.USER
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: str = "inactive"
    lead_credits_remaining: int = 0
    call_credits_remaining: int = 0
    monthly_lead_allowance: int = 0
    monthly_call_allowance: int = 0
    team_seat_count: int = 1
    trial_minutes_total: float = 15.0
    trial_seconds_used: float = 0.0
    trial_expired: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OAuthPhoneVerification(BaseModel):
    phone_number: str
    verification_code: str
