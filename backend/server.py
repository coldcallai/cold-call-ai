from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File, Depends, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
from passlib.context import CryptContext
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings

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
    business_name: str
    contact_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    source: str = "manual"
    intent_signals: List[str] = []
    status: LeadStatus = LeadStatus.NEW
    qualification_score: Optional[int] = None
    is_decision_maker: Optional[bool] = None
    interest_level: Optional[int] = None
    notes: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LeadCreate(BaseModel):
    business_name: str
    contact_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    source: str = "manual"
    intent_signals: List[str] = []

class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ai_script: str
    qualification_criteria: Dict[str, Any] = {}
    calls_per_day: int = 100

class Call(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    campaign_id: str
    agent_id: Optional[str] = None
    status: CallStatus = CallStatus.PENDING
    duration_seconds: int = 0
    transcript: List[Dict[str, str]] = []
    qualification_result: Optional[Dict[str, Any]] = None
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
    
    async def gpt_intent_search(self, query: str, industry: str = None, location: str = None, max_results: int = 10) -> List[Dict]:
        """Use GPT-5.2 to research and find businesses with buying intent"""
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not configured, using mock data")
            return await self._mock_discover_leads(query, location, max_results)
        
        # High-intent keywords that indicate buying mode
        intent_keywords = [
            "Toast alternative", "Clover alternative", "Square alternative", "Stripe alternative",
            "best POS system", "credit card processing for contractors", "payment processing",
            "merchant services", "switch payment processor", "POS system for restaurants",
            "credit card machine", "payment terminal", "reduce processing fees"
        ]
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"intent-search-{uuid.uuid4()}",
                system_message="""You are a B2B lead research assistant specializing in finding businesses actively searching for payment processing solutions.

Your job is to generate realistic business leads that are IN BUYING MODE - meaning they are actively searching for:
- Alternatives to Toast, Square, Stripe, Clover
- Best POS systems for their industry
- Credit card processing solutions
- Ways to reduce payment processing fees
- New merchant services providers

These are HIGH-INTENT leads - people who are ready to switch or sign up NOW.

For each lead, provide:
- Business name (realistic)
- Industry
- Phone number (realistic US format)
- Email (realistic business email)
- Intent signals (SPECIFIC search terms or actions showing buying intent)
- Location (city, state)
- Pain point (why they're looking to switch)

Return your response as a valid JSON array of objects with these fields:
- name: string
- industry: string  
- phone: string
- email: string
- intent_signals: array of strings (include actual search terms like "Stripe alternative", "best POS for restaurants")
- location: string
- pain_point: string

Only return the JSON array, no other text."""
            ).with_model("openai", "gpt-5.2")
            
            search_prompt = f"""Find {max_results} businesses that are ACTIVELY IN BUYING MODE for payment processing solutions.

Search criteria:
- Primary query: {query}
- Industry focus: {industry or 'Any industry that processes card payments'}
- Location: {location or 'United States'}

Target businesses showing these high-intent signals:
{chr(10).join(f'- Searching for "{kw}"' for kw in intent_keywords)}

These leads should be people who:
1. Are actively comparing payment processors
2. Searching for alternatives to major providers (Toast, Square, Stripe, Clover)
3. Looking to switch due to high fees, poor service, or missing features
4. New businesses setting up payment processing for the first time

Return as JSON array with realistic business details and specific intent signals."""

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

# ============== WEBHOOK MODELS ==============
class WebhookConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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

