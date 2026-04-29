"""
Authentication Routes Module
Contains all authentication-related API endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern.
"""
import os
import uuid
import random
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, EmailStr
from enum import Enum

from services.auth_service import (
    get_db,
    hash_password,
    verify_password,
    create_session,
    get_session_from_token,
    delete_session,
    get_current_user,
    get_optional_user,
    normalize_phone_number,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router with /auth prefix
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Get Twilio client reference (will be injected from main app)
_twilio_client = None
_twilio_phone_number = None
_twilio_sms_number = None

def set_twilio_client(client, phone_number: str, sms_number: str = None):
    """Set Twilio client for SMS sending (called from main app)"""
    global _twilio_client, _twilio_phone_number, _twilio_sms_number
    _twilio_client = client
    _twilio_phone_number = phone_number
    _twilio_sms_number = sms_number or phone_number


# ============== ENUMS ==============
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# ============== REQUEST/RESPONSE MODELS ==============
class PhoneVerificationRequest(BaseModel):
    phone_number: str
    email: EmailStr  # To check if email is already registered


class PhoneVerificationConfirm(BaseModel):
    phone_number: str
    code: str


class OAuthPhoneVerification(BaseModel):
    phone_number: str
    verification_code: str  # The verification token from verify-phone


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone_number: str  # Required for trial abuse prevention
    verification_code: str  # SMS verification code


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ============== PHONE VERIFICATION ENDPOINTS ==============

@router.post("/send-verification")
async def send_phone_verification(request: PhoneVerificationRequest):
    """
    Send SMS verification code to phone number.
    Checks if phone has already been used for a trial.
    """
    db = get_db()
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
    if _twilio_client:
        try:
            _twilio_client.messages.create(
                body=f"Your IntentBrain.ai verification code is: {verification_code}. Valid for 10 minutes.",
                from_=_twilio_sms_number,
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


@router.post("/verify-phone")
async def verify_phone_code(request: PhoneVerificationConfirm):
    """
    Verify the SMS code. Returns a verification token to use during registration.
    """
    db = get_db()
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


@router.post("/verify-phone-oauth")
async def verify_phone_for_oauth_user(
    request: OAuthPhoneVerification,
    current_user: Dict = Depends(get_current_user)
):
    """
    Complete phone verification for OAuth users.
    Required before they can use their free trial.
    """
    db = get_db()
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


# ============== REGISTRATION & LOGIN ==============

@router.post("/register")
async def register(user_data: UserCreate):
    """Register a new user with email/password. Requires verified phone number."""
    db = get_db()
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
    session_token = await create_session(user_id)
    
    # Return user without password
    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    
    return {
        "user": user_doc,
        "session_token": session_token
    }


@router.post("/login")
async def login(user_data: UserLogin, response: Response):
    """Login with email/password"""
    db = get_db()
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
    session_token = await create_session(user_doc["user_id"])
    
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


@router.post("/session")
async def exchange_session_id(request: Request, response: Response):
    """Exchange Emergent OAuth session_id for our session token"""
    db = get_db()
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
    session_token = await create_session(user_doc["user_id"])
    
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


@router.get("/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user"""
    # Import here to avoid circular imports
    from server import get_trial_status, check_low_balance_and_notify
    
    current_user.pop("password_hash", None)
    
    # Check for low balance and potentially send notification
    await check_low_balance_and_notify(current_user)
    
    # Add trial status to response
    trial_status = get_trial_status(current_user)
    current_user["trial_status"] = trial_status
    
    return current_user


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await delete_session(session_token)
    
    response.delete_cookie(key="session_token", path="/")
    
    return {"message": "Logged out successfully"}
