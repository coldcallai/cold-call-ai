from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File, Depends, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
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
from passlib.context import CryptContext
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Connect, Stream

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'coldcallai_default_secret_key')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer(auto_error=False)

# ElevenLabs client (for TTS)
elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY')
eleven_client = ElevenLabs(api_key=elevenlabs_api_key) if elevenlabs_api_key else None

# Stripe configuration
stripe_api_key = os.environ.get('STRIPE_API_KEY')

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

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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
    is_active: bool = True
    max_daily_calls: int = 50
    assigned_leads: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    max_daily_calls: int = 50

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
    transcript: List[Dict[str, str]] = []
    qualification_result: Optional[Dict[str, Any]] = None
    # AMD tracking
    answered_by: Optional[str] = None  # "human", "machine_start", "machine_end_beep", "machine_end_silence", "fax", "unknown"
    voicemail_dropped: bool = False
    amd_status: Optional[str] = None  # Raw AMD status from Twilio
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
    "starter": {
        "name": "Starter",
        "price": 199,
        "leads_per_month": 250,
        "calls_per_month": 250,
        "features": ["CSV export", "GPT-powered search", "Intent signals included"],
        "users": 1
    },
    "professional": {
        "name": "Professional",
        "price": 399,
        "leads_per_month": 1000,
        "calls_per_month": 1000,
        "features": ["Auto calendar booking", "API access", "Call transcripts", "Email notifications"],
        "users": 5
    },
    "unlimited": {
        "name": "Unlimited",
        "price": 699,
        "leads_per_month": 5000,
        "calls_per_month": -1,  # Unlimited
        "features": ["Priority support", "5 team seats", "Custom AI scripts", "Dedicated account manager"],
        "users": 5
    },
    "byl": {
        "name": "Bring Your List",
        "price": 349,
        "leads_per_month": 0,  # No leads - they bring their own
        "calls_per_month": 1500,
        "features": ["Unlimited CSV uploads", "Custom scripts", "Auto calendar booking", "Call transcripts"],
        "users": 3
    }
}

# Lead Packs (Auto-replenishing subscriptions)
LEAD_PACKS = [
    {"id": "leads_500_sub", "name": "500 Leads/mo", "quantity": 500, "price": 59, "type": "leads", "recurring": True, "per_lead": 0.118},
    {"id": "leads_1500_sub", "name": "1,500 Leads/mo", "quantity": 1500, "price": 149, "type": "leads", "recurring": True, "per_lead": 0.099},
    {"id": "leads_5000_sub", "name": "5,000 Leads/mo", "quantity": 5000, "price": 399, "type": "leads", "recurring": True, "per_lead": 0.079},
]

# Call Packs (Overage protection)
CALL_PACKS = [
    {"id": "calls_500", "name": "500 AI Calls", "quantity": 500, "price": 49, "type": "calls", "per_call": 0.098},
    {"id": "calls_2000", "name": "2,000 AI Calls", "quantity": 2000, "price": 149, "type": "calls", "per_call": 0.0745},
    {"id": "calls_5000", "name": "5,000 AI Calls", "quantity": 5000, "price": 299, "type": "calls", "per_call": 0.0598},
]