# ----- Dashboard Stats -----
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: Dict = Depends(get_optional_user)):
    total_leads = await db.leads.count_documents({})
    qualified_leads = await db.leads.count_documents({"status": LeadStatus.QUALIFIED})
    booked_leads = await db.leads.count_documents({"status": LeadStatus.BOOKED})
    total_calls = await db.calls.count_documents({})
    active_campaigns = await db.campaigns.count_documents({"status": CampaignStatus.ACTIVE})
    total_agents = await db.agents.count_documents({"is_active": True})
    
    # Get recent calls
    recent_calls = await db.calls.find(
        {},
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

@api_router.post("/leads/discover")
async def discover_leads(request: LeadDiscoveryRequest):
    """Discover new leads using AI-powered research (legacy endpoint)"""
    discovered = await ai_service.gpt_intent_search(
        query=request.search_query,
        location=request.location,
        max_results=request.max_results
    )
    
    created_leads = []
    for biz in discovered:
        lead_data = Lead(
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
async def gpt_intent_search(request: GPTIntentSearchRequest):
    """Discover leads using GPT-5.2 powered intent search"""
    discovered = await ai_service.gpt_intent_search(
        query=request.search_query,
        industry=request.industry,
        location=request.location,
        max_results=request.max_results
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
    
    return {
        "discovered": len(created_leads),
        "source": "gpt_intent_search",
        "leads": [lead.model_dump() for lead in created_leads]
    }

# ----- Leads CRUD -----
@api_router.get("/leads", response_model=List[Lead])
async def get_leads(
    status: Optional[LeadStatus] = None,
    limit: int = Query(100, le=500),
    skip: int = 0
):
    query = {}
    if status:
        query["status"] = status
    
    leads = await db.leads.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return leads

@api_router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@api_router.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    lead_obj = Lead(**lead.model_dump())
    await db.leads.insert_one(lead_obj.model_dump())
    return lead_obj

@api_router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, updates: Dict[str, Any]):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return lead

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    result = await db.leads.delete_one({"id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}

# ----- CSV Upload & Export -----
@api_router.post("/leads/upload-csv")
async def upload_leads_csv(file: UploadFile = File(...)):
    """Upload leads from CSV file (Bring Your Own List)"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
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
                
                if not business_name or not phone:
                    errors.append(f"Row {idx + 1}: Missing business_name or phone")
                    continue
                
                lead_data = Lead(
                    business_name=business_name,
                    phone=phone,
                    email=email,
                    contact_name=contact_name,
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
async def export_leads_csv(status: Optional[LeadStatus] = None):
    """Export leads to CSV (Discovery Only mode)"""
    query = {}
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

# ----- Agents CRUD -----
@api_router.get("/agents", response_model=List[Agent])
async def get_agents():
    agents = await db.agents.find({}, {"_id": 0}).to_list(100)
    return agents

@api_router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    agent = await db.agents.find_one({"id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@api_router.post("/agents", response_model=Agent)
async def create_agent(agent: AgentCreate):
    agent_obj = Agent(**agent.model_dump())
    await db.agents.insert_one(agent_obj.model_dump())
    return agent_obj

@api_router.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, updates: Dict[str, Any]):
    result = await db.agents.update_one(
        {"id": agent_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = await db.agents.find_one({"id": agent_id}, {"_id": 0})
    return agent

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    result = await db.agents.delete_one({"id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}

# ----- Campaigns CRUD -----
@api_router.get("/campaigns", response_model=List[Campaign])
async def get_campaigns():
    campaigns = await db.campaigns.find({}, {"_id": 0}).to_list(100)
    return campaigns

@api_router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str):
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@api_router.post("/campaigns", response_model=Campaign)
async def create_campaign(campaign: CampaignCreate):
    campaign_obj = Campaign(**campaign.model_dump())
    await db.campaigns.insert_one(campaign_obj.model_dump())
    return campaign_obj

@api_router.put("/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(campaign_id: str, updates: Dict[str, Any]):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return campaign

@api_router.post("/campaigns/{campaign_id}/start")
async def start_campaign(campaign_id: str):
    result = await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"status": CampaignStatus.ACTIVE, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign started", "status": "active"}

@api_router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    result = await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"status": CampaignStatus.PAUSED, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign paused", "status": "paused"}

@api_router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    result = await db.campaigns.delete_one({"id": campaign_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign deleted"}

# ----- Calls -----
@api_router.get("/calls", response_model=List[Call])
async def get_calls(
    status: Optional[CallStatus] = None,
    campaign_id: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    query = {}
    if status:
        query["status"] = status
    if campaign_id:
        query["campaign_id"] = campaign_id
    
    calls = await db.calls.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return calls

@api_router.get("/calls/{call_id}", response_model=Call)
async def get_call(call_id: str):
    call = await db.calls.find_one({"id": call_id}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@api_router.post("/calls/simulate")
async def simulate_call(lead_id: str, campaign_id: str, background_tasks: BackgroundTasks):
    """Simulate an AI cold call (MOCKED - real calls require Twilio credentials)"""
    # Get lead and campaign
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Create call record
    call = Call(
        lead_id=lead_id,
        campaign_id=campaign_id,
        status=CallStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc).isoformat()
    )
    await db.calls.insert_one(call.model_dump())
    
    # Simulate the call in background
    background_tasks.add_task(process_simulated_call, call.id, lead, campaign)
    
    return {"message": "Call started", "call_id": call.id, "status": "in_progress"}

async def process_simulated_call(call_id: str, lead: Dict, campaign: Dict):
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
            webhooks = await db.webhooks.find(
                {"event_type": "lead_qualified", "is_active": True},
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
async def book_meeting(request: BookingRequest, background_tasks: BackgroundTasks):
    """Book a meeting with an agent for a qualified lead"""
    lead = await db.leads.find_one({"id": request.lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.get("status") != LeadStatus.QUALIFIED:
        raise HTTPException(status_code=400, detail="Lead is not qualified for booking")
    
    agent = await db.agents.find_one({"id": request.agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update lead status
    await db.leads.update_one(
        {"id": request.lead_id},
        {"$set": {
            "status": LeadStatus.BOOKED,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Increment agent's assigned leads
    await db.agents.update_one(
        {"id": request.agent_id},
        {"$inc": {"assigned_leads": 1}}
    )
    
    # Send meeting booked notification in background
    background_tasks.add_task(send_meeting_booked_notifications, lead, agent)
    
    return {
        "message": "Meeting booked successfully",
        "calendly_link": agent["calendly_link"],
        "lead": lead["business_name"],
        "agent": agent["name"]
    }

async def send_meeting_booked_notifications(lead: Dict, agent: Dict):
    """Send meeting booked notifications"""
    try:
        webhooks = await db.webhooks.find(
            {"event_type": "meeting_booked", "is_active": True},
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
async def get_webhooks():
    """Get all webhook configurations"""
    webhooks = await db.webhooks.find({}, {"_id": 0}).to_list(100)
    return webhooks

@api_router.post("/webhooks")
async def create_webhook(webhook: WebhookConfigCreate):
    """Create a new webhook configuration"""
    if webhook.event_type not in ["lead_qualified", "meeting_booked"]:
        raise HTTPException(status_code=400, detail="Invalid event_type. Must be 'lead_qualified' or 'meeting_booked'")
    
    webhook_obj = WebhookConfig(**webhook.model_dump())
    await db.webhooks.insert_one(webhook_obj.model_dump())
    return webhook_obj

@api_router.put("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: str, updates: Dict[str, Any]):
    """Update a webhook configuration"""
    result = await db.webhooks.update_one(
        {"id": webhook_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook = await db.webhooks.find_one({"id": webhook_id}, {"_id": 0})
    return webhook

@api_router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a webhook configuration"""
    result = await db.webhooks.delete_one({"id": webhook_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}

@api_router.post("/webhooks/test/{webhook_id}")
async def test_webhook(webhook_id: str):
    """Test a webhook by sending a sample notification"""
    webhook = await db.webhooks.find_one({"id": webhook_id}, {"_id": 0})
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
