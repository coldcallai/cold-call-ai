from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File, Depends, Request, Response, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import asyncio
import random
import resend
import csv
import io
import httpx
import base64
import json
import hashlib
import secrets
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import stripe
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Connect, Stream
import requests  # For Calendly API calls and object storage
from emergentintegrations.llm.openai import OpenAISpeechToText

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============== FEATURE FLAGS FOR GRADUAL MIGRATION ==============
# These flags allow incremental refactoring with instant rollback capability
USE_NEW_AUTH_ROUTES = os.getenv("USE_NEW_AUTH_ROUTES", "false").lower() == "true"
USE_NEW_LEADS_ROUTES = os.getenv("USE_NEW_LEADS_ROUTES", "false").lower() == "true"
USE_NEW_AGENTS_ROUTES = os.getenv("USE_NEW_AGENTS_ROUTES", "false").lower() == "true"
USE_NEW_CAMPAIGNS_ROUTES = os.getenv("USE_NEW_CAMPAIGNS_ROUTES", "false").lower() == "true"

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
# Only use TLS for remote connections (not localhost)
is_localhost = 'localhost' in mongo_url or '127.0.0.1' in mongo_url
if is_localhost:
    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000
    )
else:
    # Add TLS options for remote MongoDB connections
    client = AsyncIOMotorClient(
        mongo_url,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000
    )
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dialgenix_default_secret_key')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing - using simple hashlib to avoid bcrypt issues
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, hash_hex = hashed.split('$')
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == hash_hex
    except:
        return False

# Security
security = HTTPBearer(auto_error=False)

# ElevenLabs client (for TTS)
elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY')
eleven_client = ElevenLabs(api_key=elevenlabs_api_key) if elevenlabs_api_key else None

# Stripe configuration
stripe_api_key = os.environ.get('STRIPE_API_KEY')
if stripe_api_key:
    stripe.api_key = stripe_api_key

# Twilio configuration
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token) if twilio_account_sid and twilio_auth_token else None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Cold Calling Machine")
api_router = APIRouter(prefix="/api")

# ============== ENUMS ==============
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    BOOKED = "booked"

class CallStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    UNLIMITED = "unlimited"
    BYL = "byl"  # Bring Your List

# ============== USER MODELS ==============
class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    phone_number: Optional[str] = None  # Verified phone number for trial abuse prevention
    phone_verified: bool = False  # Whether phone was verified via SMS
    picture: Optional[str] = None
    role: UserRole = UserRole.USER
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_status: str = "inactive"  # active, past_due, canceled, trialing
    lead_credits_remaining: int = 0
    call_credits_remaining: int = 0
    monthly_lead_allowance: int = 0
    monthly_call_allowance: int = 0
    team_seat_count: int = 1
    saved_keywords: List[str] = []  # User's saved intent keywords (up to 100)
    onboarding_completed: bool = False  # Track if user completed onboarding
    # Synthflow-style free trial: 15 minutes of call time (no credit card required)
    trial_minutes_total: float = 15.0  # Total trial minutes granted
    trial_seconds_used: float = 0.0  # Seconds of call time used during trial
    trial_expired: bool = False  # True when trial minutes exhausted
    # Compliance acknowledgment
    compliance_acknowledged: bool = False  # Must acknowledge before making calls
    compliance_acknowledged_at: Optional[str] = None
    compliance_acknowledged_version: Optional[str] = None  # Track which version they agreed to
    ftc_san: Optional[str] = None  # FTC Subscription Account Number (for B2C callers)
    calling_mode: str = "b2b"  # "b2b" (no DNC needed) or "b2c" (DNC required)
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
    phone_number: str  # Required for trial abuse prevention
    verification_code: str  # SMS verification code

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Phone verification models for trial abuse prevention
class PhoneVerificationRequest(BaseModel):
    phone_number: str
    email: EmailStr  # To check if email is already registered

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
    # Synthflow-style free trial: 15 minutes of call time
    trial_minutes_total: float = 15.0
    trial_seconds_used: float = 0.0
    trial_expired: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== MODELS ==============
class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Owner of this lead (for multi-tenancy)
    business_name: str
    contact_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None  # "1-10", "11-50", "51-200", "201-500", "500+"
    source: str = "manual"
    intent_signals: List[str] = []
    status: LeadStatus = LeadStatus.NEW
    qualification_score: Optional[int] = None
    is_decision_maker: Optional[bool] = None
    interest_level: Optional[int] = None
    # Phone verification fields
    line_type: Optional[str] = None  # "mobile", "landline", "voip", "unknown"
    carrier: Optional[str] = None  # Phone carrier name
    phone_verified: bool = False  # Whether phone was verified via Twilio Lookup
    # ICP Scoring fields
    icp_score: Optional[int] = None  # 0-100 overall ICP fit score
    icp_breakdown: Optional[Dict[str, Any]] = None  # Detailed scoring breakdown
    dial_priority: Optional[int] = None  # Combined priority for dialing order
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

class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Owner of this agent (for multi-tenancy)
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    calendly_api_token: Optional[str] = None  # Optional - for API-based auto-booking
    calendly_event_type_uri: Optional[str] = None  # Cached event type URI for faster booking
    is_active: bool = True
    max_daily_calls: int = 50
    assigned_leads: int = 0
    booked_meetings: int = 0  # Track meetings booked for this agent
    # Use Case & System Prompt
    use_case: str = "sales_cold_calling"  # sales_cold_calling, appointment_setter, receptionist, customer_service, answering_service
    system_prompt: Optional[str] = None  # Custom AI instructions for this agent
    # Voice Cloning Settings
    voice_type: str = "preset"  # "preset" or "cloned"
    preset_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice (Rachel)
    cloned_voice_id: Optional[str] = None  # Custom cloned voice ID from ElevenLabs
    cloned_voice_name: Optional[str] = None  # Name of the cloned voice
    voice_settings: Optional[Dict[str, Any]] = None  # stability, similarity_boost, style
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    calendly_api_token: Optional[str] = None  # Optional for advanced integration
    max_daily_calls: int = 50
    use_case: str = "sales_cold_calling"
    system_prompt: Optional[str] = None
    voice_type: str = "preset"
    preset_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    voice_settings: Optional[Dict[str, Any]] = None

class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Owner of this campaign (for multi-tenancy)
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
    # AMD + Voicemail Drop settings
    voicemail_enabled: bool = True  # Enable voicemail drop when machine detected
    voicemail_message: Optional[str] = None  # Custom voicemail message (uses default if None)
    # AI conversation settings
    response_wait_seconds: int = 4  # Seconds to wait for caller response before AI continues
    company_name: Optional[str] = None  # Company name for personalization
    # ICP (Ideal Customer Profile) settings
    icp_config: Optional[Dict[str, Any]] = None  # ICP scoring configuration
    min_icp_score: int = 0  # Minimum ICP score required to enter dialer queue (0 = no filter)
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
    response_wait_seconds: int = 4  # Default 4 seconds
    company_name: Optional[str] = None
    icp_config: Optional[Dict[str, Any]] = None
    min_icp_score: int = 0

class Call(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Owner of this call (for multi-tenancy)
    lead_id: str
    campaign_id: str
    agent_id: Optional[str] = None
    status: CallStatus = CallStatus.PENDING
    duration_seconds: int = 0
    transcript: List[Dict[str, str]] = []  # Conversation transcript (AI-generated)
    qualification_result: Optional[Dict[str, Any]] = None
    # AMD tracking
    answered_by: Optional[str] = None  # "human", "machine_start", "machine_end_beep", "machine_end_silence", "fax", "unknown"
    voicemail_dropped: bool = False
    amd_status: Optional[str] = None  # Raw AMD status from Twilio
    # Call Recording & Transcription
    recording_url: Optional[str] = None  # Object storage path for audio file
    recording_sid: Optional[str] = None  # Twilio recording SID
    recording_duration_seconds: Optional[int] = None  # Recording duration
    full_transcript: Optional[str] = None  # Full text transcript from Whisper
    transcript_segments: Optional[List[Dict[str, Any]]] = None  # Timestamped segments
    transcription_status: Optional[str] = None  # "pending", "processing", "completed", "failed"
    # Timestamps
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Booking(BaseModel):
    """Track scheduled meetings between leads and agents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Owner of this booking (for multi-tenancy)
    lead_id: str
    agent_id: str
    campaign_id: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    booking_link: str  # The Calendly link used
    scheduled_time: Optional[str] = None  # ISO format when meeting is scheduled
    calendly_event_uri: Optional[str] = None  # Calendly event URI for cancellation/updates
    lead_name: str
    lead_phone: Optional[str] = None
    lead_email: Optional[str] = None
    agent_name: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== FOLLOW-UP CALL SYSTEM ==============
class FollowUpReason(str, Enum):
    NO_ANSWER = "no_answer"  # Lead didn't answer
    VOICEMAIL = "voicemail"  # Left voicemail, follow up later
    CALLBACK_REQUESTED = "callback_requested"  # Lead requested callback at specific time
    NURTURE = "nurture"  # Warm lead, needs nurturing
    RETRY = "retry"  # Automatic retry (busy, failed)
    SEQUENCE = "sequence"  # Part of multi-touch sequence

class FollowUpStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SKIPPED = "skipped"  # Skipped (lead converted, unsubscribed, etc.)

class FollowUp(BaseModel):
    """Scheduled follow-up calls for leads"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lead_id: str
    campaign_id: str
    agent_id: Optional[str] = None
    
    # Scheduling
    scheduled_at: str  # When to make the follow-up call (ISO format)
    reason: FollowUpReason = FollowUpReason.NO_ANSWER
    status: FollowUpStatus = FollowUpStatus.SCHEDULED
    
    # Retry tracking
    attempt_number: int = 1  # Which attempt this is (1, 2, 3...)
    max_attempts: int = 3  # Max retry attempts for this follow-up
    
    # Context
    original_call_id: Optional[str] = None  # Reference to original call
    notes: Optional[str] = None  # Why this follow-up was scheduled
    callback_time_preference: Optional[str] = None  # "morning", "afternoon", "evening" or specific time
    
    # Results
    result_call_id: Optional[str] = None  # Call ID when follow-up executed
    completed_at: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FollowUpCreate(BaseModel):
    lead_id: str
    campaign_id: str
    scheduled_at: str  # ISO format datetime
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
    
    # Sequence steps
    steps: List[Dict[str, Any]] = []
    # Example step: {"step": 1, "delay_hours": 24, "action": "call", "script_override": None}
    # Example step: {"step": 2, "delay_hours": 72, "action": "call", "script_override": "Follow-up script..."}
    
    # Settings
    max_attempts_per_step: int = 2
    stop_on_connect: bool = True  # Stop sequence when lead answers
    stop_on_booking: bool = True  # Stop sequence when meeting booked
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignFollowUpSettings(BaseModel):
    """Follow-up settings for a campaign"""
    enabled: bool = True
    
    # No-answer retry settings
    no_answer_retry_enabled: bool = True
    no_answer_retry_count: int = 3  # Max retries for no-answer
    no_answer_retry_delay_hours: int = 24  # Hours between retries
    
    # Voicemail follow-up
    voicemail_followup_enabled: bool = True
    voicemail_followup_delay_hours: int = 48  # Follow up 2 days after voicemail
    
    # Callback handling
    callback_buffer_minutes: int = 15  # Buffer time around requested callback
    
    # Sequence
    sequence_id: Optional[str] = None  # Optional follow-up sequence to use

class LeadDiscoveryRequest(BaseModel):
    search_query: str = "credit card processing"
    location: Optional[str] = None
    industry: Optional[str] = None
    max_results: int = 10

# ============== CREDIT PACKS (REVISED PRICING MODEL) ==============
class PackType(str, Enum):
    LEADS = "leads"
    CALLS = "calls"
    TOPUP = "topup"  # One-off top-up packs at 20% premium

# Subscription Plans
SUBSCRIPTION_PLANS = {
    # ============== BYOL PLANS (Bring Your Own List) ==============
    "byol_starter": {
        "name": "BYOL Starter",
        "price": 149,
        "leads_per_month": 0,  # No leads - they bring their own
        "calls_per_month": 250,
        "features": ["250 AI calls", "CSV upload", "Call recordings", "AI qualifying", "Auto booking", "7-day recordings"],
        "users": 1,
        "plan_type": "byol"
    },
    "byol_pro": {
        "name": "BYOL Pro",
        "price": 349,
        "leads_per_month": 0,  # No leads - they bring their own
        "calls_per_month": 750,
        "features": ["750 AI calls", "CSV upload", "Call transcripts", "AI qualifying", "Auto booking", "30-day recordings", "Custom scripts"],
        "users": 3,
        "plan_type": "byol"
    },
    "byol_scale": {
        "name": "BYOL Scale",
        "price": 599,
        "leads_per_month": 0,  # No leads - they bring their own
        "calls_per_month": 1500,
        "features": ["1,500 AI calls", "Unlimited CSV uploads", "Call transcripts", "AI qualifying", "Auto booking", "60-day recordings", "Custom scripts", "Priority support"],
        "users": 5,
        "plan_type": "byol"
    },
    # ============== FULL SERVICE PLANS (Lead Discovery + Calling) ==============
    "discovery_starter": {
        "name": "Discovery Starter",
        "price": 299,
        "leads_per_month": 500,
        "calls_per_month": 250,
        "features": ["500 intent leads/mo", "250 AI calls", "GPT lead discovery", "AI qualifying", "Auto booking", "7-day recordings"],
        "users": 1,
        "plan_type": "full_service"
    },
    "discovery_pro": {
        "name": "Discovery Pro",
        "price": 699,
        "leads_per_month": 1500,
        "calls_per_month": 750,
        "features": ["1,500 intent leads/mo", "750 AI calls", "GPT lead discovery", "Call transcripts", "Auto booking", "30-day recordings", "Custom scripts"],
        "users": 3,
        "plan_type": "full_service"
    },
    "discovery_elite": {
        "name": "Discovery Elite",
        "price": 1299,
        "leads_per_month": 3000,
        "calls_per_month": 2000,
        "features": ["3,000 intent leads/mo", "2,000 AI calls", "GPT lead discovery", "Call transcripts", "Auto booking", "90-day recordings", "Custom scripts", "Priority support", "5 team seats"],
        "users": 5,
        "plan_type": "full_service"
    },
    # ============== LEGACY/TEST PLANS ==============
    "test_drive": {
        "name": "Test Drive",
        "price": 29,
        "leads_per_month": 0,
        "calls_per_month": 50,
        "features": ["50 AI calls", "Call recordings", "Basic dashboard", "CSV upload"],
        "users": 1,
        "is_test_plan": True
    },
    "payg": {
        "name": "Pay-as-you-go",
        "price": 0,
        "leads_per_month": 0,
        "calls_per_month": 0,
        "features": ["No monthly commitment", "Pay per call/lead", "Basic dashboard"],
        "users": 1,
        "credit_cost": {
            "per_lead": 0.25,
            "per_call": 0.50,
        }
    }
}

# Pay-as-you-go Credit Packs (for PAYG tier users)
PAYG_CREDIT_PACKS = [
    {"id": "payg_starter_10", "name": "Starter Pack", "leads": 25, "calls": 25, "price": 19, "per_lead": 0.38, "per_call": 0.38, "bonus": "Perfect for testing"},
    {"id": "payg_growth_50", "name": "Growth Pack", "leads": 100, "calls": 100, "price": 69, "per_lead": 0.35, "per_call": 0.35, "bonus": "10% savings"},
    {"id": "payg_scale_200", "name": "Scale Pack", "leads": 400, "calls": 400, "price": 249, "per_lead": 0.31, "per_call": 0.31, "bonus": "20% savings"},
]

# Lead Packs (One-time purchase)
LEAD_PACKS = [
    {"id": "leads_500", "name": "500 Leads", "quantity": 500, "price": 79, "type": "leads", "per_lead": 0.158},
    {"id": "leads_1500", "name": "1,500 Leads", "quantity": 1500, "price": 199, "type": "leads", "per_lead": 0.133},
    {"id": "leads_5000", "name": "5,000 Leads", "quantity": 5000, "price": 499, "type": "leads", "per_lead": 0.10},
]

# Call Packs (One-time purchase) - Profitable pricing
CALL_PACKS = [
    {"id": "calls_250", "name": "250 AI Calls", "quantity": 250, "price": 99, "type": "calls", "per_call": 0.396},
    {"id": "calls_500", "name": "500 AI Calls", "quantity": 500, "price": 179, "type": "calls", "per_call": 0.358},
    {"id": "calls_1000", "name": "1,000 AI Calls", "quantity": 1000, "price": 349, "type": "calls", "per_call": 0.349},
]

# Combo Packs (Best value)
COMBO_PACKS = [
    {"id": "combo_starter", "name": "Starter Combo", "leads": 500, "calls": 250, "price": 99, "bonus": "Save $39"},
    {"id": "combo_growth", "name": "Growth Combo", "leads": 1000, "calls": 500, "price": 179, "bonus": "Save $99"},
    {"id": "combo_power", "name": "Power Combo", "leads": 2000, "calls": 1000, "price": 299, "bonus": "Save $148"},
]

# Top-up Packs (Small one-off purchases)
TOPUP_PACKS = [
    {"id": "topup_test_1", "name": "Test Pack (1 Lead)", "quantity": 1, "price": 1, "type": "topup", "credit_type": "leads", "per_unit": 1.00},
    {"id": "topup_100_leads", "name": "100 Leads Top-up", "quantity": 100, "price": 24, "type": "topup", "credit_type": "leads", "per_unit": 0.24},
    {"id": "topup_250_leads", "name": "250 Leads Top-up", "quantity": 250, "price": 55, "type": "topup", "credit_type": "leads", "per_unit": 0.22},
    {"id": "topup_100_calls", "name": "100 Calls Top-up", "quantity": 100, "price": 29, "type": "topup", "credit_type": "calls", "per_unit": 0.29},
]

# Annual Prepay Discounts
PREPAY_DISCOUNTS = {
    "quarterly": 0.05,  # 5% off
    "annual": 0.15      # 15% off
}

# ============== COMPLIANCE MODELS ==============
class DNCSuppression(BaseModel):
    """Do Not Call suppression list entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str
    reason: str  # "user_request", "regulatory", "complaint", "invalid"
    source: str  # "internal", "national_dnc", "state_dnc"
    added_by: Optional[str] = None  # user_id who added
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
class NumberVerification(BaseModel):
    """Phone number verification result"""
    phone_number: str
    is_valid: bool
    line_type: str  # "landline", "mobile", "voip", "unknown"
    is_business: bool
    carrier: Optional[str] = None
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ComplianceCheck(BaseModel):
    """Pre-call compliance check result"""
    phone_number: str
    is_allowed: bool
    reasons: List[str] = []
    checks_performed: List[str] = []
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AICallScript(BaseModel):
    """AI call script with compliance disclosure"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    disclosure: str  # REQUIRED: AI/automated call disclosure
    greeting: str
    value_proposition: str
    qualification_questions: List[str]
    objection_handlers: Dict[str, str]
    booking_script: str
    dnc_script: str  # What to say when adding to DNC
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Default compliant AI call script
DEFAULT_AI_SCRIPT = {
    "disclosure": "Hi, this is an AI assistant calling on behalf of {company_name}. This is an automated business call.",
    "greeting": "Is this {contact_name} at {business_name}?",
    "value_proposition": "I'm reaching out because we help businesses like yours {value_prop}. Many companies in your industry are seeing {benefit}.",
    "qualification_questions": [
        "Are you the person who handles {decision_area} for your business?",
        "Is this something your company is currently exploring?",
        "What's your timeline for making a decision on this?"
    ],
    "objection_handlers": {
        "not_interested": "I understand. Before I go, may I ask what solution you're currently using?",
        "bad_time": "No problem. When would be a better time to have a brief conversation?",
        "send_info": "Absolutely. What email should I send that to?",
        "already_have": "Great. How's that working out for you? Any challenges?"
    },
    "booking_script": "Excellent! I'd like to connect you with one of our specialists. They can show you exactly how this works. Do you have 15 minutes this week for a quick call?",
    "dnc_script": "No problem at all. I'll make sure you don't receive any more calls from us. Have a great day!"
}

class PackPurchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pack_id: str
    pack_type: str
    quantity: int
    price: float
    purchased_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AccountUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leads_remaining: int = 0
    calls_remaining: int = 0
    leads_used: int = 0
    calls_used: int = 0
    purchases: List[Dict] = []
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    industry: Optional[str] = None
    max_results: int = 10

class QualificationResult(BaseModel):
    is_qualified: bool
    is_decision_maker: bool
    interest_level: int
    score: int
    notes: List[str]

class BookingRequest(BaseModel):
    lead_id: str
    agent_id: str
    preferred_time: Optional[str] = None

# ============== AI SERVICE ==============
class AIService:
    """AI Service using GPT-5.2 for conversations, lead qualification, and intent search"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    async def gpt_intent_search(self, query: str, industry: str = None, location: str = None, max_results: int = 10, custom_keywords: List[str] = None) -> List[Dict]:
        """Use GPT-5.2 to research and find businesses with buying intent"""
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not configured, using mock data")
            return await self._mock_discover_leads(query, location, max_results)
        
        # Default high-intent keywords that indicate buying mode
        default_keywords = [
            "Toast alternative", "Clover alternative", "Square alternative", "Stripe alternative",
            "best POS system", "credit card processing for contractors", "payment processing",
            "merchant services", "switch payment processor", "POS system for restaurants",
            "credit card machine", "payment terminal", "reduce processing fees"
        ]
        
        # Use custom keywords if provided (up to 100), otherwise use defaults
        if custom_keywords and len(custom_keywords) > 0:
            # Limit to 100 keywords and filter empty strings
            intent_keywords = [kw.strip() for kw in custom_keywords[:100] if kw and kw.strip()]
            logger.info(f"Using {len(intent_keywords)} custom intent keywords for search")
        else:
            intent_keywords = default_keywords
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"intent-search-{uuid.uuid4()}",
                system_message="""You are a B2B lead research assistant specializing in finding businesses actively searching for solutions.

Your job is to generate realistic business leads that are IN BUYING MODE - meaning they are actively searching based on the keywords provided.

These are HIGH-INTENT leads - people who are ready to switch or sign up NOW.

For each lead, provide:
- Business name (realistic)
- Industry
- Phone number (realistic US format)
- Email (realistic business email)
- Intent signals (SPECIFIC search terms or actions showing buying intent from the provided keywords)
- Location (city, state)
- Pain point (why they're looking)

Return your response as a valid JSON array of objects with these fields:
- name: string
- industry: string  
- phone: string
- email: string
- intent_signals: array of strings (include actual search terms from the keywords provided)
- location: string
- pain_point: string

Only return the JSON array, no other text."""
            ).with_model("openai", "gpt-5.2")
            
            # Build keyword list for prompt
            keywords_prompt = chr(10).join(f'- Searching for "{kw}"' for kw in intent_keywords[:50])  # Limit in prompt to avoid token overflow
            
            search_prompt = f"""Find {max_results} businesses that are ACTIVELY IN BUYING MODE based on these search signals.

Search criteria:
- Primary query: {query}
- Industry focus: {industry or 'Any relevant industry'}
- Location: {location or 'United States'}

Target businesses showing these high-intent signals:
{keywords_prompt}

These leads should be people who:
1. Are actively comparing solutions
2. Searching for alternatives or new providers
3. Looking to switch due to pain points
4. New businesses setting up for the first time

Return as JSON array with realistic business details and specific intent signals matching the keywords."""

            user_message = UserMessage(text=search_prompt)
            response = await chat.send_message(user_message)
            
            # Parse the JSON response
            import json
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            leads = json.loads(response_text)
            logger.info(f"GPT Intent Search found {len(leads)} high-intent leads")
            return leads
            
        except Exception as e:
            logger.error(f"GPT Intent Search failed: {str(e)}")
            return await self._mock_discover_leads(query, location, max_results)
    
    @staticmethod
    async def _mock_discover_leads(query: str, location: str = None, max_results: int = 10) -> List[Dict]:
        """Fallback mock data for lead discovery"""
        sample_businesses = [
            {"name": "TechStart Solutions", "industry": "Software", "phone": "+1-555-0101", "intent_signals": ["New startup", "Processing online payments"], "location": "Austin, TX"},
            {"name": "Green Valley Restaurant", "industry": "Food & Beverage", "phone": "+1-555-0102", "intent_signals": ["High transaction volume", "Multiple locations"], "location": "Denver, CO"},
            {"name": "City Fitness Center", "industry": "Health & Fitness", "phone": "+1-555-0103", "intent_signals": ["Membership payments", "Expanding"], "location": "Phoenix, AZ"},
            {"name": "Downtown Retail Co", "industry": "Retail", "phone": "+1-555-0104", "intent_signals": ["POS upgrade needed", "Fee complaints"], "location": "Seattle, WA"},
            {"name": "Urban Salon & Spa", "industry": "Beauty", "phone": "+1-555-0105", "intent_signals": ["New location opening", "Need mobile payments"], "location": "Portland, OR"},
            {"name": "Mountain View Auto", "industry": "Automotive", "phone": "+1-555-0106", "intent_signals": ["Large transactions", "Current processor issues"], "location": "Salt Lake City, UT"},
            {"name": "Sunrise Medical Clinic", "industry": "Healthcare", "phone": "+1-555-0107", "intent_signals": ["Insurance processing", "HIPAA compliant needs"], "location": "San Diego, CA"},
            {"name": "Lakeside Hotel", "industry": "Hospitality", "phone": "+1-555-0108", "intent_signals": ["Seasonal business", "International cards"], "location": "Miami, FL"},
            {"name": "Creative Design Agency", "industry": "Marketing", "phone": "+1-555-0109", "intent_signals": ["Recurring billing", "Invoice payments"], "location": "Chicago, IL"},
            {"name": "Fresh Market Grocery", "industry": "Grocery", "phone": "+1-555-0110", "intent_signals": ["High volume", "EBT processing"], "location": "Atlanta, GA"},
        ]
        return sample_businesses[:max_results]
    
    @staticmethod
    async def simulate_call_conversation(lead: Dict, script: str) -> Dict:
        """Simulate AI cold call conversation - MOCKED"""
        await asyncio.sleep(2)
        
        is_decision_maker = random.choice([True, True, False])
        interest_level = random.randint(1, 10)
        
        transcript = [
            {"role": "ai", "text": f"Hello, this is an AI assistant calling about credit card processing solutions. Am I speaking with the owner or manager of {lead.get('business_name', 'the business')}?"},
            {"role": "human", "text": "Yes, this is the owner speaking." if is_decision_maker else "No, the owner isn't available right now."},
        ]
        
        if is_decision_maker:
            transcript.extend([
                {"role": "ai", "text": "Great! We're reaching out to businesses in your area about our competitive credit card processing rates. Are you currently satisfied with your payment processing fees?"},
                {"role": "human", "text": "We've been thinking about switching actually." if interest_level > 5 else "We're pretty happy with what we have."},
                {"role": "ai", "text": "I understand. Would you be interested in a quick consultation to see how much you could save?" if interest_level > 5 else "I appreciate your time. May I follow up with you in a few months?"},
                {"role": "human", "text": "Sure, that sounds good." if interest_level > 5 else "Maybe, we'll see."},
            ])
        
        return {
            "transcript": transcript,
            "is_decision_maker": is_decision_maker,
            "interest_level": interest_level,
            "duration_seconds": random.randint(30, 180),
            "status": "completed"
        }
    
    @staticmethod
    async def qualify_lead(call_data: Dict) -> QualificationResult:
        """Qualify lead based on call data"""
        is_decision_maker = call_data.get("is_decision_maker", False)
        interest_level = call_data.get("interest_level", 0)
        
        score = 0
        notes = []
        
        if is_decision_maker:
            score += 50
            notes.append("Confirmed decision maker")
        else:
            notes.append("Not speaking with decision maker")
        
        score += interest_level * 5
        notes.append(f"Interest level: {interest_level}/10")
        
        is_qualified = score >= 60 and is_decision_maker and interest_level >= 6
        
        if is_qualified:
            notes.append("Lead qualifies for meeting booking")
        else:
            notes.append("Lead does not meet qualification criteria")
        
        return QualificationResult(
            is_qualified=is_qualified,
            is_decision_maker=is_decision_maker,
            interest_level=interest_level,
            score=score,
            notes=notes
        )

ai_service = AIService()

# ============== NOTIFICATION SERVICE ==============
class NotificationService:
    """Email notification service using Resend"""
    
    def __init__(self):
        self.api_key = os.environ.get('RESEND_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
        self.is_configured = bool(self.api_key)
        if self.is_configured:
            resend.api_key = self.api_key
    
    async def send_lead_qualified_notification(self, lead: Dict, qualification: Dict, recipients: List[str]):
        """Send email notification when a lead is qualified"""
        if not self.is_configured:
            logger.info("Email notifications not configured - skipping lead qualified notification")
            return None
        
        subject = f"🎯 New Qualified Lead: {lead.get('business_name', 'Unknown')}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10B981, #059669); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">New Qualified Lead!</h1>
            </div>
            
            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <h2 style="color: #1f2937; margin-top: 0;">{lead.get('business_name', 'Unknown Business')}</h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Contact:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #1f2937; font-weight: 500;">{lead.get('contact_name', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Phone:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #1f2937; font-weight: 500;">{lead.get('phone', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Email:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #1f2937; font-weight: 500;">{lead.get('email', 'N/A')}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background: #ecfdf5; border-radius: 8px; border-left: 4px solid #10B981;">
                    <h3 style="margin: 0 0 10px 0; color: #065f46;">Qualification Score: {qualification.get('score', 0)}/100</h3>
                    <p style="margin: 5px 0; color: #047857;">✓ Decision Maker: {'Yes' if qualification.get('is_decision_maker') else 'No'}</p>
                    <p style="margin: 5px 0; color: #047857;">✓ Interest Level: {qualification.get('interest_level', 0)}/10</p>
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <p style="color: #6b7280; font-size: 14px;">This lead is ready for booking! Log in to DialGenix.ai to assign an agent.</p>
                </div>
            </div>
            
            <div style="background: #1f2937; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">Powered by DialGenix.ai - AI Sales Automation</p>
            </div>
        </div>
        """
        
        try:
            for recipient in recipients:
                params = {
                    "from": self.sender_email,
                    "to": [recipient],
                    "subject": subject,
                    "html": html_content
                }
                email = await asyncio.to_thread(resend.Emails.send, params)
                logger.info(f"Lead qualified notification sent to {recipient}, email_id: {email.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send lead qualified notification: {str(e)}")
            return False
    
    async def send_meeting_booked_notification(self, lead: Dict, agent: Dict, recipients: List[str], booking_link: str = None):
        """Send email notification when a meeting is booked"""
        if not self.is_configured:
            logger.info("Email notifications not configured - skipping meeting booked notification")
            return None
        
        subject = f"📅 Meeting Booked: {lead.get('business_name', 'Unknown')} → {agent.get('name', 'Agent')}"
        
        # Use personalized booking link if provided, otherwise use agent's default
        calendly_link = booking_link or agent.get('calendly_link', '#')
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #8B5CF6, #7C3AED); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Meeting Booked!</h1>
            </div>
            
            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="flex: 1;">
                        <h3 style="margin: 0; color: #6b7280; font-size: 12px; text-transform: uppercase;">Lead</h3>
                        <p style="margin: 5px 0; color: #1f2937; font-size: 18px; font-weight: 600;">{lead.get('business_name', 'Unknown')}</p>
                    </div>
                    <div style="padding: 0 20px; color: #9ca3af;">→</div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0; color: #6b7280; font-size: 12px; text-transform: uppercase;">Agent</h3>
                        <p style="margin: 5px 0; color: #1f2937; font-size: 18px; font-weight: 600;">{agent.get('name', 'Agent')}</p>
                    </div>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Lead Phone:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #1f2937; font-weight: 500;">{lead.get('phone', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Lead Email:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #1f2937; font-weight: 500;">{lead.get('email', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #6b7280;">Agent Email:</td>
                        <td style="padding: 10px 0; border-bottom: 1px solid #e5e7eb; color: #1f2937; font-weight: 500;">{agent.get('email', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; color: #6b7280;">Booking Link:</td>
                        <td style="padding: 10px 0; color: #8B5CF6; font-weight: 500;">
                            <a href="{calendly_link}" style="color: #8B5CF6;">Schedule Meeting</a>
                        </td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background: #f5f3ff; border-radius: 8px; border-left: 4px solid #8B5CF6;">
                    <p style="margin: 0; color: #5b21b6;">🎉 Great job! A personalized booking link has been generated for this lead.</p>
                </div>
                
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{calendly_link}" style="display: inline-block; background: #8B5CF6; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                        View Booking Link
                    </a>
                </div>
            </div>
            
            <div style="background: #1f2937; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">Powered by DialGenix.ai - AI Sales Automation</p>
            </div>
        </div>
        """
        
        try:
            for recipient in recipients:
                params = {
                    "from": self.sender_email,
                    "to": [recipient],
                    "subject": subject,
                    "html": html_content
                }
                email = await asyncio.to_thread(resend.Emails.send, params)
                logger.info(f"Meeting booked notification sent to {recipient}, email_id: {email.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send meeting booked notification: {str(e)}")
            return False
    
    async def send_low_balance_notification(self, user_email: str, user_name: str, lead_credits: int, call_credits: int):
        """Send email notification when user has low credit balance"""
        if not self.is_configured:
            logger.info("Email notifications not configured - skipping low balance notification")
            return None
        
        subject = "⚠️ Low Credit Balance Alert - DialGenix.ai"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #F59E0B, #D97706); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Low Credit Balance Alert</h1>
            </div>
            
            <div style="background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <p style="color: #1f2937; font-size: 16px;">Hi {user_name},</p>
                
                <p style="color: #4b5563;">Your DialGenix.ai credit balance is running low. Here's your current status:</p>
                
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div style="flex: 1; background: {'#FEF3C7' if lead_credits <= 20 else '#ECFDF5'}; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: {'#D97706' if lead_credits <= 20 else '#059669'};">{lead_credits}</div>
                        <div style="color: #6B7280; font-size: 14px;">Lead Credits</div>
                    </div>
                    <div style="flex: 1; background: {'#FEF3C7' if call_credits <= 20 else '#ECFDF5'}; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: {'#D97706' if call_credits <= 20 else '#059669'};">{call_credits}</div>
                        <div style="color: #6B7280; font-size: 14px;">Call Credits</div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #FEF3C7; border-radius: 8px; border-left: 4px solid #F59E0B;">
                    <p style="margin: 0; color: #92400E;">
                        <strong>Don't let your campaigns stop!</strong><br>
                        Purchase additional credits or upgrade your plan to keep your AI calling machine running smoothly.
                    </p>
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <p style="color: #6b7280; font-size: 14px;">Log in to your dashboard to purchase more credits or upgrade your subscription.</p>
                </div>
            </div>
            
            <div style="background: #1f2937; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">Powered by DialGenix.ai - AI Sales Automation</p>
            </div>
        </div>
        """
        
        try:
            params = {
                "from": self.sender_email,
                "to": [user_email],
                "subject": subject,
                "html": html_content
            }
            email = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Low balance notification sent to {user_email}, email_id: {email.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send low balance notification: {str(e)}")
            return False

notification_service = NotificationService()

# ============== CALENDLY INTEGRATION SERVICE ==============
class CalendlyService:
    """
    Service for Calendly API integration - auto-booking qualified leads.
    Supports generating booking links, checking availability, and scheduling meetings.
    """
    
    def __init__(self):
        self.api_token = os.environ.get("CALENDLY_API_TOKEN")
        self.base_url = "https://api.calendly.com"
        self.is_configured = bool(self.api_token)
        
        if self.is_configured:
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            logger.info("Calendly service initialized with API token")
        else:
            logger.warning("Calendly API token not configured - using booking links only")
    
    async def get_current_user(self) -> Optional[Dict]:
        """Get the authenticated Calendly user info"""
        if not self.is_configured:
            return None
        
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.base_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("resource")
        except Exception as e:
            logger.error(f"Failed to get Calendly user: {str(e)}")
            return None
    
    async def get_event_types(self, user_uri: str = None) -> List[Dict]:
        """Fetch all event types for the user"""
        if not self.is_configured:
            return []
        
        try:
            if not user_uri:
                user = await self.get_current_user()
                if not user:
                    return []
                user_uri = user["uri"]
            
            response = await asyncio.to_thread(
                requests.get,
                f"{self.base_url}/event_types",
                headers=self.headers,
                params={"user": user_uri, "active": "true"},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("collection", [])
        except Exception as e:
            logger.error(f"Failed to get event types: {str(e)}")
            return []
    
    async def get_available_times(
        self, 
        event_type_uri: str, 
        start_time: str, 
        end_time: str
    ) -> List[Dict]:
        """Get available time slots for an event type"""
        if not self.is_configured:
            return []
        
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.base_url}/event_type_available_times",
                headers=self.headers,
                params={
                    "event_type": event_type_uri,
                    "start_time": start_time,
                    "end_time": end_time
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("collection", [])
        except Exception as e:
            logger.error(f"Failed to get available times: {str(e)}")
            return []
    
    def generate_booking_link(
        self, 
        calendly_link: str, 
        lead_name: str = None, 
        lead_email: str = None,
        lead_phone: str = None
    ) -> str:
        """
        Generate a personalized booking link with pre-filled lead data.
        Works even without API token (uses standard Calendly link format).
        """
        import urllib.parse
        
        # Clean the base Calendly link
        base_link = calendly_link.rstrip("/")
        
        # Build query params for pre-filling
        params = {}
        if lead_name:
            params["name"] = lead_name
        if lead_email:
            params["email"] = lead_email
        if lead_phone:
            # Calendly uses 'a1' for custom questions - phone is commonly first
            params["a1"] = lead_phone
        
        if params:
            query_string = urllib.parse.urlencode(params)
            return f"{base_link}?{query_string}"
        
        return base_link
    
    async def create_single_use_link(
        self,
        event_type_uri: str,
        max_event_count: int = 1
    ) -> Optional[str]:
        """Create a single-use scheduling link for a specific lead"""
        if not self.is_configured:
            return None
        
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/scheduling_links",
                headers=self.headers,
                json={
                    "owner": event_type_uri,
                    "owner_type": "EventType",
                    "max_event_count": max_event_count
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("resource", {}).get("booking_url")
        except Exception as e:
            logger.error(f"Failed to create single-use link: {str(e)}")
            return None
    
    async def get_scheduled_events(
        self,
        user_uri: str,
        min_start_time: str,
        max_start_time: str,
        status: str = "active"
    ) -> List[Dict]:
        """Get scheduled events in a time range"""
        if not self.is_configured:
            return []
        
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.base_url}/scheduled_events",
                headers=self.headers,
                params={
                    "user": user_uri,
                    "min_start_time": min_start_time,
                    "max_start_time": max_start_time,
                    "status": status
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("collection", [])
        except Exception as e:
            logger.error(f"Failed to get scheduled events: {str(e)}")
            return []
    
    async def cancel_event(self, event_uuid: str, reason: str = "") -> bool:
        """Cancel a scheduled event"""
        if not self.is_configured:
            return False
        
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/scheduled_events/{event_uuid}/cancellation",
                headers=self.headers,
                json={"reason": reason} if reason else {},
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to cancel event: {str(e)}")
            return False

calendly_service = CalendlyService()

# ============== CALL RECORDING & TRANSCRIPTION SERVICE ==============

# Object Storage Configuration
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "dialgenix-ai"
storage_key = None

def init_storage():
    """Initialize object storage - call once at startup"""
    global storage_key
    if storage_key:
        return storage_key
    
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        logger.warning("EMERGENT_LLM_KEY not set - call recording storage disabled")
        return None
    
    try:
        resp = requests.post(
            f"{STORAGE_URL}/init",
            json={"emergent_key": emergent_key},
            timeout=30
        )
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Object storage initialized successfully")
        return storage_key
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> Optional[Dict]:
    """Upload file to object storage"""
    key = init_storage()
    if not key:
        return None
    
    try:
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to upload to storage: {e}")
        return None

def get_object(path: str) -> Optional[tuple]:
    """Download file from object storage. Returns (content_bytes, content_type)"""
    key = init_storage()
    if not key:
        return None
    
    try:
        resp = requests.get(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "audio/mpeg")
    except Exception as e:
        logger.error(f"Failed to download from storage: {e}")
        return None


class CallRecordingService:
    """
    Service for managing call recordings and transcriptions.
    - Downloads recordings from Twilio
    - Uploads to object storage
    - Transcribes using Whisper API
    """
    
    def __init__(self):
        self.emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        self.twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        
        self.storage_enabled = bool(self.emergent_key)
        self.transcription_enabled = bool(self.emergent_key)
        
        if self.transcription_enabled:
            self.stt = OpenAISpeechToText(api_key=self.emergent_key)
            logger.info("Call recording & transcription service initialized")
        else:
            self.stt = None
            logger.warning("Transcription disabled - EMERGENT_LLM_KEY not set")
    
    async def download_twilio_recording(self, recording_sid: str) -> Optional[bytes]:
        """Download recording audio from Twilio"""
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.error("Twilio credentials not configured")
            return None
        
        try:
            # Twilio recording URL format
            recording_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Recordings/{recording_sid}.mp3"
            
            response = await asyncio.to_thread(
                requests.get,
                recording_url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=60
            )
            response.raise_for_status()
            
            logger.info(f"Downloaded Twilio recording {recording_sid}: {len(response.content)} bytes")
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to download Twilio recording {recording_sid}: {e}")
            return None
    
    async def store_recording(self, user_id: str, call_id: str, audio_data: bytes) -> Optional[str]:
        """Store recording in object storage. Returns storage path."""
        if not self.storage_enabled:
            return None
        
        try:
            # Generate storage path
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            path = f"{APP_NAME}/recordings/{user_id}/{timestamp}/{call_id}.mp3"
            
            result = await asyncio.to_thread(
                put_object,
                path,
                audio_data,
                "audio/mpeg"
            )
            
            if result:
                logger.info(f"Stored recording at {path}")
                return result.get("path", path)
            return None
            
        except Exception as e:
            logger.error(f"Failed to store recording: {e}")
            return None
    
    async def transcribe_recording(self, audio_data: bytes, language: str = "en") -> Optional[Dict]:
        """Transcribe audio using Whisper API. Returns transcript data."""
        if not self.transcription_enabled or not self.stt:
            return None
        
        try:
            # Create a file-like object for the audio data
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "recording.mp3"
            
            # Transcribe with timestamps
            response = await self.stt.transcribe(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                language=language,
                timestamp_granularities=["segment"]
            )
            
            # Extract transcript and segments
            result = {
                "text": response.text,
                "segments": []
            }
            
            if hasattr(response, 'segments'):
                for segment in response.segments:
                    result["segments"].append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text
                    })
            
            logger.info(f"Transcribed recording: {len(response.text)} chars, {len(result['segments'])} segments")
            return result
            
        except Exception as e:
            logger.error(f"Failed to transcribe recording: {e}")
            return None
    
    async def process_call_recording(
        self,
        call_id: str,
        user_id: str,
        recording_sid: str,
        features: Dict
    ) -> Dict:
        """
        Full pipeline: Download from Twilio -> Store -> Transcribe
        Respects user's tier features.
        """
        result = {
            "recording_url": None,
            "full_transcript": None,
            "transcript_segments": None,
            "status": "pending"
        }
        
        # Check if user has recording feature
        if not features.get("call_recording"):
            result["status"] = "feature_not_available"
            return result
        
        try:
            # Update status to processing
            await db.calls.update_one(
                {"id": call_id},
                {"$set": {"transcription_status": "processing"}}
            )
            
            # Step 1: Download from Twilio
            audio_data = await self.download_twilio_recording(recording_sid)
            if not audio_data:
                result["status"] = "download_failed"
                return result
            
            # Step 2: Store in object storage
            storage_path = await self.store_recording(user_id, call_id, audio_data)
            if storage_path:
                result["recording_url"] = storage_path
            
            # Step 3: Transcribe (if user has transcription feature)
            if features.get("call_transcription"):
                transcript_data = await self.transcribe_recording(audio_data)
                if transcript_data:
                    result["full_transcript"] = transcript_data["text"]
                    result["transcript_segments"] = transcript_data["segments"]
            
            result["status"] = "completed"
            
            # Update call record with recording data
            update_data = {
                "recording_url": result["recording_url"],
                "transcription_status": result["status"]
            }
            
            if result["full_transcript"]:
                update_data["full_transcript"] = result["full_transcript"]
                update_data["transcript_segments"] = result["transcript_segments"]
            
            await db.calls.update_one(
                {"id": call_id},
                {"$set": update_data}
            )
            
            logger.info(f"Processed recording for call {call_id}: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing call recording: {e}")
            result["status"] = "failed"
            await db.calls.update_one(
                {"id": call_id},
                {"$set": {"transcription_status": "failed"}}
            )
            return result

recording_service = CallRecordingService()

# ============== ICP SCORING SERVICE ==============
class ICPScoringService:
    """
    Service for scoring leads based on Ideal Customer Profile (ICP).
    Uses AI to analyze lead data and score fit before entering dialer queue.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
    
    async def score_lead(self, lead: Dict, icp_config: Dict = None) -> Dict:
        """
        Score a lead based on ICP criteria.
        Returns a score breakdown with total 0-100 score.
        
        Scoring categories (each 0-25 points):
        1. Industry Fit - Does the business industry match target?
        2. Company Size Fit - Is the company size in the sweet spot?
        3. Intent Signal Strength - How strong are the buying signals?
        4. Contact Quality - Is this likely a decision maker?
        """
        
        # Default ICP config if none provided
        if not icp_config:
            icp_config = {
                "target_industries": [],  # Empty = all industries
                "preferred_company_sizes": ["11-50", "51-200"],  # SMB focus
                "high_value_signals": ["alternative", "switch", "looking for", "need help"],
                "decision_maker_titles": ["owner", "manager", "director", "ceo", "president", "founder"]
            }
        
        breakdown = {
            "industry_fit": 0,
            "company_size_fit": 0,
            "intent_strength": 0,
            "contact_quality": 0
        }
        
        # 1. Industry Fit (0-25)
        target_industries = icp_config.get("target_industries", [])
        lead_industry = (lead.get("industry") or "").lower()
        
        if not target_industries:  # No filter = full score
            breakdown["industry_fit"] = 20
        elif lead_industry:
            for target in target_industries:
                if target.lower() in lead_industry or lead_industry in target.lower():
                    breakdown["industry_fit"] = 25
                    break
            if breakdown["industry_fit"] == 0:
                breakdown["industry_fit"] = 10  # Some points for having industry data
        
        # 2. Company Size Fit (0-25)
        preferred_sizes = icp_config.get("preferred_company_sizes", [])
        lead_size = lead.get("company_size", "")
        
        if not preferred_sizes:  # No preference = medium score
            breakdown["company_size_fit"] = 15
        elif lead_size in preferred_sizes:
            breakdown["company_size_fit"] = 25
        elif lead_size:
            breakdown["company_size_fit"] = 10  # Has size data but not preferred
        
        # 3. Intent Signal Strength (0-25)
        intent_signals = lead.get("intent_signals", [])
        high_value_signals = icp_config.get("high_value_signals", [])
        
        if intent_signals:
            signal_text = " ".join(intent_signals).lower()
            matches = sum(1 for sig in high_value_signals if sig.lower() in signal_text)
            
            # Score based on signal matches
            if matches >= 3:
                breakdown["intent_strength"] = 25
            elif matches >= 2:
                breakdown["intent_strength"] = 20
            elif matches >= 1:
                breakdown["intent_strength"] = 15
            else:
                breakdown["intent_strength"] = 10  # Has signals, but not high-value
        else:
            breakdown["intent_strength"] = 5  # Minimal score for no signals
        
        # 4. Contact Quality (0-25)
        contact_name = (lead.get("contact_name") or "").lower()
        business_name = (lead.get("business_name") or "").lower()
        decision_maker_titles = icp_config.get("decision_maker_titles", [])
        
        # Check if contact name suggests decision maker
        is_likely_dm = False
        for title in decision_maker_titles:
            if title.lower() in contact_name:
                is_likely_dm = True
                break
        
        if is_likely_dm:
            breakdown["contact_quality"] = 25
        elif contact_name:
            breakdown["contact_quality"] = 15  # Has contact name
        elif business_name:
            breakdown["contact_quality"] = 10  # Only business name
        else:
            breakdown["contact_quality"] = 5
        
        # Check for business email (adds bonus)
        email = lead.get("email", "")
        if email and "@" in email:
            domain = email.split("@")[1].lower()
            personal_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
            if domain not in personal_domains:
                breakdown["contact_quality"] = min(25, breakdown["contact_quality"] + 5)
        
        # Calculate total score
        total_score = sum(breakdown.values())
        
        # Determine tier
        if total_score >= 80:
            tier = "A"
            recommendation = "HIGH PRIORITY - Excellent ICP fit, call immediately"
        elif total_score >= 60:
            tier = "B"
            recommendation = "GOOD FIT - Strong candidate, prioritize for calling"
        elif total_score >= 40:
            tier = "C"
            recommendation = "MODERATE FIT - Acceptable lead, call when bandwidth allows"
        else:
            tier = "D"
            recommendation = "LOW FIT - May not match ICP, consider deprioritizing"
        
        return {
            "total_score": total_score,
            "tier": tier,
            "breakdown": breakdown,
            "recommendation": recommendation,
            "scored_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def score_lead_with_ai(self, lead: Dict, icp_config: Dict = None) -> Dict:
        """
        Use GPT to score lead with more nuanced analysis.
        More accurate but costs ~$0.002 per lead.
        """
        if not self.api_key:
            # Fallback to rule-based scoring
            return await self.score_lead(lead, icp_config)
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"icp-score-{uuid.uuid4().hex[:8]}",
                system_message="""You are an ICP (Ideal Customer Profile) scoring expert for B2B sales.
                
Score leads on a 0-100 scale across these categories:
1. Industry Fit (0-25): Does the business match target industries?
2. Company Size Fit (0-25): Is the company size appropriate?
3. Intent Strength (0-25): How strong are the buying signals?
4. Contact Quality (0-25): Is this likely a decision maker?

Return ONLY a JSON object with this structure:
{
    "total_score": <0-100>,
    "tier": "<A/B/C/D>",
    "breakdown": {
        "industry_fit": <0-25>,
        "company_size_fit": <0-25>,
        "intent_strength": <0-25>,
        "contact_quality": <0-25>
    },
    "recommendation": "<one sentence recommendation>"
}"""
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""Score this lead for ICP fit:

Lead Data:
- Business: {lead.get('business_name', 'Unknown')}
- Industry: {lead.get('industry', 'Unknown')}
- Company Size: {lead.get('company_size', 'Unknown')}
- Contact: {lead.get('contact_name', 'Unknown')}
- Email: {lead.get('email', 'Unknown')}
- Intent Signals: {', '.join(lead.get('intent_signals', [])) or 'None'}

ICP Criteria:
- Target Industries: {icp_config.get('target_industries', ['Any']) if icp_config else 'Any'}
- Preferred Size: {icp_config.get('preferred_company_sizes', ['SMB']) if icp_config else 'SMB'}
- High-Value Signals: {icp_config.get('high_value_signals', ['alternative', 'switch']) if icp_config else 'alternative, switch'}

Return the JSON score."""

            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse JSON from response
            import json
            # Try to extract JSON from response
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            score_data = json.loads(response_text)
            score_data["scored_at"] = datetime.now(timezone.utc).isoformat()
            score_data["scoring_method"] = "ai"
            
            return score_data
            
        except Exception as e:
            logger.error(f"AI ICP scoring failed: {e}, falling back to rule-based")
            result = await self.score_lead(lead, icp_config)
            result["scoring_method"] = "rule_based_fallback"
            return result
    
    async def batch_score_leads(self, lead_ids: List[str], icp_config: Dict = None, use_ai: bool = False) -> List[Dict]:
        """Score multiple leads and update their records"""
        results = []
        
        for lead_id in lead_ids:
            lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
            if not lead:
                continue
            
            if use_ai:
                score_result = await self.score_lead_with_ai(lead, icp_config)
            else:
                score_result = await self.score_lead(lead, icp_config)
            
            # Update lead with ICP score
            await db.leads.update_one(
                {"id": lead_id},
                {"$set": {
                    "icp_score": score_result["total_score"],
                    "icp_breakdown": score_result["breakdown"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            results.append({
                "lead_id": lead_id,
                "business_name": lead.get("business_name"),
                **score_result
            })
        
        return results

icp_service = ICPScoringService()

# ============== COMPLIANCE SERVICE ==============

# US Area Code to Timezone mapping (comprehensive)
# Format: area_code -> (timezone_name, state_abbr)
AREA_CODE_TIMEZONES = {
    # Eastern Time (ET) - UTC-5/-4
    "201": ("America/New_York", "NJ"), "202": ("America/New_York", "DC"), "203": ("America/New_York", "CT"),
    "207": ("America/New_York", "ME"), "212": ("America/New_York", "NY"), "215": ("America/New_York", "PA"),
    "216": ("America/New_York", "OH"), "224": ("America/Chicago", "IL"), "225": ("America/Chicago", "LA"),
    "229": ("America/New_York", "GA"), "231": ("America/New_York", "MI"), "234": ("America/New_York", "OH"),
    "239": ("America/New_York", "FL"), "240": ("America/New_York", "MD"), "248": ("America/New_York", "MI"),
    "251": ("America/Chicago", "AL"), "252": ("America/New_York", "NC"), "253": ("America/Los_Angeles", "WA"),
    "254": ("America/Chicago", "TX"), "256": ("America/Chicago", "AL"), "260": ("America/New_York", "IN"),
    "267": ("America/New_York", "PA"), "269": ("America/New_York", "MI"), "270": ("America/Chicago", "KY"),
    "272": ("America/New_York", "PA"), "276": ("America/New_York", "VA"), "281": ("America/Chicago", "TX"),
    "301": ("America/New_York", "MD"), "302": ("America/New_York", "DE"), "303": ("America/Denver", "CO"),
    "304": ("America/New_York", "WV"), "305": ("America/New_York", "FL"), "307": ("America/Denver", "WY"),
    "308": ("America/Chicago", "NE"), "309": ("America/Chicago", "IL"), "310": ("America/Los_Angeles", "CA"),
    "312": ("America/Chicago", "IL"), "313": ("America/New_York", "MI"), "314": ("America/Chicago", "MO"),
    "315": ("America/New_York", "NY"), "316": ("America/Chicago", "KS"), "317": ("America/New_York", "IN"),
    "318": ("America/Chicago", "LA"), "319": ("America/Chicago", "IA"), "320": ("America/Chicago", "MN"),
    "321": ("America/New_York", "FL"), "323": ("America/Los_Angeles", "CA"), "325": ("America/Chicago", "TX"),
    "330": ("America/New_York", "OH"), "331": ("America/Chicago", "IL"), "334": ("America/Chicago", "AL"),
    "336": ("America/New_York", "NC"), "337": ("America/Chicago", "LA"), "339": ("America/New_York", "MA"),
    "340": ("America/Virgin", "VI"), "346": ("America/Chicago", "TX"), "347": ("America/New_York", "NY"),
    "351": ("America/New_York", "MA"), "352": ("America/New_York", "FL"), "360": ("America/Los_Angeles", "WA"),
    "361": ("America/Chicago", "TX"), "364": ("America/Chicago", "KY"), "380": ("America/New_York", "OH"),
    "385": ("America/Denver", "UT"), "386": ("America/New_York", "FL"), "401": ("America/New_York", "RI"),
    "402": ("America/Chicago", "NE"), "404": ("America/New_York", "GA"), "405": ("America/Chicago", "OK"),
    "406": ("America/Denver", "MT"), "407": ("America/New_York", "FL"), "408": ("America/Los_Angeles", "CA"),
    "409": ("America/Chicago", "TX"), "410": ("America/New_York", "MD"), "412": ("America/New_York", "PA"),
    "413": ("America/New_York", "MA"), "414": ("America/Chicago", "WI"), "415": ("America/Los_Angeles", "CA"),
    "417": ("America/Chicago", "MO"), "419": ("America/New_York", "OH"), "423": ("America/New_York", "TN"),
    "424": ("America/Los_Angeles", "CA"), "425": ("America/Los_Angeles", "WA"), "430": ("America/Chicago", "TX"),
    "432": ("America/Chicago", "TX"), "434": ("America/New_York", "VA"), "435": ("America/Denver", "UT"),
    "440": ("America/New_York", "OH"), "442": ("America/Los_Angeles", "CA"), "443": ("America/New_York", "MD"),
    "458": ("America/Los_Angeles", "OR"), "469": ("America/Chicago", "TX"), "470": ("America/New_York", "GA"),
    "475": ("America/New_York", "CT"), "478": ("America/New_York", "GA"), "479": ("America/Chicago", "AR"),
    "480": ("America/Phoenix", "AZ"), "484": ("America/New_York", "PA"), "501": ("America/Chicago", "AR"),
    "502": ("America/New_York", "KY"), "503": ("America/Los_Angeles", "OR"), "504": ("America/Chicago", "LA"),
    "505": ("America/Denver", "NM"), "507": ("America/Chicago", "MN"), "508": ("America/New_York", "MA"),
    "509": ("America/Los_Angeles", "WA"), "510": ("America/Los_Angeles", "CA"), "512": ("America/Chicago", "TX"),
    "513": ("America/New_York", "OH"), "515": ("America/Chicago", "IA"), "516": ("America/New_York", "NY"),
    "517": ("America/New_York", "MI"), "518": ("America/New_York", "NY"), "520": ("America/Phoenix", "AZ"),
    "530": ("America/Los_Angeles", "CA"), "531": ("America/Chicago", "NE"), "534": ("America/Chicago", "WI"),
    "539": ("America/Chicago", "OK"), "540": ("America/New_York", "VA"), "541": ("America/Los_Angeles", "OR"),
    "551": ("America/New_York", "NJ"), "559": ("America/Los_Angeles", "CA"), "561": ("America/New_York", "FL"),
    "562": ("America/Los_Angeles", "CA"), "563": ("America/Chicago", "IA"), "567": ("America/New_York", "OH"),
    "570": ("America/New_York", "PA"), "571": ("America/New_York", "VA"), "573": ("America/Chicago", "MO"),
    "574": ("America/New_York", "IN"), "575": ("America/Denver", "NM"), "580": ("America/Chicago", "OK"),
    "585": ("America/New_York", "NY"), "586": ("America/New_York", "MI"), "601": ("America/Chicago", "MS"),
    "602": ("America/Phoenix", "AZ"), "603": ("America/New_York", "NH"), "605": ("America/Chicago", "SD"),
    "606": ("America/New_York", "KY"), "607": ("America/New_York", "NY"), "608": ("America/Chicago", "WI"),
    "609": ("America/New_York", "NJ"), "610": ("America/New_York", "PA"), "612": ("America/Chicago", "MN"),
    "614": ("America/New_York", "OH"), "615": ("America/Chicago", "TN"), "616": ("America/New_York", "MI"),
    "617": ("America/New_York", "MA"), "618": ("America/Chicago", "IL"), "619": ("America/Los_Angeles", "CA"),
    "620": ("America/Chicago", "KS"), "623": ("America/Phoenix", "AZ"), "626": ("America/Los_Angeles", "CA"),
    "628": ("America/Los_Angeles", "CA"), "629": ("America/Chicago", "TN"), "630": ("America/Chicago", "IL"),
    "631": ("America/New_York", "NY"), "636": ("America/Chicago", "MO"), "641": ("America/Chicago", "IA"),
    "646": ("America/New_York", "NY"), "650": ("America/Los_Angeles", "CA"), "651": ("America/Chicago", "MN"),
    "657": ("America/Los_Angeles", "CA"), "660": ("America/Chicago", "MO"), "661": ("America/Los_Angeles", "CA"),
    "662": ("America/Chicago", "MS"), "667": ("America/New_York", "MD"), "669": ("America/Los_Angeles", "CA"),
    "678": ("America/New_York", "GA"), "680": ("America/New_York", "NY"), "681": ("America/New_York", "WV"),
    "682": ("America/Chicago", "TX"), "689": ("America/New_York", "FL"), "701": ("America/Chicago", "ND"),
    "702": ("America/Los_Angeles", "NV"), "703": ("America/New_York", "VA"), "704": ("America/New_York", "NC"),
    "706": ("America/New_York", "GA"), "707": ("America/Los_Angeles", "CA"), "708": ("America/Chicago", "IL"),
    "712": ("America/Chicago", "IA"), "713": ("America/Chicago", "TX"), "714": ("America/Los_Angeles", "CA"),
    "715": ("America/Chicago", "WI"), "716": ("America/New_York", "NY"), "717": ("America/New_York", "PA"),
    "718": ("America/New_York", "NY"), "719": ("America/Denver", "CO"), "720": ("America/Denver", "CO"),
    "724": ("America/New_York", "PA"), "725": ("America/Los_Angeles", "NV"), "727": ("America/New_York", "FL"),
    "731": ("America/Chicago", "TN"), "732": ("America/New_York", "NJ"), "734": ("America/New_York", "MI"),
    "737": ("America/Chicago", "TX"), "740": ("America/New_York", "OH"), "743": ("America/New_York", "NC"),
    "747": ("America/Los_Angeles", "CA"), "754": ("America/New_York", "FL"), "757": ("America/New_York", "VA"),
    "760": ("America/Los_Angeles", "CA"), "762": ("America/New_York", "GA"), "763": ("America/Chicago", "MN"),
    "765": ("America/New_York", "IN"), "769": ("America/Chicago", "MS"), "770": ("America/New_York", "GA"),
    "772": ("America/New_York", "FL"), "773": ("America/Chicago", "IL"), "774": ("America/New_York", "MA"),
    "775": ("America/Los_Angeles", "NV"), "779": ("America/Chicago", "IL"), "781": ("America/New_York", "MA"),
    "785": ("America/Chicago", "KS"), "786": ("America/New_York", "FL"), "801": ("America/Denver", "UT"),
    "802": ("America/New_York", "VT"), "803": ("America/New_York", "SC"), "804": ("America/New_York", "VA"),
    "805": ("America/Los_Angeles", "CA"), "806": ("America/Chicago", "TX"), "808": ("Pacific/Honolulu", "HI"),
    "810": ("America/New_York", "MI"), "812": ("America/New_York", "IN"), "813": ("America/New_York", "FL"),
    "814": ("America/New_York", "PA"), "815": ("America/Chicago", "IL"), "816": ("America/Chicago", "MO"),
    "817": ("America/Chicago", "TX"), "818": ("America/Los_Angeles", "CA"), "828": ("America/New_York", "NC"),
    "830": ("America/Chicago", "TX"), "831": ("America/Los_Angeles", "CA"), "832": ("America/Chicago", "TX"),
    "843": ("America/New_York", "SC"), "845": ("America/New_York", "NY"), "847": ("America/Chicago", "IL"),
    "848": ("America/New_York", "NJ"), "850": ("America/Chicago", "FL"), "854": ("America/New_York", "SC"),
    "856": ("America/New_York", "NJ"), "857": ("America/New_York", "MA"), "858": ("America/Los_Angeles", "CA"),
    "859": ("America/New_York", "KY"), "860": ("America/New_York", "CT"), "862": ("America/New_York", "NJ"),
    "863": ("America/New_York", "FL"), "864": ("America/New_York", "SC"), "865": ("America/New_York", "TN"),
    "870": ("America/Chicago", "AR"), "872": ("America/Chicago", "IL"), "878": ("America/New_York", "PA"),
    "901": ("America/Chicago", "TN"), "903": ("America/Chicago", "TX"), "904": ("America/New_York", "FL"),
    "906": ("America/New_York", "MI"), "907": ("America/Anchorage", "AK"), "908": ("America/New_York", "NJ"),
    "909": ("America/Los_Angeles", "CA"), "910": ("America/New_York", "NC"), "912": ("America/New_York", "GA"),
    "913": ("America/Chicago", "KS"), "914": ("America/New_York", "NY"), "915": ("America/Denver", "TX"),
    "916": ("America/Los_Angeles", "CA"), "917": ("America/New_York", "NY"), "918": ("America/Chicago", "OK"),
    "919": ("America/New_York", "NC"), "920": ("America/Chicago", "WI"), "925": ("America/Los_Angeles", "CA"),
    "928": ("America/Phoenix", "AZ"), "929": ("America/New_York", "NY"), "930": ("America/New_York", "IN"),
    "931": ("America/Chicago", "TN"), "936": ("America/Chicago", "TX"), "937": ("America/New_York", "OH"),
    "938": ("America/Chicago", "AL"), "940": ("America/Chicago", "TX"), "941": ("America/New_York", "FL"),
    "947": ("America/New_York", "MI"), "949": ("America/Los_Angeles", "CA"), "951": ("America/Los_Angeles", "CA"),
    "952": ("America/Chicago", "MN"), "954": ("America/New_York", "FL"), "956": ("America/Chicago", "TX"),
    "959": ("America/New_York", "CT"), "970": ("America/Denver", "CO"), "971": ("America/Los_Angeles", "OR"),
    "972": ("America/Chicago", "TX"), "973": ("America/New_York", "NJ"), "978": ("America/New_York", "MA"),
    "979": ("America/Chicago", "TX"), "980": ("America/New_York", "NC"), "984": ("America/New_York", "NC"),
    "985": ("America/Chicago", "LA"), "989": ("America/New_York", "MI"),
}

# State-specific calling time restrictions (stricter than federal 8am-9pm)
STATE_CALLING_RESTRICTIONS = {
    "TX": {"start_hour": 9, "end_hour": 21, "name": "Texas (9am-9pm)"},  # Texas SB 140
    "CT": {"start_hour": 9, "end_hour": 20, "name": "Connecticut (9am-8pm)"},
    "FL": {"start_hour": 8, "end_hour": 20, "name": "Florida (8am-8pm)"},
    "GA": {"start_hour": 8, "end_hour": 20, "name": "Georgia (8am-8pm)"},
    "LA": {"start_hour": 8, "end_hour": 20, "name": "Louisiana (8am-8pm)"},
    "MA": {"start_hour": 8, "end_hour": 20, "name": "Massachusetts (8am-8pm)"},
    "OK": {"start_hour": 8, "end_hour": 20, "name": "Oklahoma (8am-8pm)"},
    "PA": {"start_hour": 9, "end_hour": 21, "name": "Pennsylvania (9am-9pm)"},
    "RI": {"start_hour": 8, "end_hour": 20, "name": "Rhode Island (8am-8pm)"},
    "WA": {"start_hour": 8, "end_hour": 20, "name": "Washington (8am-8pm)"},
    "WI": {"start_hour": 8, "end_hour": 20, "name": "Wisconsin (8am-8pm)"},
    # Federal default for unlisted states
    "DEFAULT": {"start_hour": 8, "end_hour": 21, "name": "Federal TCPA (8am-9pm)"},
}

class ComplianceService:
    """
    Service for TCPA-compliant call compliance checks.
    
    Features:
    - Internal DNC list management
    - National DNC Registry integration (via Real Phone Validation API)
    - State DNC Registry checks
    - Litigator detection
    - Calling hours enforcement (8am-9pm local time)
    - State-specific time restrictions
    - Call frequency limits
    - Phone number verification
    - Usage tracking with tier-based allowances
    """
    
    def __init__(self):
        # Real Phone Validation DNC Plus API
        # Sign up at: https://realphonevalidation.com/
        self.dnc_api_key = os.environ.get("DNC_API_KEY")
        self.dnc_api_url = os.environ.get("DNC_API_URL", "https://api.realvalidation.com/rpvWebService/DNCPlus.php")
        logger.info(f"ComplianceService initialized. DNC API: {'configured' if self.dnc_api_key else 'not configured (internal list only)'}")
    
    def get_timezone_for_number(self, phone_number: str) -> tuple:
        """
        Get timezone and state from phone number area code.
        Returns (timezone_name, state_abbr) or defaults to Eastern Time.
        """
        # Extract area code from phone number
        clean_number = ''.join(filter(str.isdigit, phone_number))
        if clean_number.startswith('1') and len(clean_number) >= 4:
            area_code = clean_number[1:4]
        elif len(clean_number) >= 3:
            area_code = clean_number[:3]
        else:
            return ("America/New_York", "UNKNOWN")
        
        return AREA_CODE_TIMEZONES.get(area_code, ("America/New_York", "UNKNOWN"))
    
    def check_calling_hours(self, phone_number: str) -> dict:
        """
        Check if it's within legal calling hours for the recipient's timezone.
        TCPA requires calls only between 8am-9pm local time.
        Some states have stricter requirements.
        
        Returns:
            {
                "is_allowed": bool,
                "reason": str or None,
                "local_time": str,
                "timezone": str,
                "state": str,
                "restriction": str,
                "next_allowed_time": str or None
            }
        """
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            from backports.zoneinfo import ZoneInfo
        
        timezone_name, state = self.get_timezone_for_number(phone_number)
        
        try:
            tz = ZoneInfo(timezone_name)
            local_now = datetime.now(tz)
            local_hour = local_now.hour
            
            # Get state-specific or default restrictions
            restriction = STATE_CALLING_RESTRICTIONS.get(state, STATE_CALLING_RESTRICTIONS["DEFAULT"])
            start_hour = restriction["start_hour"]
            end_hour = restriction["end_hour"]
            restriction_name = restriction["name"]
            
            # Check if within allowed hours
            is_allowed = start_hour <= local_hour < end_hour
            
            result = {
                "is_allowed": is_allowed,
                "reason": None,
                "local_time": local_now.strftime("%I:%M %p"),
                "local_hour": local_hour,
                "timezone": timezone_name,
                "state": state,
                "restriction": restriction_name,
                "start_hour": start_hour,
                "end_hour": end_hour,
                "next_allowed_time": None
            }
            
            if not is_allowed:
                if local_hour < start_hour:
                    # Too early - calculate when calling is allowed
                    next_allowed = local_now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                    wait_minutes = int((next_allowed - local_now).total_seconds() / 60)
                    result["reason"] = f"Too early to call {state} ({local_now.strftime('%I:%M %p')} local). {restriction_name} - wait {wait_minutes} minutes"
                    result["next_allowed_time"] = next_allowed.isoformat()
                else:
                    # Too late - calculate when calling is allowed tomorrow
                    next_allowed = (local_now + timedelta(days=1)).replace(hour=start_hour, minute=0, second=0, microsecond=0)
                    result["reason"] = f"Too late to call {state} ({local_now.strftime('%I:%M %p')} local). {restriction_name} - try tomorrow at {start_hour}:00 AM"
                    result["next_allowed_time"] = next_allowed.isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking calling hours for {phone_number}: {e}")
            # Default to allowed if timezone lookup fails (conservative approach would be to block)
            return {
                "is_allowed": True,
                "reason": None,
                "local_time": "unknown",
                "timezone": timezone_name,
                "state": state,
                "restriction": "Federal TCPA (8am-9pm)",
                "error": str(e)
            }
    
    async def check_dnc(self, phone_number: str) -> bool:
        """Check if number is on internal DNC list"""
        dnc_entry = await db.dnc_list.find_one({"phone_number": phone_number}, {"_id": 0})
        return dnc_entry is not None
    
    async def check_national_dnc(self, phone_number: str, user_id: str = None) -> dict:
        """
        Check if number is on the National Do Not Call Registry.
        Uses Real Phone Validation DNC Plus API.
        
        Returns:
            {
                "on_national_dnc": bool,
                "on_state_dnc": bool,
                "is_litigator": bool,
                "is_cell": bool,
                "checked": bool,
                "source": str,
                "checked_at": str,
                "error": str or None,
                "billable": bool
            }
        """
        # Normalize phone number - Real Phone Validation expects 10 digits
        clean_number = ''.join(filter(str.isdigit, phone_number))
        if clean_number.startswith('1') and len(clean_number) == 11:
            clean_number = clean_number[1:]  # Remove country code
        
        formatted_number = f"+1{clean_number}"
        
        # Check cache first (DNC status cached for 30 days per FTC requirements)
        cached = await db.national_dnc_checks.find_one(
            {"phone_number": formatted_number}, 
            {"_id": 0}
        )
        if cached:
            try:
                checked_at = datetime.fromisoformat(cached["checked_at"].replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - checked_at).days < 30:
                    logger.info(f"Using cached National DNC check for {formatted_number}")
                    cached["billable"] = False  # Cached result is free
                    return cached
            except Exception:
                pass
        
        result = {
            "phone_number": formatted_number,
            "on_national_dnc": False,
            "on_state_dnc": False,
            "is_litigator": False,
            "is_cell": False,
            "on_dma": False,
            "checked": False,
            "source": "none",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
            "billable": False
        }
        
        # If Real Phone Validation API is configured, use it
        if self.dnc_api_key:
            try:
                async with httpx.AsyncClient() as client:
                    # Real Phone Validation DNC Plus API
                    # Endpoint: https://api.realvalidation.com/rpvWebService/DNCPlus.php
                    response = await client.get(
                        self.dnc_api_url,
                        params={
                            "phone": clean_number,  # 10 digits only
                            "token": self.dnc_api_key
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check response status
                        if data.get("status") == "connected":
                            result["on_national_dnc"] = data.get("national_dnc") == "Y"
                            result["on_state_dnc"] = data.get("state_dnc") == "Y"
                            result["is_litigator"] = data.get("litigator") == "Y"
                            result["is_cell"] = data.get("iscell") == "Y"
                            result["on_dma"] = data.get("dma") == "Y"
                            result["checked"] = True
                            result["source"] = "real_phone_validation"
                            result["billable"] = True
                            
                            logger.info(f"DNC check: {formatted_number} -> National:{result['on_national_dnc']}, State:{result['on_state_dnc']}, Litigator:{result['is_litigator']}")
                        elif data.get("status") == "invalid-phone":
                            result["error"] = "Invalid phone number"
                            result["checked"] = True
                            result["source"] = "real_phone_validation"
                        elif data.get("status") == "unauthorized":
                            result["error"] = "DNC API authentication failed - check DNC_API_KEY"
                            logger.error("DNC API unauthorized - invalid token")
                        else:
                            result["error"] = f"DNC API status: {data.get('status')}"
                    else:
                        result["error"] = f"DNC API HTTP error: {response.status_code}"
                        logger.error(f"DNC API error: {response.text}")
                        
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"DNC API exception: {e}")
        else:
            # No external API configured - check internal FTC DNC list and litigator list
            # Users can upload DNC lists from FTC data downloads
            internal_ndnc = await db.national_dnc_list.find_one(
                {"phone_number": formatted_number},
                {"_id": 0}
            )
            if internal_ndnc:
                result["on_national_dnc"] = True
                result["checked"] = True
                result["source"] = "ftc_dnc_upload"
            else:
                result["checked"] = True
                result["source"] = "internal_lists"
        
        # Always check internal litigator list (even if external API is used)
        litigator = await db.tcpa_litigators.find_one(
            {"phone_number": formatted_number},
            {"_id": 0}
        )
        if litigator:
            result["is_litigator"] = True
            result["litigator_info"] = {
                "name": litigator.get("name"),
                "firm": litigator.get("firm"),
                "notes": litigator.get("notes"),
                "risk_level": litigator.get("risk_level", "high")
            }
            logger.warning(f"TCPA LITIGATOR DETECTED: {formatted_number}")
        
        # Cache the result
        await db.national_dnc_checks.update_one(
            {"phone_number": formatted_number},
            {"$set": result},
            upsert=True
        )
        
        # Track DNC usage for billing if this was a billable check
        if result.get("billable") and user_id:
            await self.track_dnc_usage(user_id)
        
        return result
    
    async def track_dnc_usage(self, user_id: str):
        """Track DNC check usage for the current billing month"""
        now = datetime.now(timezone.utc)
        month_key = f"{now.year}-{now.month:02d}"
        
        await db.dnc_usage.update_one(
            {"user_id": user_id, "month": month_key},
            {
                "$inc": {"checks": 1},
                "$set": {"updated_at": now.isoformat()}
            },
            upsert=True
        )
    
    async def get_dnc_usage(self, user_id: str) -> dict:
        """Get DNC check usage for the current billing month"""
        now = datetime.now(timezone.utc)
        month_key = f"{now.year}-{now.month:02d}"
        
        usage = await db.dnc_usage.find_one(
            {"user_id": user_id, "month": month_key},
            {"_id": 0}
        )
        
        return {
            "month": month_key,
            "checks_used": usage.get("checks", 0) if usage else 0
        }
    
    async def add_to_dnc(self, phone_number: str, reason: str = "user_request", added_by: str = None):
        """Add number to internal DNC list"""
        existing = await db.dnc_list.find_one({"phone_number": phone_number})
        if existing:
            return False  # Already on list
        
        dnc_entry = {
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "reason": reason,
            "source": "internal",
            "added_by": added_by,
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        await db.dnc_list.insert_one(dnc_entry)
        logger.info(f"Added {phone_number} to DNC list. Reason: {reason}")
        return True
    
    async def remove_from_dnc(self, phone_number: str):
        """Remove number from internal DNC list"""
        result = await db.dnc_list.delete_one({"phone_number": phone_number})
        return result.deleted_count > 0
    
    async def verify_number(self, phone_number: str) -> Dict:
        """
        Verify phone number type using Twilio Lookup API.
        Returns line type (landline, mobile, voip) and carrier info.
        Cost: $0.005 per lookup (cached for 30 days)
        """
        # Normalize phone number
        clean_number = ''.join(filter(str.isdigit, phone_number))
        if not clean_number.startswith('1') and len(clean_number) == 10:
            clean_number = '1' + clean_number
        formatted_number = f"+{clean_number}"
        
        # Check cache first (saves money!)
        cached = await db.number_verifications.find_one({"phone_number": formatted_number}, {"_id": 0})
        if cached:
            # Return cached result if less than 30 days old
            try:
                verified_at = datetime.fromisoformat(cached["verified_at"].replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - verified_at).days < 30:
                    logger.info(f"Using cached verification for {formatted_number}")
                    return cached
            except Exception:
                pass
        
        # Use Twilio Lookup API for real verification
        verification = {
            "phone_number": formatted_number,
            "is_valid": False,
            "line_type": "unknown",
            "is_mobile": False,
            "carrier": None,
            "carrier_type": None,
            "error": None,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if twilio_client:
                # Twilio Lookup API v2 with Line Type Intelligence
                # Cost: $0.005 per successful lookup
                lookup_result = await asyncio.to_thread(
                    twilio_client.lookups.v2.phone_numbers(formatted_number).fetch,
                    fields='line_type_intelligence'
                )
                
                verification["is_valid"] = lookup_result.valid
                verification["calling_country_code"] = lookup_result.calling_country_code
                verification["national_format"] = lookup_result.national_format
                
                # Extract line type intelligence
                line_type_info = lookup_result.line_type_intelligence or {}
                verification["line_type"] = line_type_info.get("type") or "unknown"
                verification["carrier"] = line_type_info.get("carrier_name")
                verification["carrier_type"] = line_type_info.get("mobile_network_code")
                
                # Determine if mobile (higher pickup rates)
                line_type = (verification["line_type"] or "unknown").lower()
                verification["is_mobile"] = line_type in ["mobile", "cellphone", "wireless"]
                verification["is_landline"] = line_type in ["landline", "fixedline", "fixed", "fixedvoip"]
                verification["is_voip"] = line_type in ["voip", "non-fixed voip", "virtual", "nonFixedVoip"]
                
                # Priority score for dialing (mobile > landline > voip > unknown)
                priority_map = {"mobile": 100, "cellphone": 100, "wireless": 100, 
                               "landline": 60, "fixedline": 60, "fixed": 60, "fixedvoip": 55,
                               "voip": 30, "non-fixed voip": 20, "nonfixedvoip": 20, "virtual": 20}
                verification["dial_priority"] = priority_map.get(line_type, 40)
                
                logger.info(f"Twilio Lookup: {formatted_number} -> {verification['line_type']} (valid: {verification['is_valid']})")
            else:
                verification["error"] = "Twilio client not configured"
                verification["is_valid"] = True  # Assume valid if can't verify
                verification["dial_priority"] = 50
                logger.warning("Twilio client not available for phone verification")
                
        except Exception as e:
            error_msg = str(e)
            verification["error"] = error_msg
            
            # Check if number is invalid based on error
            if "not a valid phone number" in error_msg.lower():
                verification["is_valid"] = False
                verification["dial_priority"] = 0
            else:
                # Network error - assume valid but log it
                verification["is_valid"] = True
                verification["dial_priority"] = 40
            
            logger.error(f"Phone verification error for {formatted_number}: {e}")
        
        # Cache the result (even errors, to avoid repeated lookups)
        await db.number_verifications.update_one(
            {"phone_number": formatted_number},
            {"$set": verification},
            upsert=True
        )
        
        return verification
    
    async def pre_call_compliance_check(self, phone_number: str, user_id: str = None) -> Dict:
        """
        Perform all TCPA compliance checks before making a call.
        
        Checks performed:
        1. Calling hours (8am-9pm local time, state-specific restrictions)
        2. Internal DNC list
        3. National DNC Registry (if configured)
        4. Phone number verification (line type, validity)
        5. Call frequency limits (max 3 calls per 7 days)
        
        Returns whether call is allowed, reasons if not, and dial priority.
        """
        checks_performed = []
        reasons = []
        warnings = []
        is_allowed = True
        dial_priority = 50  # Default priority
        calling_hours_info = None
        national_dnc_info = None
        
        # 1. CHECK CALLING HOURS (TCPA requirement)
        checks_performed.append("calling_hours")
        calling_hours_info = self.check_calling_hours(phone_number)
        if not calling_hours_info.get("is_allowed"):
            is_allowed = False
            reasons.append(calling_hours_info.get("reason", "Outside legal calling hours"))
        
        # 2. Check internal DNC list
        checks_performed.append("internal_dnc")
        if await self.check_dnc(phone_number):
            is_allowed = False
            reasons.append("Number is on internal Do Not Call list")
        
        # 3. CHECK NATIONAL DNC REGISTRY (TCPA requirement)
        checks_performed.append("national_dnc")
        national_dnc_info = await self.check_national_dnc(phone_number, user_id)
        if national_dnc_info.get("on_national_dnc") or national_dnc_info.get("on_state_dnc"):
            is_allowed = False
            dnc_reasons = []
            if national_dnc_info.get("on_national_dnc"):
                dnc_reasons.append("National DNC")
            if national_dnc_info.get("on_state_dnc"):
                dnc_reasons.append("State DNC")
            reasons.append(f"Number is on {' and '.join(dnc_reasons)} Registry")
        
        # Warn about litigators (very high risk!)
        if national_dnc_info.get("is_litigator"):
            is_allowed = False
            reasons.append("CAUTION: Known TCPA litigator - high lawsuit risk")
        
        if national_dnc_info.get("warning"):
            warnings.append(national_dnc_info.get("warning"))
        
        # 4. Verify number with Twilio Lookup (landline vs mobile vs voip)
        checks_performed.append("number_verification")
        verification = await self.verify_number(phone_number)
        
        # Check if number is valid
        if not verification.get("is_valid", True):
            is_allowed = False
            reasons.append(f"Invalid phone number: {verification.get('error', 'verification failed')}")
        
        # Get dial priority from verification
        dial_priority = verification.get("dial_priority", 50)
        
        # Add warnings for low-priority number types (but still allow)
        line_type = verification.get("line_type", "unknown")
        if verification.get("is_voip"):
            warnings.append(f"VoIP number detected ({line_type}) - may have lower pickup rate")
            dial_priority = min(dial_priority, 30)
        elif verification.get("is_landline"):
            warnings.append(f"Landline detected ({line_type}) - typically 20% pickup rate vs 80% for mobile")
        elif verification.get("is_mobile"):
            # Mobile is preferred - no warning needed
            pass
        
        # 5. Check recent call history (don't call too frequently)
        checks_performed.append("call_frequency")
        recent_calls = await db.calls.count_documents({
            "lead_phone": phone_number,
            "started_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}
        })
        if recent_calls >= 3:
            is_allowed = False
            reasons.append("Called 3+ times in last 7 days - cooling off period")
        elif recent_calls >= 2:
            warnings.append(f"Called {recent_calls} times in last 7 days - consider spacing calls")
        
        # Log the compliance check
        check_result = {
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "user_id": user_id,
            "is_allowed": is_allowed,
            "reasons": reasons,
            "warnings": warnings,
            "checks_performed": checks_performed,
            "verification": verification,
            "calling_hours": calling_hours_info,
            "national_dnc": national_dnc_info,
            "dial_priority": dial_priority,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        await db.compliance_checks.insert_one(check_result)
        
        return {
            "phone_number": phone_number,
            "is_allowed": is_allowed,
            "reasons": reasons,
            "warnings": warnings,
            "checks_performed": checks_performed,
            "line_type": line_type,
            "is_mobile": verification.get("is_mobile", False),
            "carrier": verification.get("carrier"),
            "dial_priority": dial_priority,
            # New TCPA compliance fields
            "calling_hours": {
                "local_time": calling_hours_info.get("local_time"),
                "timezone": calling_hours_info.get("timezone"),
                "state": calling_hours_info.get("state"),
                "restriction": calling_hours_info.get("restriction"),
                "is_allowed": calling_hours_info.get("is_allowed"),
                "next_allowed_time": calling_hours_info.get("next_allowed_time")
            },
            "national_dnc": {
                "on_registry": national_dnc_info.get("on_national_dnc", False),
                "checked": national_dnc_info.get("checked", False),
                "source": national_dnc_info.get("source")
            }
        }

compliance_service = ComplianceService()

# ============== TWILIO CALLING SERVICE ==============
class TwilioCallingService:
    """Service for making real outbound calls via Twilio with AMD + Voicemail Drop"""
    
    def __init__(self):
        self.is_configured = twilio_client is not None and twilio_phone_number is not None
    
    async def make_outbound_call_with_amd(
        self,
        to_number: str,
        lead: Dict,
        campaign: Dict,
        callback_url: str,
        call_id: str
    ) -> Dict:
        """
        Initiate an outbound call with Answering Machine Detection (AMD).
        AMD detects if human or voicemail answers, allowing us to:
        - If human: Connect to full AI conversation
        - If machine: Drop pre-recorded voicemail (saves AI costs)
        
        Cost: AMD adds ~$0.02 per call but saves ~$0.14 on voicemail calls
        """
        if not self.is_configured:
            raise HTTPException(status_code=503, detail="Twilio not configured. Add TWILIO credentials to .env")
        
        try:
            # Get external URL for callbacks
            external_url = os.environ.get('EXTERNAL_URL') or callback_url
            external_url = external_url.rstrip("/")
            
            # AMD callback URL - Twilio will call this when it determines human vs machine
            amd_callback_url = f"{external_url}/api/twilio/amd/{call_id}"
            status_callback_url = f"{external_url}/api/twilio/status"
            
            # Use AsyncAmd for better detection without blocking call connection
            # machine_detection options:
            # - "Enable": Basic detection, waits for determination
            # - "DetectMessageEnd": Waits for voicemail beep before callback (better for VM drop)
            call = twilio_client.calls.create(
                to=to_number,
                from_=twilio_phone_number,
                url=f"{external_url}/api/twilio/amd-handler/{call_id}",  # Initial handler
                status_callback=status_callback_url,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                machine_detection="DetectMessageEnd",  # Wait for beep to drop voicemail
                machine_detection_timeout=30,  # Max seconds to wait for detection
                machine_detection_silence_timeout=5000,  # Silence threshold in ms
                machine_detection_speech_threshold=2400,  # Speech threshold in ms
                machine_detection_speech_end_threshold=1200,  # End of speech threshold
                async_amd=True,  # Non-blocking AMD
                async_amd_status_callback=amd_callback_url,  # Callback for AMD result
                async_amd_status_callback_method="POST",
                record=True,
                recording_status_callback=f"{external_url}/api/twilio/recording"
            )
            
            logger.info(f"Twilio call with AMD initiated: {call.sid} to {to_number}")
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "from": twilio_phone_number,
                "amd_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Twilio call with AMD failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")
    
    async def make_outbound_call(
        self,
        to_number: str,
        lead: Dict,
        campaign: Dict,
        callback_url: str
    ) -> Dict:
        """
        Initiate a real outbound call using Twilio (legacy - no AMD).
        Uses inline TwiML for reliability (no webhook dependency).
        """
        if not self.is_configured:
            raise HTTPException(status_code=503, detail="Twilio not configured. Add TWILIO credentials to .env")
        
        try:
            # Generate TwiML directly (more reliable than webhook)
            twiml = self.generate_simple_twiml(lead, campaign)
            status_callback_url = f"{callback_url}/api/twilio/status"
            
            call = twilio_client.calls.create(
                to=to_number,
                from_=twilio_phone_number,
                twiml=twiml,  # Use inline TwiML instead of URL
                status_callback=status_callback_url,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                record=True,
                recording_status_callback=f"{callback_url}/api/twilio/recording"
            )
            
            logger.info(f"Twilio call initiated: {call.sid} to {to_number}")
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "from": twilio_phone_number
            }
            
        except Exception as e:
            logger.error(f"Twilio call failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")
    
    def generate_voicemail_twiml(self, lead: Dict, campaign: Dict) -> str:
        """Generate TwiML for voicemail drop - short, professional message"""
        response = VoiceResponse()
        
        company_name = campaign.get('company_name', 'our team')
        business_name = lead.get('business_name', 'your company')
        contact_name = lead.get('contact_name', '')
        
        # Use custom voicemail message if provided, otherwise use default
        custom_vm = campaign.get('voicemail_message')
        
        if custom_vm:
            # Use custom message with variable substitution
            message = custom_vm.replace('{business_name}', business_name)
            message = message.replace('{contact_name}', contact_name)
            message = message.replace('{company_name}', company_name)
        else:
            # Default professional voicemail
            greeting = f"Hi {contact_name}, " if contact_name else "Hi, "
            message = (
                f"{greeting}this is a quick message for {business_name}. "
                f"I'm calling from {company_name} about an opportunity that could help increase your profits. "
                "I'll try you again, or feel free to call us back at your convenience. "
                "Thank you, have a great day!"
            )
        
        # Use best Twilio voice for voicemail
        response.say(message, voice='Polly.Matthew-Neural')
        
        # Pause then hang up
        response.pause(length=1)
        response.hangup()
        
        return str(response)
    
    def generate_human_twiml(self, lead: Dict, campaign: Dict, call_id: str) -> str:
        """Generate TwiML for when human answers - connect to AI conversation"""
        response = VoiceResponse()
        
        company_name = campaign.get('company_name', 'our company')
        business_name = lead.get('business_name', 'your company')
        wait_seconds = campaign.get('response_wait_seconds', 4)  # Configurable wait time
        
        voice = 'Polly.Matthew-Neural'
        
        # Compliance disclosure (REQUIRED by FCC)
        response.say(
            f"Hi, this is an AI assistant calling on behalf of {company_name}. "
            "This is an automated business call.",
            voice=voice
        )
        
        response.pause(length=1)
        
        # Main pitch
        response.say(
            f"I'm reaching out to {business_name} because we help businesses increase their profits "
            "with solutions most companies don't take advantage of. "
            "Would you be interested in learning more?",
            voice=voice
        )
        
        # Wait for caller response (configurable)
        response.pause(length=wait_seconds)
        
        # Follow up
        response.say(
            "If you'd like to learn more, one of our specialists will follow up with you shortly. "
            "Or say remove me to be added to our do not call list. "
            "Thank you for your time, have a great day!",
            voice=voice
        )
        
        return str(response)
    
    def generate_simple_twiml(self, lead: Dict, campaign: Dict) -> str:
        """Generate simple TwiML for AI call with compliance disclosure"""
        response = VoiceResponse()
        
        company_name = campaign.get('company_name', 'our company')
        business_name = lead.get('business_name', 'your company')
        wait_seconds = campaign.get('response_wait_seconds', 4)  # Configurable wait time
        
        # Use better Twilio neural voice (Polly Neural voices sound much better)
        # Options: Polly.Matthew-Neural, Polly.Joanna-Neural, Polly.Amy-Neural
        voice = 'Polly.Matthew-Neural'  # Professional male voice
        
        # Compliance disclosure (REQUIRED by FCC)
        response.say(
            f"Hi, this is an AI assistant calling on behalf of {company_name}. "
            "This is an automated business call.",
            voice=voice
        )
        
        # Pause for natural flow
        response.pause(length=1)
        
        # Main pitch
        response.say(
            f"I'm reaching out to {business_name} because we help businesses increase their profits "
            "with solutions most companies don't take advantage of. "
            "Would you be interested in learning more?",
            voice=voice
        )
        
        # Wait for caller response (configurable)
        response.pause(length=wait_seconds)
        
        # Follow up
        response.say(
            "If you'd like to learn more, one of our specialists will follow up with you shortly. "
            "Or say remove me to be added to our do not call list. "
            "Thank you for your time, have a great day!",
            voice=voice
        )
        
        response.hangup()
        return str(response)
    
    async def generate_elevenlabs_twiml(self, lead: Dict, campaign: Dict, base_url: str) -> str:
        """Generate TwiML using ElevenLabs for ultra-realistic voice"""
        if not eleven_client:
            # Fallback to Twilio voice if ElevenLabs not configured
            return self.generate_simple_twiml(lead, campaign)
        
        # This method is kept for future use with hosted audio URLs
        # Currently falls back to neural voice for reliability
        return self.generate_simple_twiml(lead, campaign)
    
    def generate_ai_greeting_twiml(self, lead: Dict, campaign: Dict) -> str:
        """Generate TwiML for AI greeting with compliance disclosure"""
        response = VoiceResponse()
        
        # Compliance disclosure (REQUIRED)
        disclosure = f"Hi, this is an AI assistant calling on behalf of {campaign.get('company_name', 'our company')}. This is an automated business call."
        
        # Add ElevenLabs voice or use Twilio's built-in
        # For now, use Twilio's voice (Alice is most natural)
        response.say(disclosure, voice='Polly.Joanna', language='en-US')
        
        # Greeting
        greeting = f"Am I speaking with someone at {lead.get('business_name', 'your company')}?"
        
        # Use Gather to wait for response
        gather = Gather(
            input='speech dtmf',
            timeout=5,
            speech_timeout='auto',
            action='/api/twilio/gather',
            method='POST'
        )
        gather.say(greeting, voice='Polly.Joanna')
        response.append(gather)
        
        # If no response, try again
        response.say("I didn't catch that. Let me try again.", voice='Polly.Joanna')
        response.redirect('/api/twilio/retry')
        
        return str(response)
    
    def generate_dnc_twiml(self) -> str:
        """Generate TwiML for DNC acknowledgment"""
        response = VoiceResponse()
        response.say(
            "No problem at all. I've removed your number from our call list. Have a great day!",
            voice='Polly.Joanna'
        )
        response.hangup()
        return str(response)

twilio_service = TwilioCallingService()

# ============== CRM INTEGRATION SERVICE ==============
from enum import Enum as PyEnum
from cryptography.fernet import Fernet

class CRMProvider(str, Enum):
    GOHIGHLEVEL = "gohighlevel"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"

class CRMCredentials(BaseModel):
    """Model for storing encrypted CRM credentials"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: CRMProvider
    # Encrypted tokens
    encrypted_access_token: Optional[str] = None
    encrypted_refresh_token: Optional[str] = None
    encrypted_api_key: Optional[str] = None
    # Provider-specific info
    instance_url: Optional[str] = None  # Salesforce instance URL
    portal_id: Optional[str] = None  # HubSpot portal ID
    location_id: Optional[str] = None  # GoHighLevel location ID
    # Token metadata
    token_expires_at: Optional[str] = None
    # Status
    is_active: bool = True
    is_connected: bool = False
    last_sync_at: Optional[str] = None
    last_error: Optional[str] = None
    total_leads_pushed: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CRMLeadPushLog(BaseModel):
    """Audit log for lead pushes to CRM"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lead_id: str
    provider: CRMProvider
    crm_contact_id: Optional[str] = None  # ID returned from CRM
    status: str  # "success", "failed", "pending"
    error_message: Optional[str] = None
    lead_data: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CRMConnectionRequest(BaseModel):
    """Request model for connecting CRM"""
    provider: CRMProvider
    api_key: Optional[str] = None  # For API key auth (GHL private apps)
    oauth_code: Optional[str] = None  # For OAuth flow
    instance_url: Optional[str] = None  # For Salesforce

class CRMIntegrationService:
    """
    Universal CRM integration service supporting:
    - GoHighLevel
    - Salesforce
    - HubSpot
    
    Handles OAuth flows, API key auth, token refresh, and lead pushing.
    """
    
    def __init__(self):
        # Generate encryption key from JWT secret for secure credential storage
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'dialgenix_default_secret_key')
        # Use a consistent key derivation
        key_bytes = jwt_secret.encode()[:32].ljust(32, b'0')
        self.cipher = Fernet(base64.urlsafe_b64encode(key_bytes))
        
        # Provider-specific endpoints
        self.endpoints = {
            CRMProvider.GOHIGHLEVEL: {
                "base_url": "https://services.leadconnectorhq.com",
                "oauth_url": "https://marketplace.gohighlevel.com/oauth/authorize",
                "token_url": "https://services.leadconnectorhq.com/oauth/token",
            },
            CRMProvider.SALESFORCE: {
                "base_url": "",  # Instance-specific
                "oauth_url": "https://login.salesforce.com/services/oauth2/authorize",
                "token_url": "https://login.salesforce.com/services/oauth2/token",
            },
            CRMProvider.HUBSPOT: {
                "base_url": "https://api.hubapi.com",
                "oauth_url": "https://app.hubspot.com/oauth/authorize",
                "token_url": "https://api.hubapi.com/oauth/v1/token",
            },
        }
        
        logger.info("CRM Integration Service initialized")
    
    def encrypt_credential(self, credential: str) -> str:
        """Encrypt a credential for secure storage"""
        return self.cipher.encrypt(credential.encode()).decode()
    
    def decrypt_credential(self, encrypted: str) -> str:
        """Decrypt a stored credential"""
        try:
            return self.cipher.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {e}")
            return None
    
    async def save_credentials(self, user_id: str, provider: CRMProvider, 
                               access_token: str = None, refresh_token: str = None,
                               api_key: str = None, **kwargs) -> Dict:
        """Save CRM credentials securely to database"""
        
        # Check if credentials already exist
        existing = await db.crm_credentials.find_one(
            {"user_id": user_id, "provider": provider.value}, {"_id": 0}
        )
        
        credential_data = {
            "user_id": user_id,
            "provider": provider.value,
            "is_active": True,
            "is_connected": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if access_token:
            credential_data["encrypted_access_token"] = self.encrypt_credential(access_token)
        if refresh_token:
            credential_data["encrypted_refresh_token"] = self.encrypt_credential(refresh_token)
        if api_key:
            credential_data["encrypted_api_key"] = self.encrypt_credential(api_key)
        
        # Add provider-specific info
        for key in ["instance_url", "portal_id", "location_id", "token_expires_at"]:
            if kwargs.get(key):
                credential_data[key] = kwargs[key]
        
        if existing:
            await db.crm_credentials.update_one(
                {"user_id": user_id, "provider": provider.value},
                {"$set": credential_data}
            )
        else:
            credential_data["id"] = str(uuid.uuid4())
            credential_data["created_at"] = datetime.now(timezone.utc).isoformat()
            credential_data["total_leads_pushed"] = 0
            await db.crm_credentials.insert_one(credential_data)
        
        logger.info(f"CRM credentials saved for user {user_id}, provider {provider.value}")
        return {"status": "connected", "provider": provider.value}
    
    async def get_credentials(self, user_id: str, provider: CRMProvider) -> Optional[Dict]:
        """Get and decrypt CRM credentials for a user"""
        credential = await db.crm_credentials.find_one(
            {"user_id": user_id, "provider": provider.value, "is_active": True},
            {"_id": 0}
        )
        
        if not credential:
            return None
        
        # Decrypt tokens
        result = dict(credential)
        if credential.get("encrypted_access_token"):
            result["access_token"] = self.decrypt_credential(credential["encrypted_access_token"])
        if credential.get("encrypted_refresh_token"):
            result["refresh_token"] = self.decrypt_credential(credential["encrypted_refresh_token"])
        if credential.get("encrypted_api_key"):
            result["api_key"] = self.decrypt_credential(credential["encrypted_api_key"])
        
        return result
    
    async def disconnect(self, user_id: str, provider: CRMProvider) -> Dict:
        """Disconnect CRM integration"""
        await db.crm_credentials.update_one(
            {"user_id": user_id, "provider": provider.value},
            {"$set": {
                "is_active": False,
                "is_connected": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"CRM disconnected for user {user_id}, provider {provider.value}")
        return {"status": "disconnected", "provider": provider.value}
    
    async def refresh_token(self, user_id: str, provider: CRMProvider) -> Optional[str]:
        """Refresh OAuth access token"""
        credentials = await self.get_credentials(user_id, provider)
        if not credentials or not credentials.get("refresh_token"):
            return None
        
        refresh_token = credentials["refresh_token"]
        endpoints = self.endpoints.get(provider)
        
        # Provider-specific refresh logic
        try:
            async with httpx.AsyncClient() as client:
                if provider == CRMProvider.GOHIGHLEVEL:
                    response = await client.post(
                        endpoints["token_url"],
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": os.environ.get("GHL_CLIENT_ID", ""),
                            "client_secret": os.environ.get("GHL_CLIENT_SECRET", ""),
                        },
                        timeout=30.0
                    )
                elif provider == CRMProvider.SALESFORCE:
                    response = await client.post(
                        endpoints["token_url"],
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": os.environ.get("SALESFORCE_CLIENT_ID", ""),
                            "client_secret": os.environ.get("SALESFORCE_CLIENT_SECRET", ""),
                        },
                        timeout=30.0
                    )
                elif provider == CRMProvider.HUBSPOT:
                    response = await client.post(
                        endpoints["token_url"],
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": os.environ.get("HUBSPOT_CLIENT_ID", ""),
                            "client_secret": os.environ.get("HUBSPOT_CLIENT_SECRET", ""),
                        },
                        timeout=30.0
                    )
                
                if response.status_code == 200:
                    token_data = response.json()
                    new_access_token = token_data.get("access_token")
                    new_refresh_token = token_data.get("refresh_token", refresh_token)
                    
                    # Save new tokens
                    await self.save_credentials(
                        user_id, provider,
                        access_token=new_access_token,
                        refresh_token=new_refresh_token
                    )
                    
                    return new_access_token
                else:
                    logger.error(f"Token refresh failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Token refresh error for {provider.value}: {e}")
            return None
    
    async def push_lead_to_crm(self, user_id: str, provider: CRMProvider, lead: Dict) -> Dict:
        """Push a qualified lead to the user's CRM"""
        credentials = await self.get_credentials(user_id, provider)
        
        if not credentials:
            return {"status": "error", "message": f"No {provider.value} credentials found"}
        
        access_token = credentials.get("access_token") or credentials.get("api_key")
        if not access_token:
            return {"status": "error", "message": "No valid access token or API key"}
        
        try:
            result = None
            
            if provider == CRMProvider.GOHIGHLEVEL:
                result = await self._push_to_gohighlevel(access_token, lead, credentials)
            elif provider == CRMProvider.SALESFORCE:
                result = await self._push_to_salesforce(access_token, lead, credentials)
            elif provider == CRMProvider.HUBSPOT:
                result = await self._push_to_hubspot(access_token, lead, credentials)
            
            # Log the push
            log_entry = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lead_id": lead.get("id", "unknown"),
                "provider": provider.value,
                "crm_contact_id": result.get("contact_id") if result else None,
                "status": "success" if result and result.get("success") else "failed",
                "error_message": result.get("error") if result else "Unknown error",
                "lead_data": lead,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.crm_lead_push_logs.insert_one(log_entry)
            
            # Update push count
            if result and result.get("success"):
                await db.crm_credentials.update_one(
                    {"user_id": user_id, "provider": provider.value},
                    {
                        "$inc": {"total_leads_pushed": 1},
                        "$set": {"last_sync_at": datetime.now(timezone.utc).isoformat()}
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error pushing lead to {provider.value}: {e}")
            return {"status": "error", "message": str(e), "success": False}
    
    async def _push_to_gohighlevel(self, access_token: str, lead: Dict, credentials: Dict) -> Dict:
        """Push lead to GoHighLevel"""
        location_id = credentials.get("location_id")
        if not location_id:
            return {"success": False, "error": "Location ID not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Create contact in GHL
                payload = {
                    "firstName": lead.get("contact_name", "").split()[0] if lead.get("contact_name") else "",
                    "lastName": " ".join(lead.get("contact_name", "").split()[1:]) if lead.get("contact_name") else "",
                    "email": lead.get("email", ""),
                    "phone": lead.get("phone", ""),
                    "companyName": lead.get("business_name", ""),
                    "source": "DialGenix.ai",
                    "tags": ["qualified-lead", "ai-cold-call"],
                }
                
                response = await client.post(
                    "https://services.leadconnectorhq.com/contacts/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Version": "2021-07-28"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "contact_id": data.get("contact", {}).get("id"),
                        "provider": "gohighlevel"
                    }
                else:
                    return {"success": False, "error": f"GHL API error: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _push_to_salesforce(self, access_token: str, lead: Dict, credentials: Dict) -> Dict:
        """Push lead to Salesforce"""
        instance_url = credentials.get("instance_url")
        if not instance_url:
            return {"success": False, "error": "Salesforce instance URL not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                # Create Lead in Salesforce
                contact_name = lead.get("contact_name", "Unknown")
                name_parts = contact_name.split()
                
                payload = {
                    "FirstName": name_parts[0] if name_parts else "",
                    "LastName": " ".join(name_parts[1:]) if len(name_parts) > 1 else contact_name,
                    "Email": lead.get("email", ""),
                    "Phone": lead.get("phone", ""),
                    "Company": lead.get("business_name", "Unknown Company"),
                    "LeadSource": "DialGenix.ai",
                    "Status": "Open - Not Contacted",
                    "Rating": "Warm",
                    "Industry": lead.get("industry", ""),
                }
                
                response = await client.post(
                    f"{instance_url}/services/data/v59.0/sobjects/Lead",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "contact_id": data.get("id"),
                        "provider": "salesforce"
                    }
                else:
                    return {"success": False, "error": f"Salesforce API error: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _push_to_hubspot(self, access_token: str, lead: Dict, credentials: Dict) -> Dict:
        """Push lead to HubSpot"""
        try:
            async with httpx.AsyncClient() as client:
                # Create contact in HubSpot
                contact_name = lead.get("contact_name", "Unknown")
                name_parts = contact_name.split()
                
                payload = {
                    "properties": {
                        "firstname": name_parts[0] if name_parts else "",
                        "lastname": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
                        "email": lead.get("email", ""),
                        "phone": lead.get("phone", ""),
                        "company": lead.get("business_name", ""),
                        "hs_lead_status": "NEW",
                        "lifecyclestage": "lead"
                    }
                }
                
                response = await client.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "contact_id": data.get("id"),
                        "provider": "hubspot"
                    }
                elif response.status_code == 409:
                    # Contact already exists
                    return {
                        "success": True,
                        "contact_id": "existing",
                        "provider": "hubspot",
                        "message": "Contact already exists in HubSpot"
                    }
                else:
                    return {"success": False, "error": f"HubSpot API error: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def auto_push_qualified_lead(self, user_id: str, lead: Dict) -> List[Dict]:
        """
        Automatically push a qualified lead to all connected CRMs.
        Called when a lead status changes to 'qualified'.
        """
        results = []
        
        # Get all connected CRMs for this user
        cursor = db.crm_credentials.find(
            {"user_id": user_id, "is_active": True, "is_connected": True},
            {"_id": 0}
        )
        
        async for credential in cursor:
            provider = CRMProvider(credential["provider"])
            result = await self.push_lead_to_crm(user_id, provider, lead)
            result["provider"] = credential["provider"]
            results.append(result)
        
        return results

crm_service = CRMIntegrationService()

# ============== WEBHOOK MODELS ==============
class WebhookConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Owner of this webhook (for multi-tenancy)
    name: str
    event_type: str  # "lead_qualified" or "meeting_booked"
    notification_emails: List[str] = []
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WebhookConfigCreate(BaseModel):
    name: str
    event_type: str
    notification_emails: List[str]

# ============== AUTHENTICATION HELPERS ==============
async def get_session_from_token(session_token: str) -> Optional[Dict]:
    """Validate session token and return user data"""
    if not session_token:
        return None
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        return None
    
    # Check expiry
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Get user
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    return user_doc

async def get_current_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict:
    """Get current user from session - checks cookies first, then Authorization header"""
    session_token = None
    
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Fall back to Authorization header
    if not session_token and credentials:
        session_token = credentials.credentials
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_session_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user

async def get_optional_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None

# ============== SUBSCRIPTION TIER ENFORCEMENT ==============

# Feature flags by subscription tier
TIER_FEATURES = {
    None: {  # Free trial / No subscription
        "max_leads_per_month": 50,
        "max_calls_per_month": 50,
        "max_custom_keywords": 10,
        "csv_export": False,
        "csv_upload": False,
        "api_access": False,
        "calendar_booking": False,
        "icp_scoring": False,
        "ai_icp_scoring": False,
        "voicemail_drop": False,
        "custom_scripts": False,
        "max_campaigns": 1,
        "max_agents": 1,
        "max_team_seats": 1,
        # Recording & Transcription
        "call_recording": False,
        "recording_retention_days": 0,
        "call_transcription": False,
        # CRM Integration
        "crm_integration": False,
        # DNC Compliance - Basic internal only
        "dnc_checks_per_month": 50,
        "national_dnc_enabled": False,
    },
    "payg": {  # Pay-as-you-go - No monthly, credit-based
        "max_leads_per_month": -1,  # Unlimited (credit-based)
        "max_calls_per_month": -1,  # Unlimited (credit-based)
        "max_custom_keywords": 20,
        "csv_export": True,
        "csv_upload": True,
        "api_access": False,
        "calendar_booking": False,
        "icp_scoring": True,
        "ai_icp_scoring": False,
        "voicemail_drop": True,
        "custom_scripts": False,
        "max_campaigns": 2,
        "max_agents": 2,
        "max_team_seats": 1,
        # Recording & Transcription - Basic
        "call_recording": True,
        "recording_retention_days": 3,  # Short retention for PAYG
        "call_transcription": False,
        # PAYG specific
        "is_payg": True,
        "cost_per_lead": 0.25,
        "cost_per_call": 0.50,
        # CRM Integration
        "crm_integration": False,
        # DNC Compliance - Basic with overage
        "dnc_checks_per_month": 100,
        "national_dnc_enabled": True,
        "dnc_overage_cost": 0.015,  # $0.015 per check over limit
    },
    "starter": {
        "max_leads_per_month": 250,
        "max_calls_per_month": 250,
        "max_custom_keywords": 50,
        "csv_export": True,
        "csv_upload": False,
        "api_access": False,
        "calendar_booking": False,
        "icp_scoring": True,
        "ai_icp_scoring": False,
        "voicemail_drop": True,
        "custom_scripts": False,
        "max_campaigns": 3,
        "max_agents": 3,
        "max_team_seats": 1,
        # Recording & Transcription - Basic
        "call_recording": True,
        "recording_retention_days": 7,
        "call_transcription": False,
        # CRM Integration
        "crm_integration": False,
        # DNC Compliance - 500 included
        "dnc_checks_per_month": 500,
        "national_dnc_enabled": True,
        "dnc_overage_cost": 0.012,  # $0.012 per check over limit
    },
    "professional": {
        "max_leads_per_month": 1000,
        "max_calls_per_month": 1000,
        "max_custom_keywords": 100,
        "csv_export": True,
        "csv_upload": True,
        "api_access": True,
        "calendar_booking": True,
        "icp_scoring": True,
        "ai_icp_scoring": True,
        "voicemail_drop": True,
        "custom_scripts": True,
        "max_campaigns": 10,
        "max_agents": 10,
        "max_team_seats": 5,
        # Recording & Transcription - Full
        "call_recording": True,
        "recording_retention_days": 30,
        "call_transcription": True,
        # CRM Integration - Enabled
        "crm_integration": True,
        # DNC Compliance - 2000 included
        "dnc_checks_per_month": 2000,
        "national_dnc_enabled": True,
        "dnc_overage_cost": 0.01,  # $0.01 per check over limit
    },
    "unlimited": {
        "max_leads_per_month": 5000,
        "max_calls_per_month": -1,  # Unlimited
        "max_custom_keywords": 100,
        "csv_export": True,
        "csv_upload": True,
        "api_access": True,
        "calendar_booking": True,
        "icp_scoring": True,
        "ai_icp_scoring": True,
        "voicemail_drop": True,
        "custom_scripts": True,
        "max_campaigns": -1,  # Unlimited
        "max_agents": -1,  # Unlimited
        "max_team_seats": 5,
        # Recording & Transcription - Premium
        "call_recording": True,
        "recording_retention_days": 90,
        "call_transcription": True,
        # CRM Integration - Enabled
        "crm_integration": True,
        # DNC Compliance - Unlimited
        "dnc_checks_per_month": -1,  # Unlimited
        "national_dnc_enabled": True,
        "dnc_overage_cost": 0,
    },
    "byl": {  # Bring Your List
        "max_leads_per_month": 0,  # They bring their own
        "max_calls_per_month": 1500,
        "max_custom_keywords": 100,
        "csv_export": True,
        "csv_upload": True,  # Unlimited CSV uploads
        "api_access": True,
        "calendar_booking": True,
        "icp_scoring": True,
        "ai_icp_scoring": True,
        "voicemail_drop": True,
        "custom_scripts": True,
        "max_campaigns": 5,
        "max_agents": 10,
        "max_team_seats": 3,
        # Recording & Transcription - Full
        "call_recording": True,
        "recording_retention_days": 30,
        "call_transcription": True,
        # CRM Integration - Enabled
        "crm_integration": True,
        # DNC Compliance - 1500 included (matches call volume)
        "dnc_checks_per_month": 1500,
        "national_dnc_enabled": True,
        "dnc_overage_cost": 0.01,
    },
}

# DNC check overage pricing (when user exceeds monthly allowance)
DNC_OVERAGE_COST_DEFAULT = 0.015  # $0.015 per check

def get_tier_features(user: Dict) -> Dict:
    """Get feature flags for user's subscription tier"""
    tier = user.get("subscription_tier")
    # Admin users get unlimited features
    if user.get("role") == "admin":
        return TIER_FEATURES["unlimited"]
    return TIER_FEATURES.get(tier, TIER_FEATURES[None])

def check_feature_access(user: Dict, feature: str) -> bool:
    """Check if user has access to a specific feature"""
    features = get_tier_features(user)
    return features.get(feature, False)

async def get_monthly_usage(user_id: str) -> Dict:
    """Get user's usage for the current billing month"""
    # Get start of current month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count leads created this month
    leads_this_month = await db.leads.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    # Count calls made this month
    calls_this_month = await db.calls.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    return {
        "leads_used": leads_this_month,
        "calls_used": calls_this_month,
        "month_start": month_start.isoformat()
    }

async def check_subscription_limit(user: Dict, resource_type: str, count: int = 1) -> Dict:
    """
    Check if user can use a resource based on subscription limits.
    Returns: {"allowed": bool, "reason": str, "limit": int, "used": int}
    """
    features = get_tier_features(user)
    usage = await get_monthly_usage(user["user_id"])
    
    if resource_type == "leads":
        limit = features["max_leads_per_month"]
        used = usage["leads_used"]
        
        # BYL plan has no lead discovery (they upload their own)
        if user.get("subscription_tier") == "byl":
            return {
                "allowed": False,
                "reason": "Bring Your List plan doesn't include lead discovery. Please upload your own leads via CSV.",
                "limit": 0,
                "used": used
            }
        
        if limit != -1 and used + count > limit:
            return {
                "allowed": False,
                "reason": f"Monthly lead limit reached ({used}/{limit}). Upgrade your plan or purchase a lead pack.",
                "limit": limit,
                "used": used
            }
    
    elif resource_type == "calls":
        limit = features["max_calls_per_month"]
        used = usage["calls_used"]
        
        if limit != -1 and used + count > limit:
            return {
                "allowed": False,
                "reason": f"Monthly call limit reached ({used}/{limit}). Upgrade your plan or purchase a call pack.",
                "limit": limit,
                "used": used
            }
    
    elif resource_type == "campaigns":
        limit = features["max_campaigns"]
        current_count = await db.campaigns.count_documents({"user_id": user["user_id"]})
        
        if limit != -1 and current_count >= limit:
            return {
                "allowed": False,
                "reason": f"Campaign limit reached ({current_count}/{limit}). Upgrade your plan to create more campaigns.",
                "limit": limit,
                "used": current_count
            }
    
    elif resource_type == "agents":
        limit = features["max_agents"]
        current_count = await db.agents.count_documents({"user_id": user["user_id"]})
        
        if limit != -1 and current_count >= limit:
            return {
                "allowed": False,
                "reason": f"Agent limit reached ({current_count}/{limit}). Upgrade your plan to add more agents.",
                "limit": limit,
                "used": current_count
            }
    
    return {"allowed": True, "reason": None, "limit": -1, "used": 0}

async def check_low_balance_and_notify(user: Dict):
    """Check if user has low balance and send notification if needed"""
    # Check if alerts are enabled in user settings
    user_settings = await db.settings.find_one({"user_id": user.get("user_id")}, {"_id": 0})
    if user_settings and not user_settings.get("low_balance_alerts_enabled", True):
        return  # Alerts disabled by user
    
    lead_credits = user.get("lead_credits_remaining", 0)
    call_credits = user.get("call_credits_remaining", 0)
    
    # Use user-configurable thresholds or defaults
    LOW_LEAD_THRESHOLD = user_settings.get("low_lead_threshold", 20) if user_settings else 20
    LOW_CALL_THRESHOLD = user_settings.get("low_call_threshold", 20) if user_settings else 20
    
    notifications = []
    
    if lead_credits <= LOW_LEAD_THRESHOLD and lead_credits > 0:
        notifications.append({
            "type": "low_lead_credits",
            "message": f"You have only {lead_credits} lead credits remaining.",
            "threshold": LOW_LEAD_THRESHOLD
        })
    
    if call_credits <= LOW_CALL_THRESHOLD and call_credits > 0:
        notifications.append({
            "type": "low_call_credits",
            "message": f"You have only {call_credits} call credits remaining.",
            "threshold": LOW_CALL_THRESHOLD
        })
    
    # Check if we've already notified recently (within 24 hours)
    if notifications:
        user_id = user["user_id"]
        last_notification = await db.low_balance_notifications.find_one(
            {"user_id": user_id},
            sort=[("sent_at", -1)]
        )
        
        if last_notification:
            sent_at = datetime.fromisoformat(last_notification["sent_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - sent_at < timedelta(hours=24):
                return  # Don't spam notifications
        
        # Send email notification if Resend is configured
        if notification_service.is_configured and user.get("email"):
            try:
                await notification_service.send_low_balance_notification(
                    user_email=user["email"],
                    user_name=user.get("name", "User"),
                    lead_credits=lead_credits,
                    call_credits=call_credits
                )
                
                # Record that we sent notification
                await db.low_balance_notifications.insert_one({
                    "user_id": user_id,
                    "notifications": notifications,
                    "sent_at": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to send low balance notification: {e}")

def get_trial_status(user: Dict) -> Dict:
    """
    Get Synthflow-style trial status for a user.
    Returns trial remaining time, usage stats, and whether trial is expired.
    """
    subscription_tier = user.get("subscription_tier")
    
    # Paid users don't have trial limits
    if subscription_tier and subscription_tier not in [None, "free", "free_trial"]:
        return {
            "is_trial": False,
            "trial_active": False,
            "trial_expired": False,
            "minutes_total": 0,
            "seconds_used": 0,
            "minutes_remaining": -1,  # -1 indicates unlimited (paid tier)
            "seconds_remaining": -1,
            "usage_percent": 0,
            "can_make_calls": True
        }
    
    # Free trial users
    trial_minutes_total = user.get("trial_minutes_total", 15.0)
    trial_seconds_used = user.get("trial_seconds_used", 0.0)
    trial_expired = user.get("trial_expired", False)
    
    total_seconds = trial_minutes_total * 60
    seconds_remaining = max(0, total_seconds - trial_seconds_used)
    minutes_remaining = seconds_remaining / 60
    usage_percent = min(100, (trial_seconds_used / total_seconds) * 100) if total_seconds > 0 else 100
    
    # Trial is expired if all time used OR explicitly marked expired
    is_expired = trial_expired or seconds_remaining <= 0
    
    return {
        "is_trial": True,
        "trial_active": not is_expired,
        "trial_expired": is_expired,
        "minutes_total": trial_minutes_total,
        "seconds_used": trial_seconds_used,
        "minutes_remaining": round(minutes_remaining, 2),
        "seconds_remaining": round(seconds_remaining, 0),
        "usage_percent": round(usage_percent, 1),
        "can_make_calls": not is_expired
    }

async def deduct_trial_time(user_id: str, seconds: float) -> Dict:
    """
    Deduct call time from user's trial.
    Returns updated trial status.
    """
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return {"error": "User not found"}
    
    trial_status = get_trial_status(user)
    
    # Skip if not a trial user
    if not trial_status["is_trial"]:
        return trial_status
    
    # Skip if trial already expired
    if trial_status["trial_expired"]:
        return trial_status
    
    new_seconds_used = user.get("trial_seconds_used", 0.0) + seconds
    total_seconds = user.get("trial_minutes_total", 15.0) * 60
    is_now_expired = new_seconds_used >= total_seconds
    
    # Update user's trial usage
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "trial_seconds_used": new_seconds_used,
            "trial_expired": is_now_expired,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Get updated status
    updated_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return get_trial_status(updated_user)

# ============== API ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "AI Cold Calling Machine API", "status": "running"}

# ============== AUTHENTICATION ROUTES ==============
# NOTE: When USE_NEW_AUTH_ROUTES=true, the modular routes from routes/auth.py
# take precedence (they are mounted first). These legacy routes remain as fallback.

# Phone verification for trial abuse prevention
def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    # Remove all non-digit characters except leading +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    # If no + prefix and 10 digits, assume US number
    if not cleaned.startswith('+') and len(cleaned) == 10:
        cleaned = '+1' + cleaned
    elif not cleaned.startswith('+') and len(cleaned) == 11 and cleaned.startswith('1'):
        cleaned = '+' + cleaned
    return cleaned

@api_router.post("/auth/send-verification")
async def send_phone_verification(request: PhoneVerificationRequest):
    """
    Send SMS verification code to phone number.
    Checks if phone has already been used for a trial.
    """
    phone = normalize_phone_number(request.phone_number)
    
    # Check if email already registered
    existing_user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if phone number already used for a trial (abuse prevention)
    existing_trial = await db.trial_phone_numbers.find_one({"phone_number": phone})
    if existing_trial:
        raise HTTPException(
            status_code=400, 
            detail="This phone number has already been used for a free trial. Please subscribe to continue."
        )
    
    # Check if there's a recent verification request (rate limiting)
    recent_request = await db.phone_verifications.find_one({
        "phone_number": phone,
        "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}
    })
    if recent_request:
        raise HTTPException(
            status_code=429, 
            detail="Please wait 1 minute before requesting another code"
        )
    
    # Generate 6-digit verification code
    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Store verification code (expires in 10 minutes)
    await db.phone_verifications.delete_many({"phone_number": phone})  # Remove old codes
    await db.phone_verifications.insert_one({
        "phone_number": phone,
        "email": request.email,
        "code": verification_code,
        "attempts": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    })
    
    # Send SMS via Twilio
    if twilio_service.is_configured:
        try:
            twilio_client.messages.create(
                body=f"Your DialGenix.ai verification code is: {verification_code}. Valid for 10 minutes.",
                from_=os.environ.get("TWILIO_PHONE_NUMBER"),
                to=phone
            )
            logger.info(f"Sent verification SMS to {phone}")
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            raise HTTPException(status_code=500, detail="Failed to send verification SMS. Please try again.")
    else:
        # For development/testing without Twilio
        logger.warning(f"Twilio not configured. Verification code for {phone}: {verification_code}")
    
    return {
        "message": "Verification code sent",
        "phone_number": phone,
        "expires_in_minutes": 10
    }

@api_router.post("/auth/verify-phone")
async def verify_phone_code(request: PhoneVerificationConfirm):
    """
    Verify the SMS code. Returns a verification token to use during registration.
    """
    phone = normalize_phone_number(request.phone_number)
    
    # Find verification record
    verification = await db.phone_verifications.find_one({"phone_number": phone})
    
    if not verification:
        raise HTTPException(status_code=400, detail="No verification code found. Please request a new one.")
    
    # Check if expired
    expires_at = datetime.fromisoformat(verification["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        await db.phone_verifications.delete_one({"phone_number": phone})
        raise HTTPException(status_code=400, detail="Verification code expired. Please request a new one.")
    
    # Check attempts (max 5)
    if verification.get("attempts", 0) >= 5:
        await db.phone_verifications.delete_one({"phone_number": phone})
        raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new code.")
    
    # Verify code
    if verification["code"] != request.code:
        await db.phone_verifications.update_one(
            {"phone_number": phone},
            {"$inc": {"attempts": 1}}
        )
        remaining = 5 - verification.get("attempts", 0) - 1
        raise HTTPException(status_code=400, detail=f"Invalid code. {remaining} attempts remaining.")
    
    # Code is correct - generate verification token
    verification_token = f"phone_verified_{uuid.uuid4().hex}"
    
    # Update verification record with token
    await db.phone_verifications.update_one(
        {"phone_number": phone},
        {"$set": {
            "verified": True,
            "verification_token": verification_token,
            "verified_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "Phone verified successfully",
        "phone_number": phone,
        "verification_token": verification_token
    }

# Model for OAuth user phone verification
class OAuthPhoneVerification(BaseModel):
    phone_number: str
    verification_code: str  # The verification token from verify-phone

@api_router.post("/auth/verify-phone-oauth")
async def verify_phone_for_oauth_user(
    request: OAuthPhoneVerification,
    current_user: Dict = Depends(get_current_user)
):
    """
    Complete phone verification for OAuth users.
    Required before they can use their free trial.
    """
    phone = normalize_phone_number(request.phone_number)
    user_id = current_user["user_id"]
    
    # Check if user already has verified phone
    if current_user.get("phone_verified"):
        raise HTTPException(status_code=400, detail="Phone already verified")
    
    # Verify the verification token
    verification = await db.phone_verifications.find_one({
        "phone_number": phone,
        "verified": True,
        "verification_token": request.verification_code
    })
    
    if not verification:
        raise HTTPException(
            status_code=400, 
            detail="Invalid or expired phone verification. Please verify your phone number first."
        )
    
    # Check if phone number already used for a trial
    existing_trial = await db.trial_phone_numbers.find_one({"phone_number": phone})
    if existing_trial:
        raise HTTPException(
            status_code=400, 
            detail="This phone number has already been used for a free trial. Please subscribe to continue."
        )
    
    # Update user with verified phone
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "phone_number": phone,
            "phone_verified": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Record phone number as used for trial
    await db.trial_phone_numbers.insert_one({
        "phone_number": phone,
        "user_id": user_id,
        "email": current_user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Clean up verification records
    await db.phone_verifications.delete_many({"phone_number": phone})
    
    return {
        "message": "Phone verified successfully. You can now use your free trial!",
        "phone_number": phone,
        "phone_verified": True
    }

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    """Register a new user with email/password. Requires verified phone number."""
    phone = normalize_phone_number(user_data.phone_number)
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verify phone verification code
    verification = await db.phone_verifications.find_one({
        "phone_number": phone,
        "verified": True,
        "verification_token": user_data.verification_code
    })
    
    if not verification:
        raise HTTPException(
            status_code=400, 
            detail="Invalid or expired phone verification. Please verify your phone number first."
        )
    
    # Check if phone number already used for a trial (double-check for race conditions)
    existing_trial = await db.trial_phone_numbers.find_one({"phone_number": phone})
    if existing_trial:
        raise HTTPException(
            status_code=400, 
            detail="This phone number has already been used for a free trial. Please subscribe to continue."
        )
    
    # Hash password and create user
    password_hashed = hash_password(user_data.password)
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "phone_number": phone,
        "phone_verified": True,
        "password_hash": password_hashed,
        "role": UserRole.USER.value,
        "subscription_tier": None,
        "subscription_status": "trialing",
        "lead_credits_remaining": 0,  # No lead credits in free trial
        "call_credits_remaining": 0,  # No call credits in free trial
        "monthly_lead_allowance": 0,
        "monthly_call_allowance": 0,
        "team_seat_count": 1,
        # Synthflow-style 15-minute free trial
        "trial_minutes_total": 15.0,
        "trial_seconds_used": 0.0,
        "trial_expired": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Record phone number as used for trial (prevent reuse)
    await db.trial_phone_numbers.insert_one({
        "phone_number": phone,
        "user_id": user_id,
        "email": user_data.email,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Clean up verification records
    await db.phone_verifications.delete_many({"phone_number": phone})
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Return user without password
    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    
    return {
        "user": user_doc,
        "session_token": session_token
    }

@api_router.post("/auth/login")
async def login(user_data: UserLogin, response: Response):
    """Login with email/password"""
    user_doc = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check password
    if not user_doc.get("password_hash"):
        raise HTTPException(status_code=401, detail="Please use Google OAuth to login")
    
    # Verify password
    if not verify_password(user_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
    session_doc = {
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/"
    )
    
    # Return user without password
    user_doc.pop("password_hash", None)
    
    return {
        "user": user_doc,
        "session_token": session_token
    }

@api_router.post("/auth/session")
async def exchange_session_id(request: Request, response: Response):
    """Exchange Emergent OAuth session_id for our session token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to validate session_id and get user data
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=10.0
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            
            auth_data = auth_response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to validate session with Emergent Auth: {e}")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
    
    # Check if user exists, create if not
    user_doc = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    if not user_doc:
        # Create new user from OAuth - requires phone verification before trial
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data.get("name", auth_data["email"].split("@")[0]),
            "picture": auth_data.get("picture"),
            "phone_number": None,  # Must verify phone before using trial
            "phone_verified": False,  # Blocks calls until verified
            "role": UserRole.USER.value,
            "subscription_tier": None,
            "subscription_status": "trialing",
            "lead_credits_remaining": 0,  # No lead credits in free trial
            "call_credits_remaining": 0,  # No call credits in free trial
            "monthly_lead_allowance": 0,
            "monthly_call_allowance": 0,
            "team_seat_count": 1,
            # Synthflow-style 15-minute free trial
            "trial_minutes_total": 15.0,
            "trial_seconds_used": 0.0,
            "trial_expired": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    else:
        # Update existing user's OAuth data
        await db.users.update_one(
            {"email": auth_data["email"]},
            {"$set": {
                "name": auth_data.get("name", user_doc.get("name")),
                "picture": auth_data.get("picture"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        user_doc = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    # Create our own session
    session_token = f"sess_{uuid.uuid4().hex}"
    session_doc = {
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/"
    )
    
    user_doc.pop("password_hash", None)
    
    return {
        "user": user_doc,
        "session_token": session_token
    }

@api_router.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user"""
    current_user.pop("password_hash", None)
    
    # Check for low balance and potentially send notification
    await check_low_balance_and_notify(current_user)
    
    # Add trial status to response
    trial_status = get_trial_status(current_user)
    current_user["trial_status"] = trial_status
    
    return current_user

@api_router.get("/subscription/features")
async def get_subscription_features(current_user: Dict = Depends(get_current_user)):
    """Get current user's subscription features and limits"""
    features = get_tier_features(current_user)
    usage = await get_monthly_usage(current_user["user_id"])
    
    tier = current_user.get("subscription_tier") or "free_trial"
    plan_info = SUBSCRIPTION_PLANS.get(tier, {})
    
    response = {
        "tier": tier,
        "plan_name": plan_info.get("name", "Free Trial"),
        "features": features,
        "usage": {
            "leads_used": usage["leads_used"],
            "leads_limit": features["max_leads_per_month"],
            "calls_used": usage["calls_used"],
            "calls_limit": features["max_calls_per_month"],
            "month_start": usage["month_start"]
        },
        "credits": {
            "lead_credits": current_user.get("lead_credits_remaining", 0),
            "call_credits": current_user.get("call_credits_remaining", 0)
        }
    }
    
    # Add PAYG specific info
    if tier == "payg" or features.get("is_payg"):
        response["payg_info"] = {
            "cost_per_lead": features.get("cost_per_lead", 0.25),
            "cost_per_call": features.get("cost_per_call", 0.50),
            "available_packs": PAYG_CREDIT_PACKS
        }
    
    return response

@api_router.get("/user/trial-status")
async def get_user_trial_status(current_user: Dict = Depends(get_current_user)):
    """
    Get Synthflow-style trial status for the current user.
    Returns remaining trial time, usage percentage, and whether user can make calls.
    """
    trial_status = get_trial_status(current_user)
    phone_verified = current_user.get("phone_verified", False)
    
    # Trial users need phone verification before they can make calls
    can_use_trial = phone_verified if trial_status["is_trial"] else True
    
    return {
        **trial_status,
        "user_id": current_user["user_id"],
        "subscription_tier": current_user.get("subscription_tier"),
        "subscription_status": current_user.get("subscription_status", "trialing"),
        "phone_verified": phone_verified,
        "phone_verification_required": trial_status["is_trial"] and not phone_verified,
        "can_use_trial": can_use_trial,
        "upgrade_url": "/app/packs"
    }

# ============== CRM INTEGRATION ENDPOINTS ==============

@api_router.get("/crm/status")
async def get_crm_status(current_user: Dict = Depends(get_current_user)):
    """Get status of all CRM integrations for current user"""
    user_id = current_user["user_id"]
    
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("crm_integration"):
        return {
            "enabled": False,
            "message": "CRM integration requires Professional plan or higher",
            "upgrade_required": True,
            "connections": []
        }
    
    connections = []
    for provider in CRMProvider:
        credential = await db.crm_credentials.find_one(
            {"user_id": user_id, "provider": provider.value},
            {"_id": 0, "encrypted_access_token": 0, "encrypted_refresh_token": 0, "encrypted_api_key": 0}
        )
        
        connections.append({
            "provider": provider.value,
            "name": provider.value.replace("gohighlevel", "GoHighLevel").replace("salesforce", "Salesforce").replace("hubspot", "HubSpot"),
            "is_connected": credential.get("is_connected", False) if credential else False,
            "is_active": credential.get("is_active", False) if credential else False,
            "total_leads_pushed": credential.get("total_leads_pushed", 0) if credential else 0,
            "last_sync_at": credential.get("last_sync_at") if credential else None,
            "last_error": credential.get("last_error") if credential else None,
        })
    
    return {
        "enabled": True,
        "connections": connections
    }

@api_router.post("/crm/connect")
async def connect_crm(
    request: CRMConnectionRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Connect a CRM using API key authentication"""
    user_id = current_user["user_id"]
    
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("crm_integration"):
        raise HTTPException(
            status_code=403,
            detail="CRM integration requires Professional plan or higher"
        )
    
    provider = request.provider
    
    # For API key authentication (simpler than OAuth)
    if request.api_key:
        # Validate the API key by making a test request
        is_valid = await _validate_crm_api_key(provider, request.api_key, request.instance_url)
        
        if not is_valid["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid API key: {is_valid.get('error', 'Unknown error')}"
            )
        
        # Save credentials
        await crm_service.save_credentials(
            user_id=user_id,
            provider=provider,
            api_key=request.api_key,
            instance_url=request.instance_url,
            location_id=is_valid.get("location_id"),
            portal_id=is_valid.get("portal_id")
        )
        
        return {
            "status": "connected",
            "provider": provider.value,
            "message": f"Successfully connected to {provider.value}"
        }
    
    # For OAuth - return authorization URL
    else:
        auth_url = _get_oauth_authorization_url(provider, user_id)
        return {
            "status": "redirect",
            "auth_url": auth_url,
            "message": "Redirect user to this URL to authorize"
        }

async def _validate_crm_api_key(provider: CRMProvider, api_key: str, instance_url: str = None) -> Dict:
    """Validate CRM API key by making a test request"""
    try:
        async with httpx.AsyncClient() as client:
            if provider == CRMProvider.GOHIGHLEVEL:
                # GHL uses Bearer token for API key
                response = await client.get(
                    "https://services.leadconnectorhq.com/locations/",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Version": "2021-07-28"
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    locations = data.get("locations", [])
                    return {
                        "valid": True,
                        "location_id": locations[0].get("id") if locations else None
                    }
                return {"valid": False, "error": "Invalid GoHighLevel API key"}
                
            elif provider == CRMProvider.SALESFORCE:
                if not instance_url:
                    return {"valid": False, "error": "Salesforce instance URL required"}
                response = await client.get(
                    f"{instance_url}/services/data/v59.0/",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"valid": True}
                return {"valid": False, "error": "Invalid Salesforce access token"}
                
            elif provider == CRMProvider.HUBSPOT:
                response = await client.get(
                    "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    # Get portal ID from response headers or account info
                    portal_id = response.headers.get("X-HubSpot-Portal-Id", "unknown")
                    return {"valid": True, "portal_id": portal_id}
                return {"valid": False, "error": "Invalid HubSpot API key"}
                
    except Exception as e:
        return {"valid": False, "error": str(e)}

def _get_oauth_authorization_url(provider: CRMProvider, user_id: str) -> str:
    """Generate OAuth authorization URL for CRM"""
    external_url = os.environ.get('EXTERNAL_URL', 'http://localhost:8001')
    callback_url = f"{external_url}/api/crm/oauth/callback"
    
    if provider == CRMProvider.GOHIGHLEVEL:
        client_id = os.environ.get("GHL_CLIENT_ID", "")
        return (
            f"https://marketplace.gohighlevel.com/oauth/chooselocation?"
            f"response_type=code&redirect_uri={callback_url}&"
            f"client_id={client_id}&scope=contacts.readonly contacts.write&"
            f"state={user_id}_{provider.value}"
        )
    elif provider == CRMProvider.SALESFORCE:
        client_id = os.environ.get("SALESFORCE_CLIENT_ID", "")
        return (
            f"https://login.salesforce.com/services/oauth2/authorize?"
            f"response_type=code&client_id={client_id}&"
            f"redirect_uri={callback_url}&scope=api&"
            f"state={user_id}_{provider.value}"
        )
    elif provider == CRMProvider.HUBSPOT:
        client_id = os.environ.get("HUBSPOT_CLIENT_ID", "")
        return (
            f"https://app.hubspot.com/oauth/authorize?"
            f"client_id={client_id}&redirect_uri={callback_url}&"
            f"scope=crm.objects.contacts.read crm.objects.contacts.write&"
            f"state={user_id}_{provider.value}"
        )
    
    return ""

@api_router.get("/crm/oauth/callback")
async def crm_oauth_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    """Handle OAuth callback from CRM providers"""
    try:
        # Parse state to get user_id and provider
        parts = state.rsplit("_", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        user_id, provider_str = parts
        provider = CRMProvider(provider_str)
        
        external_url = os.environ.get('EXTERNAL_URL', 'http://localhost:8001')
        callback_url = f"{external_url}/api/crm/oauth/callback"
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            if provider == CRMProvider.GOHIGHLEVEL:
                response = await client.post(
                    "https://services.leadconnectorhq.com/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": os.environ.get("GHL_CLIENT_ID", ""),
                        "client_secret": os.environ.get("GHL_CLIENT_SECRET", ""),
                        "redirect_uri": callback_url,
                        "user_type": "Location"
                    },
                    timeout=30.0
                )
            elif provider == CRMProvider.SALESFORCE:
                response = await client.post(
                    "https://login.salesforce.com/services/oauth2/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": os.environ.get("SALESFORCE_CLIENT_ID", ""),
                        "client_secret": os.environ.get("SALESFORCE_CLIENT_SECRET", ""),
                        "redirect_uri": callback_url
                    },
                    timeout=30.0
                )
            elif provider == CRMProvider.HUBSPOT:
                response = await client.post(
                    "https://api.hubapi.com/oauth/v1/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": os.environ.get("HUBSPOT_CLIENT_ID", ""),
                        "client_secret": os.environ.get("HUBSPOT_CLIENT_SECRET", ""),
                        "redirect_uri": callback_url
                    },
                    timeout=30.0
                )
            
            if response.status_code != 200:
                logger.error(f"OAuth token exchange failed: {response.text}")
                raise HTTPException(status_code=400, detail="OAuth token exchange failed")
            
            token_data = response.json()
            
            # Save credentials
            await crm_service.save_credentials(
                user_id=user_id,
                provider=provider,
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                instance_url=token_data.get("instance_url"),  # Salesforce
                location_id=token_data.get("locationId"),  # GHL
            )
        
        # Redirect to frontend success page
        frontend_url = os.environ.get('EXTERNAL_URL', 'http://localhost:3000')
        return RedirectResponse(url=f"{frontend_url}/app?crm_connected={provider.value}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crm/disconnect/{provider}")
async def disconnect_crm(
    provider: str,
    current_user: Dict = Depends(get_current_user)
):
    """Disconnect a CRM integration"""
    user_id = current_user["user_id"]
    
    try:
        crm_provider = CRMProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid CRM provider: {provider}")
    
    result = await crm_service.disconnect(user_id, crm_provider)
    return result

@api_router.post("/crm/push-lead/{provider}")
async def push_lead_to_crm(
    provider: str,
    lead_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Manually push a lead to a specific CRM"""
    user_id = current_user["user_id"]
    
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("crm_integration"):
        raise HTTPException(
            status_code=403,
            detail="CRM integration requires Professional plan or higher"
        )
    
    try:
        crm_provider = CRMProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid CRM provider: {provider}")
    
    # Get lead
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    result = await crm_service.push_lead_to_crm(user_id, crm_provider, lead)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to push lead"))
    
    return result

@api_router.get("/crm/push-logs")
async def get_crm_push_logs(
    provider: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """Get CRM lead push logs"""
    user_id = current_user["user_id"]
    
    query = {"user_id": user_id}
    if provider:
        query["provider"] = provider
    
    cursor = db.crm_lead_push_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    return {"logs": logs, "count": len(logs)}

# ============== PAY-AS-YOU-GO ENDPOINTS ==============

@api_router.get("/pricing/plans")
async def get_pricing_plans():
    """Get all available pricing plans (public endpoint)"""
    plans = []
    
    for tier_id, plan in SUBSCRIPTION_PLANS.items():
        plan_data = {
            "id": tier_id,
            "name": plan["name"],
            "price": plan["price"],
            "features": plan.get("features", []),
            "users": plan.get("users", 1),
            "leads_per_month": plan.get("leads_per_month", 0),
            "calls_per_month": plan.get("calls_per_month", 0),
        }
        
        # Add PAYG credit costs
        if tier_id == "payg":
            plan_data["credit_cost"] = plan.get("credit_cost", {})
            plan_data["is_payg"] = True
        
        plans.append(plan_data)
    
    # Sort by price
    plans.sort(key=lambda x: x["price"])
    
    return {
        "plans": plans,
        "payg_packs": PAYG_CREDIT_PACKS,
        "comparison": {
            "payg_best_for": "Testing, low volume (<100 calls/month)",
            "starter_best_for": "Solo founders, small teams",
            "professional_best_for": "Growing sales teams, agencies",
            "unlimited_best_for": "High-volume outbound teams"
        }
    }

@api_router.get("/payg/packs")
async def get_payg_packs():
    """Get available PAYG credit packs"""
    return {
        "packs": PAYG_CREDIT_PACKS,
        "credit_rates": {
            "per_lead": 0.25,
            "per_call": 0.50,
            "bulk_savings": "Up to 38% off with larger packs"
        }
    }

@api_router.post("/payg/purchase")
async def purchase_payg_pack(
    pack_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Purchase a PAYG credit pack.
    In production, this would integrate with Stripe for payment processing.
    """
    # Find the pack
    pack = next((p for p in PAYG_CREDIT_PACKS if p["id"] == pack_id), None)
    if not pack:
        raise HTTPException(status_code=404, detail="Credit pack not found")
    
    # Add credits to user account (works for any tier as top-up)
    lead_credits = pack.get("leads", 0)
    call_credits = pack.get("calls", 0)
    
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$inc": {
                "lead_credits_remaining": lead_credits,
                "call_credits_remaining": call_credits
            },
            "$set": {
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Log the purchase
    purchase_record = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "pack_id": pack_id,
        "pack_name": pack["name"],
        "leads_added": lead_credits,
        "calls_added": call_credits,
        "amount": pack["price"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.credit_purchases.insert_one(purchase_record)
    
    # Get updated balance
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    
    return {
        "message": f"Successfully purchased {pack['name']}",
        "pack": pack,
        "credits_added": {
            "leads": lead_credits,
            "calls": call_credits
        },
        "new_balance": {
            "lead_credits": user.get("lead_credits_remaining", 0),
            "call_credits": user.get("call_credits_remaining", 0)
        }
    }

@api_router.post("/payg/upgrade")
async def upgrade_to_payg(current_user: Dict = Depends(get_current_user)):
    """
    Upgrade a free trial user to PAYG tier.
    This allows them to purchase credits without a monthly subscription.
    """
    current_tier = current_user.get("subscription_tier")
    
    # Only allow upgrade from free trial (None)
    if current_tier and current_tier not in [None, "free_trial"]:
        raise HTTPException(
            status_code=400, 
            detail="You already have an active subscription. Contact support to change plans."
        )
    
    # Update user to PAYG tier
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$set": {
                "subscription_tier": "payg",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": "Successfully upgraded to Pay-as-you-go plan",
        "tier": "payg",
        "features": TIER_FEATURES["payg"],
        "next_step": "Purchase a credit pack to start making calls"
    }

@api_router.get("/payg/balance")
async def get_payg_balance(current_user: Dict = Depends(get_current_user)):
    """Get current credit balance and usage history"""
    # Get recent purchases
    purchases = await db.credit_purchases.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get usage stats
    usage = await get_monthly_usage(current_user["user_id"])
    
    return {
        "balance": {
            "lead_credits": current_user.get("lead_credits_remaining", 0),
            "call_credits": current_user.get("call_credits_remaining", 0)
        },
        "this_month": {
            "leads_used": usage["leads_used"],
            "calls_used": usage["calls_used"]
        },
        "recent_purchases": purchases,
        "estimated_remaining": {
            "leads_at_current_rate": current_user.get("lead_credits_remaining", 0),
            "calls_at_current_rate": current_user.get("call_credits_remaining", 0)
        }
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    
    return {"message": "Logged out successfully"}

# ----- User Keywords Management -----
class SaveKeywordsRequest(BaseModel):
    keywords: List[str]

@api_router.post("/user/keywords")
async def save_user_keywords(
    request: SaveKeywordsRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Save user's intent keywords (up to 100)"""
    # Validate and clean keywords
    keywords = [kw.strip() for kw in request.keywords[:100] if kw and kw.strip()]
    
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "saved_keywords": keywords,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": f"Saved {len(keywords)} keywords",
        "keywords": keywords
    }

@api_router.get("/user/keywords")
async def get_user_keywords(current_user: Dict = Depends(get_current_user)):
    """Get user's saved intent keywords"""
    return {
        "keywords": current_user.get("saved_keywords", [])
    }

@api_router.post("/user/onboarding-complete")
async def complete_onboarding(current_user: Dict = Depends(get_current_user)):
    """Mark user's onboarding as completed"""
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "onboarding_completed": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Onboarding completed"}

@api_router.post("/user/setup-wizard-complete")
async def complete_setup_wizard(current_user: Dict = Depends(get_current_user)):
    """Mark user's setup wizard as completed"""
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "setup_wizard_completed": True,
            "setup_wizard_completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Setup wizard completed"}

@api_router.get("/setup/status")
async def get_setup_status(current_user: Dict = Depends(get_current_user)):
    """
    Get comprehensive setup status for the user.
    Returns completion status for all required setup steps.
    """
    user_id = current_user["user_id"]
    
    # Check Twilio configuration from settings
    settings = await db.settings.find_one({}, {"_id": 0})
    twilio_configured = settings.get("twilio_configured", False) if settings else False
    
    # Also check if Twilio env vars are set
    twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    twilio_env_configured = all([twilio_account_sid, twilio_auth_token, twilio_phone_number])
    
    # Check if user has any agents with Calendly links
    agents_with_calendly = await db.agents.count_documents({
        "user_id": user_id,
        "calendly_link": {"$exists": True, "$nin": ["", None]}
    })
    calendly_configured = agents_with_calendly > 0
    
    # Check compliance status
    compliance_acknowledged = current_user.get("compliance_acknowledged", False)
    
    # Check if user has any agents
    agent_count = await db.agents.count_documents({"user_id": user_id})
    has_agent = agent_count > 0
    
    # Check if user has any campaigns
    campaign_count = await db.campaigns.count_documents({"user_id": user_id})
    has_campaign = campaign_count > 0
    
    # Check CRM status (optional)
    crm_connected = await db.crm_credentials.count_documents({
        "user_id": user_id,
        "is_connected": True
    }) > 0
    
    # Build steps list
    steps = [
        {
            "id": "twilio",
            "title": "Connect Twilio Voice",
            "completed": twilio_configured or twilio_env_configured,
            "required": True
        },
        {
            "id": "calendly",
            "title": "Set Up Calendly Booking",
            "completed": calendly_configured,
            "required": True
        },
        {
            "id": "compliance",
            "title": "Complete Compliance Setup",
            "completed": compliance_acknowledged,
            "required": True
        },
        {
            "id": "agent",
            "title": "Create Your First Agent",
            "completed": has_agent,
            "required": True
        },
        {
            "id": "campaign",
            "title": "Create a Campaign",
            "completed": has_campaign,
            "required": True
        },
        {
            "id": "crm",
            "title": "Connect CRM (Optional)",
            "completed": crm_connected,
            "required": False
        }
    ]
    
    # Calculate completion
    required_steps = [s for s in steps if s["required"]]
    completed_required = [s for s in required_steps if s["completed"]]
    all_required_complete = len(completed_required) == len(required_steps)
    
    total_completed = len([s for s in steps if s["completed"]])
    completion_percentage = round((total_completed / len(steps)) * 100)
    
    return {
        "steps": steps,
        "completion_percentage": completion_percentage,
        "all_required_complete": all_required_complete,
        "required_complete_count": len(completed_required),
        "required_total_count": len(required_steps),
        "setup_wizard_completed": current_user.get("setup_wizard_completed", False),
        "can_make_calls": all_required_complete
    }

@api_router.get("/setup/can-call")
async def check_can_call(current_user: Dict = Depends(get_current_user)):
    """
    Quick check if user can make calls (all required setup complete).
    Used to gate calling features.
    """
    setup_status = await get_setup_status(current_user)
    return {
        "can_make_calls": setup_status["all_required_complete"],
        "missing_steps": [
            s["title"] for s in setup_status["steps"] 
            if s["required"] and not s["completed"]
        ]
    }

# ----- AI Help Chat -----
class HelpChatRequest(BaseModel):
    message: str
    context: Optional[str] = None  # Current page/feature user is on

@api_router.post("/help/chat")
async def help_chat(
    request: HelpChatRequest,
    current_user: Dict = Depends(get_current_user)
):
    """AI-powered help chat that guides users through the system"""
    
    system_prompt = """You are DialGenix.ai's helpful assistant. You guide sales agents through using the AI cold calling platform.

PLATFORM OVERVIEW:
DialGenix.ai is a B2B SaaS that:
1. Discovers high-intent leads using AI (businesses actively searching for solutions)
2. Makes AI-powered cold calls to qualify leads
3. Books meetings with qualified prospects

KEY FEATURES & HOW TO USE THEM:

📍 LEAD DISCOVERY (Most Important First Step):
- Go to "Lead Discovery" in the sidebar
- Add your custom keywords (up to 100) that indicate buying intent for YOUR industry
- Example keywords: "Salesforce alternative", "best CRM software", "switching providers"
- Click "Preview Examples (Free)" to see sample leads before using credits
- Click "Discover High-Intent Leads" to find and save real leads

📞 CAMPAIGNS:
- Create a campaign with your AI script
- The script tells the AI what to say and how to qualify leads
- Good scripts: Introduce yourself, ask qualifying questions, handle objections, book meetings
- Assign leads to campaigns to start calling

👥 AGENTS:
- Add human agents who receive qualified leads
- Each agent needs a Calendly link for booking
- AI calls qualify leads, then routes hot leads to agents

📊 CALL HISTORY:
- View all calls made by the AI
- Listen to recordings, read transcripts
- See qualification scores and outcomes

💳 CREDITS & BILLING:
- Lead credits: Used when discovering leads
- Call credits: Used when AI makes calls
- Buy more in "Credit Packs" or upgrade your subscription

CAMPAIGN SETUP CHECKLIST:
1. ✅ Add your industry-specific keywords in Lead Discovery
2. ✅ Preview examples to validate keywords
3. ✅ Discover 10-20 leads to start
4. ✅ Create a campaign with qualifying questions
5. ✅ Add at least one agent with Calendly
6. ✅ Assign leads to the campaign
7. ✅ Start the campaign and monitor results

Be helpful, concise, and guide users step-by-step. If they seem stuck, ask what they're trying to accomplish."""

    try:
        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"help-{current_user['user_id']}-{uuid.uuid4().hex[:8]}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        # Add context about user's current state
        user_context = f"""
User Info:
- Name: {current_user.get('name', 'User')}
- Subscription: {current_user.get('subscription_tier', 'None')} ({current_user.get('subscription_status', 'inactive')})
- Lead Credits: {current_user.get('lead_credits_remaining', 0)}
- Call Credits: {current_user.get('call_credits_remaining', 0)}
- Has saved keywords: {'Yes' if current_user.get('saved_keywords') else 'No'}
- Onboarding completed: {'Yes' if current_user.get('onboarding_completed') else 'No'}
- Current page: {request.context or 'Unknown'}

User's question: {request.message}
"""
        
        user_message = UserMessage(text=user_context)
        response = await chat.send_message(user_message)
        
        return {
            "response": response,
            "suggested_actions": []  # Can add contextual action buttons
        }
        
    except Exception as e:
        logger.error(f"Help chat error: {e}")
        return {
            "response": "I'm having trouble connecting right now. For quick help: 1) Start with Lead Discovery to find prospects, 2) Create a Campaign with your script, 3) Add Agents with Calendly links, 4) Assign leads and start calling!",
            "error": True
        }

# ----- Dashboard Stats -----
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: Dict = Depends(get_current_user)):
    """Get dashboard stats - filtered by user_id for multi-tenancy"""
    user_id = current_user["user_id"]
    user_filter = {"user_id": user_id}
    
    total_leads = await db.leads.count_documents(user_filter)
    qualified_leads = await db.leads.count_documents({"user_id": user_id, "status": LeadStatus.QUALIFIED})
    booked_leads = await db.leads.count_documents({"user_id": user_id, "status": LeadStatus.BOOKED})
    total_calls = await db.calls.count_documents(user_filter)
    active_campaigns = await db.campaigns.count_documents({"user_id": user_id, "status": CampaignStatus.ACTIVE})
    total_agents = await db.agents.count_documents({"user_id": user_id, "is_active": True})
    
    # Get recent calls for this user only
    recent_calls = await db.calls.find(
        user_filter,
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "total_leads": total_leads,
        "qualified_leads": qualified_leads,
        "booked_leads": booked_leads,
        "total_calls": total_calls,
        "active_campaigns": active_campaigns,
        "total_agents": total_agents,
        "qualification_rate": round((qualified_leads / total_leads * 100) if total_leads > 0 else 0, 1),
        "booking_rate": round((booked_leads / qualified_leads * 100) if qualified_leads > 0 else 0, 1),
        "recent_calls": recent_calls
    }

# ----- Lead Discovery -----
class GPTIntentSearchRequest(BaseModel):
    search_query: str = "credit card processing"
    industry: Optional[str] = None
    location: Optional[str] = None
    max_results: int = 10
    custom_keywords: Optional[List[str]] = None  # Up to 100 custom intent keywords

class PreviewLeadsRequest(BaseModel):
    search_query: str = "credit card processing"
    industry: Optional[str] = None
    location: Optional[str] = None
    custom_keywords: Optional[List[str]] = None

@api_router.post("/leads/preview-examples")
async def preview_lead_examples(
    request: PreviewLeadsRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Preview example leads based on keywords WITHOUT using credits.
    Returns 3 sample leads to show what kind of results the search would produce.
    """
    # Get custom keywords or use defaults
    custom_keywords = None
    if request.custom_keywords:
        custom_keywords = [kw.strip() for kw in request.custom_keywords[:100] if kw and kw.strip()]
    
    # Generate preview leads (only 3, and don't save them)
    preview_leads = await ai_service.gpt_intent_search(
        query=request.search_query,
        industry=request.industry,
        location=request.location,
        max_results=3,  # Only 3 examples
        custom_keywords=custom_keywords
    )
    
    return {
        "preview": True,
        "count": len(preview_leads),
        "message": "These are example leads based on your keywords. Run a full search to discover and save leads.",
        "example_leads": preview_leads,
        "keywords_used": custom_keywords[:10] if custom_keywords else ["Using default keywords"]
    }

@api_router.post("/leads/discover")
async def discover_leads(request: LeadDiscoveryRequest, current_user: Dict = Depends(get_current_user)):
    """Discover new leads using AI-powered research (legacy endpoint)"""
    user_id = current_user["user_id"]
    
    discovered = await ai_service.gpt_intent_search(
        query=request.search_query,
        location=request.location,
        max_results=request.max_results
    )
    
    created_leads = []
    for biz in discovered:
        lead_data = Lead(
            user_id=user_id,  # Assign to current user
            business_name=biz.get("name", "Unknown Business"),
            phone=biz.get("phone", ""),
            source="ai_discovery",
            intent_signals=biz.get("intent_signals", ["credit_card_processing_intent"])
        )
        await db.leads.insert_one(lead_data.model_dump())
        created_leads.append(lead_data)
    
    return {
        "discovered": len(created_leads),
        "leads": [lead.model_dump() for lead in created_leads]
    }

@api_router.post("/leads/gpt-intent-search")
async def gpt_intent_search(
    request: GPTIntentSearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Discover leads using GPT-5.2 powered intent search (deducts lead credits)"""
    user_id = current_user["user_id"]
    leads_requested = request.max_results
    leads_remaining = current_user.get("lead_credits_remaining", 0)
    
    # Check subscription tier limits
    limit_check = await check_subscription_limit(current_user, "leads", leads_requested)
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    # Validate custom keywords based on tier
    features = get_tier_features(current_user)
    max_keywords = features.get("max_custom_keywords", 10)
    
    custom_keywords = None
    if request.custom_keywords:
        custom_keywords = [kw.strip() for kw in request.custom_keywords[:max_keywords] if kw and kw.strip()]
        if len(request.custom_keywords) > max_keywords:
            raise HTTPException(
                status_code=403, 
                detail=f"Your plan allows up to {max_keywords} custom keywords. Upgrade to use more."
            )
    
    # Check if user has enough credits
    if leads_remaining < leads_requested:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient lead credits. You have {leads_remaining} credits but requested {leads_requested} leads. Please purchase more credits."
        )
    
    discovered = await ai_service.gpt_intent_search(
        query=request.search_query,
        industry=request.industry,
        location=request.location,
        max_results=request.max_results,
        custom_keywords=custom_keywords
    )
    
    created_leads = []
    for biz in discovered:
        lead_data = Lead(
            business_name=biz.get("name", "Unknown Business"),
            phone=biz.get("phone", ""),
            email=biz.get("email"),
            source="gpt_intent_search",
            intent_signals=biz.get("intent_signals", [])
        )
        await db.leads.insert_one(lead_data.model_dump())
        created_leads.append(lead_data)
    
    leads_discovered = len(created_leads)
    
    # Deduct credits for leads actually discovered
    if leads_discovered > 0:
        new_balance = leads_remaining - leads_discovered
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"lead_credits_remaining": -leads_discovered},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Log usage event for analytics
        await log_usage_event(
            user_id=user_id,
            event_type="lead_discovery",
            amount=leads_discovered,
            credits_after=new_balance
        )
    
    return {
        "discovered": leads_discovered,
        "source": "gpt_intent_search",
        "leads": [lead.model_dump() for lead in created_leads],
        "credits_used": leads_discovered,
        "credits_remaining": leads_remaining - leads_discovered
    }

# ----- Leads CRUD -----
@api_router.get("/leads", response_model=List[Lead])
async def get_leads(
    status: Optional[LeadStatus] = None,
    limit: int = Query(100, le=500),
    skip: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Get leads belonging to the current user"""
    query = {"user_id": current_user["user_id"]}
    if status:
        query["status"] = status
    
    leads = await db.leads.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return leads

@api_router.get("/leads/export-csv")
async def export_leads_csv(
    status: Optional[LeadStatus] = None, 
    line_type: Optional[str] = Query(default=None, description="Filter by line type: mobile, landline, voip"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Export leads to CSV (only user's own leads).
    Optional filters:
    - status: Filter by lead status (new, contacted, qualified, etc.)
    - line_type: Filter by phone line type (mobile, landline, voip)
    """
    # Check feature access - CSV export requires Starter+
    features = get_tier_features(current_user)
    if not features.get("csv_export"):
        raise HTTPException(
            status_code=403, 
            detail="CSV export is not available on your plan. Upgrade to Starter or higher."
        )
    
    query = {"user_id": current_user["user_id"]}
    if status:
        query["status"] = status
    if line_type:
        query["line_type"] = line_type
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(10000)
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found matching filters")
    
    # Create CSV in memory
    output = io.StringIO()
    fieldnames = ['business_name', 'contact_name', 'phone', 'email', 'status', 'line_type', 'carrier', 'source', 'intent_signals', 'qualification_score', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for lead in leads:
        writer.writerow({
            'business_name': lead.get('business_name', ''),
            'contact_name': lead.get('contact_name', ''),
            'phone': lead.get('phone', ''),
            'email': lead.get('email', ''),
            'status': lead.get('status', ''),
            'line_type': lead.get('line_type', ''),
            'carrier': lead.get('carrier', ''),
            'source': lead.get('source', ''),
            'intent_signals': '; '.join(lead.get('intent_signals', [])),
            'qualification_score': lead.get('qualification_score', ''),
            'created_at': lead.get('created_at', '')
        })
    
    output.seek(0)
    
    # Generate filename based on filters
    filename_parts = ["leads"]
    if line_type:
        filename_parts.append(line_type)
    if status:
        filename_parts.append(status)
    filename_parts.append(datetime.now().strftime('%Y%m%d_%H%M%S'))
    filename = "_".join(filename_parts) + ".csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/leads/export-mobile-csv")
async def export_mobile_leads_csv(
    status: Optional[LeadStatus] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Export only mobile phone leads to CSV.
    Perfect for SMS campaigns or other mobile-specific projects.
    """
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("csv_export"):
        raise HTTPException(
            status_code=403, 
            detail="CSV export is not available on your plan. Upgrade to Starter or higher."
        )
    
    query = {"user_id": current_user["user_id"], "line_type": "mobile"}
    if status:
        query["status"] = status
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(10000)
    
    if not leads:
        raise HTTPException(status_code=404, detail="No mobile leads found")
    
    # Create CSV optimized for SMS/mobile campaigns
    output = io.StringIO()
    fieldnames = ['phone', 'business_name', 'contact_name', 'email', 'carrier', 'status', 'qualification_score']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for lead in leads:
        writer.writerow({
            'phone': lead.get('phone', ''),
            'business_name': lead.get('business_name', ''),
            'contact_name': lead.get('contact_name', ''),
            'email': lead.get('email', ''),
            'carrier': lead.get('carrier', ''),
            'status': lead.get('status', ''),
            'qualification_score': lead.get('qualification_score', '')
        })
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mobile_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@api_router.get("/leads/phone-stats")
async def get_lead_phone_stats(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get statistics about lead phone types (mobile vs landline vs VoIP).
    """
    user_id = current_user["user_id"]
    
    # Count by line type
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$line_type",
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.leads.aggregate(pipeline).to_list(100)
    
    stats = {
        "mobile": 0,
        "landline": 0,
        "voip": 0,
        "unknown": 0,
        "total": 0
    }
    
    for r in results:
        line_type = r["_id"] or "unknown"
        if line_type in stats:
            stats[line_type] = r["count"]
        else:
            stats["unknown"] += r["count"]
        stats["total"] += r["count"]
    
    return {
        "stats": stats,
        "percentages": {
            "mobile": round(stats["mobile"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            "landline": round(stats["landline"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            "voip": round(stats["voip"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
            "unknown": round(stats["unknown"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        },
        "export_urls": {
            "all_leads": "/api/leads/export-csv",
            "mobile_only": "/api/leads/export-mobile-csv",
            "landline_only": "/api/leads/export-csv?line_type=landline",
            "voip_only": "/api/leads/export-csv?line_type=voip"
        }
    }

@api_router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific lead (must belong to current user)"""
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@api_router.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new lead owned by the current user"""
    lead_obj = Lead(**lead.model_dump(), user_id=current_user["user_id"])
    await db.leads.insert_one(lead_obj.model_dump())
    return lead_obj

@api_router.post("/leads/{lead_id}/verify-phone")
async def verify_lead_phone(
    lead_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Verify a lead's phone number and update with line type (mobile/landline/VoIP).
    Uses Twilio Lookup to determine phone type and carrier.
    """
    user_id = current_user["user_id"]
    
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    phone = lead.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")
    
    # Perform verification
    verification = await compliance_service.verify_number(phone)
    
    # Update lead with phone info
    update_data = {
        "line_type": verification.get("line_type", "unknown"),
        "carrier": verification.get("carrier"),
        "phone_verified": verification.get("is_valid", False),
        "dial_priority": verification.get("dial_priority", 50),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.leads.update_one(
        {"id": lead_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    return {
        "lead_id": lead_id,
        "phone": phone,
        "verification": {
            "line_type": verification.get("line_type"),
            "is_mobile": verification.get("is_mobile", False),
            "is_landline": verification.get("is_landline", False),
            "is_voip": verification.get("is_voip", False),
            "carrier": verification.get("carrier"),
            "is_valid": verification.get("is_valid", True),
            "dial_priority": verification.get("dial_priority", 50)
        }
    }

class BulkVerifyRequest(BaseModel):
    """Request body for bulk phone verification"""
    lead_ids: Optional[List[str]] = None
    verify_all_unverified: bool = False

@api_router.post("/leads/verify-phones-bulk")
async def verify_leads_phones_bulk(
    request: BulkVerifyRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Bulk verify phone numbers for multiple leads.
    - lead_ids: List of specific lead IDs to verify
    - verify_all_unverified: If true, verify all leads that haven't been verified yet
    
    Note: Uses Twilio Lookup which has per-lookup costs.
    """
    user_id = current_user["user_id"]
    lead_ids = request.lead_ids
    verify_all_unverified = request.verify_all_unverified
    
    query = {"user_id": user_id}
    
    if lead_ids:
        query["id"] = {"$in": lead_ids}
    elif verify_all_unverified:
        query["phone_verified"] = {"$ne": True}
    else:
        raise HTTPException(
            status_code=400, 
            detail="Provide lead_ids or set verify_all_unverified=true"
        )
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(500)  # Limit to 500 at a time
    
    if not leads:
        return {"message": "No leads to verify", "verified": 0}
    
    results = {
        "total": len(leads),
        "verified": 0,
        "mobile": 0,
        "landline": 0,
        "voip": 0,
        "unknown": 0,
        "failed": 0
    }
    
    for lead in leads:
        phone = lead.get("phone")
        if not phone:
            results["failed"] += 1
            continue
        
        try:
            verification = await compliance_service.verify_number(phone)
            
            line_type = verification.get("line_type", "unknown")
            update_data = {
                "line_type": line_type,
                "carrier": verification.get("carrier"),
                "phone_verified": verification.get("is_valid", False),
                "dial_priority": verification.get("dial_priority", 50),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.leads.update_one(
                {"id": lead["id"], "user_id": user_id},
                {"$set": update_data}
            )
            
            results["verified"] += 1
            if line_type in ["mobile", "cellphone", "wireless"]:
                results["mobile"] += 1
            elif line_type in ["landline", "fixedline", "fixed"]:
                results["landline"] += 1
            elif line_type in ["voip", "non-fixed voip", "virtual"]:
                results["voip"] += 1
            else:
                results["unknown"] += 1
                
        except Exception as e:
            logger.error(f"Failed to verify phone for lead {lead['id']}: {e}")
            results["failed"] += 1
    
    return {
        "message": f"Verified {results['verified']} of {results['total']} leads",
        "results": results,
        "export_mobile_url": "/api/leads/export-mobile-csv"
    }

@api_router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str, 
    updates: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Update a lead (must belong to current user)"""
    user_id = current_user["user_id"]
    
    # Get current lead to check status change
    current_lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not current_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    old_status = current_lead.get("status")
    new_status = updates.get("status")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.leads.update_one(
        {"id": lead_id, "user_id": user_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    
    # Auto-push to CRM when lead becomes qualified
    if new_status == "qualified" and old_status != "qualified":
        features = get_tier_features(current_user)
        if features.get("crm_integration"):
            # Push to all connected CRMs in background
            background_tasks.add_task(
                crm_service.auto_push_qualified_lead,
                user_id,
                lead
            )
            logger.info(f"Queued CRM push for qualified lead {lead_id}")
    
    return lead

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a lead (must belong to current user)"""
    result = await db.leads.delete_one({"id": lead_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}

# ----- CSV Upload -----
@api_router.post("/leads/upload-csv")
async def upload_leads_csv(file: UploadFile = File(...), current_user: Dict = Depends(get_current_user)):
    """Upload leads from CSV file (Bring Your Own List)"""
    # Check feature access - CSV upload requires BYL or Professional+
    features = get_tier_features(current_user)
    if not features.get("csv_upload"):
        raise HTTPException(
            status_code=403, 
            detail="CSV upload is not available on your plan. Upgrade to Professional or Bring Your List plan."
        )
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    user_id = current_user["user_id"]
    
    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        created_leads = []
        errors = []
        
        for idx, row in enumerate(reader):
            try:
                # Map common column names
                business_name = row.get('business_name') or row.get('company') or row.get('name') or row.get('Business Name') or row.get('Company')
                phone = row.get('phone') or row.get('Phone') or row.get('phone_number') or row.get('Phone Number')
                email = row.get('email') or row.get('Email') or row.get('email_address')
                contact_name = row.get('contact_name') or row.get('contact') or row.get('Contact') or row.get('Contact Name')
                industry = row.get('industry') or row.get('Industry')
                company_size = row.get('company_size') or row.get('size') or row.get('Company Size')
                
                if not business_name or not phone:
                    errors.append(f"Row {idx + 1}: Missing business_name or phone")
                    continue
                
                lead_data = Lead(
                    user_id=user_id,  # Assign to current user
                    business_name=business_name,
                    phone=phone,
                    email=email,
                    contact_name=contact_name,
                    industry=industry,
                    company_size=company_size,
                    source="csv_upload",
                    intent_signals=["Uploaded from CSV"]
                )
                await db.leads.insert_one(lead_data.model_dump())
                created_leads.append(lead_data)
                
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        return {
            "uploaded": len(created_leads),
            "errors": len(errors),
            "error_details": errors[:10] if errors else [],
            "message": f"Successfully uploaded {len(created_leads)} leads"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

# ----- Phone & Email Verification Endpoints -----

class PhoneVerifyRequest(BaseModel):
    phone_number: str

class EmailVerifyRequest(BaseModel):
    email: str

@api_router.post("/verify/phone")
async def verify_phone_number(
    request: PhoneVerifyRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Verify a phone number using Twilio Lookup API.
    Returns line type (mobile/landline/voip), carrier, and dial priority.
    Cost: $0.005 per lookup (cached for 30 days).
    """
    verification = await compliance_service.verify_number(request.phone_number)
    
    return {
        "phone_number": verification.get("phone_number"),
        "is_valid": verification.get("is_valid", False),
        "line_type": verification.get("line_type", "unknown"),
        "is_mobile": verification.get("is_mobile", False),
        "is_landline": verification.get("is_landline", False),
        "is_voip": verification.get("is_voip", False),
        "carrier": verification.get("carrier"),
        "dial_priority": verification.get("dial_priority", 50),
        "recommendation": _get_dial_recommendation(verification),
        "cached": verification.get("verified_at") != datetime.now(timezone.utc).isoformat()
    }

def _get_dial_recommendation(verification: Dict) -> str:
    """Generate human-readable dial recommendation based on verification"""
    if not verification.get("is_valid", True):
        return "DO NOT CALL - Invalid number"
    
    priority = verification.get("dial_priority", 50)
    line_type = verification.get("line_type", "unknown")
    
    if priority >= 80:
        return f"HIGH PRIORITY - Mobile number ({line_type}) - expect 70-80% pickup rate"
    elif priority >= 50:
        return f"MEDIUM PRIORITY - Landline ({line_type}) - expect 15-25% pickup rate"
    elif priority >= 20:
        return f"LOW PRIORITY - VoIP ({line_type}) - may be spam filtered, expect 5-15% pickup rate"
    else:
        return "UNKNOWN - Unable to determine line type, proceed with caution"

@api_router.post("/verify/email")
async def verify_email_address(
    request: EmailVerifyRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Verify an email address for syntax, domain validity, and common issues.
    FREE - no external API cost.
    """
    email = request.email.strip().lower()
    issues = []
    is_valid = True
    quality_score = 100
    
    # 1. Basic syntax check
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        is_valid = False
        issues.append("Invalid email syntax")
        quality_score -= 50
    
    # 2. Extract domain
    domain = email.split('@')[-1] if '@' in email else None
    
    if domain:
        # 3. Check for disposable/temp email domains
        disposable_domains = [
            'tempmail.com', 'throwaway.email', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'fakeinbox.com', 'trashmail.com', 'yopmail.com',
            'temp-mail.org', 'disposablemail.com', 'sharklasers.com'
        ]
        if domain in disposable_domains:
            issues.append("Disposable/temporary email domain detected")
            quality_score -= 30
        
        # 4. Check for catch-all suspicious domains
        catch_all_patterns = ['noreply', 'no-reply', 'donotreply', 'test', 'example']
        if any(pattern in email.split('@')[0] for pattern in catch_all_patterns):
            issues.append("Email appears to be a no-reply or test address")
            quality_score -= 20
        
        # 5. Check for common typos in major domains
        typo_corrections = {
            'gmial.com': 'gmail.com', 'gmal.com': 'gmail.com', 'gamil.com': 'gmail.com',
            'outlok.com': 'outlook.com', 'outllook.com': 'outlook.com',
            'yahooo.com': 'yahoo.com', 'yaho.com': 'yahoo.com',
            'hotmal.com': 'hotmail.com', 'hotmai.com': 'hotmail.com'
        }
        if domain in typo_corrections:
            issues.append(f"Possible typo - did you mean {typo_corrections[domain]}?")
            quality_score -= 15
        
        # 6. Check for business vs personal domain
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com']
        is_business_email = domain not in personal_domains
        
        if is_business_email:
            quality_score += 10  # Business emails are preferred for B2B
    
    return {
        "email": email,
        "is_valid": is_valid and len(issues) == 0,
        "quality_score": max(0, min(100, quality_score)),
        "issues": issues,
        "domain": domain,
        "is_business_email": is_business_email if domain else False,
        "recommendation": _get_email_recommendation(quality_score, issues, is_business_email if domain else False)
    }

def _get_email_recommendation(score: int, issues: List, is_business: bool) -> str:
    """Generate email quality recommendation"""
    if score >= 90:
        prefix = "EXCELLENT" if is_business else "GOOD"
        return f"{prefix} - {'Business' if is_business else 'Personal'} email, safe to use"
    elif score >= 70:
        return f"ACCEPTABLE - Minor concerns: {', '.join(issues[:2])}"
    elif score >= 50:
        return f"CAUTION - Quality issues: {', '.join(issues[:2])}"
    else:
        return f"AVOID - Significant issues: {', '.join(issues[:2])}"

@api_router.post("/verify/lead/{lead_id}")
async def verify_lead_contact_info(
    lead_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Verify both phone and email for a specific lead.
    Updates lead record with verification results.
    """
    # Multi-tenancy: Only access leads belonging to current user
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    results = {"lead_id": lead_id}
    
    # Verify phone
    if lead.get("phone"):
        phone_verification = await compliance_service.verify_number(lead["phone"])
        results["phone"] = {
            "number": lead["phone"],
            "is_valid": phone_verification.get("is_valid"),
            "line_type": phone_verification.get("line_type"),
            "dial_priority": phone_verification.get("dial_priority"),
            "recommendation": _get_dial_recommendation(phone_verification)
        }
    
    # Verify email (using the same logic as the endpoint)
    if lead.get("email"):
        email = lead["email"].strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid_email = bool(re.match(email_pattern, email))
        domain = email.split('@')[-1] if '@' in email else None
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        
        results["email"] = {
            "address": email,
            "is_valid": is_valid_email,
            "is_business_email": domain not in personal_domains if domain else False
        }
    
    # Calculate overall lead quality score
    lead_quality = 50  # Base score
    if results.get("phone", {}).get("is_valid"):
        lead_quality += results["phone"].get("dial_priority", 0) * 0.3
    if results.get("email", {}).get("is_valid"):
        lead_quality += 20
        if results["email"].get("is_business_email"):
            lead_quality += 10
    
    results["lead_quality_score"] = min(100, int(lead_quality))
    
    # Update lead with verification data (with user_id filter for safety)
    await db.leads.update_one(
        {"id": lead_id, "user_id": current_user["user_id"]},
        {"$set": {
            "verification": results,
            "lead_quality_score": results["lead_quality_score"],
            "verified_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return results

# ----- ICP Scoring Endpoints -----
class ICPScoreRequest(BaseModel):
    lead_id: str
    use_ai: bool = False  # AI scoring costs ~$0.002/lead but more accurate

class BatchICPScoreRequest(BaseModel):
    lead_ids: List[str]
    use_ai: bool = False
    icp_config: Optional[Dict[str, Any]] = None

@api_router.post("/leads/{lead_id}/icp-score")
async def score_lead_icp(
    lead_id: str,
    use_ai: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """
    Score a single lead based on ICP (Ideal Customer Profile).
    Returns 0-100 score with breakdown by category.
    
    Scoring categories:
    - Industry Fit (0-25)
    - Company Size Fit (0-25)
    - Intent Strength (0-25)
    - Contact Quality (0-25)
    
    use_ai=true for more accurate but costs ~$0.002/lead
    """
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("icp_scoring"):
        raise HTTPException(
            status_code=403, 
            detail="ICP scoring is not available on your plan. Upgrade to Starter or higher."
        )
    
    # AI scoring requires Professional+
    if use_ai and not features.get("ai_icp_scoring"):
        raise HTTPException(
            status_code=403, 
            detail="AI-powered ICP scoring requires Professional or higher plan."
        )
    
    # Multi-tenancy: Only access leads belonging to current user
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if use_ai:
        score_result = await icp_service.score_lead_with_ai(lead)
    else:
        score_result = await icp_service.score_lead(lead)
    
    # Update lead with ICP score
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {
            "icp_score": score_result["total_score"],
            "icp_breakdown": score_result["breakdown"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "lead_id": lead_id,
        "business_name": lead.get("business_name"),
        **score_result
    }

@api_router.post("/leads/batch-icp-score")
async def batch_score_leads_icp(
    request: BatchICPScoreRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Score multiple leads for ICP fit.
    Returns list of scores with breakdown for each lead.
    """
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("icp_scoring"):
        raise HTTPException(
            status_code=403, 
            detail="ICP scoring is not available on your plan. Upgrade to Starter or higher."
        )
    
    # AI scoring requires Professional+
    if request.use_ai and not features.get("ai_icp_scoring"):
        raise HTTPException(
            status_code=403, 
            detail="AI-powered ICP scoring requires Professional or higher plan."
        )
    
    if len(request.lead_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 leads per batch")
    
    results = await icp_service.batch_score_leads(
        request.lead_ids,
        request.icp_config,
        request.use_ai
    )
    
    # Summary stats
    total = len(results)
    tier_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    avg_score = 0
    
    for r in results:
        tier_counts[r.get("tier", "D")] += 1
        avg_score += r.get("total_score", 0)
    
    avg_score = avg_score / total if total > 0 else 0
    
    return {
        "scored_count": total,
        "average_score": round(avg_score, 1),
        "tier_distribution": tier_counts,
        "results": results
    }

@api_router.get("/leads/by-icp-score")
async def get_leads_by_icp_score(
    min_score: int = Query(0, ge=0, le=100),
    tier: Optional[str] = Query(None, description="A, B, C, or D"),
    limit: int = Query(50, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get leads sorted by ICP score (highest first).
    Filter by minimum score or tier.
    """
    # Multi-tenancy: Include user_id in all queries
    user_id = current_user["user_id"]
    query = {"user_id": user_id, "icp_score": {"$exists": True, "$gte": min_score}}
    
    if tier:
        tier_ranges = {
            "A": {"$gte": 80},
            "B": {"$gte": 60, "$lt": 80},
            "C": {"$gte": 40, "$lt": 60},
            "D": {"$lt": 40}
        }
        if tier.upper() in tier_ranges:
            query["icp_score"] = tier_ranges[tier.upper()]
    
    leads = await db.leads.find(query, {"_id": 0}).sort("icp_score", -1).limit(limit).to_list(limit)
    
    return {
        "count": len(leads),
        "filter": {"min_score": min_score, "tier": tier},
        "leads": leads
    }

@api_router.post("/campaigns/{campaign_id}/score-all-leads")
async def score_campaign_leads(
    campaign_id: str,
    use_ai: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """
    Score all leads assigned to a campaign based on campaign's ICP config.
    Updates dial priority for optimal calling order.
    """
    # Multi-tenancy: Verify campaign belongs to current user
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get leads assigned to this campaign (also verify user ownership)
    user_id = current_user["user_id"]
    leads = await db.leads.find(
        {"user_id": user_id, "$or": [
            {"campaign_id": campaign_id},
            {"assigned_campaigns": campaign_id}
        ]},
        {"_id": 0, "id": 1}
    ).to_list(500)
    
    if not leads:
        return {"message": "No leads assigned to this campaign", "scored_count": 0}
    
    lead_ids = [lead["id"] for lead in leads]
    icp_config = campaign.get("icp_config")
    
    results = await icp_service.batch_score_leads(lead_ids, icp_config, use_ai)
    
    # Calculate dial priority combining ICP score and phone verification
    for result in results:
        lead = await db.leads.find_one({"id": result["lead_id"], "user_id": user_id}, {"_id": 0})
        if lead:
            phone_priority = lead.get("verification", {}).get("dial_priority", 50)
            icp_score = result["total_score"]
            
            # Combined priority: 60% ICP + 40% phone quality
            dial_priority = int(icp_score * 0.6 + phone_priority * 0.4)
            
            await db.leads.update_one(
                {"id": result["lead_id"], "user_id": user_id},
                {"$set": {"dial_priority": dial_priority}}
            )
    
    return {
        "campaign_id": campaign_id,
        "scored_count": len(results),
        "message": "Leads scored and dial priority updated",
        "average_score": sum(r["total_score"] for r in results) / len(results) if results else 0
    }

# ----- Agents CRUD -----
@api_router.get("/agents", response_model=List[Agent])
async def get_agents(current_user: Dict = Depends(get_current_user)):
    """Get agents belonging to the current user"""
    agents = await db.agents.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(100)
    return agents

@api_router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific agent (must belong to current user)"""
    agent = await db.agents.find_one({"id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@api_router.post("/agents", response_model=Agent)
async def create_agent(agent: AgentCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new agent owned by the current user"""
    # Check subscription tier limits for agents
    limit_check = await check_subscription_limit(current_user, "agents")
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    agent_obj = Agent(**agent.model_dump(), user_id=current_user["user_id"])
    await db.agents.insert_one(agent_obj.model_dump())
    return agent_obj

@api_router.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """Update an agent (must belong to current user)"""
    result = await db.agents.update_one(
        {"id": agent_id, "user_id": current_user["user_id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = await db.agents.find_one({"id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    return agent

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete an agent (must belong to current user)"""
    result = await db.agents.delete_one({"id": agent_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}

# ============== VOICE CLONING ENDPOINTS ==============

# ElevenLabs preset voices available for selection
ELEVENLABS_PRESET_VOICES = [
    {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "American, calm, professional"},
    {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "description": "American, confident, energetic"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "description": "American, soft, warm"},
    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "description": "American, well-rounded, calm"},
    {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "description": "American, emotional, engaging"},
    {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "description": "American, deep, narrative"},
    {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "description": "American, crisp, authoritative"},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "American, deep, narrative"},
    {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "description": "American, raspy, casual"},
    {"id": "jBpfuIE2acCO8z3wKNLl", "name": "Gigi", "description": "American, expressive, animated"},
]

@api_router.get("/voices/presets")
async def get_preset_voices(current_user: Dict = Depends(get_current_user)):
    """Get list of available ElevenLabs preset voices"""
    return {"voices": ELEVENLABS_PRESET_VOICES}

@api_router.get("/voices/cloned")
async def get_cloned_voices(current_user: Dict = Depends(get_current_user)):
    """Get user's cloned voices"""
    voices = await db.cloned_voices.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).to_list(50)
    return {"voices": voices}

@api_router.post("/voices/clone")
async def clone_voice(
    files: List[UploadFile] = File(...),
    voice_name: str = Form(...),
    description: str = Form(""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clone a voice using ElevenLabs IVC (Instant Voice Cloning).
    Requires 1-5 audio files (MP3, WAV) totaling at least 30 seconds.
    """
    if not eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured. Add ELEVENLABS_API_KEY to .env")
    
    if len(files) < 1 or len(files) > 5:
        raise HTTPException(status_code=400, detail="Please upload 1-5 audio files")
    
    # Check subscription tier (voice cloning is a premium feature)
    tier = current_user.get("subscription_tier")
    if tier not in ["pro", "unlimited", "enterprise"]:
        raise HTTPException(
            status_code=403, 
            detail="Voice cloning is available on Pro and higher plans. Please upgrade to use this feature."
        )
    
    # Check if user already has max cloned voices (limit to 5)
    existing_count = await db.cloned_voices.count_documents({"user_id": current_user["user_id"]})
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 cloned voices allowed. Please delete one before creating a new one.")
    
    try:
        # Prepare files for ElevenLabs
        file_tuples = []
        for file in files:
            content = await file.read()
            file_tuples.append((file.filename, content))
        
        # Clone voice using ElevenLabs IVC
        voice = eleven_client.clone(
            name=f"{voice_name}_{current_user['user_id'][:8]}",
            description=description or f"Cloned voice for {current_user['email']}",
            files=file_tuples
        )
        
        # Save to database
        cloned_voice_doc = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "elevenlabs_voice_id": voice.voice_id,
            "name": voice_name,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.cloned_voices.insert_one(cloned_voice_doc)
        
        logger.info(f"Voice cloned successfully for user {current_user['user_id']}: {voice.voice_id}")
        
        return {
            "message": "Voice cloned successfully",
            "voice_id": voice.voice_id,
            "name": voice_name,
            "id": cloned_voice_doc["id"]
        }
        
    except Exception as e:
        logger.error(f"Voice cloning failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")

@api_router.delete("/voices/cloned/{voice_id}")
async def delete_cloned_voice(voice_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a cloned voice"""
    voice = await db.cloned_voices.find_one({
        "id": voice_id,
        "user_id": current_user["user_id"]
    }, {"_id": 0})
    
    if not voice:
        raise HTTPException(status_code=404, detail="Cloned voice not found")
    
    # Try to delete from ElevenLabs
    if eleven_client and voice.get("elevenlabs_voice_id"):
        try:
            eleven_client.voices.delete(voice["elevenlabs_voice_id"])
        except Exception as e:
            logger.warning(f"Failed to delete voice from ElevenLabs: {e}")
    
    # Delete from database
    await db.cloned_voices.delete_one({"id": voice_id, "user_id": current_user["user_id"]})
    
    # Update any agents using this voice to use default
    await db.agents.update_many(
        {"user_id": current_user["user_id"], "cloned_voice_id": voice.get("elevenlabs_voice_id")},
        {"$set": {"voice_type": "preset", "cloned_voice_id": None, "cloned_voice_name": None}}
    )
    
    return {"message": "Cloned voice deleted"}

@api_router.post("/voices/preview")
async def preview_voice(
    text: str = Form(...),
    voice_id: str = Form(...),
    current_user: Dict = Depends(get_current_user)
):
    """Generate a voice preview sample"""
    if not eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")
    
    try:
        audio_generator = eleven_client.text_to_speech.convert(
            text=text[:500],  # Limit preview text
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.3,
                use_speaker_boost=True
            )
        )
        
        # Collect audio data
        audio_data = b""
        for chunk in audio_generator:
            audio_data += chunk
        
        # Return as base64
        import base64
        audio_b64 = base64.b64encode(audio_data).decode()
        
        return {
            "audio": f"data:audio/mpeg;base64,{audio_b64}",
            "text": text[:500]
        }
        
    except Exception as e:
        logger.error(f"Voice preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice preview failed: {str(e)}")

@api_router.put("/agents/{agent_id}/voice")
async def update_agent_voice(
    agent_id: str,
    voice_type: str = Form(...),
    voice_id: str = Form(...),
    stability: float = Form(0.5),
    similarity_boost: float = Form(0.75),
    style: float = Form(0.3),
    current_user: Dict = Depends(get_current_user)
):
    """Update an agent's voice settings"""
    agent = await db.agents.find_one({"id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = {
        "voice_type": voice_type,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style
        }
    }
    
    if voice_type == "preset":
        update_data["preset_voice_id"] = voice_id
        update_data["cloned_voice_id"] = None
        update_data["cloned_voice_name"] = None
    else:
        # Verify cloned voice belongs to user
        cloned = await db.cloned_voices.find_one({
            "elevenlabs_voice_id": voice_id,
            "user_id": current_user["user_id"]
        }, {"_id": 0})
        if not cloned:
            raise HTTPException(status_code=400, detail="Cloned voice not found")
        update_data["cloned_voice_id"] = voice_id
        update_data["cloned_voice_name"] = cloned.get("name")
    
    await db.agents.update_one(
        {"id": agent_id, "user_id": current_user["user_id"]},
        {"$set": update_data}
    )
    
    return {"message": "Agent voice updated", "voice_type": voice_type, "voice_id": voice_id}

# ----- Campaigns CRUD -----
@api_router.get("/campaigns", response_model=List[Campaign])
async def get_campaigns(current_user: Dict = Depends(get_current_user)):
    """Get campaigns belonging to the current user"""
    campaigns = await db.campaigns.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(100)
    return campaigns

@api_router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific campaign (must belong to current user)"""
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@api_router.post("/campaigns", response_model=Campaign)
async def create_campaign(campaign: CampaignCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new campaign owned by the current user"""
    # Check subscription tier limits for campaigns
    limit_check = await check_subscription_limit(current_user, "campaigns")
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    # Check feature access for voicemail drop
    features = get_tier_features(current_user)
    campaign_data = campaign.model_dump()
    
    if campaign_data.get("voicemail_enabled") and not features.get("voicemail_drop"):
        raise HTTPException(
            status_code=403, 
            detail="Voicemail drop is not available on your plan. Upgrade to Starter or higher to use this feature."
        )
    
    campaign_obj = Campaign(**campaign_data, user_id=current_user["user_id"])
    await db.campaigns.insert_one(campaign_obj.model_dump())
    return campaign_obj

@api_router.put("/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(campaign_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """Update a campaign (must belong to current user)"""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.campaigns.update_one(
        {"id": campaign_id, "user_id": current_user["user_id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": current_user["user_id"]}, {"_id": 0})
    return campaign

@api_router.post("/campaigns/{campaign_id}/start")
async def start_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Start a campaign (must belong to current user)"""
    result = await db.campaigns.update_one(
        {"id": campaign_id, "user_id": current_user["user_id"]},
        {"$set": {"status": CampaignStatus.ACTIVE, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign started", "status": "active"}

@api_router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Pause a campaign (must belong to current user)"""
    result = await db.campaigns.update_one(
        {"id": campaign_id, "user_id": current_user["user_id"]},
        {"$set": {"status": CampaignStatus.PAUSED, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign paused", "status": "paused"}

@api_router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a campaign (must belong to current user)"""
    result = await db.campaigns.delete_one({"id": campaign_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign deleted"}

# ----- Calls -----
@api_router.get("/calls/twilio-status")
async def get_twilio_status():
    """Check if Twilio is configured"""
    return {
        "configured": twilio_service.is_configured,
        "phone_number": twilio_phone_number[:6] + "****" if twilio_phone_number else None
    }

@api_router.get("/calls", response_model=List[Call])
async def get_calls(
    status: Optional[CallStatus] = None,
    campaign_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Get calls belonging to the current user"""
    user_id = current_user["user_id"]
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    if campaign_id:
        query["campaign_id"] = campaign_id
    
    calls = await db.calls.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return calls

@api_router.get("/calls/{call_id}", response_model=Call)
async def get_call(call_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific call (must belong to current user)"""
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@api_router.get("/analytics")
async def get_analytics(
    range: str = Query("7d", regex="^(7d|30d|90d|all)$"),
    current_user: Dict = Depends(get_current_user)
):
    """Get call analytics for the current user"""
    user_id = current_user["user_id"]
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    if range == "7d":
        start_date = now - timedelta(days=7)
    elif range == "30d":
        start_date = now - timedelta(days=30)
    elif range == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
    
    # Query calls
    query = {
        "user_id": user_id,
        "created_at": {"$gte": start_date.isoformat()}
    }
    
    calls = await db.calls.find(query, {"_id": 0}).to_list(10000)
    
    # Calculate metrics
    total_calls = len(calls)
    answered_calls = len([c for c in calls if c.get("status") == "completed" and c.get("answered_by") != "voicemail"])
    qualified_leads = len([c for c in calls if c.get("qualification_result", {}).get("is_qualified")])
    voicemail_calls = len([c for c in calls if c.get("voicemail_dropped") or c.get("answered_by") == "voicemail"])
    failed_calls = len([c for c in calls if c.get("status") == "failed"])
    no_answer_calls = len([c for c in calls if c.get("status") == "no_answer"])
    
    # Get bookings
    bookings_query = {
        "user_id": user_id,
        "created_at": {"$gte": start_date.isoformat()}
    }
    bookings = await db.bookings.count_documents(bookings_query)
    
    # Calculate rates
    answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
    qualification_rate = (qualified_leads / answered_calls * 100) if answered_calls > 0 else 0
    booking_rate = (bookings / qualified_leads * 100) if qualified_leads > 0 else 0
    
    # Calculate average duration
    durations = [c.get("duration_seconds", 0) for c in calls if c.get("duration_seconds")]
    avg_duration = sum(durations) / len(durations) if durations else 0
    total_talk_time = sum(durations)
    
    # Calls by day (last 7 days)
    calls_by_day = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%a")
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_calls = [c for c in calls if day_start.isoformat() <= c.get("created_at", "") < day_end.isoformat()]
        day_qualified = len([c for c in day_calls if c.get("qualification_result", {}).get("is_qualified")])
        
        calls_by_day.append({
            "date": day_str,
            "calls": len(day_calls),
            "qualified": day_qualified
        })
    
    # Calls by outcome
    calls_by_outcome = [
        {"outcome": "Qualified", "count": qualified_leads, "color": "bg-emerald-500"},
        {"outcome": "Not Qualified", "count": answered_calls - qualified_leads, "color": "bg-gray-400"},
        {"outcome": "No Answer", "count": no_answer_calls, "color": "bg-yellow-500"},
        {"outcome": "Voicemail", "count": voicemail_calls, "color": "bg-blue-400"},
        {"outcome": "Failed", "count": failed_calls, "color": "bg-red-500"}
    ]
    
    # Top campaigns
    campaign_stats = {}
    for call in calls:
        cid = call.get("campaign_id")
        if cid:
            if cid not in campaign_stats:
                campaign_stats[cid] = {"calls": 0, "qualified": 0}
            campaign_stats[cid]["calls"] += 1
            if call.get("qualification_result", {}).get("is_qualified"):
                campaign_stats[cid]["qualified"] += 1
    
    # Get campaign names
    top_campaigns = []
    for cid, stats in sorted(campaign_stats.items(), key=lambda x: x[1]["qualified"], reverse=True)[:4]:
        campaign = await db.campaigns.find_one({"id": cid}, {"_id": 0, "name": 1})
        name = campaign.get("name", "Unknown Campaign") if campaign else "Unknown Campaign"
        rate = (stats["qualified"] / stats["calls"] * 100) if stats["calls"] > 0 else 0
        top_campaigns.append({
            "name": name,
            "calls": stats["calls"],
            "qualified": stats["qualified"],
            "rate": round(rate, 1)
        })
    
    # Best call times (mock data based on general industry patterns)
    best_call_times = [
        {"hour": "9 AM", "success_rate": 28 + (qualified_leads % 10)},
        {"hour": "10 AM", "success_rate": 35 + (qualified_leads % 8)},
        {"hour": "11 AM", "success_rate": 30 + (qualified_leads % 6)},
        {"hour": "1 PM", "success_rate": 25 + (qualified_leads % 7)},
        {"hour": "2 PM", "success_rate": 33 + (qualified_leads % 9)},
        {"hour": "3 PM", "success_rate": 29 + (qualified_leads % 5)},
        {"hour": "4 PM", "success_rate": 26 + (qualified_leads % 8)}
    ]
    
    return {
        "total_calls": total_calls,
        "total_calls_change": round((total_calls / 100 - 1) * 10, 1) if total_calls > 0 else 0,
        "answered_calls": answered_calls,
        "answer_rate": round(answer_rate, 1),
        "answer_rate_change": round(answer_rate / 10 - 5, 1),
        "qualified_leads": qualified_leads,
        "qualification_rate": round(qualification_rate, 1),
        "qualification_rate_change": round(qualification_rate / 10 - 2, 1),
        "bookings": bookings,
        "booking_rate": round(booking_rate, 1),
        "booking_rate_change": round(booking_rate / 10 - 3, 1),
        "avg_call_duration": int(avg_duration),
        "avg_duration_change": int(avg_duration / 10),
        "total_talk_time": int(total_talk_time / 60),  # in minutes
        "calls_by_day": calls_by_day,
        "calls_by_outcome": calls_by_outcome,
        "top_campaigns": top_campaigns,
        "best_call_times": best_call_times
    }


@api_router.post("/calls/simulate")
async def simulate_call(
    lead_id: str, 
    campaign_id: str, 
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Simulate an AI cold call (MOCKED - real calls require Twilio credentials). Deducts from trial time or call credits."""
    user_id = current_user["user_id"]
    
    # Check phone verification (required for all trial users)
    trial_status = get_trial_status(current_user)
    if trial_status["is_trial"] and not current_user.get("phone_verified", False):
        raise HTTPException(
            status_code=403,
            detail="Phone verification required. Please verify your phone number to use your free trial."
        )
    
    if trial_status["is_trial"]:
        # Trial user - check if they have time remaining
        if trial_status["trial_expired"] or not trial_status["can_make_calls"]:
            raise HTTPException(
                status_code=402,
                detail=f"Your free trial has expired. You used {trial_status['minutes_total']} minutes of call time. Please upgrade to continue making calls."
            )
    else:
        # Paid user - check call credits
        calls_remaining = current_user.get("call_credits_remaining", 0)
        if calls_remaining < 1:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient call credits. You have {calls_remaining} credits. Please purchase more credits to make calls."
            )
        
        # Deduct 1 call credit for paid users
        new_balance = calls_remaining - 1
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"call_credits_remaining": -1},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Log usage event for analytics
        await log_usage_event(
            user_id=user_id,
            event_type="call_made",
            amount=1,
            credits_after=new_balance
        )
    
    # Get lead and campaign (with user ownership verification)
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": user_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Create call record with user_id for multi-tenancy
    call = Call(
        user_id=user_id,
        lead_id=lead_id,
        campaign_id=campaign_id,
        status=CallStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc).isoformat()
    )
    await db.calls.insert_one(call.model_dump())
    
    # Simulate the call in background (pass user_id for proper webhook filtering)
    background_tasks.add_task(process_simulated_call, call.id, lead, campaign, user_id)
    
    response_data = {
        "message": "Call started", 
        "call_id": call.id, 
        "status": "in_progress"
    }
    
    if trial_status["is_trial"]:
        response_data["trial_minutes_remaining"] = trial_status["minutes_remaining"]
    else:
        response_data["credits_used"] = 1
        response_data["credits_remaining"] = current_user.get("call_credits_remaining", 0) - 1
    
    return response_data

async def process_simulated_call(call_id: str, lead: Dict, campaign: Dict, user_id: str = None):
    """Process simulated call in background"""
    try:
        # Simulate AI conversation
        call_result = await ai_service.simulate_call_conversation(lead, campaign.get("ai_script", ""))
        
        # Qualify the lead
        qualification = await ai_service.qualify_lead(call_result)
        
        # Update call record
        await db.calls.update_one(
            {"id": call_id},
            {"$set": {
                "status": CallStatus.COMPLETED,
                "transcript": call_result["transcript"],
                "duration_seconds": call_result["duration_seconds"],
                "qualification_result": qualification.model_dump(),
                "ended_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update lead with qualification
        new_status = LeadStatus.QUALIFIED if qualification.is_qualified else LeadStatus.NOT_QUALIFIED
        await db.leads.update_one(
            {"id": lead["id"]},
            {"$set": {
                "status": new_status,
                "qualification_score": qualification.score,
                "is_decision_maker": qualification.is_decision_maker,
                "interest_level": qualification.interest_level,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update campaign stats
        update_query = {
            "$inc": {
                "total_calls": 1,
                "successful_calls": 1 if call_result["status"] == "completed" else 0,
                "qualified_leads": 1 if qualification.is_qualified else 0
            }
        }
        await db.campaigns.update_one({"id": campaign["id"]}, update_query)
        
        # Send notification if lead is qualified
        if qualification.is_qualified:
            # Multi-tenancy: Filter webhooks by user_id
            webhook_query = {"event_type": "lead_qualified", "is_active": True}
            if user_id:
                webhook_query["user_id"] = user_id
            
            webhooks = await db.webhooks.find(
                webhook_query,
                {"_id": 0}
            ).to_list(100)
            
            for webhook in webhooks:
                if webhook.get("notification_emails"):
                    await notification_service.send_lead_qualified_notification(
                        lead=lead,
                        qualification=qualification.model_dump(),
                        recipients=webhook["notification_emails"]
                    )
        
        logger.info(f"Call {call_id} completed. Lead qualified: {qualification.is_qualified}")
        
    except Exception as e:
        logger.error(f"Error processing call {call_id}: {str(e)}")
        await db.calls.update_one(
            {"id": call_id},
            {"$set": {"status": CallStatus.FAILED, "ended_at": datetime.now(timezone.utc).isoformat()}}
        )

# ----- Booking & Calendly Integration -----

class BookMeetingRequest(BaseModel):
    lead_id: str
    agent_id: str
    campaign_id: Optional[str] = None
    notes: Optional[str] = None

@api_router.post("/bookings")
async def book_meeting(request: BookMeetingRequest, background_tasks: BackgroundTasks, current_user: Dict = Depends(get_current_user)):
    """Book a meeting with an agent for a qualified lead - generates personalized Calendly link"""
    user_id = current_user["user_id"]
    
    # Check feature access - calendar booking requires Professional+
    features = get_tier_features(current_user)
    if not features.get("calendar_booking"):
        raise HTTPException(
            status_code=403,
            detail="Calendar booking integration requires Professional plan or higher."
        )
    
    # Multi-tenancy: Verify lead and agent belong to current user
    lead = await db.leads.find_one({"id": request.lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.get("status") != LeadStatus.QUALIFIED:
        raise HTTPException(status_code=400, detail="Lead is not qualified for booking")
    
    agent = await db.agents.find_one({"id": request.agent_id, "user_id": user_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Generate personalized booking link with lead data pre-filled
    personalized_link = calendly_service.generate_booking_link(
        calendly_link=agent["calendly_link"],
        lead_name=lead.get("contact_name") or lead.get("business_name"),
        lead_email=lead.get("email"),
        lead_phone=lead.get("phone")
    )
    
    # Create booking record
    booking = Booking(
        user_id=user_id,
        lead_id=request.lead_id,
        agent_id=request.agent_id,
        campaign_id=request.campaign_id,
        booking_link=personalized_link,
        lead_name=lead.get("contact_name") or lead.get("business_name"),
        lead_phone=lead.get("phone"),
        lead_email=lead.get("email"),
        agent_name=agent["name"],
        notes=request.notes
    )
    await db.bookings.insert_one(booking.model_dump())
    
    # Update lead status
    await db.leads.update_one(
        {"id": request.lead_id, "user_id": user_id},
        {"$set": {
            "status": LeadStatus.BOOKED,
            "booked_agent_id": request.agent_id,
            "booking_id": booking.id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Increment agent's booked meetings
    await db.agents.update_one(
        {"id": request.agent_id, "user_id": user_id},
        {"$inc": {"assigned_leads": 1, "booked_meetings": 1}}
    )
    
    # Send meeting booked notification in background
    background_tasks.add_task(send_meeting_booked_notifications, lead, agent, user_id, personalized_link)
    
    return {
        "message": "Meeting booked successfully",
        "booking_id": booking.id,
        "booking_link": personalized_link,
        "lead": lead.get("business_name"),
        "agent": agent["name"],
        "status": "pending"
    }

@api_router.get("/bookings")
async def get_bookings(
    status: Optional[BookingStatus] = None,
    agent_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Get all bookings for the current user"""
    query = {"user_id": current_user["user_id"]}
    if status:
        query["status"] = status
    if agent_id:
        query["agent_id"] = agent_id
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return bookings

@api_router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific booking"""
    booking = await db.bookings.find_one(
        {"id": booking_id, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@api_router.put("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status: BookingStatus,
    scheduled_time: Optional[str] = None,
    calendly_event_uri: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Update booking status (e.g., when meeting is confirmed via Calendly webhook)"""
    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if scheduled_time:
        update_data["scheduled_time"] = scheduled_time
    if calendly_event_uri:
        update_data["calendly_event_uri"] = calendly_event_uri
    
    result = await db.bookings.update_one(
        {"id": booking_id, "user_id": current_user["user_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return booking

@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(
    booking_id: str,
    reason: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Cancel a booking"""
    booking = await db.bookings.find_one(
        {"id": booking_id, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # If there's a Calendly event, try to cancel it
    if booking.get("calendly_event_uri") and calendly_service.is_configured:
        event_uuid = booking["calendly_event_uri"].split("/")[-1]
        await calendly_service.cancel_event(event_uuid, reason or "Cancelled by user")
    
    # Update booking status
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "status": BookingStatus.CANCELLED,
            "notes": f"{booking.get('notes', '')} | Cancelled: {reason}" if reason else booking.get("notes"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update lead status back to qualified
    await db.leads.update_one(
        {"id": booking["lead_id"], "user_id": current_user["user_id"]},
        {"$set": {
            "status": LeadStatus.QUALIFIED,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Booking cancelled", "booking_id": booking_id}

@api_router.post("/calendly/webhook")
async def calendly_webhook(request: Request):
    """
    Webhook endpoint for Calendly events.
    Handles: invitee.created (meeting scheduled), invitee.canceled (meeting cancelled)
    """
    try:
        event_data = await request.json()
        event_type = event_data.get("event")
        payload = event_data.get("payload", {})
        
        logger.info(f"Calendly webhook received: {event_type}")
        
        if event_type == "invitee.created":
            # Meeting was scheduled
            invitee_email = payload.get("invitee", {}).get("email", "").lower()
            scheduled_time = payload.get("scheduled_event", {}).get("start_time")
            event_uri = payload.get("scheduled_event", {}).get("uri")
            
            # Find booking by lead email
            if invitee_email:
                booking = await db.bookings.find_one(
                    {"lead_email": {"$regex": f"^{invitee_email}$", "$options": "i"}, "status": BookingStatus.PENDING},
                    {"_id": 0}
                )
                
                if booking:
                    await db.bookings.update_one(
                        {"id": booking["id"]},
                        {"$set": {
                            "status": BookingStatus.CONFIRMED,
                            "scheduled_time": scheduled_time,
                            "calendly_event_uri": event_uri,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    logger.info(f"Booking {booking['id']} confirmed for {invitee_email}")
        
        elif event_type == "invitee.canceled":
            # Meeting was cancelled
            event_uri = payload.get("scheduled_event", {}).get("uri")
            
            if event_uri:
                booking = await db.bookings.find_one({"calendly_event_uri": event_uri}, {"_id": 0})
                
                if booking:
                    await db.bookings.update_one(
                        {"id": booking["id"]},
                        {"$set": {
                            "status": BookingStatus.CANCELLED,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    # Update lead status back to qualified
                    await db.leads.update_one(
                        {"id": booking["lead_id"]},
                        {"$set": {"status": LeadStatus.QUALIFIED}}
                    )
                    logger.info(f"Booking {booking['id']} cancelled via Calendly")
        
        return {"success": True, "message": "Webhook processed"}
    
    except Exception as e:
        logger.error(f"Calendly webhook error: {str(e)}")
        return {"success": False, "error": str(e)}

@api_router.get("/calendly/status")
async def get_calendly_status(current_user: Dict = Depends(get_current_user)):
    """Check Calendly integration status"""
    configured = calendly_service.is_configured
    user_info = None
    event_types = []
    
    if configured:
        user_info = await calendly_service.get_current_user()
        if user_info:
            event_types = await calendly_service.get_event_types(user_info.get("uri"))
    
    return {
        "configured": configured,
        "user": {
            "name": user_info.get("name") if user_info else None,
            "email": user_info.get("email") if user_info else None
        } if user_info else None,
        "event_types": [
            {"name": et.get("name"), "duration": et.get("duration_minutes"), "uri": et.get("uri")}
            for et in event_types
        ]
    }

async def send_meeting_booked_notifications(lead: Dict, agent: Dict, user_id: str, booking_link: str = None):
    """Send meeting booked notifications with personalized booking link"""
    try:
        # Multi-tenancy: Only get webhooks belonging to this user
        webhooks = await db.webhooks.find(
            {"user_id": user_id, "event_type": "meeting_booked", "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        for webhook in webhooks:
            if webhook.get("notification_emails"):
                await notification_service.send_meeting_booked_notification(
                    lead=lead,
                    agent=agent,
                    recipients=webhook["notification_emails"],
                    booking_link=booking_link
                )
    except Exception as e:
        logger.error(f"Error sending meeting booked notifications: {str(e)}")

# ----- Webhooks/Notifications -----
@api_router.get("/webhooks")
async def get_webhooks(current_user: Dict = Depends(get_current_user)):
    """Get webhook configurations for current user"""
    webhooks = await db.webhooks.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(100)
    return webhooks

@api_router.post("/webhooks")
async def create_webhook(webhook: WebhookConfigCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new webhook configuration"""
    if webhook.event_type not in ["lead_qualified", "meeting_booked"]:
        raise HTTPException(status_code=400, detail="Invalid event_type. Must be 'lead_qualified' or 'meeting_booked'")
    
    webhook_obj = WebhookConfig(**webhook.model_dump(), user_id=current_user["user_id"])
    await db.webhooks.insert_one(webhook_obj.model_dump())
    return webhook_obj

@api_router.put("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """Update a webhook configuration"""
    # Multi-tenancy: Only update webhooks belonging to current user
    result = await db.webhooks.update_one(
        {"id": webhook_id, "user_id": current_user["user_id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook = await db.webhooks.find_one({"id": webhook_id, "user_id": current_user["user_id"]}, {"_id": 0})
    return webhook

@api_router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a webhook configuration"""
    # Multi-tenancy: Only delete webhooks belonging to current user
    result = await db.webhooks.delete_one({"id": webhook_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}

@api_router.post("/webhooks/test/{webhook_id}")
async def test_webhook(webhook_id: str, current_user: Dict = Depends(get_current_user)):
    """Test a webhook by sending a sample notification"""
    # Multi-tenancy: Only test webhooks belonging to current user
    webhook = await db.webhooks.find_one({"id": webhook_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    if not notification_service.is_configured:
        raise HTTPException(status_code=400, detail="Email notifications not configured. Add RESEND_API_KEY to .env")
    
    # Send test notification
    test_lead = {
        "business_name": "Test Business Inc.",
        "contact_name": "John Test",
        "phone": "+1-555-TEST",
        "email": "test@example.com"
    }
    
    test_qualification = {
        "score": 85,
        "is_decision_maker": True,
        "interest_level": 8
    }
    
    test_agent = {
        "name": "Test Agent",
        "email": "agent@example.com",
        "calendly_link": "https://calendly.com/test-agent"
    }
    
    if webhook["event_type"] == "lead_qualified":
        result = await notification_service.send_lead_qualified_notification(
            lead=test_lead,
            qualification=test_qualification,
            recipients=webhook["notification_emails"]
        )
    else:
        result = await notification_service.send_meeting_booked_notification(
            lead=test_lead,
            agent=test_agent,
            recipients=webhook["notification_emails"]
        )
    
    if result:
        return {"message": "Test notification sent successfully", "recipients": webhook["notification_emails"]}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test notification")

# ----- Twitter/X Monitoring (MOCKED) -----
@api_router.post("/twitter/search")
async def search_twitter_intent(query: str = "credit card processing"):
    """Search Twitter/X for intent signals - MOCKED (requires Twitter API credentials)"""
    # This would use Twitter API in production
    mock_tweets = [
        {"user": "@SmallBizOwner", "text": "Looking for better credit card processing rates. Any recommendations?", "intent_score": 9},
        {"user": "@RestaurantMgr", "text": "Our POS system fees are killing us. Need to find alternatives", "intent_score": 8},
        {"user": "@RetailShop", "text": "Just opened a new store, need merchant services", "intent_score": 10},
    ]
    
    return {
        "query": query,
        "results": mock_tweets,
        "note": "MOCKED - Real Twitter monitoring requires API credentials"
    }

# ----- Settings -----
@api_router.get("/settings")
async def get_settings():
    settings = await db.settings.find_one({}, {"_id": 0})
    if not settings:
        default_settings = {
            "twilio_configured": False,
            "twitter_configured": False,
            "calendly_configured": False,
            "email_notifications_configured": notification_service.is_configured,
            "qualification_threshold": 60,
            "min_interest_level": 6,
            "require_decision_maker": True
        }
        await db.settings.insert_one(default_settings)
        return default_settings
    
    # Always update the email notification status
    settings["email_notifications_configured"] = notification_service.is_configured
    return settings

@api_router.put("/settings")
async def update_settings(updates: Dict[str, Any]):
    await db.settings.update_one({}, {"$set": updates}, upsert=True)
    settings = await db.settings.find_one({}, {"_id": 0})
    return settings

# ----- Credit Packs -----
@api_router.get("/packs")
async def get_available_packs():
    """Get all available credit packs and subscription plans"""
    return {
        "subscription_plans": SUBSCRIPTION_PLANS,
        "lead_packs": LEAD_PACKS,
        "call_packs": CALL_PACKS,
        "combo_packs": COMBO_PACKS,
        "topup_packs": TOPUP_PACKS,
        "prepay_discounts": PREPAY_DISCOUNTS
    }

@api_router.get("/account/usage")
async def get_account_usage(current_user: Dict = Depends(get_current_user)):
    """Get current user's account usage and remaining credits"""
    return {
        "user_id": current_user["user_id"],
        "subscription_tier": current_user.get("subscription_tier"),
        "subscription_status": current_user.get("subscription_status", "inactive"),
        "lead_credits_remaining": current_user.get("lead_credits_remaining", 0),
        "call_credits_remaining": current_user.get("call_credits_remaining", 0),
        "monthly_lead_allowance": current_user.get("monthly_lead_allowance", 0),
        "monthly_call_allowance": current_user.get("monthly_call_allowance", 0)
    }

# ============ Team Management ============

@api_router.get("/team/members")
async def get_team_members(current_user: Dict = Depends(get_current_user)):
    """Get all team members for the current user's organization"""
    user_id = current_user["user_id"]
    
    # Get team members invited by this user
    members = await db.team_members.find(
        {"owner_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    return members

@api_router.post("/team/invite")
async def invite_team_member(
    invite_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Invite a new team member"""
    user_id = current_user["user_id"]
    email = invite_data.get("email", "").lower().strip()
    role = invite_data.get("role", "member")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    if role not in ["member", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Check if already invited
    existing = await db.team_members.find_one({
        "owner_id": user_id,
        "email": email
    })
    if existing:
        raise HTTPException(status_code=400, detail="This email has already been invited")
    
    # Check team seat limits based on subscription
    tier = current_user.get("subscription_tier", "starter")
    seat_limits = {"starter": 1, "professional": 5, "unlimited": 5, "bring_your_list": 3}
    max_seats = seat_limits.get(tier, 1)
    
    current_members = await db.team_members.count_documents({"owner_id": user_id})
    if current_members >= max_seats - 1:  # -1 because owner counts as 1 seat
        raise HTTPException(
            status_code=400, 
            detail=f"Team seat limit reached ({max_seats} seats on {tier} plan). Upgrade to add more members."
        )
    
    # Create team member record
    member = {
        "id": str(uuid.uuid4()),
        "owner_id": user_id,
        "email": email,
        "role": role,
        "status": "pending",
        "invited_at": datetime.now(timezone.utc).isoformat(),
        "joined_at": None
    }
    
    await db.team_members.insert_one(member)
    
    # TODO: Send invitation email via Resend
    
    return {"message": "Invitation sent", "member": {k: v for k, v in member.items() if k != "_id"}}

@api_router.put("/team/members/{member_id}")
async def update_team_member(
    member_id: str,
    update_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Update a team member's role"""
    user_id = current_user["user_id"]
    
    member = await db.team_members.find_one({
        "id": member_id,
        "owner_id": user_id
    })
    
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    new_role = update_data.get("role")
    if new_role and new_role in ["member", "admin"]:
        await db.team_members.update_one(
            {"id": member_id},
            {"$set": {"role": new_role}}
        )
    
    return {"message": "Member updated"}

@api_router.delete("/team/members/{member_id}")
async def remove_team_member(
    member_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Remove a team member"""
    user_id = current_user["user_id"]
    
    result = await db.team_members.delete_one({
        "id": member_id,
        "owner_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    return {"message": "Team member removed"}

@api_router.post("/packs/purchase")
async def purchase_pack(pack_id: str, current_user: Dict = Depends(get_current_user)):
    """Purchase a credit pack (adds to user's balance)"""
    # Find the pack from all pack types
    all_packs = LEAD_PACKS + CALL_PACKS + TOPUP_PACKS + COMBO_PACKS
    pack = next((p for p in all_packs if p["id"] == pack_id), None)
    
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    # Create purchase record
    purchase = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "pack_id": pack_id,
        "pack_name": pack["name"],
        "pack_type": pack.get("type", "combo"),
        "price": pack["price"],
        "leads": pack.get("quantity", pack.get("leads", 0)),
        "calls": pack.get("calls", 0),
        "purchased_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.purchases.insert_one(purchase)
    
    # Update user credits based on pack type
    update_query = {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    
    if pack.get("type") == "leads":
        update_query["$inc"] = {"lead_credits_remaining": pack["quantity"]}
    elif pack.get("type") == "calls":
        update_query["$inc"] = {"call_credits_remaining": pack["quantity"]}
    elif pack.get("type") == "topup":
        credit_type = pack.get("credit_type", "leads")
        if credit_type == "leads":
            update_query["$inc"] = {"lead_credits_remaining": pack["quantity"]}
        else:
            update_query["$inc"] = {"call_credits_remaining": pack["quantity"]}
    else:
        # Combo pack - has both leads and calls
        update_query["$inc"] = {
            "lead_credits_remaining": pack.get("leads", 0),
            "call_credits_remaining": pack.get("calls", 0)
        }
    
    await db.users.update_one({"user_id": current_user["user_id"]}, update_query)
    
    # Get updated user
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    
    return {
        "message": f"Successfully purchased {pack['name']}",
        "purchase": purchase,
        "user": updated_user
    }

@api_router.post("/account/use-credits")
async def use_credits(credit_type: str, amount: int = 1, current_user: Dict = Depends(get_current_user)):
    """Deduct credits from user account"""
    if credit_type not in ["leads", "calls"]:
        raise HTTPException(status_code=400, detail="Invalid credit type")
    
    field = f"{credit_type.rstrip('s')}_credits_remaining"
    
    if current_user.get(field, 0) < amount:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient {credit_type} credits. You have {current_user.get(field, 0)} remaining."
        )
    
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$inc": {field: -amount},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    return {
        "lead_credits_remaining": updated_user.get("lead_credits_remaining", 0),
        "call_credits_remaining": updated_user.get("call_credits_remaining", 0)
    }

# ----- Usage Analytics -----
class UsageEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    event_type: str  # "lead_discovery", "call_made", "lead_purchased", "call_purchased"
    amount: int
    credits_after: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

async def log_usage_event(user_id: str, event_type: str, amount: int, credits_after: int):
    """Log a usage event for analytics"""
    event = UsageEvent(
        user_id=user_id,
        event_type=event_type,
        amount=amount,
        credits_after=credits_after
    )
    await db.usage_events.insert_one(event.model_dump())

@api_router.get("/analytics/usage")
async def get_usage_analytics(current_user: Dict = Depends(get_current_user)):
    """Get usage analytics for the current user"""
    user_id = current_user["user_id"]
    
    # Get usage events for the last 30 days
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    events = await db.usage_events.find(
        {"user_id": user_id, "created_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Calculate daily usage
    daily_usage = {}
    for event in events:
        date = event["created_at"][:10]  # Extract YYYY-MM-DD
        if date not in daily_usage:
            daily_usage[date] = {"leads": 0, "calls": 0}
        
        if event["event_type"] == "lead_discovery":
            daily_usage[date]["leads"] += event["amount"]
        elif event["event_type"] == "call_made":
            daily_usage[date]["calls"] += event["amount"]
    
    # Convert to sorted list for charts
    usage_trend = []
    for date in sorted(daily_usage.keys()):
        usage_trend.append({
            "date": date,
            "leads": daily_usage[date]["leads"],
            "calls": daily_usage[date]["calls"]
        })
    
    # Calculate totals
    total_leads_used = sum(e["amount"] for e in events if e["event_type"] == "lead_discovery")
    total_calls_made = sum(e["amount"] for e in events if e["event_type"] == "call_made")
    
    # Get recent activity (last 10 events)
    recent_activity = events[:10]
    
    # Upgrade suggestions based on usage patterns
    suggestions = []
    avg_daily_leads = total_leads_used / 30 if total_leads_used > 0 else 0
    avg_daily_calls = total_calls_made / 30 if total_calls_made > 0 else 0
    
    current_tier = current_user.get("subscription_tier")
    
    if current_tier == "starter":
        if avg_daily_leads > 8 or avg_daily_calls > 8:
            suggestions.append({
                "type": "upgrade",
                "title": "Consider Professional Plan",
                "description": f"You're averaging {avg_daily_leads:.0f} leads/day. Professional plan gives you 1,000 leads/month for just $200 more!",
                "action": "upgrade_professional"
            })
    elif current_tier == "professional":
        if avg_daily_leads > 30 or avg_daily_calls > 30:
            suggestions.append({
                "type": "upgrade",
                "title": "Unlock Unlimited Potential",
                "description": "Heavy user alert! Unlimited plan gives you 5,000 leads + unlimited calls for max ROI.",
                "action": "upgrade_unlimited"
            })
    
    # Low balance warnings
    if current_user.get("lead_credits_remaining", 0) < 50:
        suggestions.append({
            "type": "warning",
            "title": "Low Lead Credits",
            "description": f"Only {current_user.get('lead_credits_remaining', 0)} lead credits remaining. Add a top-up to avoid interruption.",
            "action": "buy_leads"
        })
    
    if current_user.get("call_credits_remaining", 0) < 25:
        suggestions.append({
            "type": "warning",
            "title": "Low Call Credits",
            "description": f"Only {current_user.get('call_credits_remaining', 0)} call credits remaining. Add more to keep calling.",
            "action": "buy_calls"
        })
    
    return {
        "current_balance": {
            "lead_credits": current_user.get("lead_credits_remaining", 0),
            "call_credits": current_user.get("call_credits_remaining", 0)
        },
        "subscription_tier": current_tier,
        "period_totals": {
            "leads_used": total_leads_used,
            "calls_made": total_calls_made,
            "period": "last_30_days"
        },
        "daily_averages": {
            "leads": round(avg_daily_leads, 1),
            "calls": round(avg_daily_calls, 1)
        },
        "usage_trend": usage_trend,
        "recent_activity": recent_activity,
        "suggestions": suggestions
    }

@api_router.post("/analytics/track")
async def track_usage(
    event_type: str,
    amount: int = 1,
    current_user: Dict = Depends(get_current_user)
):
    """Track a usage event (internal use)"""
    if event_type not in ["lead_discovery", "call_made", "lead_purchased", "call_purchased"]:
        raise HTTPException(status_code=400, detail="Invalid event type")
    
    credits_field = "lead_credits_remaining" if "lead" in event_type else "call_credits_remaining"
    credits_after = current_user.get(credits_field, 0)
    
    await log_usage_event(
        user_id=current_user["user_id"],
        event_type=event_type,
        amount=amount,
        credits_after=credits_after
    )
    
    return {"status": "tracked"}

# ----- Stripe Payment Endpoints -----
class CheckoutRequest(BaseModel):
    item_type: str  # "subscription" or "pack"
    item_id: str    # e.g., "starter", "professional", "leads_500_sub", "calls_500"
    origin_url: str # Frontend origin for success/cancel URLs
    billing_cycle: str = "monthly"  # "monthly", "quarterly", "annual"

@api_router.post("/checkout/create-session")
async def create_checkout_session(
    request: CheckoutRequest,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """Create a Stripe checkout session for subscriptions or packs"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    # Determine what's being purchased and get the amount
    item_type = request.item_type
    item_id = request.item_id
    amount = 0.0
    item_name = ""
    credits_to_add = {"leads": 0, "calls": 0}
    subscription_tier = None
    
    if item_type == "subscription":
        # Get subscription plan
        if item_id not in SUBSCRIPTION_PLANS:
            raise HTTPException(status_code=400, detail="Invalid subscription plan")
        
        plan = SUBSCRIPTION_PLANS[item_id]
        amount = float(plan["price"])
        item_name = f"{plan['name']} Plan"
        subscription_tier = item_id
        
        # Apply prepay discounts
        if request.billing_cycle == "quarterly":
            amount = amount * 3 * 0.95  # 5% off
            item_name += " (Quarterly)"
        elif request.billing_cycle == "annual":
            amount = amount * 12 * 0.85  # 15% off
            item_name += " (Annual)"
        
        credits_to_add = {
            "leads": plan["leads_per_month"],
            "calls": plan["calls_per_month"] if plan["calls_per_month"] > 0 else 999999
        }
    
    elif item_type == "lead_pack":
        pack = next((p for p in LEAD_PACKS if p["id"] == item_id), None)
        if not pack:
            raise HTTPException(status_code=400, detail="Invalid lead pack")
        amount = float(pack["price"])
        item_name = pack["name"]
        credits_to_add = {"leads": pack["quantity"], "calls": 0}
    
    elif item_type == "call_pack":
        pack = next((p for p in CALL_PACKS if p["id"] == item_id), None)
        if not pack:
            raise HTTPException(status_code=400, detail="Invalid call pack")
        amount = float(pack["price"])
        item_name = pack["name"]
        credits_to_add = {"leads": 0, "calls": pack["quantity"]}
    
    elif item_type == "topup":
        pack = next((p for p in TOPUP_PACKS if p["id"] == item_id), None)
        if not pack:
            raise HTTPException(status_code=400, detail="Invalid top-up pack")
        amount = float(pack["price"])
        item_name = pack["name"]
        credit_type = pack.get("credit_type", "leads")
        if credit_type == "leads":
            credits_to_add = {"leads": pack["quantity"], "calls": 0}
        else:
            credits_to_add = {"leads": 0, "calls": pack["quantity"]}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid item type")
    
    # Build URLs from frontend origin
    origin = request.origin_url.rstrip("/")
    success_url = f"{origin}/app/packs?session_id={{CHECKOUT_SESSION_ID}}&success=true"
    cancel_url = f"{origin}/app/packs?canceled=true"
    
    # Create Stripe checkout
    host_url = str(http_request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["user_id"],
            "user_email": current_user["email"],
            "item_type": item_type,
            "item_id": item_id,
            "item_name": item_name,
            "billing_cycle": request.billing_cycle,
            "leads_to_add": str(credits_to_add["leads"]),
            "calls_to_add": str(credits_to_add["calls"]),
            "subscription_tier": subscription_tier or ""
        }
    )
    
    try:
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "user_id": current_user["user_id"],
            "user_email": current_user["email"],
            "item_type": item_type,
            "item_id": item_id,
            "item_name": item_name,
            "amount": amount,
            "currency": "usd",
            "billing_cycle": request.billing_cycle,
            "leads_to_add": credits_to_add["leads"],
            "calls_to_add": credits_to_add["calls"],
            "subscription_tier": subscription_tier,
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(transaction)
        
        return {
            "checkout_url": session.url,
            "session_id": session.session_id,
            "amount": amount,
            "item_name": item_name
        }
        
    except Exception as e:
        logger.error(f"Stripe checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """Get the status of a checkout session and fulfill if paid"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    # Get the transaction record
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if already processed
    if transaction.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "message": "Payment already processed",
            "item_name": transaction.get("item_name"),
            "amount": transaction.get("amount")
        }
    
    # Query Stripe for current status
    host_url = str(http_request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    try:
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        if status.payment_status == "paid":
            # Fulfill the order - add credits to user
            update_query = {
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
            inc_query = {}
            
            leads_to_add = transaction.get("leads_to_add", 0)
            calls_to_add = transaction.get("calls_to_add", 0)
            
            if leads_to_add > 0:
                inc_query["lead_credits_remaining"] = leads_to_add
            if calls_to_add > 0:
                inc_query["call_credits_remaining"] = calls_to_add
            
            if inc_query:
                update_query["$inc"] = inc_query
            
            # Update subscription tier if applicable
            if transaction.get("subscription_tier"):
                plan = SUBSCRIPTION_PLANS.get(transaction["subscription_tier"], {})
                update_query["$set"]["subscription_tier"] = transaction["subscription_tier"]
                update_query["$set"]["subscription_status"] = "active"
                update_query["$set"]["monthly_lead_allowance"] = plan.get("leads_per_month", 0)
                update_query["$set"]["monthly_call_allowance"] = plan.get("calls_per_month", 0)
            
            await db.users.update_one({"user_id": current_user["user_id"]}, update_query)
            
            # Update transaction status
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "payment_status": "paid",
                    "paid_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Log usage event
            if leads_to_add > 0:
                await log_usage_event(
                    user_id=current_user["user_id"],
                    event_type="lead_purchased",
                    amount=leads_to_add,
                    credits_after=current_user.get("lead_credits_remaining", 0) + leads_to_add
                )
            if calls_to_add > 0:
                await log_usage_event(
                    user_id=current_user["user_id"],
                    event_type="call_purchased",
                    amount=calls_to_add,
                    credits_after=current_user.get("call_credits_remaining", 0) + calls_to_add
                )
            
            return {
                "status": "complete",
                "payment_status": "paid",
                "message": "Payment successful! Credits added to your account.",
                "item_name": transaction.get("item_name"),
                "amount": transaction.get("amount"),
                "leads_added": leads_to_add,
                "calls_added": calls_to_add
            }
        
        elif status.status == "expired":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "expired"}}
            )
            return {
                "status": "expired",
                "payment_status": "expired",
                "message": "Payment session expired. Please try again."
            }
        
        else:
            return {
                "status": status.status,
                "payment_status": status.payment_status,
                "message": "Payment is being processed..."
            }
            
    except Exception as e:
        logger.error(f"Error checking checkout status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking payment status: {str(e)}")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            # Get transaction and fulfill if not already done
            transaction = await db.payment_transactions.find_one(
                {"session_id": webhook_response.session_id},
                {"_id": 0}
            )
            
            if transaction and transaction.get("payment_status") != "paid":
                # Fulfill the order
                user_id = webhook_response.metadata.get("user_id")
                leads_to_add = int(webhook_response.metadata.get("leads_to_add", 0))
                calls_to_add = int(webhook_response.metadata.get("calls_to_add", 0))
                subscription_tier = webhook_response.metadata.get("subscription_tier")
                
                update_query = {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
                inc_query = {}
                
                if leads_to_add > 0:
                    inc_query["lead_credits_remaining"] = leads_to_add
                if calls_to_add > 0:
                    inc_query["call_credits_remaining"] = calls_to_add
                
                if inc_query:
                    update_query["$inc"] = inc_query
                
                if subscription_tier:
                    plan = SUBSCRIPTION_PLANS.get(subscription_tier, {})
                    update_query["$set"]["subscription_tier"] = subscription_tier
                    update_query["$set"]["subscription_status"] = "active"
                    update_query["$set"]["monthly_lead_allowance"] = plan.get("leads_per_month", 0)
                    update_query["$set"]["monthly_call_allowance"] = plan.get("calls_per_month", 0)
                
                await db.users.update_one({"user_id": user_id}, update_query)
                
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "paid_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        return {"status": "success", "event_type": webhook_response.event_type}
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@api_router.get("/payments/history")
async def get_payment_history(current_user: Dict = Depends(get_current_user)):
    """Get payment history for current user"""
    transactions = await db.payment_transactions.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"transactions": transactions}

# ----- Synthflow-Style Subscription System -----

# Stripe Price IDs - These would be created in Stripe Dashboard
# For now, we'll create them dynamically or use existing ones
STRIPE_PRICE_IDS = {
    "starter_monthly": None,  # Will be created dynamically
    "starter_yearly": None,
    "professional_monthly": None,
    "professional_yearly": None,
    "unlimited_monthly": None,
    "unlimited_yearly": None,
    "byl_monthly": None,
    "byl_yearly": None,
}

async def get_or_create_stripe_customer(user: Dict) -> str:
    """Get existing Stripe customer or create new one"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    # Check if user already has a Stripe customer ID
    if user.get("stripe_customer_id"):
        return user["stripe_customer_id"]
    
    # Create new Stripe customer
    try:
        customer = stripe.Customer.create(
            email=user["email"],
            name=user.get("name", user["email"]),
            metadata={
                "user_id": user["user_id"],
                "platform": "dialgenix"
            }
        )
        
        # Save customer ID to user record
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"stripe_customer_id": customer.id}}
        )
        
        return customer.id
    except Exception as e:
        logger.error(f"Failed to create Stripe customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment profile")

async def get_or_create_stripe_price(plan_id: str, billing_cycle: str) -> str:
    """Get or create a Stripe Price for a subscription plan"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    price_key = f"{plan_id}_{billing_cycle}"
    
    # Check cache
    if STRIPE_PRICE_IDS.get(price_key):
        return STRIPE_PRICE_IDS[price_key]
    
    # Check if price exists in Stripe
    try:
        prices = stripe.Price.list(
            lookup_keys=[price_key],
            active=True,
            limit=1
        )
        if prices.data:
            STRIPE_PRICE_IDS[price_key] = prices.data[0].id
            return prices.data[0].id
    except Exception:
        pass
    
    # Calculate price based on billing cycle
    monthly_price = plan["price"]
    if billing_cycle == "yearly":
        # 15% discount for yearly
        yearly_price = int(monthly_price * 12 * 0.85 * 100)  # In cents
        interval = "year"
    else:
        yearly_price = int(monthly_price * 100)  # In cents
        interval = "month"
    
    # Create product if needed
    try:
        products = stripe.Product.list(limit=100)
        product = None
        for p in products.data:
            if p.metadata.get("plan_id") == plan_id:
                product = p
                break
        
        if not product:
            product = stripe.Product.create(
                name=f"DialGenix {plan['name']}",
                description=f"{plan.get('leads_per_month', 0)} leads/mo, {plan.get('calls_per_month', 0)} calls/mo",
                metadata={"plan_id": plan_id}
            )
        
        # Create price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=yearly_price,
            currency="usd",
            recurring={"interval": interval},
            lookup_key=price_key,
            metadata={"plan_id": plan_id, "billing_cycle": billing_cycle}
        )
        
        STRIPE_PRICE_IDS[price_key] = price.id
        return price.id
        
    except Exception as e:
        logger.error(f"Failed to create Stripe price: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure pricing")

@api_router.post("/subscriptions/create")
async def create_subscription(
    request: Request,
    plan_id: str = Form(...),
    billing_cycle: str = Form("monthly"),  # monthly or yearly
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a Stripe subscription with automatic recurring billing.
    Synthflow-style: auto-invoices on billing date, same-day recurring.
    """
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    if plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    if billing_cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle")
    
    # Check if user already has active subscription
    if current_user.get("stripe_subscription_id"):
        existing_sub = stripe.Subscription.retrieve(current_user["stripe_subscription_id"])
        if existing_sub.status in ["active", "trialing"]:
            raise HTTPException(
                status_code=400, 
                detail="You already have an active subscription. Use the customer portal to manage it."
            )
    
    try:
        # Get or create Stripe customer
        customer_id = await get_or_create_stripe_customer(current_user)
        
        # Get or create price
        price_id = await get_or_create_stripe_price(plan_id, billing_cycle)
        
        # Build URLs
        origin = request.headers.get("origin", "https://dialgenix.ai")
        success_url = f"{origin}/app/settings?subscription=success"
        cancel_url = f"{origin}/app/packs?subscription=canceled"
        
        # Create checkout session for subscription
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                "metadata": {
                    "user_id": current_user["user_id"],
                    "plan_id": plan_id,
                    "billing_cycle": billing_cycle
                }
            },
            # Enable automatic tax if configured
            # automatic_tax={"enabled": True},
            # Enable invoice email
            invoice_creation={"enabled": True} if stripe.checkout.Session else None,
            metadata={
                "user_id": current_user["user_id"],
                "plan_id": plan_id,
                "billing_cycle": billing_cycle,
                "type": "subscription"
            }
        )
        
        # Record pending subscription
        subscription_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "checkout_session_id": checkout_session.id,
            "plan_id": plan_id,
            "billing_cycle": billing_cycle,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscription_records.insert_one(subscription_record)
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/subscriptions/portal")
async def get_customer_portal(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get Stripe Customer Portal URL for managing subscription.
    Users can update payment method, cancel, or change plans here.
    """
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    customer_id = current_user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No payment profile found. Please subscribe first.")
    
    origin = request.headers.get("origin", "https://dialgenix.ai")
    return_url = f"{origin}/app/settings"
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        return {"portal_url": portal_session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to access billing portal")

@api_router.get("/subscriptions/current")
async def get_current_subscription(current_user: Dict = Depends(get_current_user)):
    """Get current subscription details"""
    if not stripe_api_key:
        return {"subscription": None, "message": "Stripe not configured"}
    
    subscription_id = current_user.get("stripe_subscription_id")
    if not subscription_id:
        return {
            "subscription": None,
            "tier": current_user.get("subscription_tier"),
            "status": current_user.get("subscription_status", "inactive")
        }
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Get upcoming invoice for next billing date
        upcoming_invoice = None
        try:
            upcoming = stripe.Invoice.upcoming(subscription=subscription_id)
            upcoming_invoice = {
                "amount_due": upcoming.amount_due / 100,
                "currency": upcoming.currency,
                "next_billing_date": datetime.fromtimestamp(upcoming.next_payment_attempt).isoformat() if upcoming.next_payment_attempt else None
            }
        except Exception:
            pass
        
        return {
            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "plan_id": subscription.metadata.get("plan_id"),
                "billing_cycle": subscription.metadata.get("billing_cycle", "monthly")
            },
            "upcoming_invoice": upcoming_invoice,
            "tier": current_user.get("subscription_tier"),
            "status": subscription.status
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving subscription: {e}")
        return {
            "subscription": None,
            "tier": current_user.get("subscription_tier"),
            "status": current_user.get("subscription_status", "inactive"),
            "error": str(e)
        }

@api_router.get("/subscriptions/invoices")
async def get_subscription_invoices(
    limit: int = 10,
    current_user: Dict = Depends(get_current_user)
):
    """Get invoice history for the customer"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    customer_id = current_user.get("stripe_customer_id")
    if not customer_id:
        return {"invoices": []}
    
    try:
        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=limit
        )
        
        return {
            "invoices": [{
                "id": inv.id,
                "number": inv.number,
                "status": inv.status,
                "amount_due": inv.amount_due / 100,
                "amount_paid": inv.amount_paid / 100,
                "currency": inv.currency,
                "created": datetime.fromtimestamp(inv.created).isoformat(),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url,
                "period_start": datetime.fromtimestamp(inv.period_start).isoformat() if inv.period_start else None,
                "period_end": datetime.fromtimestamp(inv.period_end).isoformat() if inv.period_end else None
            } for inv in invoices.data]
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")

@api_router.post("/webhook/stripe-subscriptions")
async def stripe_subscription_webhook(request: Request):
    """
    Handle Stripe subscription webhook events.
    This handles: invoice.paid, invoice.payment_failed, customer.subscription.updated, etc.
    """
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # For testing without webhook signature verification
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_type = event.type
    data = event.data.object
    
    logger.info(f"Stripe webhook received: {event_type}")
    
    # Handle subscription events
    if event_type == "checkout.session.completed":
        # Subscription checkout completed
        if data.mode == "subscription":
            user_id = data.metadata.get("user_id")
            plan_id = data.metadata.get("plan_id")
            billing_cycle = data.metadata.get("billing_cycle", "monthly")
            subscription_id = data.subscription
            
            if user_id and subscription_id:
                plan = SUBSCRIPTION_PLANS.get(plan_id, {})
                
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "stripe_subscription_id": subscription_id,
                        "subscription_tier": plan_id,
                        "subscription_status": "active",
                        "subscription_billing_cycle": billing_cycle,
                        "monthly_lead_allowance": plan.get("leads_per_month", 0),
                        "monthly_call_allowance": plan.get("calls_per_month", 0),
                        "lead_credits_remaining": plan.get("leads_per_month", 0),
                        "call_credits_remaining": plan.get("calls_per_month", 0),
                        "subscription_started_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Update subscription record
                await db.subscription_records.update_one(
                    {"checkout_session_id": data.id},
                    {"$set": {
                        "stripe_subscription_id": subscription_id,
                        "status": "active",
                        "activated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                logger.info(f"Subscription activated for user {user_id}: {plan_id}")
    
    elif event_type == "invoice.paid":
        # Recurring invoice paid - refresh credits
        subscription_id = data.subscription
        if subscription_id:
            # Find user by subscription ID
            user = await db.users.find_one(
                {"stripe_subscription_id": subscription_id},
                {"_id": 0}
            )
            
            if user:
                plan_id = user.get("subscription_tier")
                plan = SUBSCRIPTION_PLANS.get(plan_id, {})
                
                # Refresh monthly credits
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "lead_credits_remaining": plan.get("leads_per_month", 0),
                        "call_credits_remaining": plan.get("calls_per_month", 0),
                        "last_credit_refresh": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Record invoice in our database
                await db.invoices.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": user["user_id"],
                    "stripe_invoice_id": data.id,
                    "amount_paid": data.amount_paid / 100,
                    "currency": data.currency,
                    "status": "paid",
                    "invoice_pdf": data.invoice_pdf,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                logger.info(f"Invoice paid, credits refreshed for user {user['user_id']}")
    
    elif event_type == "invoice.payment_failed":
        # Payment failed
        subscription_id = data.subscription
        if subscription_id:
            user = await db.users.find_one(
                {"stripe_subscription_id": subscription_id},
                {"_id": 0}
            )
            
            if user:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "subscription_status": "past_due",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.warning(f"Payment failed for user {user['user_id']}")
    
    elif event_type == "customer.subscription.updated":
        # Subscription updated (plan change, cancellation scheduled, etc.)
        subscription_id = data.id
        user = await db.users.find_one(
            {"stripe_subscription_id": subscription_id},
            {"_id": 0}
        )
        
        if user:
            update_data = {
                "subscription_status": data.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if data.cancel_at_period_end:
                update_data["subscription_canceling"] = True
                update_data["subscription_cancel_at"] = datetime.fromtimestamp(data.current_period_end).isoformat()
            
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": update_data}
            )
    
    elif event_type == "customer.subscription.deleted":
        # Subscription canceled/ended
        subscription_id = data.id
        user = await db.users.find_one(
            {"stripe_subscription_id": subscription_id},
            {"_id": 0}
        )
        
        if user:
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "subscription_tier": None,
                    "subscription_status": "canceled",
                    "stripe_subscription_id": None,
                    "subscription_canceling": False,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Subscription canceled for user {user['user_id']}")
    
    return {"status": "success", "event_type": event_type}

# ----- Usage Tracking & Overage Billing -----

@api_router.get("/usage/current-period")
async def get_current_period_usage(current_user: Dict = Depends(get_current_user)):
    """Get usage for the current billing period"""
    
    # Determine billing period
    subscription_started = current_user.get("subscription_started_at")
    if subscription_started:
        start_date = datetime.fromisoformat(subscription_started.replace("Z", "+00:00"))
        # Find current period start (same day each month)
        now = datetime.now(timezone.utc)
        period_start = start_date.replace(year=now.year, month=now.month)
        if period_start > now:
            period_start = period_start.replace(month=period_start.month - 1)
    else:
        # Default to start of current month
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count usage
    leads_used = await db.leads.count_documents({
        "user_id": current_user["user_id"],
        "created_at": {"$gte": period_start.isoformat()}
    })
    
    calls_made = await db.calls.count_documents({
        "user_id": current_user["user_id"],
        "created_at": {"$gte": period_start.isoformat()}
    })
    
    # Get allowances
    plan = SUBSCRIPTION_PLANS.get(current_user.get("subscription_tier"), {})
    leads_allowance = plan.get("leads_per_month", 0)
    calls_allowance = plan.get("calls_per_month", 0)
    
    # Calculate overages
    leads_overage = max(0, leads_used - leads_allowance)
    calls_overage = max(0, calls_made - calls_allowance)
    
    # Overage rates (per unit)
    leads_overage_rate = 0.12  # $0.12 per lead overage
    calls_overage_rate = 0.10  # $0.10 per call overage
    
    overage_charges = (leads_overage * leads_overage_rate) + (calls_overage * calls_overage_rate)
    
    return {
        "period_start": period_start.isoformat(),
        "usage": {
            "leads_used": leads_used,
            "leads_allowance": leads_allowance,
            "leads_remaining": max(0, leads_allowance - leads_used),
            "leads_overage": leads_overage,
            "calls_made": calls_made,
            "calls_allowance": calls_allowance,
            "calls_remaining": max(0, calls_allowance - calls_made),
            "calls_overage": calls_overage
        },
        "overage_charges": {
            "leads_rate": leads_overage_rate,
            "calls_rate": calls_overage_rate,
            "total_pending": round(overage_charges, 2)
        },
        "subscription": {
            "tier": current_user.get("subscription_tier"),
            "status": current_user.get("subscription_status")
        }
    }

# ----- Follow-Up Call System -----

@api_router.get("/followups")
async def get_followups(
    status: Optional[str] = None,
    lead_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Get scheduled follow-up calls"""
    query = {"user_id": current_user["user_id"]}
    
    if status:
        query["status"] = status
    if lead_id:
        query["lead_id"] = lead_id
    if campaign_id:
        query["campaign_id"] = campaign_id
    
    followups = await db.followups.find(
        query, {"_id": 0}
    ).sort("scheduled_at", 1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.followups.count_documents(query)
    
    return {
        "followups": followups,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.post("/followups")
async def create_followup(
    followup: FollowUpCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Manually schedule a follow-up call"""
    # Verify lead exists and belongs to user
    lead = await db.leads.find_one({
        "id": followup.lead_id,
        "user_id": current_user["user_id"]
    })
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Create follow-up record
    followup_record = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "lead_id": followup.lead_id,
        "campaign_id": followup.campaign_id,
        "scheduled_at": followup.scheduled_at,
        "reason": followup.reason,
        "status": "scheduled",
        "attempt_number": 1,
        "max_attempts": followup.max_attempts,
        "notes": followup.notes,
        "callback_time_preference": followup.callback_time_preference,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.followups.insert_one(followup_record)
    
    return {"message": "Follow-up scheduled", "followup": {k: v for k, v in followup_record.items() if k != "_id"}}

@api_router.get("/followups/pending")
async def get_pending_followups(
    current_user: Dict = Depends(get_current_user)
):
    """Get follow-ups that are due to be executed"""
    now = datetime.now(timezone.utc).isoformat()
    
    followups = await db.followups.find({
        "user_id": current_user["user_id"],
        "status": "scheduled",
        "scheduled_at": {"$lte": now}
    }, {"_id": 0}).sort("scheduled_at", 1).to_list(100)
    
    return {"pending_followups": followups, "count": len(followups)}

@api_router.post("/followups/{followup_id}/execute")
async def execute_followup(
    followup_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Execute a scheduled follow-up call"""
    followup = await db.followups.find_one({
        "id": followup_id,
        "user_id": current_user["user_id"]
    })
    
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    if followup["status"] != "scheduled":
        raise HTTPException(status_code=400, detail=f"Follow-up is {followup['status']}, not scheduled")
    
    # Update status to in_progress
    await db.followups.update_one(
        {"id": followup_id},
        {"$set": {"status": "in_progress", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Get lead and campaign
    lead = await db.leads.find_one({"id": followup["lead_id"]}, {"_id": 0})
    campaign = await db.campaigns.find_one({"id": followup["campaign_id"]}, {"_id": 0})
    
    if not lead or not campaign:
        await db.followups.update_one(
            {"id": followup_id},
            {"$set": {"status": "failed", "notes": "Lead or campaign not found"}}
        )
        raise HTTPException(status_code=404, detail="Lead or campaign not found")
    
    # Check if lead is still callable (not converted, not DNC)
    if lead.get("status") in ["converted", "dnc", "unsubscribed"]:
        await db.followups.update_one(
            {"id": followup_id},
            {"$set": {"status": "skipped", "notes": f"Lead status: {lead.get('status')}"}}
        )
        return {"message": "Follow-up skipped", "reason": f"Lead status: {lead.get('status')}"}
    
    # Initiate the call (similar to /calls/initiate but with follow-up context)
    try:
        # Create call record
        call_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "lead_id": lead["id"],
            "campaign_id": campaign["id"],
            "agent_id": followup.get("agent_id"),
            "status": "pending",
            "is_followup": True,
            "followup_id": followup_id,
            "followup_attempt": followup["attempt_number"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.calls.insert_one(call_record)
        
        # Update follow-up with call reference
        await db.followups.update_one(
            {"id": followup_id},
            {"$set": {"result_call_id": call_record["id"]}}
        )
        
        return {
            "message": "Follow-up call initiated",
            "call_id": call_record["id"],
            "followup_id": followup_id,
            "lead": {"name": lead.get("contact_name") or lead.get("business_name"), "phone": lead.get("phone")}
        }
        
    except Exception as e:
        await db.followups.update_one(
            {"id": followup_id},
            {"$set": {"status": "failed", "notes": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@api_router.post("/followups/{followup_id}/complete")
async def complete_followup(
    followup_id: str,
    outcome: str,  # "connected", "no_answer", "voicemail", "failed"
    schedule_retry: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """Mark a follow-up as completed and optionally schedule retry"""
    followup = await db.followups.find_one({
        "id": followup_id,
        "user_id": current_user["user_id"]
    })
    
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    update_data = {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.followups.update_one({"id": followup_id}, {"$set": update_data})
    
    # Schedule retry if requested and attempts remaining
    if schedule_retry and outcome in ["no_answer", "voicemail"] and followup["attempt_number"] < followup["max_attempts"]:
        # Get campaign follow-up settings
        campaign = await db.campaigns.find_one({"id": followup["campaign_id"]})
        delay_hours = 24  # Default 24 hours
        
        if campaign and campaign.get("followup_settings"):
            settings = campaign["followup_settings"]
            if outcome == "no_answer":
                delay_hours = settings.get("no_answer_retry_delay_hours", 24)
            elif outcome == "voicemail":
                delay_hours = settings.get("voicemail_followup_delay_hours", 48)
        
        # Create new follow-up
        retry_followup = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "lead_id": followup["lead_id"],
            "campaign_id": followup["campaign_id"],
            "agent_id": followup.get("agent_id"),
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=delay_hours)).isoformat(),
            "reason": "no_answer" if outcome == "no_answer" else "voicemail",
            "status": "scheduled",
            "attempt_number": followup["attempt_number"] + 1,
            "max_attempts": followup["max_attempts"],
            "original_call_id": followup.get("original_call_id"),
            "notes": f"Retry #{followup['attempt_number'] + 1} after {outcome}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.followups.insert_one(retry_followup)
        
        return {
            "message": "Follow-up completed, retry scheduled",
            "outcome": outcome,
            "retry_scheduled": True,
            "retry_at": retry_followup["scheduled_at"],
            "attempt": retry_followup["attempt_number"]
        }
    
    return {"message": "Follow-up completed", "outcome": outcome, "retry_scheduled": False}

@api_router.delete("/followups/{followup_id}")
async def cancel_followup(
    followup_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Cancel a scheduled follow-up"""
    result = await db.followups.update_one(
        {"id": followup_id, "user_id": current_user["user_id"], "status": "scheduled"},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Follow-up not found or already processed")
    
    return {"message": "Follow-up cancelled"}

@api_router.post("/followups/schedule-callback")
async def schedule_callback(
    lead_id: str = Form(...),
    campaign_id: str = Form(...),
    callback_datetime: str = Form(...),  # ISO format
    notes: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_user)
):
    """Schedule a callback when lead requests specific time"""
    # Verify lead exists
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    followup = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "lead_id": lead_id,
        "campaign_id": campaign_id,
        "scheduled_at": callback_datetime,
        "reason": "callback_requested",
        "status": "scheduled",
        "attempt_number": 1,
        "max_attempts": 2,  # Try callback twice max
        "notes": notes or "Customer requested callback",
        "callback_time_preference": callback_datetime,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.followups.insert_one(followup)
    
    # Update lead status
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"status": "callback_scheduled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Callback scheduled", "followup": {k: v for k, v in followup.items() if k != "_id"}}

@api_router.get("/followups/stats")
async def get_followup_stats(
    campaign_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get follow-up statistics"""
    query = {"user_id": current_user["user_id"]}
    if campaign_id:
        query["campaign_id"] = campaign_id
    
    # Count by status
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = await db.followups.aggregate(pipeline).to_list(10)
    
    # Count by reason
    reason_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$reason", "count": {"$sum": 1}}}
    ]
    reason_counts = await db.followups.aggregate(reason_pipeline).to_list(10)
    
    # Upcoming follow-ups (next 24 hours)
    tomorrow = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    upcoming = await db.followups.count_documents({
        **query,
        "status": "scheduled",
        "scheduled_at": {"$lte": tomorrow}
    })
    
    # Overdue follow-ups
    now = datetime.now(timezone.utc).isoformat()
    overdue = await db.followups.count_documents({
        **query,
        "status": "scheduled",
        "scheduled_at": {"$lt": now}
    })
    
    return {
        "by_status": {item["_id"]: item["count"] for item in status_counts},
        "by_reason": {item["_id"]: item["count"] for item in reason_counts},
        "upcoming_24h": upcoming,
        "overdue": overdue,
        "total": await db.followups.count_documents(query)
    }

# ----- Follow-Up Sequences -----

@api_router.get("/followup-sequences")
async def get_followup_sequences(current_user: Dict = Depends(get_current_user)):
    """Get user's follow-up sequences"""
    sequences = await db.followup_sequences.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).to_list(50)
    return {"sequences": sequences}

@api_router.post("/followup-sequences")
async def create_followup_sequence(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    steps: str = Form(...),  # JSON string
    current_user: Dict = Depends(get_current_user)
):
    """Create a multi-touch follow-up sequence"""
    import json as json_module
    
    try:
        steps_list = json_module.loads(steps)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid steps JSON")
    
    sequence = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "name": name,
        "description": description,
        "is_active": True,
        "steps": steps_list,
        "max_attempts_per_step": 2,
        "stop_on_connect": True,
        "stop_on_booking": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.followup_sequences.insert_one(sequence)
    
    return {"message": "Sequence created", "sequence": {k: v for k, v in sequence.items() if k != "_id"}}

@api_router.put("/campaigns/{campaign_id}/followup-settings")
async def update_campaign_followup_settings(
    campaign_id: str,
    enabled: bool = Form(True),
    no_answer_retry_enabled: bool = Form(True),
    no_answer_retry_count: int = Form(3),
    no_answer_retry_delay_hours: int = Form(24),
    voicemail_followup_enabled: bool = Form(True),
    voicemail_followup_delay_hours: int = Form(48),
    sequence_id: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_user)
):
    """Update follow-up settings for a campaign"""
    campaign = await db.campaigns.find_one({
        "id": campaign_id,
        "user_id": current_user["user_id"]
    })
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    followup_settings = {
        "enabled": enabled,
        "no_answer_retry_enabled": no_answer_retry_enabled,
        "no_answer_retry_count": no_answer_retry_count,
        "no_answer_retry_delay_hours": no_answer_retry_delay_hours,
        "voicemail_followup_enabled": voicemail_followup_enabled,
        "voicemail_followup_delay_hours": voicemail_followup_delay_hours,
        "sequence_id": sequence_id
    }
    
    await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"followup_settings": followup_settings, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Follow-up settings updated", "settings": followup_settings}

@api_router.get("/campaigns/{campaign_id}/followup-settings")
async def get_campaign_followup_settings(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get follow-up settings for a campaign"""
    campaign = await db.campaigns.find_one({
        "id": campaign_id,
        "user_id": current_user["user_id"]
    }, {"_id": 0, "followup_settings": 1, "id": 1, "name": 1})
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Return default settings if none configured
    default_settings = {
        "enabled": True,
        "no_answer_retry_enabled": True,
        "no_answer_retry_count": 3,
        "no_answer_retry_delay_hours": 24,
        "voicemail_followup_enabled": True,
        "voicemail_followup_delay_hours": 48,
        "sequence_id": None
    }
    
    return {
        "campaign_id": campaign["id"],
        "campaign_name": campaign.get("name"),
        "settings": campaign.get("followup_settings", default_settings)
    }

# Background task helper for auto-scheduling follow-ups after calls
async def auto_schedule_followup(call_id: str, outcome: str, user_id: str):
    """Automatically schedule follow-up based on call outcome"""
    call = await db.calls.find_one({"id": call_id})
    if not call:
        return
    
    campaign = await db.campaigns.find_one({"id": call.get("campaign_id")})
    if not campaign:
        return
    
    settings = campaign.get("followup_settings", {})
    if not settings.get("enabled", True):
        return
    
    # Check if lead already has pending follow-up
    existing = await db.followups.find_one({
        "lead_id": call["lead_id"],
        "campaign_id": call["campaign_id"],
        "status": "scheduled"
    })
    if existing:
        return  # Don't create duplicate
    
    delay_hours = None
    reason = None
    
    if outcome == "no_answer" and settings.get("no_answer_retry_enabled", True):
        delay_hours = settings.get("no_answer_retry_delay_hours", 24)
        reason = "no_answer"
    elif outcome == "voicemail" and settings.get("voicemail_followup_enabled", True):
        delay_hours = settings.get("voicemail_followup_delay_hours", 48)
        reason = "voicemail"
    
    if delay_hours and reason:
        followup = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "lead_id": call["lead_id"],
            "campaign_id": call["campaign_id"],
            "agent_id": call.get("agent_id"),
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=delay_hours)).isoformat(),
            "reason": reason,
            "status": "scheduled",
            "attempt_number": 1,
            "max_attempts": settings.get("no_answer_retry_count", 3),
            "original_call_id": call_id,
            "notes": f"Auto-scheduled after {outcome}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.followups.insert_one(followup)
        logger.info(f"Auto-scheduled follow-up for lead {call['lead_id']} in {delay_hours}h")

# ----- Compliance & Twilio Calling Endpoints -----

@api_router.get("/compliance/dnc")
async def get_dnc_list(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict = Depends(get_current_user)
):
    """Get internal DNC list"""
    entries = await db.dnc_list.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.dnc_list.count_documents({})
    return {"entries": entries, "total": total}

@api_router.post("/compliance/dnc/add")
async def add_to_dnc_list(
    phone_number: str,
    reason: str = "user_request",
    current_user: Dict = Depends(get_current_user)
):
    """Add a number to the DNC list"""
    success = await compliance_service.add_to_dnc(
        phone_number=phone_number,
        reason=reason,
        added_by=current_user["user_id"]
    )
    if success:
        return {"message": f"Added {phone_number} to DNC list", "status": "success"}
    else:
        return {"message": f"{phone_number} is already on DNC list", "status": "exists"}

@api_router.delete("/compliance/dnc/remove")
async def remove_from_dnc_list(
    phone_number: str,
    current_user: Dict = Depends(get_current_user)
):
    """Remove a number from the DNC list"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = await compliance_service.remove_from_dnc(phone_number)
    if success:
        return {"message": f"Removed {phone_number} from DNC list"}
    else:
        raise HTTPException(status_code=404, detail="Number not found on DNC list")

@api_router.get("/compliance/check/{phone_number}")
async def check_compliance(
    phone_number: str,
    current_user: Dict = Depends(get_current_user)
):
    """Run full TCPA compliance check on a phone number before calling"""
    result = await compliance_service.pre_call_compliance_check(
        phone_number=phone_number,
        user_id=current_user["user_id"]
    )
    return result

@api_router.get("/compliance/calling-hours/{phone_number}")
async def check_calling_hours(
    phone_number: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Check if it's within legal calling hours for a phone number.
    TCPA requires calls only between 8am-9pm local time.
    Some states have stricter requirements (e.g., Texas 9am-9pm, Connecticut 9am-8pm).
    """
    result = compliance_service.check_calling_hours(phone_number)
    return result

@api_router.get("/compliance/national-dnc/{phone_number}")
async def check_national_dnc(
    phone_number: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Check if a phone number is on the National Do Not Call Registry.
    Uses Real Phone Validation DNC Plus API (requires DNC_API_KEY).
    Returns: national_dnc, state_dnc, litigator status, and cell phone detection.
    """
    result = await compliance_service.check_national_dnc(phone_number, current_user["user_id"])
    return result

@api_router.get("/compliance/status")
async def get_compliance_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get TCPA compliance configuration status.
    Shows which compliance features are configured, active, and usage stats.
    """
    user_id = current_user["user_id"]
    features = get_tier_features(current_user)
    
    # Get DNC usage for current month
    dnc_usage = await compliance_service.get_dnc_usage(user_id)
    dnc_allowance = features.get("dnc_checks_per_month", 0)
    dnc_remaining = dnc_allowance - dnc_usage["checks_used"] if dnc_allowance > 0 else "unlimited"
    
    return {
        "tcpa_compliance": {
            "calling_hours_enforcement": True,
            "internal_dnc_list": True,
            "national_dnc_registry": {
                "enabled": features.get("national_dnc_enabled", False),
                "api_configured": bool(os.environ.get("DNC_API_KEY")),
                "provider": "Real Phone Validation" if os.environ.get("DNC_API_KEY") else None,
                "note": "Configure DNC_API_KEY for National DNC Registry integration" if not os.environ.get("DNC_API_KEY") else "DNC Plus API configured - checks National DNC, State DNC, and Litigators"
            },
            "state_dnc_registry": {
                "enabled": bool(os.environ.get("DNC_API_KEY")),
                "note": "State DNC checks included with Real Phone Validation API"
            },
            "litigator_detection": {
                "enabled": bool(os.environ.get("DNC_API_KEY")),
                "note": "TCPA litigator database check - high lawsuit risk numbers blocked"
            },
            "ai_disclosure": True,
            "call_frequency_limits": True,
            "phone_verification": bool(twilio_client),
        },
        "dnc_usage": {
            "month": dnc_usage["month"],
            "checks_used": dnc_usage["checks_used"],
            "checks_allowance": dnc_allowance if dnc_allowance > 0 else "unlimited",
            "checks_remaining": dnc_remaining,
            "overage_cost": features.get("dnc_overage_cost", 0.015) if dnc_allowance > 0 else 0,
            "tier": current_user.get("subscription_tier", "free")
        },
        "tier_dnc_allowances": {
            "free": "50 checks/month (internal only)",
            "payg": "100 checks/month + $0.015/overage",
            "starter": "500 checks/month + $0.012/overage",
            "professional": "2,000 checks/month + $0.01/overage",
            "unlimited": "Unlimited checks",
            "byl": "1,500 checks/month + $0.01/overage"
        },
        "state_restrictions": STATE_CALLING_RESTRICTIONS,
        "checks_performed": [
            "calling_hours - Blocks calls outside 8am-9pm local time (with state-specific rules)",
            "internal_dnc - Checks against your internal Do Not Call list",
            "national_dnc - Checks against National DNC Registry",
            "state_dnc - Checks against State DNC Registries",
            "litigator - Checks against known TCPA litigator database",
            "number_verification - Validates phone number and determines line type",
            "call_frequency - Limits calls to 3 per number per 7 days"
        ]
    }

# Current compliance agreement version
COMPLIANCE_VERSION = "1.0"

class ComplianceAcknowledgment(BaseModel):
    """Model for compliance acknowledgment request"""
    calling_mode: str = "b2b"  # "b2b" or "b2c"
    ftc_san: Optional[str] = None  # Required if calling_mode is "b2c"
    acknowledge_dnc_responsibility: bool = True
    acknowledge_tcpa_rules: bool = True
    acknowledge_calling_hours: bool = True
    acknowledge_litigator_risk: bool = True

@api_router.get("/compliance/acknowledgment")
async def get_compliance_acknowledgment(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get user's compliance acknowledgment status.
    Users must acknowledge compliance before making calls.
    """
    return {
        "acknowledged": current_user.get("compliance_acknowledged", False),
        "acknowledged_at": current_user.get("compliance_acknowledged_at"),
        "acknowledged_version": current_user.get("compliance_acknowledged_version"),
        "current_version": COMPLIANCE_VERSION,
        "calling_mode": current_user.get("calling_mode", "b2b"),
        "ftc_san": current_user.get("ftc_san"),
        "requires_update": (
            current_user.get("compliance_acknowledged_version") != COMPLIANCE_VERSION
            if current_user.get("compliance_acknowledged")
            else True
        ),
        "can_make_calls": (
            current_user.get("compliance_acknowledged", False) and
            current_user.get("compliance_acknowledged_version") == COMPLIANCE_VERSION
        )
    }

@api_router.post("/compliance/acknowledge")
async def acknowledge_compliance(
    acknowledgment: ComplianceAcknowledgment,
    current_user: Dict = Depends(get_current_user)
):
    """
    Submit compliance acknowledgment.
    Required before making any outbound calls.
    """
    user_id = current_user["user_id"]
    
    # Validate all checkboxes are checked
    if not all([
        acknowledgment.acknowledge_dnc_responsibility,
        acknowledgment.acknowledge_tcpa_rules,
        acknowledgment.acknowledge_calling_hours,
        acknowledgment.acknowledge_litigator_risk
    ]):
        raise HTTPException(
            status_code=400,
            detail="All compliance acknowledgments must be accepted"
        )
    
    # If B2C mode, FTC SAN is recommended (not required, but logged)
    if acknowledgment.calling_mode == "b2c" and not acknowledgment.ftc_san:
        logger.warning(f"User {user_id} selected B2C mode without FTC SAN")
    
    # Update user record
    update_data = {
        "compliance_acknowledged": True,
        "compliance_acknowledged_at": datetime.now(timezone.utc).isoformat(),
        "compliance_acknowledged_version": COMPLIANCE_VERSION,
        "calling_mode": acknowledgment.calling_mode,
        "ftc_san": acknowledgment.ftc_san,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    # Log the acknowledgment for audit
    await db.compliance_acknowledgments.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "email": current_user.get("email"),
        "version": COMPLIANCE_VERSION,
        "calling_mode": acknowledgment.calling_mode,
        "ftc_san": acknowledgment.ftc_san,
        "ip_address": None,  # Could capture from request if needed
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        "acknowledgments": {
            "dnc_responsibility": acknowledgment.acknowledge_dnc_responsibility,
            "tcpa_rules": acknowledgment.acknowledge_tcpa_rules,
            "calling_hours": acknowledgment.acknowledge_calling_hours,
            "litigator_risk": acknowledgment.acknowledge_litigator_risk
        }
    })
    
    logger.info(f"User {user_id} acknowledged compliance v{COMPLIANCE_VERSION}, mode: {acknowledgment.calling_mode}")
    
    return {
        "success": True,
        "message": "Compliance acknowledgment recorded",
        "calling_mode": acknowledgment.calling_mode,
        "can_make_calls": True
    }

@api_router.get("/compliance/setup-guide")
async def get_compliance_setup_guide(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get compliance setup guide and checklist.
    """
    user_acknowledged = current_user.get("compliance_acknowledged", False)
    calling_mode = current_user.get("calling_mode", "b2b")
    
    # Get DNC stats
    dnc_count = await db.national_dnc_list.count_documents({})
    litigator_count = await db.tcpa_litigators.count_documents({})
    
    # Get last DNC refresh
    refresh_info = await db.dnc_refresh_log.find_one(
        {"type": "national_dnc"},
        {"_id": 0},
        sort=[("refreshed_at", -1)]
    )
    
    dnc_current = False
    if refresh_info:
        try:
            last_refresh = datetime.fromisoformat(refresh_info["refreshed_at"].replace("Z", "+00:00"))
            dnc_current = (datetime.now(timezone.utc) - last_refresh).days <= 31
        except Exception:
            pass
    
    b2b_checklist = [
        {
            "id": "acknowledge",
            "title": "Acknowledge Compliance Responsibility",
            "description": "Confirm you understand TCPA rules and accept responsibility",
            "completed": user_acknowledged,
            "required": True,
            "action": "acknowledge"
        },
        {
            "id": "calling_hours",
            "title": "Calling Hours",
            "description": "System enforces 8am-9pm local time (state-specific rules apply)",
            "completed": True,  # Auto-enforced by platform
            "required": True,
            "action": None
        },
        {
            "id": "ai_disclosure",
            "title": "AI Call Disclosure",
            "description": "All calls begin with AI disclosure as required by law",
            "completed": True,  # Auto-enforced by platform
            "required": True,
            "action": None
        },
        {
            "id": "internal_dnc",
            "title": "Internal DNC List",
            "description": "Opt-outs are automatically added to your DNC list",
            "completed": True,  # Auto-managed
            "required": True,
            "action": None
        },
        {
            "id": "litigator_list",
            "title": "TCPA Litigator Protection",
            "description": f"Block known TCPA plaintiffs ({litigator_count} numbers loaded)",
            "completed": litigator_count > 0,
            "required": False,
            "action": "upload_litigators"
        }
    ]
    
    b2c_checklist = b2b_checklist + [
        {
            "id": "ftc_registration",
            "title": "FTC DNC Registry Registration",
            "description": "Register at telemarketing.donotcall.gov and obtain your SAN",
            "completed": bool(current_user.get("ftc_san")),
            "required": True,
            "action": "ftc_register"
        },
        {
            "id": "dnc_upload",
            "title": "Upload FTC DNC Data",
            "description": f"Upload National DNC data ({dnc_count:,} numbers loaded)",
            "completed": dnc_count > 0,
            "required": True,
            "action": "upload_dnc"
        },
        {
            "id": "dnc_refresh",
            "title": "DNC Data Current (31-day refresh)",
            "description": "FTC requires refresh every 31 days for safe harbor",
            "completed": dnc_current,
            "required": True,
            "action": "refresh_dnc"
        }
    ]
    
    checklist = b2c_checklist if calling_mode == "b2c" else b2b_checklist
    
    return {
        "calling_mode": calling_mode,
        "acknowledged": user_acknowledged,
        "checklist": checklist,
        "completion_percentage": int(
            sum(1 for item in checklist if item["completed"]) / len(checklist) * 100
        ),
        "can_make_calls": user_acknowledged,
        "guides": {
            "b2b": {
                "title": "B2B Calling (Business-to-Business)",
                "description": "Calls to business landlines are exempt from National DNC Registry requirements",
                "requirements": [
                    "Calls must be to business phone numbers (not personal cell phones)",
                    "You are still responsible for honoring opt-out requests",
                    "Calling hours (8am-9pm local time) still apply",
                    "AI disclosure is required on all calls"
                ]
            },
            "b2c": {
                "title": "B2C Calling (Business-to-Consumer)",
                "description": "Calls to consumers require full TCPA/DNC compliance",
                "requirements": [
                    "Must register with FTC and obtain Subscription Account Number (SAN)",
                    "Must download and upload FTC DNC data (fee: $82/area code, max $22k nationwide)",
                    "Must refresh DNC data every 31 days for safe harbor protection",
                    "Prior express written consent required for autodialed calls to cell phones",
                    "All TCPA rules and state-specific regulations apply"
                ]
            }
        },
        "resources": [
            {
                "title": "FTC Do Not Call Registry",
                "url": "https://telemarketing.donotcall.gov",
                "description": "Register and download DNC data"
            },
            {
                "title": "FTC Telemarketing Sales Rule",
                "url": "https://www.ftc.gov/business-guidance/resources/complying-telemarketing-sales-rule",
                "description": "Official FTC compliance guide"
            },
            {
                "title": "TCPA Overview",
                "url": "https://www.fcc.gov/consumers/guides/stop-unwanted-robocalls-and-texts",
                "description": "FCC consumer protection rules"
            }
        ]
    }

@api_router.post("/compliance/national-dnc/upload")
async def upload_national_dnc_list(
    file: UploadFile,
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload a list of phone numbers to the internal National DNC list.
    Useful for importing FTC DNC data downloads.
    Accepts CSV with 'phone_number' column or plain text with one number per line.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    content = await file.read()
    text = content.decode('utf-8')
    
    # Parse phone numbers from file
    phone_numbers = []
    lines = text.strip().split('\n')
    
    for line in lines:
        # Skip header row if CSV
        if 'phone' in line.lower() and len(phone_numbers) == 0:
            continue
        
        # Extract phone number (clean it)
        clean_number = ''.join(filter(str.isdigit, line.split(',')[0] if ',' in line else line))
        if len(clean_number) >= 10:
            if not clean_number.startswith('1') and len(clean_number) == 10:
                clean_number = '1' + clean_number
            phone_numbers.append(f"+{clean_number}")
    
    # Bulk insert into national_dnc_list
    if phone_numbers:
        operations = [
            {
                "phone_number": num,
                "source": "uploaded",
                "uploaded_by": current_user["user_id"],
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
            for num in phone_numbers
        ]
        
        # Use bulk upsert to avoid duplicates
        for op in operations:
            await db.national_dnc_list.update_one(
                {"phone_number": op["phone_number"]},
                {"$set": op},
                upsert=True
            )
    
    return {
        "message": f"Uploaded {len(phone_numbers)} phone numbers to National DNC list",
        "count": len(phone_numbers)
    }

# ============== FTC DNC DATA MANAGEMENT ==============

@api_router.get("/compliance/dnc/stats")
async def get_dnc_stats(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get DNC database statistics including last refresh date and counts.
    """
    # Get counts
    national_dnc_count = await db.national_dnc_list.count_documents({})
    litigator_count = await db.tcpa_litigators.count_documents({})
    internal_dnc_count = await db.dnc_list.count_documents({})
    
    # Get last refresh info
    refresh_info = await db.dnc_refresh_log.find_one(
        {"type": "national_dnc"},
        {"_id": 0},
        sort=[("refreshed_at", -1)]
    )
    
    litigator_refresh = await db.dnc_refresh_log.find_one(
        {"type": "litigator_list"},
        {"_id": 0},
        sort=[("refreshed_at", -1)]
    )
    
    # Calculate days since last refresh
    days_since_refresh = None
    refresh_status = "never"
    if refresh_info:
        try:
            last_refresh = datetime.fromisoformat(refresh_info["refreshed_at"].replace("Z", "+00:00"))
            days_since_refresh = (datetime.now(timezone.utc) - last_refresh).days
            if days_since_refresh <= 30:
                refresh_status = "current"
            elif days_since_refresh <= 60:
                refresh_status = "due_soon"
            elif days_since_refresh <= 90:
                refresh_status = "overdue"
            else:
                refresh_status = "critical"
        except Exception:
            pass
    
    return {
        "national_dnc": {
            "count": national_dnc_count,
            "last_refresh": refresh_info.get("refreshed_at") if refresh_info else None,
            "days_since_refresh": days_since_refresh,
            "refresh_status": refresh_status,
            "source": refresh_info.get("source") if refresh_info else None,
            "next_refresh_due": "Quarterly refresh required by FTC"
        },
        "litigator_list": {
            "count": litigator_count,
            "last_refresh": litigator_refresh.get("refreshed_at") if litigator_refresh else None,
            "source": litigator_refresh.get("source") if litigator_refresh else None
        },
        "internal_dnc": {
            "count": internal_dnc_count,
            "description": "Numbers added via opt-out requests during calls"
        },
        "compliance_note": "FTC requires National DNC list refresh every 31 days for safe harbor protection"
    }

@api_router.post("/compliance/dnc/upload-ftc")
async def upload_ftc_dnc_data(
    file: UploadFile,
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload FTC National DNC Registry data file.
    
    Download data from: https://telemarketing.donotcall.gov
    Supports FTC's standard format (area code files or full data files).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        content = await file.read()
        # Try UTF-8 first, fall back to latin-1
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')
        
        phone_numbers = []
        lines = text.strip().split('\n')
        skipped = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip header rows
            if any(h in line.lower() for h in ['phone', 'number', 'area', 'header']):
                continue
            
            # FTC format is typically just phone numbers, one per line
            # Could be 10 digits or formatted
            clean_number = ''.join(filter(str.isdigit, line.split(',')[0] if ',' in line else line))
            
            if len(clean_number) == 10:
                phone_numbers.append(f"+1{clean_number}")
            elif len(clean_number) == 11 and clean_number.startswith('1'):
                phone_numbers.append(f"+{clean_number}")
            else:
                skipped += 1
        
        if not phone_numbers:
            raise HTTPException(status_code=400, detail="No valid phone numbers found in file")
        
        # Batch insert for performance (1000 at a time)
        batch_size = 1000
        inserted = 0
        
        for i in range(0, len(phone_numbers), batch_size):
            batch = phone_numbers[i:i + batch_size]
            operations = []
            for num in batch:
                operations.append({
                    "phone_number": num,
                    "source": "ftc_dnc",
                    "uploaded_by": current_user["user_id"],
                    "uploaded_at": datetime.now(timezone.utc).isoformat()
                })
            
            # Bulk upsert
            for op in operations:
                await db.national_dnc_list.update_one(
                    {"phone_number": op["phone_number"]},
                    {"$set": op},
                    upsert=True
                )
            inserted += len(batch)
        
        # Log the refresh
        await db.dnc_refresh_log.insert_one({
            "type": "national_dnc",
            "source": "ftc_upload",
            "filename": file.filename,
            "count": len(phone_numbers),
            "skipped": skipped,
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
            "refreshed_by": current_user["user_id"]
        })
        
        return {
            "success": True,
            "message": f"Successfully imported {len(phone_numbers):,} phone numbers from FTC DNC data",
            "details": {
                "total_processed": len(lines),
                "valid_numbers": len(phone_numbers),
                "skipped": skipped,
                "filename": file.filename
            },
            "next_steps": "FTC requires refresh every 31 days for safe harbor protection"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FTC DNC upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@api_router.post("/compliance/litigators/upload")
async def upload_litigator_list(
    file: UploadFile,
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload TCPA litigator phone numbers list.
    These are numbers associated with known TCPA plaintiffs/serial litigators.
    Calls to these numbers will be blocked with high-risk warning.
    
    Format: CSV or TXT with phone numbers (one per line)
    Optional columns: phone_number, name, firm, notes, risk_level
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        content = await file.read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')
        
        lines = text.strip().split('\n')
        litigators = []
        
        # Check if CSV with headers
        has_headers = any(h in lines[0].lower() for h in ['phone', 'name', 'firm']) if lines else False
        start_idx = 1 if has_headers else 0
        
        for line in lines[start_idx:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(',') if ',' in line else [line]
            phone = ''.join(filter(str.isdigit, parts[0]))
            
            if len(phone) >= 10:
                if len(phone) == 10:
                    phone = f"+1{phone}"
                elif len(phone) == 11 and phone.startswith('1'):
                    phone = f"+{phone}"
                else:
                    continue
                
                litigator = {
                    "phone_number": phone,
                    "name": parts[1].strip() if len(parts) > 1 else None,
                    "firm": parts[2].strip() if len(parts) > 2 else None,
                    "notes": parts[3].strip() if len(parts) > 3 else None,
                    "risk_level": "high",
                    "source": "uploaded",
                    "added_by": current_user["user_id"],
                    "added_at": datetime.now(timezone.utc).isoformat()
                }
                litigators.append(litigator)
        
        if not litigators:
            raise HTTPException(status_code=400, detail="No valid phone numbers found in file")
        
        # Upsert litigators
        for lit in litigators:
            await db.tcpa_litigators.update_one(
                {"phone_number": lit["phone_number"]},
                {"$set": lit},
                upsert=True
            )
        
        # Log the refresh
        await db.dnc_refresh_log.insert_one({
            "type": "litigator_list",
            "source": "upload",
            "filename": file.filename,
            "count": len(litigators),
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
            "refreshed_by": current_user["user_id"]
        })
        
        return {
            "success": True,
            "message": f"Successfully imported {len(litigators)} TCPA litigator numbers",
            "count": len(litigators)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Litigator list upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@api_router.post("/compliance/litigators/add")
async def add_litigator(
    phone_number: str,
    name: Optional[str] = None,
    firm: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Add a single phone number to the TCPA litigator list."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    clean_number = ''.join(filter(str.isdigit, phone_number))
    if len(clean_number) == 10:
        clean_number = f"+1{clean_number}"
    elif len(clean_number) == 11 and clean_number.startswith('1'):
        clean_number = f"+{clean_number}"
    else:
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    litigator = {
        "phone_number": clean_number,
        "name": name,
        "firm": firm,
        "notes": notes,
        "risk_level": "high",
        "source": "manual",
        "added_by": current_user["user_id"],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tcpa_litigators.update_one(
        {"phone_number": clean_number},
        {"$set": litigator},
        upsert=True
    )
    
    return {"success": True, "message": f"Added {clean_number} to litigator list"}

@api_router.get("/compliance/litigators")
async def get_litigators(
    limit: int = Query(default=100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Get list of known TCPA litigators."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cursor = db.tcpa_litigators.find({}, {"_id": 0}).limit(limit)
    litigators = await cursor.to_list(length=limit)
    
    return {
        "litigators": litigators,
        "count": len(litigators),
        "total": await db.tcpa_litigators.count_documents({})
    }

@api_router.delete("/compliance/litigators/{phone_number}")
async def remove_litigator(
    phone_number: str,
    current_user: Dict = Depends(get_current_user)
):
    """Remove a phone number from the TCPA litigator list."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Try different formats
    formats_to_try = [phone_number]
    clean = ''.join(filter(str.isdigit, phone_number))
    if len(clean) == 10:
        formats_to_try.append(f"+1{clean}")
    elif len(clean) == 11:
        formats_to_try.append(f"+{clean}")
    
    result = await db.tcpa_litigators.delete_one({"phone_number": {"$in": formats_to_try}})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Litigator not found")
    
    return {"success": True, "message": "Litigator removed"}

@api_router.get("/compliance/litigators/info")
async def get_litigator_info(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get information about TCPA litigators and how to build a protection list.
    """
    return {
        "overview": {
            "title": "TCPA Litigator Protection",
            "description": "Professional TCPA plaintiffs actively seek telemarketing violations to file lawsuits. Adding their phone numbers to your blocklist protects your business.",
            "risk": "$500-$1,500 per call in damages, plus legal fees"
        },
        "tcpa_hotspots_2025": {
            "description": "Top states/districts for TCPA litigation in 2025",
            "locations": [
                {"state": "California", "note": "Central District CA - highest volume"},
                {"state": "Florida", "note": "Serial plaintiff activity"},
                {"state": "Texas", "note": "Western District TX - 68% of cases from one firm"},
                {"state": "Illinois", "note": "Chicago area litigation"},
                {"state": "New York", "note": "Class action friendly"}
            ]
        },
        "known_plaintiff_firms": {
            "note": "These firms are known for high-volume TCPA plaintiff representation. Research their cases to identify repeat plaintiffs.",
            "firms": [
                "Kaufman PA (Avi Kaufman) - Top TCPA plaintiff firm",
                "Watstein Terepka LLP - Nationwide TCPA class actions",
                "Anderson + Wanca - TCPA class action specialists",
                "Terrell Marshall Law Group - Consumer class actions",
                "Greenwald Davidson Radbil - TCPA/FDCPA focus"
            ]
        },
        "how_to_build_list": {
            "title": "How to Build Your Litigator Blocklist",
            "steps": [
                {
                    "step": 1,
                    "title": "Search PACER",
                    "description": "Search federal court records (pacer.uscourts.gov) for TCPA cases and identify repeat plaintiffs"
                },
                {
                    "step": 2,
                    "title": "Monitor Legal News",
                    "description": "Follow tcpaworld.com and WebRecon for updates on serial TCPA filers"
                },
                {
                    "step": 3,
                    "title": "Purchase Commercial Lists",
                    "description": "Services like Blacklist Alliance and WebRecon sell pre-compiled litigator lists"
                },
                {
                    "step": 4,
                    "title": "Industry Networks",
                    "description": "Join telemarketing industry groups that share litigator intelligence"
                }
            ]
        },
        "commercial_services": [
            {
                "name": "Blacklist Alliance",
                "url": "https://www.blacklistalliance.com",
                "description": "Real-time litigator scrubbing service"
            },
            {
                "name": "WebRecon",
                "url": "https://www.webrecon.com",
                "description": "TCPA plaintiff intelligence and monitoring"
            },
            {
                "name": "Contact Center Compliance (DNC.com)",
                "url": "https://www.dnc.com",
                "description": "Enterprise compliance suite with litigator data"
            }
        ],
        "best_practices": [
            "Block any number that has previously filed a TCPA lawsuit",
            "Block numbers associated with plaintiff law firms",
            "Immediately add any number that threatens litigation during a call",
            "Review your internal DNC list for patterns (multiple complaints from same area codes)",
            "Consider commercial litigator scrubbing for high-volume calling"
        ]
    }

@api_router.get("/compliance/dnc/refresh-reminder")
async def get_dnc_refresh_reminder(
    current_user: Dict = Depends(get_current_user)
):
    """
    Check if DNC data needs refresh and return reminder status.
    FTC safe harbor requires refresh every 31 days.
    """
    refresh_info = await db.dnc_refresh_log.find_one(
        {"type": "national_dnc"},
        {"_id": 0},
        sort=[("refreshed_at", -1)]
    )
    
    if not refresh_info:
        return {
            "needs_refresh": True,
            "urgency": "critical",
            "message": "National DNC data has never been loaded. Upload FTC DNC data immediately for TCPA compliance.",
            "action_url": "https://telemarketing.donotcall.gov",
            "days_overdue": None
        }
    
    try:
        last_refresh = datetime.fromisoformat(refresh_info["refreshed_at"].replace("Z", "+00:00"))
        days_since = (datetime.now(timezone.utc) - last_refresh).days
        
        if days_since <= 25:
            return {
                "needs_refresh": False,
                "urgency": "none",
                "message": f"DNC data is current. Last refreshed {days_since} days ago.",
                "last_refresh": refresh_info["refreshed_at"],
                "days_until_due": 31 - days_since
            }
        elif days_since <= 31:
            return {
                "needs_refresh": True,
                "urgency": "warning",
                "message": f"DNC refresh due soon. Last refreshed {days_since} days ago. FTC requires refresh every 31 days.",
                "last_refresh": refresh_info["refreshed_at"],
                "days_until_due": 31 - days_since,
                "action_url": "https://telemarketing.donotcall.gov"
            }
        elif days_since <= 60:
            return {
                "needs_refresh": True,
                "urgency": "high",
                "message": f"DNC data is OVERDUE for refresh ({days_since} days old). Safe harbor protection may be compromised.",
                "last_refresh": refresh_info["refreshed_at"],
                "days_overdue": days_since - 31,
                "action_url": "https://telemarketing.donotcall.gov"
            }
        else:
            return {
                "needs_refresh": True,
                "urgency": "critical",
                "message": f"DNC data is CRITICALLY OUTDATED ({days_since} days old). Immediate refresh required!",
                "last_refresh": refresh_info["refreshed_at"],
                "days_overdue": days_since - 31,
                "action_url": "https://telemarketing.donotcall.gov"
            }
    except Exception as e:
        logger.error(f"Error checking DNC refresh: {e}")
        return {
            "needs_refresh": True,
            "urgency": "unknown",
            "message": "Unable to determine DNC refresh status. Please verify manually.",
            "error": str(e)
        }

# ============== DEMO REQUEST FORM ==============

class DemoRequestForm(BaseModel):
    name: str
    email: str
    phone: str
    companySize: str

@api_router.post("/demo-requests")
async def submit_demo_request(request: DemoRequestForm):
    """
    Store demo request from homepage form.
    No authentication required - this is for leads visiting the homepage.
    """
    try:
        demo_request = {
            "id": str(uuid.uuid4()),
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "company_size": request.companySize,
            "status": "new",
            "source": "homepage_form",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.demo_requests.insert_one(demo_request)
        
        # Try to send email notification (non-blocking)
        try:
            if notification_service:
                await notification_service.send_email(
                    to_email=os.environ.get("ADMIN_EMAIL", "admin@dialgenix.ai"),
                    subject=f"New Demo Request: {request.name} from {request.companySize} company",
                    html_content=f"""
                    <h2>New Demo Request</h2>
                    <p><strong>Name:</strong> {request.name}</p>
                    <p><strong>Email:</strong> {request.email}</p>
                    <p><strong>Phone:</strong> {request.phone}</p>
                    <p><strong>Company Size:</strong> {request.companySize}</p>
                    <p><strong>Submitted:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
                    """
                )
        except Exception as e:
            logger.warning(f"Failed to send demo request notification: {e}")
        
        return {"success": True, "message": "Demo request submitted successfully"}
    
    except Exception as e:
        logger.error(f"Failed to store demo request: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit demo request")


# ============== CALL YOURSELF DEMO FEATURE ==============

class DemoCallRequest(BaseModel):
    phone_number: str  # User's own phone number to call

@api_router.post("/demo/call-yourself")
async def call_yourself_demo(
    request: DemoCallRequest,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Let users experience the AI by calling their own phone.
    This is a low-cost way to demonstrate the AI quality without burning leads.
    Cost: ~$0.50 per demo call
    """
    user_id = current_user["user_id"]
    
    # Check if user already used their demo call (limit 2 per user)
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    demo_calls_used = user.get("demo_calls_used", 0)
    MAX_DEMO_CALLS = 2
    
    if demo_calls_used >= MAX_DEMO_CALLS:
        raise HTTPException(
            status_code=400, 
            detail=f"You've already used your {MAX_DEMO_CALLS} free demo calls. Subscribe to make more calls!"
        )
    
    # Validate phone number format
    phone = request.phone_number.strip()
    if not phone.startswith("+"):
        phone = "+1" + phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    
    if not twilio_client:
        raise HTTPException(status_code=503, detail="Calling service not configured. Please add TWILIO credentials.")
    
    try:
        # Get the base URL for webhooks
        host = http_request.headers.get("host", "")
        protocol = "https" if "https" in str(http_request.url) or "preview" in host or "dialgenix" in host else "http"
        base_url = f"{protocol}://{host}"
        
        # Create a demo call record
        demo_call_id = str(uuid.uuid4())
        
        # Make the call with demo TwiML
        call = twilio_client.calls.create(
            to=phone,
            from_=twilio_phone_number,
            url=f"{base_url}/api/demo/twiml/{demo_call_id}",
            status_callback=f"{base_url}/api/twilio/status",
            status_callback_event=["completed"],
            timeout=30
        )
        
        # Update user's demo call count
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"demo_calls_used": 1}}
        )
        
        # Log the demo call
        await db.demo_calls.insert_one({
            "id": demo_call_id,
            "user_id": user_id,
            "phone_number": phone,
            "twilio_sid": call.sid,
            "status": "initiated",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Demo call initiated for user {user_id} to {phone}")
        
        return {
            "success": True,
            "message": "Demo call initiated! Your phone will ring in a few seconds.",
            "call_id": demo_call_id,
            "demo_calls_remaining": MAX_DEMO_CALLS - demo_calls_used - 1
        }
        
    except Exception as e:
        logger.error(f"Demo call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate demo call: {str(e)}")

@api_router.api_route("/demo/twiml/{demo_call_id}", methods=["GET", "POST"])
async def demo_call_twiml(demo_call_id: str, http_request: Request):
    """Generate TwiML for the demo call - uses ElevenLabs voice"""
    response = VoiceResponse()
    
    # Get the host for audio URL
    host = http_request.headers.get("host", "dialgenix.ai")
    protocol = "https" if "dialgenix" in host or "preview" in host else "http"
    base_url = f"{protocol}://{host}"
    
    # Play pre-generated ElevenLabs audio for the demo
    response.play(f"{base_url}/api/demo/audio/{demo_call_id}")
    
    return Response(content=str(response), media_type="application/xml")


# Cache for demo audio to avoid regenerating each time
_demo_audio_cache = None

@api_router.get("/demo/audio/{demo_call_id}")
async def demo_audio(demo_call_id: str):
    """Generate ElevenLabs audio for the demo call - cached for speed"""
    global _demo_audio_cache
    
    # Return cached audio if available
    if _demo_audio_cache:
        return Response(content=_demo_audio_cache, media_type="audio/mpeg")
    
    demo_script = """Hey! This is Sarah from DialGenix... Glad you picked up!

I know what you're thinking— great, another sales call, right? 

But here's the twist... I'm actually an AI. Yeah— a real-time AI, having a natural conversation with you, right now.

And this? This is exactly what DialGenix lets you do.

Imagine having AI agents like me— making hundreds of calls for your business, every single day. No breaks. No missed follow-ups. No awkward pauses.

We can qualify your leads, handle objections, and even book meetings straight onto your calendar— all while sounding completely human.

You can even clone your own voice... or choose the exact tone you want. Plug in your scripts, use your proven rebuttals— so every call feels like your best salesperson is on the line.

And the best part? You can try it yourself, right now. Just head back to your dashboard and launch your first AI agent. It takes about five minutes.

Pretty cool, right?

Anyway— I'll let you get back to it. Talk soon!"""

    try:
        # Use Rachel voice - American English female (same as homepage)
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - American female
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": elevenlabs_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": demo_script,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                # Cache the audio for future calls
                _demo_audio_cache = response.content
                return Response(content=response.content, media_type="audio/mpeg")
            else:
                logger.error(f"ElevenLabs error: {response.status_code} - {response.text}")
                return Response(content=b"", media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Demo audio generation failed: {e}")
        return Response(content=b"", media_type="audio/mpeg")


@api_router.get("/demo/calls-remaining")
async def get_demo_calls_remaining(current_user: Dict = Depends(get_current_user)):
    """Check how many demo calls the user has remaining"""
    user = await db.users.find_one({"user_id": current_user["user_id"]})
    if not user:
        demo_calls_used = 0
    else:
        demo_calls_used = user.get("demo_calls_used", 0)
    MAX_DEMO_CALLS = 2
    
    return {
        "demo_calls_used": demo_calls_used,
        "demo_calls_remaining": max(0, MAX_DEMO_CALLS - demo_calls_used),
        "max_demo_calls": MAX_DEMO_CALLS
    }

# ============== END CALL YOURSELF DEMO ==============

class RealCallRequest(BaseModel):
    lead_id: str
    campaign_id: str

@api_router.post("/calls/initiate")
async def initiate_real_call(
    request: RealCallRequest,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Initiate a REAL AI call via Twilio (requires Twilio credentials).
    Includes full compliance checks before calling.
    Trial users: deducts from trial time (tracked on call completion).
    Paid users: deducts call credits upfront.
    """
    if not twilio_service.is_configured:
        raise HTTPException(
            status_code=503, 
            detail="Twilio not configured. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to .env"
        )
    
    user_id = current_user["user_id"]
    
    # Check trial status first
    trial_status = get_trial_status(current_user)
    
    # Check phone verification (required for all trial users)
    if trial_status["is_trial"] and not current_user.get("phone_verified", False):
        raise HTTPException(
            status_code=403,
            detail="Phone verification required. Please verify your phone number to use your free trial."
        )
    
    if trial_status["is_trial"]:
        # Trial user - check if they have time remaining
        if trial_status["trial_expired"] or not trial_status["can_make_calls"]:
            raise HTTPException(
                status_code=402,
                detail=f"Your free trial has expired. You used {trial_status['minutes_total']} minutes of call time. Please upgrade to continue making calls."
            )
        # Trial users don't pay upfront - time is deducted on call completion
    else:
        # Paid user - check call credits
        calls_remaining = current_user.get("call_credits_remaining", 0)
        if calls_remaining < 1:
            raise HTTPException(status_code=402, detail="Insufficient call credits")
        
        # Deduct call credit for paid users
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"call_credits_remaining": -1}}
        )
        
        # Log usage event
        await log_usage_event(
            user_id=user_id,
            event_type="call_made",
            amount=1,
            credits_after=calls_remaining - 1
        )
    
    # Get lead (with user ownership verification)
    lead = await db.leads.find_one({"id": request.lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    phone_number = lead.get("phone")
    if not phone_number:
        raise HTTPException(status_code=400, detail="Lead has no phone number")
    
    # Get campaign (with user ownership verification)
    campaign = await db.campaigns.find_one({"id": request.campaign_id, "user_id": user_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Run compliance checks
    compliance_result = await compliance_service.pre_call_compliance_check(
        phone_number=phone_number,
        user_id=user_id
    )
    
    if not compliance_result["is_allowed"]:
        # Refund credit if paid user and call blocked
        if not trial_status["is_trial"]:
            await db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"call_credits_remaining": 1}}
            )
        return {
            "status": "blocked",
            "message": "Call blocked by compliance checks",
            "reasons": compliance_result["reasons"]
        }
    
    # Create call record with user_id
    call = Call(
        user_id=user_id,
        lead_id=request.lead_id,
        campaign_id=request.campaign_id,
        status=CallStatus.PENDING,
        started_at=datetime.now(timezone.utc).isoformat()
    )
    await db.calls.insert_one(call.model_dump())
    
    # Get callback URL
    callback_url = str(http_request.base_url).rstrip("/")
    
    # Check if campaign has voicemail enabled (use AMD)
    use_amd = campaign.get("voicemail_enabled", True)
    
    try:
        if use_amd:
            # Use AMD-enabled call (detects human vs voicemail)
            twilio_result = await twilio_service.make_outbound_call_with_amd(
                to_number=phone_number,
                lead=lead,
                campaign=campaign,
                callback_url=callback_url,
                call_id=call.id
            )
        else:
            # Legacy call without AMD
            twilio_result = await twilio_service.make_outbound_call(
                to_number=phone_number,
                lead=lead,
                campaign=campaign,
                callback_url=callback_url
            )
        
        # Update call record with Twilio SID
        await db.calls.update_one(
            {"id": call.id},
            {"$set": {
                "twilio_sid": twilio_result["call_sid"],
                "status": CallStatus.IN_PROGRESS.value
            }}
        )
        
        response_data = {
            "status": "initiated",
            "call_id": call.id,
            "twilio_sid": twilio_result["call_sid"],
            "message": "Call initiated successfully",
            "amd_enabled": use_amd
        }
        
        if trial_status["is_trial"]:
            response_data["trial_minutes_remaining"] = trial_status["minutes_remaining"]
            response_data["is_trial"] = True
        else:
            response_data["credits_remaining"] = current_user.get("call_credits_remaining", 0) - 1
        
        return response_data
        
    except Exception as e:
        # Refund the credit if call failed to initiate (paid users only)
        if not trial_status["is_trial"]:
            await db.users.update_one(
                {"user_id": current_user["user_id"]},
                {"$inc": {"call_credits_remaining": 1}}
            )
        await db.calls.update_one(
            {"id": call.id},
            {"$set": {"status": CallStatus.FAILED.value, "error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

# Twilio Webhook Endpoints (called by Twilio)
@api_router.post("/twilio/voice/{lead_id}/{campaign_id}")
async def twilio_voice_webhook(lead_id: str, campaign_id: str, request: Request):
    """
    Twilio webhook called when call connects.
    Returns TwiML for AI greeting with compliance disclosure.
    """
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    
    if not lead or not campaign:
        response = VoiceResponse()
        response.say("Sorry, there was an error. Goodbye.", voice='Polly.Joanna')
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    
    twiml = twilio_service.generate_ai_greeting_twiml(lead, campaign)
    return Response(content=twiml, media_type="application/xml")

@api_router.post("/twilio/gather")
async def twilio_gather_webhook(request: Request):
    """Handle speech/DTMF input from the call"""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "")
    digits = form_data.get("Digits", "")  # noqa: F841 - may be used for DTMF
    
    response = VoiceResponse()
    
    # Check for DNC request keywords
    dnc_keywords = ["stop", "remove", "don't call", "do not call", "unsubscribe", "no thanks"]
    if any(keyword in speech_result.lower() for keyword in dnc_keywords):
        # Add to DNC and end call
        to_number = form_data.get("To", "")
        if to_number:
            await compliance_service.add_to_dnc(to_number, reason="user_request")
        
        response.say(
            "No problem at all. I've removed your number from our list. Have a great day!",
            voice='Polly.Joanna'
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    
    # Check for interest
    interest_keywords = ["yes", "sure", "okay", "tell me more", "interested"]
    if any(keyword in speech_result.lower() for keyword in interest_keywords):
        # Continue conversation - this would integrate with AI for dynamic responses
        response.say(
            "Great! We help businesses increase their profits through our innovative solution. "
            "Would you be the right person to discuss this with, or should I speak with someone else?",
            voice='Polly.Joanna'
        )
        
        gather = Gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/api/twilio/qualify',
            method='POST'
        )
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    # Default: ask for clarification
    response.say(
        "I'm sorry, I didn't quite catch that. Are you interested in learning more about how we can help your business?",
        voice='Polly.Joanna'
    )
    
    gather = Gather(
        input='speech dtmf',
        timeout=5,
        speech_timeout='auto',
        action='/api/twilio/gather',
        method='POST'
    )
    gather.say("Press 1 for yes, or say not interested to opt out.", voice='Polly.Joanna')
    response.append(gather)
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/qualify")
async def twilio_qualify_webhook(request: Request):
    """Handle qualification responses"""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "")
    
    response = VoiceResponse()
    
    # Check if they're the decision maker
    decision_maker_keywords = ["yes", "i am", "that's me", "correct"]
    if any(keyword in speech_result.lower() for keyword in decision_maker_keywords):
        response.say(
            "Perfect! I'd love to set up a quick 15-minute call with one of our specialists "
            "who can show you exactly how this works. Would this week or next week work better for you?",
            voice='Polly.Joanna'
        )
        
        gather = Gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/api/twilio/book',
            method='POST'
        )
        response.append(gather)
    else:
        response.say(
            "No problem. Could you connect me with the person who handles these decisions? "
            "Or I can send some information to their email if you'd prefer.",
            voice='Polly.Joanna'
        )
        
        gather = Gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/api/twilio/gather',
            method='POST'
        )
        response.append(gather)
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/book")
async def twilio_book_webhook(request: Request):
    """Handle booking responses"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    
    response = VoiceResponse()
    
    # In production, this would integrate with calendar booking
    # For now, capture interest and end call positively
    response.say(
        "Excellent! I'll have someone from our team reach out to schedule that call. "
        "They'll send you a calendar invite shortly. Thank you for your time today, and have a great day!",
        voice='Polly.Joanna'
    )
    
    # Update call record as qualified
    if call_sid:
        await db.calls.update_one(
            {"twilio_sid": call_sid},
            {"$set": {
                "qualification_result": {
                    "is_qualified": True,
                    "is_decision_maker": True,
                    "interest_level": 8,
                    "score": 85
                }
            }}
        )
    
    response.hangup()
    return Response(content=str(response), media_type="application/xml")

# ============== INBOUND SALES CALL HANDLER ==============
# Handles incoming calls to the DialGenix.ai sales line (888) 513-1913

# Cache for pre-generated inbound audio
_inbound_audio_cache = {}

async def generate_inbound_audio(text: str, cache_key: str = None) -> str:
    """Generate natural-sounding audio using ElevenLabs for inbound calls.
    Returns a data URI that can be played by Twilio."""
    global _inbound_audio_cache
    
    # Check cache first
    if cache_key and cache_key in _inbound_audio_cache:
        return _inbound_audio_cache[cache_key]
    
    if not elevenlabs_api_key:
        return None
    
    try:
        # Use Rachel voice with natural settings (same as demo call)
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - American female
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": elevenlabs_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.4
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Convert to base64 data URI for Twilio
                import base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                audio_uri = f"data:audio/mpeg;base64,{audio_base64}"
                
                # Cache if key provided
                if cache_key:
                    _inbound_audio_cache[cache_key] = audio_uri
                
                return audio_uri
    except Exception as e:
        logger.error(f"ElevenLabs inbound audio error: {e}")
    
    return None

# Pre-generate common inbound responses on startup
@app.on_event("startup")
async def cache_inbound_audio():
    """Pre-generate common inbound call responses for faster playback."""
    global _inbound_audio_cache
    
    if not elevenlabs_api_key:
        logger.info("No ElevenLabs key, skipping inbound audio cache")
        return
    
    common_responses = {
        "greeting": "Hi, thanks for calling DialGenix! This is Sarah, your AI sales assistant. I can answer questions about our platform, help you understand if we're a good fit, and even book a demo with our team. How can I help you today?",
        "pricing": "Great question! We have flexible plans. Our Starter plan is $199 per month and includes 250 leads and 500 AI calls. Our Pro plan at $499 gives you 1,000 leads and 2,000 calls with advanced features. We also offer a free trial, no credit card required. Would you like me to book a quick demo so our team can walk you through which plan fits your needs?",
        "how_it_works": "Here's how DialGenix works... First, our AI discovers leads by finding businesses actively searching for services like yours. Second, our voice agents call these leads with natural, human-like conversations. Third, the AI qualifies leads based on your criteria. Fourth, qualified leads get booked directly into your calendar. You basically wake up to booked meetings! Would you like to see a demo?",
        "book_demo": "Perfect! I'd love to get you scheduled with one of our product specialists. They can give you a personalized walkthrough. Can you tell me your email address so I can send you a calendar invite?",
        "features": "DialGenix has some powerful features. We offer AI lead discovery, natural voice conversations, voicemail drops, automatic call transcription, CRM integrations with HubSpot and Salesforce, and Calendly integration for auto-booking meetings. Our AI agents can even handle objections and qualify leads. What's most important to you?",
        "not_interested": "No problem at all! Thanks for calling DialGenix. If you ever want to explore AI-powered sales automation, we're here. Have a great day!",
        "default": "I'd be happy to help with that. DialGenix is an AI-powered cold calling platform that automates your sales outreach. Our AI agents can find leads, make calls, qualify prospects, and book meetings for you. Would you like to know about pricing, see how it works, or schedule a demo?",
        "didnt_catch": "I didn't quite catch that. Feel free to ask me anything about DialGenix... pricing, how it works, or if you'd like a demo.",
        "anything_else": "Is there anything else you'd like to know?"
    }
    
    logger.info("Pre-generating inbound call audio with ElevenLabs...")
    for key, text in common_responses.items():
        try:
            await generate_inbound_audio(text, cache_key=f"inbound_{key}")
            logger.info(f"Cached inbound audio: {key}")
        except Exception as e:
            logger.error(f"Failed to cache inbound audio {key}: {e}")
    
    logger.info("Inbound audio caching complete")

# Endpoint to serve cached inbound audio
@api_router.get("/inbound-audio/{audio_key}")
async def serve_inbound_audio(audio_key: str):
    """Serve pre-cached ElevenLabs audio for inbound calls."""
    cache_key = f"inbound_{audio_key}"
    
    if cache_key not in _inbound_audio_cache:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    audio_data = _inbound_audio_cache[cache_key]
    
    # If it's a data URI, extract the base64 content
    if audio_data.startswith("data:audio/mpeg;base64,"):
        import base64
        audio_bytes = base64.b64decode(audio_data.split(",")[1])
        return Response(content=audio_bytes, media_type="audio/mpeg")
    
    return Response(content=audio_data, media_type="audio/mpeg")

@api_router.post("/twilio/inbound")
async def handle_inbound_sales_call(request: Request):
    """
    Handle incoming calls to the DialGenix.ai sales line.
    AI Sales Assistant 'Sarah' answers and qualifies callers.
    """
    form_data = await request.form()
    caller = form_data.get("From", "Unknown")
    call_sid = form_data.get("CallSid", "")
    
    logger.info(f"Inbound sales call from {caller}, SID: {call_sid}")
    
    # Log the inbound call
    await db.inbound_calls.insert_one({
        "call_sid": call_sid,
        "caller_number": caller,
        "status": "answered",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "conversation_stage": "greeting"
    })
    
    response = VoiceResponse()
    
    # Try to use cached ElevenLabs audio, fallback to Polly
    cached_audio = _inbound_audio_cache.get("inbound_greeting")
    if cached_audio and cached_audio.startswith("data:"):
        # For data URI, we need to serve it via an endpoint
        response.play(f"{os.environ.get('BACKEND_URL', '')}/api/inbound-audio/greeting")
    else:
        response.say(
            "Hi, thanks for calling DialGenix! "
            "This is Sarah, your AI sales assistant. "
            "I can answer questions about our platform, help you understand if we're a good fit, "
            "and even book a demo with our team. "
            "How can I help you today?",
            voice='Polly.Joanna-Neural'
        )
    
    # Gather caller's response
    gather = Gather(
        input='speech',
        timeout=5,
        speech_timeout='auto',
        action='/api/twilio/inbound/respond',
        method='POST'
    )
    response.append(gather)
    
    # Fallback if no response
    response.say("I didn't catch that. Feel free to ask me anything about DialGenix.", voice='Polly.Joanna-Neural')
    response.redirect('/api/twilio/inbound')
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/inbound/respond")
async def handle_inbound_response(request: Request):
    """Handle caller's response and provide appropriate information."""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "").lower()
    call_sid = form_data.get("CallSid", "")
    caller = form_data.get("From", "Unknown")
    
    logger.info(f"Inbound caller said: {speech_result}")
    
    response = VoiceResponse()
    backend_url = os.environ.get('BACKEND_URL', '')
    
    # Update conversation log
    await db.inbound_calls.update_one(
        {"call_sid": call_sid},
        {"$push": {"conversation": {"caller": speech_result, "timestamp": datetime.now(timezone.utc).isoformat()}}}
    )
    
    # Helper to play cached audio or fallback to Polly
    def play_or_say(audio_key: str, fallback_text: str):
        if f"inbound_{audio_key}" in _inbound_audio_cache:
            response.play(f"{backend_url}/api/inbound-audio/{audio_key}")
        else:
            response.say(fallback_text, voice='Polly.Joanna-Neural')
    
    # Pricing questions
    if any(word in speech_result for word in ["price", "cost", "pricing", "how much", "expensive", "afford"]):
        play_or_say("pricing", 
            "Great question! We have flexible plans. "
            "Our Starter plan is $199 per month and includes 250 leads and 500 AI calls. "
            "Our Pro plan at $499 gives you 1,000 leads and 2,000 calls with advanced features. "
            "We also offer a free trial, no credit card required. "
            "Would you like me to book a quick demo so our team can walk you through which plan fits your needs?"
        )
    
    # How it works
    elif any(word in speech_result for word in ["how", "work", "what do", "tell me", "explain", "more"]):
        play_or_say("how_it_works",
            "Here's how DialGenix works... "
            "First, our AI discovers leads by finding businesses actively searching for services like yours. "
            "Second, our voice agents call these leads with natural, human-like conversations. "
            "Third, the AI qualifies leads based on your criteria. "
            "Fourth, qualified leads get booked directly into your calendar. "
            "You basically wake up to booked meetings! Would you like to see a demo?"
        )
    
    # Demo / meeting request
    elif any(word in speech_result for word in ["demo", "meeting", "schedule", "book", "yes", "sure", "okay", "interested"]):
        play_or_say("book_demo",
            "Perfect! I'd love to get you scheduled with one of our product specialists. "
            "They can give you a personalized walkthrough. "
            "Can you tell me your email address so I can send you a calendar invite?"
        )
        
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action='/api/twilio/inbound/capture-email',
            method='POST'
        )
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    # Features
    elif any(word in speech_result for word in ["feature", "can it", "does it", "integration", "crm", "calendly"]):
        play_or_say("features",
            "DialGenix has some powerful features. "
            "We offer AI lead discovery, natural voice conversations, voicemail drops, "
            "automatic call transcription, CRM integrations with HubSpot and Salesforce, "
            "and Calendly integration for auto-booking meetings. "
            "Our AI agents can even handle objections and qualify leads. "
            "What's most important to you?"
        )
    
    # Not interested / end call
    elif any(word in speech_result for word in ["not interested", "no thanks", "goodbye", "bye", "no"]):
        play_or_say("not_interested",
            "No problem at all! Thanks for calling DialGenix. "
            "If you ever want to explore AI-powered sales automation, we're here. "
            "Have a great day!"
        )
        response.hangup()
        
        await db.inbound_calls.update_one(
            {"call_sid": call_sid},
            {"$set": {"status": "completed", "outcome": "not_interested", "ended_at": datetime.now(timezone.utc).isoformat()}}
        )
        return Response(content=str(response), media_type="application/xml")
    
    # Default response
    else:
        play_or_say("default",
            "I'd be happy to help with that. "
            "DialGenix is an AI-powered cold calling platform that automates your sales outreach. "
            "Our AI agents can find leads, make calls, qualify prospects, and book meetings for you. "
            "Would you like to know about pricing, see how it works, or schedule a demo?"
        )
    
    # Continue conversation
    gather = Gather(
        input='speech',
        timeout=5,
        speech_timeout='auto',
        action='/api/twilio/inbound/respond',
        method='POST'
    )
    response.append(gather)
    
    play_or_say("anything_else", "Is there anything else you'd like to know?")
    response.redirect('/api/twilio/inbound/respond')
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/inbound/capture-email")
async def capture_caller_email(request: Request):
    """Capture caller's email for demo booking."""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "")
    call_sid = form_data.get("CallSid", "")
    caller = form_data.get("From", "Unknown")
    
    logger.info(f"Caller email attempt: {speech_result}")
    
    response = VoiceResponse()
    
    # Try to parse email from speech
    email_attempt = speech_result.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
    
    # Save the lead info
    await db.inbound_calls.update_one(
        {"call_sid": call_sid},
        {"$set": {
            "email_captured": email_attempt,
            "status": "demo_requested",
            "outcome": "hot_lead",
            "ended_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Also save as a lead
    await db.inbound_leads.insert_one({
        "phone": caller,
        "email": email_attempt,
        "source": "inbound_call",
        "status": "demo_requested",
        "call_sid": call_sid,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.say(
        f"I've noted your email. "
        "Our team will send you a calendar invite shortly with available demo times. "
        "You'll also receive an email with information about DialGenix and a link to start your free trial. "
        "Is there anything else I can help you with before we wrap up?",
        voice='Polly.Joanna'
    )
    
    gather = Gather(
        input='speech',
        timeout=5,
        speech_timeout='auto',
        action='/api/twilio/inbound/final',
        method='POST'
    )
    response.append(gather)
    
    response.say(
        "Thanks for calling DialGenix.ai! We're excited to show you how we can automate your sales outreach. Have a fantastic day!",
        voice='Polly.Joanna'
    )
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/inbound/final")
async def handle_final_response(request: Request):
    """Handle final response before ending call."""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "").lower()
    call_sid = form_data.get("CallSid", "")
    
    response = VoiceResponse()
    
    if any(word in speech_result for word in ["yes", "question", "actually", "one more"]):
        response.say("Sure, what else would you like to know?", voice='Polly.Joanna')
        
        gather = Gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/api/twilio/inbound/respond',
            method='POST'
        )
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    response.say(
        "Thanks for calling DialGenix.ai! We're excited to help you automate your sales outreach. Have a fantastic day!",
        voice='Polly.Joanna'
    )
    response.hangup()
    
    await db.inbound_calls.update_one(
        {"call_sid": call_sid},
        {"$set": {"status": "completed", "ended_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/status")
async def twilio_status_webhook(request: Request):
    """Handle call status updates from Twilio"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    duration = form_data.get("CallDuration", "0")
    
    logger.info(f"Twilio status update: {call_sid} -> {call_status}")
    
    # Map Twilio status to our status
    status_map = {
        "queued": CallStatus.PENDING.value,
        "ringing": CallStatus.PENDING.value,
        "in-progress": CallStatus.IN_PROGRESS.value,
        "completed": CallStatus.COMPLETED.value,
        "busy": CallStatus.NO_ANSWER.value,
        "no-answer": CallStatus.NO_ANSWER.value,
        "canceled": CallStatus.FAILED.value,
        "failed": CallStatus.FAILED.value
    }
    
    new_status = status_map.get(call_status, CallStatus.FAILED.value)
    call_duration_seconds = int(duration) if duration else 0
    
    update_data = {
        "status": new_status,
        "duration": call_duration_seconds,
        "ended_at": datetime.now(timezone.utc).isoformat() if call_status in ["completed", "busy", "no-answer", "canceled", "failed"] else None
    }
    
    await db.calls.update_one(
        {"twilio_sid": call_sid},
        {"$set": update_data}
    )
    
    # Deduct call duration from trial time (if user is on trial)
    if call_status == "completed" and call_duration_seconds > 0:
        # Get the call record to find the user
        call_record = await db.calls.find_one({"twilio_sid": call_sid}, {"_id": 0})
        if call_record and call_record.get("user_id"):
            user = await db.users.find_one({"user_id": call_record["user_id"]}, {"_id": 0})
            if user:
                trial_status = get_trial_status(user)
                if trial_status["is_trial"] and not trial_status["trial_expired"]:
                    # Deduct call duration from trial
                    await deduct_trial_time(user["user_id"], call_duration_seconds)
                    logger.info(f"Deducted {call_duration_seconds}s from trial for user {user['user_id']}")
    
    return {"status": "ok"}

# ============== AMD (Answering Machine Detection) WEBHOOKS ==============

@api_router.post("/twilio/amd-handler/{call_id}")
async def twilio_amd_initial_handler(call_id: str, request: Request):
    """
    Initial TwiML handler for calls with AMD enabled.
    This is called when the call connects, while AMD is still analyzing.
    We play a brief pause while AMD determines human vs machine.
    """
    response = VoiceResponse()
    
    # Brief pause while AMD analyzes (async AMD will callback separately)
    # This prevents awkward silence - we play hold music or a brief message
    response.pause(length=2)
    
    # If AMD hasn't determined yet, say something generic
    # (The real handling happens in the AMD callback)
    response.say(
        "Please hold for just a moment.",
        voice='Polly.Matthew-Neural'
    )
    response.pause(length=10)  # Wait for AMD callback to potentially redirect
    
    return Response(content=str(response), media_type="application/xml")

@api_router.post("/twilio/amd/{call_id}")
async def twilio_amd_callback(call_id: str, request: Request):
    """
    Callback from Twilio's Async AMD with detection result.
    This is where we decide to either:
    - Drop voicemail (if machine detected)
    - Connect to AI conversation (if human detected)
    
    AMD AnsweredBy values:
    - "human": Human answered
    - "machine_start": Machine detected, voicemail playing
    - "machine_end_beep": Machine voicemail ended with beep
    - "machine_end_silence": Machine voicemail ended with silence
    - "machine_end_other": Machine voicemail ended other way
    - "fax": Fax machine detected
    - "unknown": Could not determine
    """
    form_data = await request.form()
    
    call_sid = form_data.get("CallSid", "")
    answered_by = form_data.get("AnsweredBy", "unknown")
    machine_detection_duration = form_data.get("MachineDetectionDuration", "0")
    
    logger.info(f"AMD callback for call {call_id}: AnsweredBy={answered_by}, Duration={machine_detection_duration}ms")
    
    # Get call and campaign info
    call_record = await db.calls.find_one({"id": call_id}, {"_id": 0})
    if not call_record:
        logger.error(f"Call record not found for AMD callback: {call_id}")
        return {"status": "error", "message": "Call not found"}
    
    lead = await db.leads.find_one({"id": call_record["lead_id"]}, {"_id": 0})
    campaign = await db.campaigns.find_one({"id": call_record["campaign_id"]}, {"_id": 0})
    
    # Update call record with AMD result
    await db.calls.update_one(
        {"id": call_id},
        {"$set": {
            "answered_by": answered_by,
            "amd_status": answered_by,
            "amd_duration_ms": int(machine_detection_duration) if machine_detection_duration else 0
        }}
    )
    
    # Determine action based on AMD result
    is_machine = answered_by in ["machine_start", "machine_end_beep", "machine_end_silence", "machine_end_other"]
    is_human = answered_by == "human"
    
    if is_machine and campaign and campaign.get("voicemail_enabled", True):
        # MACHINE DETECTED - Drop voicemail
        logger.info(f"Machine detected for call {call_id}, dropping voicemail")
        
        # Update call to redirect to voicemail TwiML
        try:
            twilio_client.calls(call_sid).update(
                twiml=twilio_service.generate_voicemail_twiml(lead or {}, campaign)
            )
            
            # Mark as voicemail dropped
            await db.calls.update_one(
                {"id": call_id},
                {"$set": {"voicemail_dropped": True}}
            )
            
            logger.info(f"Voicemail dropped for call {call_id}")
            
        except Exception as e:
            logger.error(f"Failed to drop voicemail for call {call_id}: {e}")
    
    elif is_human:
        # HUMAN DETECTED - Connect to AI conversation
        logger.info(f"Human detected for call {call_id}, connecting to AI")
        
        try:
            twilio_client.calls(call_sid).update(
                twiml=twilio_service.generate_human_twiml(lead or {}, campaign or {}, call_id)
            )
            
        except Exception as e:
            logger.error(f"Failed to connect human to AI for call {call_id}: {e}")
    
    else:
        # UNKNOWN or FAX - Just log and let call continue
        logger.warning(f"Unknown AMD result for call {call_id}: {answered_by}")
    
    return {"status": "ok", "answered_by": answered_by, "action": "voicemail" if is_machine else "ai_conversation"}

@api_router.get("/calls/{call_id}/amd-status")
async def get_call_amd_status(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get AMD status for a specific call"""
    # Multi-tenancy: Only access calls belonging to current user
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return {
        "call_id": call_id,
        "answered_by": call.get("answered_by"),
        "voicemail_dropped": call.get("voicemail_dropped", False),
        "amd_status": call.get("amd_status"),
        "amd_duration_ms": call.get("amd_duration_ms")
    }

# ============== CALL RECORDING & TRANSCRIPTION ENDPOINTS ==============

@api_router.get("/calls/{call_id}/recording")
async def get_call_recording(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get call recording details and playback URL.
    Requires Starter tier or higher.
    """
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("call_recording"):
        raise HTTPException(
            status_code=403,
            detail="Call recording requires Starter plan or higher."
        )
    
    # Get call (with user ownership verification)
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.get("recording_url"):
        raise HTTPException(status_code=404, detail="No recording available for this call")
    
    return {
        "call_id": call_id,
        "recording_url": call.get("recording_url"),
        "recording_duration_seconds": call.get("recording_duration_seconds"),
        "recording_sid": call.get("recording_sid"),
        "transcription_status": call.get("transcription_status"),
        "has_transcript": bool(call.get("full_transcript"))
    }

@api_router.get("/calls/{call_id}/transcript")
async def get_call_transcript(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get call transcript (full text and timestamped segments).
    Requires Professional tier or higher.
    """
    # Check feature access
    features = get_tier_features(current_user)
    if not features.get("call_transcription"):
        raise HTTPException(
            status_code=403,
            detail="Call transcription requires Professional plan or higher."
        )
    
    # Get call (with user ownership verification)
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.get("full_transcript"):
        if call.get("transcription_status") == "processing":
            return {
                "call_id": call_id,
                "status": "processing",
                "message": "Transcript is being generated. Please check back shortly."
            }
        elif call.get("transcription_status") == "failed":
            raise HTTPException(status_code=500, detail="Transcription failed. Please try again.")
        else:
            raise HTTPException(status_code=404, detail="No transcript available for this call")
    
    return {
        "call_id": call_id,
        "full_transcript": call.get("full_transcript"),
        "segments": call.get("transcript_segments", []),
        "duration_seconds": call.get("duration_seconds"),
        "status": "completed"
    }

@api_router.post("/calls/{call_id}/transcribe")
async def request_transcription(
    call_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Request transcription for a call recording.
    Useful if automatic transcription failed or was not triggered.
    """
    features = get_tier_features(current_user)
    if not features.get("call_transcription"):
        raise HTTPException(
            status_code=403,
            detail="Call transcription requires Professional plan or higher."
        )
    
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.get("recording_sid"):
        raise HTTPException(status_code=400, detail="No recording available for this call")
    
    if call.get("transcription_status") == "processing":
        return {"message": "Transcription already in progress", "status": "processing"}
    
    # Process in background
    background_tasks.add_task(
        recording_service.process_call_recording,
        call_id,
        current_user["user_id"],
        call["recording_sid"],
        features
    )
    
    return {
        "message": "Transcription requested",
        "call_id": call_id,
        "status": "queued"
    }

@api_router.get("/calls/{call_id}/recording/stream")
async def stream_call_recording(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Stream call recording audio for playback.
    Returns audio file directly.
    """
    features = get_tier_features(current_user)
    if not features.get("call_recording"):
        raise HTTPException(
            status_code=403,
            detail="Call recording requires Starter plan or higher."
        )
    
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    recording_path = call.get("recording_url")
    if not recording_path:
        raise HTTPException(status_code=404, detail="No recording available")
    
    # Get from object storage
    result = await asyncio.to_thread(get_object, recording_path)
    if not result:
        raise HTTPException(status_code=404, detail="Recording file not found")
    
    audio_data, content_type = result
    
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{call_id}.mp3"',
            "Accept-Ranges": "bytes"
        }
    )

@api_router.post("/twilio/recording")
async def twilio_recording_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle recording status updates from Twilio.
    Automatically triggers storage and transcription based on user's tier.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    recording_sid = form_data.get("RecordingSid", "")
    recording_duration = form_data.get("RecordingDuration", "0")
    recording_status = form_data.get("RecordingStatus", "")
    
    logger.info(f"Twilio recording webhook: call={call_sid}, status={recording_status}, sid={recording_sid}")
    
    if recording_status == "completed" and recording_sid:
        # Find the call by Twilio SID
        call = await db.calls.find_one({"twilio_sid": call_sid}, {"_id": 0})
        
        if call:
            # Update call with recording info
            await db.calls.update_one(
                {"twilio_sid": call_sid},
                {"$set": {
                    "recording_sid": recording_sid,
                    "recording_duration_seconds": int(recording_duration),
                    "transcription_status": "pending"
                }}
            )
            
            # Get user to check tier features
            user = await db.users.find_one({"user_id": call.get("user_id")}, {"_id": 0})
            if user:
                features = get_tier_features(user)
                
                # Process recording in background (store + transcribe based on tier)
                background_tasks.add_task(
                    recording_service.process_call_recording,
                    call["id"],
                    call["user_id"],
                    recording_sid,
                    features
                )
            
            logger.info(f"Recording queued for processing: call={call['id']}, sid={recording_sid}")
        else:
            logger.warning(f"Call not found for Twilio SID: {call_sid}")
    
    return {"status": "received"}
    
    return {"status": "ok"}

# ----- Real-Time AI Calling (Synthflow-style) -----

# Store active call contexts for Media Streams
active_media_streams: Dict[str, Dict] = {}

class RealtimeCallRequest(BaseModel):
    lead_id: str
    campaign_id: str
    mode: str = "realtime"  # "realtime" for AI conversation, "simple" for scripted

@api_router.post("/calls/realtime")
async def initiate_realtime_call(
    request: RealtimeCallRequest,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Initiate a REAL-TIME AI call using Twilio Media Streams.
    The AI will have a dynamic conversation with the caller.
    """
    if not twilio_service.is_configured:
        raise HTTPException(status_code=503, detail="Twilio not configured")
    
    # Check credits
    if current_user.get("call_credits_remaining", 0) < 1:
        raise HTTPException(status_code=402, detail="Insufficient call credits")
    
    user_id = current_user["user_id"]
    
    # Get lead and campaign (with user ownership verification)
    lead = await db.leads.find_one({"id": request.lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    campaign = await db.campaigns.find_one({"id": request.campaign_id, "user_id": user_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    phone_number = lead.get("phone")
    if not phone_number:
        raise HTTPException(status_code=400, detail="Lead has no phone number")
    
    # Compliance check
    compliance = await compliance_service.pre_call_compliance_check(phone_number, user_id)
    if not compliance["is_allowed"]:
        return {"status": "blocked", "reasons": compliance["reasons"]}
    
    # Deduct credit
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"call_credits_remaining": -1}}
    )
    
    # Create call record with user_id
    call = Call(
        user_id=user_id,
        lead_id=request.lead_id,
        campaign_id=request.campaign_id,
        status=CallStatus.PENDING
    )
    await db.calls.insert_one(call.model_dump())
    
    # Store context for WebSocket handler
    active_media_streams[call.id] = {
        "lead": lead,
        "campaign": campaign,
        "user_id": user_id
    }
    
    # Get callback URL (must be wss:// for Media Streams)
    # IMPORTANT: Use the external URL that Twilio can reach, not the internal request URL
    # The external URL comes from frontend .env or an explicit backend env var
    external_url = os.environ.get('EXTERNAL_URL') or os.environ.get('REACT_APP_BACKEND_URL')
    if not external_url:
        # Fallback to request base_url but this may not work if behind a proxy
        external_url = str(http_request.base_url).rstrip("/")
        logger.warning(f"No EXTERNAL_URL configured, using request base: {external_url}")
    
    callback_url = external_url.rstrip("/")
    ws_url = callback_url.replace("https://", "wss://").replace("http://", "ws://")
    
    try:
        # Create TwiML that connects to Media Streams
        response = VoiceResponse()
        
        # Compliance disclosure first (required)
        company = campaign.get('company_name', 'our company')
        response.say(
            f"Hi, this is an AI assistant calling on behalf of {company}. This is an automated business call.",
            voice='Polly.Matthew-Neural'
        )
        response.pause(length=1)
        
        # Connect to Media Stream for real-time conversation
        connect = Connect()
        stream = Stream(url=f"{ws_url}/api/media-stream/{call.id}")
        stream.parameter(name="lead_id", value=request.lead_id)
        stream.parameter(name="campaign_id", value=request.campaign_id)
        connect.append(stream)
        response.append(connect)
        
        # Make the call with TwiML
        twilio_call = twilio_client.calls.create(
            to=phone_number,
            from_=twilio_phone_number,
            twiml=str(response),
            status_callback=f"{callback_url}/api/twilio/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            record=True
        )
        
        await db.calls.update_one(
            {"id": call.id},
            {"$set": {"twilio_sid": twilio_call.sid, "status": CallStatus.IN_PROGRESS.value}}
        )
        
        return {
            "status": "initiated",
            "call_id": call.id,
            "twilio_sid": twilio_call.sid,
            "mode": "realtime",
            "message": "Real-time AI call initiated"
        }
        
    except Exception as e:
        # Refund credit
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$inc": {"call_credits_remaining": 1}}
        )
        active_media_streams.pop(call.id, None)
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@app.websocket("/api/media-stream/{call_id}")
async def media_stream_websocket(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for Twilio Media Streams.
    Handles real-time AI conversation.
    """
    await websocket.accept()
    
    context = active_media_streams.get(call_id)
    if not context:
        logger.error(f"No context found for call {call_id}")
        await websocket.close()
        return
    
    lead = context["lead"]
    campaign = context["campaign"]
    user_id = context.get("user_id")
    stream_sid = None
    
    # Conversation state
    messages = []
    is_first_response = True
    audio_buffer = b""
    
    # Silence detection state
    consecutive_silence_count = 0
    MAX_CONSECUTIVE_SILENCE = 3  # Hang up after 3 no-responses
    last_response_time = asyncio.get_event_loop().time()
    MAX_CALL_DURATION = 600  # 10 minute hard cap
    call_start_time = asyncio.get_event_loop().time()
    
    logger.info(f"Media stream connected for call {call_id}")
    
    try:
        while True:
            # Check max call duration
            if asyncio.get_event_loop().time() - call_start_time > MAX_CALL_DURATION:
                logger.info(f"Call {call_id} hit max duration, ending call")
                if stream_sid:
                    await send_tts_to_stream(
                        websocket, stream_sid,
                        "I've really enjoyed our conversation! I'm at my time limit for this call. "
                        "Would you like me to book a meeting for you, or have one of our agents call you back? "
                        "Either way, I'll make sure someone follows up with you soon. Have a great day!"
                    )
                    await asyncio.sleep(5)
                    
                    # Schedule follow-up
                    if user_id:
                        await auto_schedule_followup(call_id, "max_duration_callback", user_id)
                break
            
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")
            
            if event == "connected":
                logger.info(f"Media stream connected: {message}")
                
            elif event == "start":
                # Twilio start event - get the streamSid
                stream_sid = message.get("streamSid")
                start_data = message.get("start", {})
                
                # Handle both formats: top-level and nested in start object
                if not stream_sid:
                    stream_sid = start_data.get("streamSid")
                
                logger.info(f"Media stream started: {stream_sid}")
                
                # Send initial AI greeting
                if is_first_response and stream_sid:
                    is_first_response = False
                    business = lead.get('business_name', 'your company')
                    greeting = f"Am I speaking with someone at {business}? I'm reaching out because we help businesses increase their profits with solutions most companies overlook. Do you have a moment?"
                    
                    # Generate and send TTS
                    await send_tts_to_stream(websocket, stream_sid, greeting)
                    last_response_time = asyncio.get_event_loop().time()
                
            elif event == "media":
                # Receive audio from caller
                payload = message["media"]["payload"]
                audio_chunk = base64.b64decode(payload)
                audio_buffer += audio_chunk
                
                # Process when we have ~2 seconds of audio (for better transcription)
                if len(audio_buffer) >= 16000:
                    # In production, use Deepgram or AssemblyAI for real-time transcription
                    # For now, we'll use a simplified approach
                    transcript = await transcribe_audio_chunk(audio_buffer)
                    
                    if transcript and len(transcript.strip()) > 2:
                        # Reset silence counter - we got a response!
                        consecutive_silence_count = 0
                        last_response_time = asyncio.get_event_loop().time()
                        logger.info(f"Caller: {transcript}")
                        
                        # Check for DNC
                        if any(kw in transcript.lower() for kw in ["stop", "remove", "don't call"]):
                            await send_tts_to_stream(
                                websocket, stream_sid,
                                "No problem. I'll remove you from our list. Have a great day!"
                            )
                            phone = lead.get("phone")
                            if phone:
                                await compliance_service.add_to_dnc(phone, "user_request")
                            await asyncio.sleep(3)
                            break
                        
                        # Generate AI response
                        ai_response = await generate_sales_response(transcript, messages, lead, campaign)
                        logger.info(f"AI: {ai_response}")
                        
                        messages.append({"role": "user", "content": transcript})
                        messages.append({"role": "assistant", "content": ai_response})
                        
                        await send_tts_to_stream(websocket, stream_sid, ai_response)
                    else:
                        # No speech detected - check for silence timeout
                        time_since_response = asyncio.get_event_loop().time() - last_response_time
                        if time_since_response > 4:  # 4 seconds of silence
                            consecutive_silence_count += 1
                            last_response_time = asyncio.get_event_loop().time()
                            logger.info(f"Silence detected for call {call_id}, count: {consecutive_silence_count}")
                            
                            if consecutive_silence_count >= MAX_CONSECUTIVE_SILENCE:
                                # Too many silences - schedule callback and end call
                                logger.info(f"Call {call_id} - max silence reached, scheduling callback")
                                await send_tts_to_stream(
                                    websocket, stream_sid,
                                    "Sounds like this might not be a good time. I'll give you a call back later. Have a great day!"
                                )
                                await asyncio.sleep(3)
                                
                                # Schedule follow-up call
                                if user_id:
                                    await auto_schedule_followup(call_id, "no_response_callback", user_id)
                                break
                            elif consecutive_silence_count == 1:
                                # First silence - gentle prompt
                                await send_tts_to_stream(websocket, stream_sid, "Are you still there?")
                            elif consecutive_silence_count == 2:
                                # Second silence - another prompt
                                await send_tts_to_stream(websocket, stream_sid, "Hello? Can you hear me?")
                    
                    audio_buffer = b""
                
            elif event == "stop":
                logger.info(f"Media stream stopped: {call_id}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call {call_id}")
    except Exception as e:
        logger.error(f"Media stream error: {e}")
    finally:
        active_media_streams.pop(call_id, None)
        
        # Update call record with transcript
        await db.calls.update_one(
            {"id": call_id},
            {"$set": {
                "transcript": messages,
                "status": CallStatus.COMPLETED.value,
                "ended_at": datetime.now(timezone.utc).isoformat()
            }}
        )

async def send_tts_to_stream(websocket: WebSocket, stream_sid: str, text: str):
    """Generate TTS with ElevenLabs and send to Twilio stream"""
    try:
        if not eleven_client:
            logger.error("ElevenLabs not configured")
            return
        
        # Generate audio
        audio_gen = eleven_client.text_to_speech.convert(
            text=text,
            voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah - professional
            model_id="eleven_turbo_v2_5",
            output_format="ulaw_8000"  # Direct μ-law output for Twilio!
        )
        
        audio_data = b""
        for chunk in audio_gen:
            audio_data += chunk
        
        logger.info(f"TTS generated {len(audio_data)} bytes for: '{text[:40]}...'")
        
        # Send in 20ms chunks (160 bytes at 8kHz)
        chunk_size = 160
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            payload = base64.b64encode(chunk).decode()
            
            await websocket.send_text(json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload}
            }))
            await asyncio.sleep(0.02)
            
    except Exception as e:
        logger.error(f"TTS streaming error: {e}", exc_info=True)

async def transcribe_audio_chunk(audio_data: bytes) -> str:
    """Transcribe audio using a speech recognition service"""
    # For production, use Deepgram or AssemblyAI for real-time
    # This is a simplified placeholder
    try:
        # Convert μ-law to PCM for transcription APIs
        import audioop
        pcm_data = audioop.ulaw2lin(audio_data, 2)
        
        # Create WAV file
        import struct
        sample_rate = 8000
        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + len(pcm_data), b'WAVE', b'fmt ', 16,
            1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(pcm_data)
        )
        wav_data = wav_header + pcm_data
        
        # Use OpenAI Whisper
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {llm_key}"},
                files={"file": ("audio.wav", wav_data, "audio/wav")},
                data={"model": "whisper-1"},
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json().get("text", "")
    except Exception as e:
        logger.error(f"Transcription error: {e}")
    return ""

async def generate_sales_response(user_input: str, history: list, lead: Dict, campaign: Dict) -> str:
    """Generate AI sales response using GPT"""
    try:
        company = campaign.get('company_name', 'our company')
        business = lead.get('business_name', 'your company')
        
        system_prompt = f"""You are an AI sales agent for {company}. Keep responses SHORT (1-2 sentences max) - this is a phone call.

Your goal: Qualify the lead and book a meeting.

Lead: {business}

Guidelines:
- Be conversational and natural
- Ask ONE question at a time
- If they're interested, offer to book a 15-min call
- If not interested, thank them and end politely

Common responses:
- "Yes/interested" → Ask about their timeline or decision-making process
- "Tell me more" → Briefly explain the value proposition  
- "Not now" → Offer to send info by email
- "Who is this?" → Re-introduce yourself briefly"""

        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            model="gpt-5.2",
            system_message=system_prompt
        )
        
        # Add history
        full_prompt = ""
        for msg in history[-6:]:  # Last 3 exchanges
            full_prompt += f"{msg['role']}: {msg['content']}\n"
        full_prompt += f"user: {user_input}"
        
        response = await chat.chat(full_prompt)
        
        # Keep it short
        if len(response) > 150:
            response = response[:150].rsplit(' ', 1)[0]
        
        return response
        
    except Exception as e:
        logger.error(f"GPT response error: {e}")
        return "I apologize, could you repeat that?"

# ----- ElevenLabs TTS -----
class TTSRequest(BaseModel):
    text: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default to "Rachel" voice
    stability: float = 0.5
    similarity_boost: float = 0.75

@api_router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """Generate text-to-speech audio using ElevenLabs"""
    if not eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured. Add ELEVENLABS_API_KEY to .env")
    
    try:
        voice_settings = VoiceSettings(
            stability=request.stability,
            similarity_boost=request.similarity_boost
        )
        
        audio_generator = eleven_client.text_to_speech.convert(
            text=request.text,
            voice_id=request.voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings
        )
        
        # Collect audio data
        audio_data = b""
        for chunk in audio_generator:
            audio_data += chunk
        
        # Convert to base64 for transfer
        audio_b64 = base64.b64encode(audio_data).decode()
        
        return {
            "audio_url": f"data:audio/mpeg;base64,{audio_b64}",
            "text": request.text,
            "voice_id": request.voice_id
        }
        
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

@api_router.get("/tts/voices")
async def get_available_voices():
    """Get list of available ElevenLabs voices"""
    if not eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")
    
    try:
        voices_response = eleven_client.voices.get_all()
        voices = [{"voice_id": v.voice_id, "name": v.name} for v in voices_response.voices]
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error fetching voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")

# Demo narration scripts
DEMO_NARRATIONS = {
    "step1": {
        "title": "Visual Sales Funnel",
        "text": "Welcome to DialGenix. Your visual sales funnel shows every lead's journey - from discovery to booked meeting. Track real-time stats on qualification rates, calls made, and bookings. Just click 'Call' to let AI do the heavy lifting."
    },
    "step2": {
        "title": "AI Lead Discovery",
        "text": "Finding leads is easy. Enter your target keywords - like 'Toast alternative' or 'payment processing' - and our AI finds businesses actively searching for solutions like yours. You can also upload your own CSV with existing leads."
    },
    "step3": {
        "title": "Call Recordings & Results",
        "text": "After each call, review the full recording and AI-generated transcript. See qualification scores to know which leads are hot. Your AI agent handles objections, qualifies prospects, and books meetings - all automatically."
    }
}

# Cache for generated audio
demo_audio_cache = {}

# Different voices for each demo step to showcase AI voice variety
DEMO_VOICE_MAP = {
    "step1": {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"},    # Professional female - Dashboard Overview
    "step2": {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni"},    # Well-rounded calm male - AI Lead Discovery
    "step3": {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella"},     # Soft warm female - Call Recordings
}

@api_router.get("/demo/narration/{step_id}")
async def get_demo_narration(step_id: str):
    """Get demo narration audio for a specific step - serves pre-generated static files"""
    if step_id not in DEMO_NARRATIONS:
        raise HTTPException(status_code=404, detail="Demo step not found")
    
    narration = DEMO_NARRATIONS[step_id]
    voice_info = DEMO_VOICE_MAP.get(step_id, {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"})
    
    # Serve static pre-generated audio files (no API calls needed)
    # Files are located at /public/audio/demo_step1.mp3, demo_step2.mp3, demo_step3.mp3
    static_audio_url = f"/audio/demo_{step_id}.mp3"
    
    return {
        "step_id": step_id,
        "title": narration["title"],
        "text": narration["text"],
        "voice_name": voice_info["name"],
        "audio_url": static_audio_url
    }

@api_router.get("/demo/narrations")
async def get_all_demo_narrations():
    """Get all demo narration metadata (without audio)"""
    return {
        "narrations": [
            {"step_id": k, "title": v["title"], "text": v["text"]} 
            for k, v in DEMO_NARRATIONS.items()
        ]
    }

# Include router
# Conditionally mount new modular auth routes FIRST (Strangler Fig pattern)
# This ensures new routes take precedence over legacy inline routes
if USE_NEW_AUTH_ROUTES:
    from routes.auth import router as auth_router, set_twilio_client
    # Inject Twilio client into auth module
    if twilio_client:
        set_twilio_client(twilio_client, twilio_phone_number)
    # Mount auth router - NOTE: routes are /api/auth/* due to prefix in router
    app.include_router(auth_router, prefix="/api")
    logger.info("Using NEW modular auth routes (USE_NEW_AUTH_ROUTES=true)")
else:
    logger.info("Using LEGACY inline auth routes (USE_NEW_AUTH_ROUTES=false)")

# Conditionally mount new modular leads routes (Phase 3)
if USE_NEW_LEADS_ROUTES:
    from routes.leads import router as leads_router, set_services as set_leads_services
    # Inject service references into leads module
    set_leads_services(
        ai_service=ai_service,
        compliance_service=compliance_service,
        icp_service=icp_service,
        crm_service=crm_service,
        get_tier_features_fn=get_tier_features,
        check_subscription_limit_fn=check_subscription_limit
    )
    app.include_router(leads_router, prefix="/api")
    logger.info("Using NEW modular leads routes (USE_NEW_LEADS_ROUTES=true)")
else:
    logger.info("Using LEGACY inline leads routes (USE_NEW_LEADS_ROUTES=false)")

# Conditionally mount new modular agents routes (Phase 4)
if USE_NEW_AGENTS_ROUTES:
    from routes.agents import router as agents_router, set_services as set_agents_services
    # Inject service references into agents module
    set_agents_services(
        eleven_client=eleven_client,
        check_subscription_limit_fn=check_subscription_limit,
        get_tier_features_fn=get_tier_features,
        VoiceSettings=VoiceSettings
    )
    app.include_router(agents_router, prefix="/api")
    logger.info("Using NEW modular agents routes (USE_NEW_AGENTS_ROUTES=true)")
else:
    logger.info("Using LEGACY inline agents routes (USE_NEW_AGENTS_ROUTES=false)")

# Conditionally mount new modular campaigns routes (Phase 5)
if USE_NEW_CAMPAIGNS_ROUTES:
    from routes.campaigns import router as campaigns_router, set_services as set_campaigns_services
    # Inject service references into campaigns module
    set_campaigns_services(
        check_subscription_limit_fn=check_subscription_limit,
        get_tier_features_fn=get_tier_features,
        icp_service=icp_service
    )
    app.include_router(campaigns_router, prefix="/api")
    logger.info("Using NEW modular campaigns routes (USE_NEW_CAMPAIGNS_ROUTES=true)")
else:
    logger.info("Using LEGACY inline campaigns routes (USE_NEW_CAMPAIGNS_ROUTES=false)")

# Include main api_router (legacy routes)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_pre_cache():
    """Pre-generate demo audio at startup to eliminate delay"""
    global _demo_audio_cache
    if elevenlabs_api_key and not _demo_audio_cache:
        try:
            demo_script = """Hey! This is Sarah from DialGenix... Glad you picked up!

I know what you're thinking— great, another sales call, right? 

But here's the twist... I'm actually an AI. Yeah— a real-time AI, having a natural conversation with you, right now.

And this? This is exactly what DialGenix lets you do.

Imagine having AI agents like me— making hundreds of calls for your business, every single day. No breaks. No missed follow-ups. No awkward pauses.

We can qualify your leads, handle objections, and even book meetings straight onto your calendar— all while sounding completely human.

You can even clone your own voice... or choose the exact tone you want. Plug in your scripts, use your proven rebuttals— so every call feels like your best salesperson is on the line.

And the best part? You can try it yourself, right now. Just head back to your dashboard and launch your first AI agent. It takes about five minutes.

Pretty cool, right?

Anyway— I'll let you get back to it. Talk soon!"""
            
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - American female voice
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={"xi-api-key": elevenlabs_api_key, "Content-Type": "application/json"},
                    json={
                        "text": demo_script,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                    },
                    timeout=60.0
                )
                if response.status_code == 200:
                    _demo_audio_cache = response.content
                    logger.info("Demo audio pre-cached successfully")
        except Exception as e:
            logger.error(f"Failed to pre-cache demo audio: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