# Top-up Packs (20% premium for one-off purchases)
TOPUP_PACKS = [
    {"id": "topup_100_leads", "name": "100 Leads Top-up", "quantity": 100, "price": 24, "type": "topup", "credit_type": "leads", "per_unit": 0.24},
    {"id": "topup_250_leads", "name": "250 Leads Top-up", "quantity": 250, "price": 55, "type": "topup", "credit_type": "leads", "per_unit": 0.22},
    {"id": "topup_100_calls", "name": "100 Calls Top-up", "quantity": 100, "price": 15, "type": "topup", "credit_type": "calls", "per_unit": 0.15},
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
                    <p style="color: #6b7280; font-size: 14px;">This lead is ready for booking! Log in to ColdCall.ai to assign an agent.</p>
                </div>
            </div>
            
            <div style="background: #1f2937; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">Powered by ColdCall.ai - AI Sales Automation</p>
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
    
    async def send_meeting_booked_notification(self, lead: Dict, agent: Dict, recipients: List[str]):
        """Send email notification when a meeting is booked"""
        if not self.is_configured:
            logger.info("Email notifications not configured - skipping meeting booked notification")
            return None
        
        subject = f"📅 Meeting Booked: {lead.get('business_name', 'Unknown')} → {agent.get('name', 'Agent')}"
        
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
                        <td style="padding: 10px 0; color: #6b7280;">Calendly Link:</td>
                        <td style="padding: 10px 0; color: #8B5CF6; font-weight: 500;">
                            <a href="{agent.get('calendly_link', '#')}" style="color: #8B5CF6;">{agent.get('calendly_link', 'N/A')}</a>
                        </td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background: #f5f3ff; border-radius: 8px; border-left: 4px solid #8B5CF6;">
                    <p style="margin: 0; color: #5b21b6;">🎉 Great job! The lead has been directed to the agent's Calendly for scheduling.</p>
                </div>
            </div>
            
            <div style="background: #1f2937; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
                <p style="color: #9ca3af; margin: 0; font-size: 12px;">Powered by ColdCall.ai - AI Sales Automation</p>
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

notification_service = NotificationService()

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
class ComplianceService:
    """Service for handling call compliance checks"""
    
    async def check_dnc(self, phone_number: str) -> bool:
        """Check if number is on internal DNC list"""
        dnc_entry = await db.dnc_list.find_one({"phone_number": phone_number}, {"_id": 0})
        return dnc_entry is not None
    
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
        Perform all compliance checks before making a call.
        Returns whether call is allowed, reasons if not, and dial priority.
        """
        checks_performed = []
        reasons = []
        warnings = []
        is_allowed = True
        dial_priority = 50  # Default priority
        
        # 1. Check internal DNC list
        checks_performed.append("internal_dnc")
        if await self.check_dnc(phone_number):
            is_allowed = False
            reasons.append("Number is on internal Do Not Call list")
        
        # 2. Verify number with Twilio Lookup (landline vs mobile vs voip)
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
        
        # 3. Check recent call history (don't call too frequently)
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
            "dial_priority": dial_priority
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

# ============== API ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "AI Cold Calling Machine API", "status": "running"}

# ============== AUTHENTICATION ROUTES ==============

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    """Register a new user with email/password"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    password_hash = pwd_context.hash(user_data.password)
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": password_hash,
        "role": UserRole.USER.value,
        "subscription_tier": None,
        "subscription_status": "inactive",
        "lead_credits_remaining": 50,  # Free trial credits
        "call_credits_remaining": 50,
        "monthly_lead_allowance": 0,
        "monthly_call_allowance": 0,
        "team_seat_count": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
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
    
    if not pwd_context.verify(user_data.password, user_doc["password_hash"]):
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
        # Create new user from OAuth
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data.get("name", auth_data["email"].split("@")[0]),
            "picture": auth_data.get("picture"),
            "role": UserRole.USER.value,
            "subscription_tier": None,
            "subscription_status": "inactive",
            "lead_credits_remaining": 50,  # Free trial credits
            "call_credits_remaining": 50,
            "monthly_lead_allowance": 0,
            "monthly_call_allowance": 0,
            "team_seat_count": 1,
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
    return current_user

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
    
    system_prompt = """You are ColdCall.ai's helpful assistant. You guide sales agents through using the AI cold calling platform.

PLATFORM OVERVIEW:
ColdCall.ai is a B2B SaaS that:
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
    
    # Validate custom keywords (max 100)
    custom_keywords = None
    if request.custom_keywords:
        custom_keywords = [kw.strip() for kw in request.custom_keywords[:100] if kw and kw.strip()]
        if len(custom_keywords) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 custom keywords allowed")
    
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

@api_router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """Update a lead (must belong to current user)"""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.leads.update_one(
        {"id": lead_id, "user_id": current_user["user_id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]}, {"_id": 0})
    return lead

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a lead (must belong to current user)"""
    result = await db.leads.delete_one({"id": lead_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}

# ----- CSV Upload & Export -----
@api_router.post("/leads/upload-csv")
async def upload_leads_csv(file: UploadFile = File(...), current_user: Dict = Depends(get_current_user)):
    """Upload leads from CSV file (Bring Your Own List)"""
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

@api_router.get("/leads/export-csv")
async def export_leads_csv(status: Optional[LeadStatus] = None, current_user: Dict = Depends(get_current_user)):
    """Export leads to CSV (only user's own leads)"""
    query = {"user_id": current_user["user_id"]}
    if status:
        query["status"] = status
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(10000)
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads to export")
    
    # Create CSV in memory
    output = io.StringIO()
    fieldnames = ['business_name', 'contact_name', 'phone', 'email', 'status', 'source', 'intent_signals', 'qualification_score', 'created_at']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for lead in leads:
        writer.writerow({
            'business_name': lead.get('business_name', ''),
            'contact_name': lead.get('contact_name', ''),
            'phone': lead.get('phone', ''),
            'email': lead.get('email', ''),
            'status': lead.get('status', ''),
            'source': lead.get('source', ''),
            'intent_signals': '; '.join(lead.get('intent_signals', [])),
            'qualification_score': lead.get('qualification_score', ''),
            'created_at': lead.get('created_at', '')
        })
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

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
    campaign_obj = Campaign(**campaign.model_dump(), user_id=current_user["user_id"])
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

@api_router.post("/calls/simulate")
async def simulate_call(
    lead_id: str, 
    campaign_id: str, 
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Simulate an AI cold call (MOCKED - real calls require Twilio credentials). Deducts 1 call credit."""
    user_id = current_user["user_id"]
    calls_remaining = current_user.get("call_credits_remaining", 0)
    
    # Check if user has call credits
    if calls_remaining < 1:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient call credits. You have {calls_remaining} credits. Please purchase more credits to make calls."
        )
    
    # Get lead and campaign (with user ownership verification)
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": user_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Deduct 1 call credit
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
    
    return {
        "message": "Call started", 
        "call_id": call.id, 
        "status": "in_progress",
        "credits_used": 1,
        "credits_remaining": new_balance
    }

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

# ----- Booking -----
@api_router.post("/bookings")
async def book_meeting(request: BookingRequest, background_tasks: BackgroundTasks, current_user: Dict = Depends(get_current_user)):
    """Book a meeting with an agent for a qualified lead"""
    user_id = current_user["user_id"]
    
    # Multi-tenancy: Verify lead and agent belong to current user
    lead = await db.leads.find_one({"id": request.lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.get("status") != LeadStatus.QUALIFIED:
        raise HTTPException(status_code=400, detail="Lead is not qualified for booking")
    
    agent = await db.agents.find_one({"id": request.agent_id, "user_id": user_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update lead status (with user_id filter for safety)
    await db.leads.update_one(
        {"id": request.lead_id, "user_id": user_id},
        {"$set": {
            "status": LeadStatus.BOOKED,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Increment agent's assigned leads (with user_id filter for safety)
    await db.agents.update_one(
        {"id": request.agent_id, "user_id": user_id},
        {"$inc": {"assigned_leads": 1}}
    )
    
    # Send meeting booked notification in background
    background_tasks.add_task(send_meeting_booked_notifications, lead, agent, user_id)
    
    return {
        "message": "Meeting booked successfully",
        "calendly_link": agent["calendly_link"],
        "lead": lead["business_name"],
        "agent": agent["name"]
    }

async def send_meeting_booked_notifications(lead: Dict, agent: Dict, user_id: str):
    """Send meeting booked notifications"""
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
                    recipients=webhook["notification_emails"]
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

@api_router.post("/packs/purchase")
async def purchase_pack(pack_id: str, current_user: Dict = Depends(get_current_user)):
    """Purchase a credit pack (adds to user's balance)"""
    # Find the pack from all pack types
    all_packs = LEAD_PACKS + CALL_PACKS + TOPUP_PACKS
    pack = next((p for p in all_packs if p["id"] == pack_id), None)
    
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    # Create purchase record
    purchase = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "pack_id": pack_id,
        "pack_name": pack["name"],
        "pack_type": pack["type"],
        "price": pack["price"],
        "quantity": pack["quantity"],
        "purchased_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.purchases.insert_one(purchase)
    
    # Update user credits based on pack type
    update_query = {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    
    if pack["type"] == "leads":
        update_query["$inc"] = {"lead_credits_remaining": pack["quantity"]}
    elif pack["type"] == "calls":
        update_query["$inc"] = {"call_credits_remaining": pack["quantity"]}
    elif pack["type"] == "topup":
        credit_type = pack.get("credit_type", "leads")
        if credit_type == "leads":
            update_query["$inc"] = {"lead_credits_remaining": pack["quantity"]}
        else:
            update_query["$inc"] = {"call_credits_remaining": pack["quantity"]}
    
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
    """Run compliance check on a phone number before calling"""
    result = await compliance_service.pre_call_compliance_check(
        phone_number=phone_number,
        user_id=current_user["user_id"]
    )
    return result

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
    """
    if not twilio_service.is_configured:
        raise HTTPException(
            status_code=503, 
            detail="Twilio not configured. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to .env"
        )
    
    # Check call credits
    calls_remaining = current_user.get("call_credits_remaining", 0)
    if calls_remaining < 1:
        raise HTTPException(status_code=402, detail="Insufficient call credits")
    
    user_id = current_user["user_id"]
    
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
        return {
            "status": "blocked",
            "message": "Call blocked by compliance checks",
            "reasons": compliance_result["reasons"]
        }
    
    # Deduct call credit
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
        
        return {
            "status": "initiated",
            "call_id": call.id,
            "twilio_sid": twilio_result["call_sid"],
            "message": "Call initiated successfully",
            "amd_enabled": use_amd,
            "credits_remaining": calls_remaining - 1
        }
        
    except Exception as e:
        # Refund the credit if call failed to initiate
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
    
    update_data = {
        "status": new_status,
        "duration": int(duration) if duration else 0,
        "ended_at": datetime.now(timezone.utc).isoformat() if call_status in ["completed", "busy", "no-answer", "canceled", "failed"] else None
    }
    
    await db.calls.update_one(
        {"twilio_sid": call_sid},
        {"$set": update_data}
    )
    
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

@api_router.post("/twilio/recording")
async def twilio_recording_webhook(request: Request):
    """Handle recording status updates from Twilio"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    recording_url = form_data.get("RecordingUrl", "")
    recording_sid = form_data.get("RecordingSid", "")
    
    if call_sid and recording_url:
        await db.calls.update_one(
            {"twilio_sid": call_sid},
            {"$set": {
                "recording_url": recording_url,
                "recording_sid": recording_sid
            }}
        )
        logger.info(f"Recording saved for call {call_sid}: {recording_url}")
    
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
    stream_sid = None
    
    # Conversation state
    messages = []
    is_first_response = True
    audio_buffer = b""
    
    logger.info(f"Media stream connected for call {call_id}")
    
    try:
        while True:
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

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
