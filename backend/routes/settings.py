"""
Settings Routes Module
Contains settings, packs, account usage, team management, and BYOK integration endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 7).
"""
import os
import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import httpx
from cryptography.fernet import Fernet

from services.auth_service import get_current_user, get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Settings"])

# External service references (injected from main app)
_notification_service = None
_get_tier_features = None
_SUBSCRIPTION_PLANS = None
_LEAD_PACKS = None
_CALL_PACKS = None
_COMBO_PACKS = None
_TOPUP_PACKS = None
_PREPAY_DISCOUNTS = None

# Encryption cipher for API keys
_cipher = None

def _get_cipher():
    global _cipher
    if _cipher is None:
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'dialgenix_default_secret_key')
        key_bytes = jwt_secret.encode()[:32].ljust(32, b'0')
        _cipher = Fernet(base64.urlsafe_b64encode(key_bytes))
    return _cipher


def set_services(
    notification_service,
    get_tier_features_fn,
    subscription_plans,
    lead_packs,
    call_packs,
    combo_packs,
    topup_packs,
    prepay_discounts
):
    """Inject service references from main app"""
    global _notification_service, _get_tier_features
    global _SUBSCRIPTION_PLANS, _LEAD_PACKS, _CALL_PACKS, _COMBO_PACKS, _TOPUP_PACKS, _PREPAY_DISCOUNTS
    _notification_service = notification_service
    _get_tier_features = get_tier_features_fn
    _SUBSCRIPTION_PLANS = subscription_plans
    _LEAD_PACKS = lead_packs
    _CALL_PACKS = call_packs
    _COMBO_PACKS = combo_packs
    _TOPUP_PACKS = topup_packs
    _PREPAY_DISCOUNTS = prepay_discounts


# ============== BYOK INTEGRATION MODELS ==============

class TwilioVerifyRequest(BaseModel):
    account_sid: str
    auth_token: str
    phone_number: Optional[str] = None

class ElevenLabsVerifyRequest(BaseModel):
    api_key: str

class SaveIntegrationsRequest(BaseModel):
    twilio: Optional[Dict[str, str]] = None
    elevenlabs: Optional[Dict[str, str]] = None


# ============== SETTINGS ENDPOINTS ==============

@router.get("/settings")
async def get_settings():
    """Get application settings"""
    db = get_db()
    settings = await db.settings.find_one({}, {"_id": 0})
    if not settings:
        default_settings = {
            "twilio_configured": False,
            "twitter_configured": False,
            "calendly_configured": False,
            "email_notifications_configured": _notification_service.is_configured if _notification_service else False,
            "qualification_threshold": 60,
            "min_interest_level": 6,
            "require_decision_maker": True
        }
        await db.settings.insert_one(default_settings)
        return default_settings
    
    # Always update the email notification status
    settings["email_notifications_configured"] = _notification_service.is_configured if _notification_service else False
    return settings


@router.put("/settings")
async def update_settings(updates: Dict[str, Any]):
    """Update application settings"""
    db = get_db()
    await db.settings.update_one({}, {"$set": updates}, upsert=True)
    settings = await db.settings.find_one({}, {"_id": 0})
    return settings


# ============== CREDIT PACKS ENDPOINTS ==============

@router.get("/packs")
async def get_available_packs():
    """Get all available credit packs and subscription plans"""
    return {
        "subscription_plans": _SUBSCRIPTION_PLANS or {},
        "lead_packs": _LEAD_PACKS or {},
        "call_packs": _CALL_PACKS or {},
        "combo_packs": _COMBO_PACKS or {},
        "topup_packs": _TOPUP_PACKS or {},
        "prepay_discounts": _PREPAY_DISCOUNTS or {}
    }


# ============== ACCOUNT USAGE ENDPOINTS ==============

@router.get("/account/usage")
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


# ============== TEAM MANAGEMENT ENDPOINTS ==============

@router.get("/team/members")
async def get_team_members(current_user: Dict = Depends(get_current_user)):
    """Get all team members for the current user's organization"""
    db = get_db()
    user_id = current_user["user_id"]
    
    # Check if team seats feature is available
    features = _get_tier_features(current_user)
    max_team_seats = features.get("max_team_seats", 0)
    if not max_team_seats or max_team_seats <= 0:
        raise HTTPException(
            status_code=403,
            detail="Team management requires Professional plan or higher."
        )
    
    # Get team members invited by this user
    members = await db.team_members.find(
        {"owner_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    return members


@router.post("/team/invite")
async def invite_team_member(
    invite_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Invite a new team member"""
    db = get_db()
    user_id = current_user["user_id"]
    email = invite_data.get("email", "").lower().strip()
    role = invite_data.get("role", "member")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check feature access
    features = _get_tier_features(current_user)
    max_team_seats = features.get("max_team_seats", 0)
    if not max_team_seats or max_team_seats <= 0:
        raise HTTPException(
            status_code=403,
            detail="Team management requires Professional plan or higher."
        )
    
    # Check if user already invited
    existing = await db.team_members.find_one({
        "owner_id": user_id,
        "email": email
    })
    if existing:
        raise HTTPException(status_code=400, detail="This email is already on your team")
    
    # Check team seat limit
    current_count = await db.team_members.count_documents({"owner_id": user_id})
    max_seats = current_user.get("team_seat_count", 1)
    if current_count >= max_seats:
        raise HTTPException(
            status_code=403,
            detail=f"Team seat limit reached ({max_seats}). Please upgrade to add more members."
        )
    
    # Create team member invitation
    member = {
        "id": str(uuid.uuid4()),
        "owner_id": user_id,
        "email": email,
        "role": role,
        "status": "pending",
        "invite_token": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.team_members.insert_one(member)
    
    # TODO: Send invitation email
    
    return {"message": "Invitation sent", "member": {k: v for k, v in member.items() if k != "_id"}}


@router.delete("/team/members/{member_id}")
async def remove_team_member(
    member_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Remove a team member"""
    db = get_db()
    result = await db.team_members.delete_one({
        "id": member_id,
        "owner_id": current_user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    return {"message": "Team member removed"}



# ============== BYOK INTEGRATION ENDPOINTS ==============

@router.post("/settings/verify-twilio")
async def verify_twilio_credentials(
    data: TwilioVerifyRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Verify Twilio Account SID and Auth Token, return balance"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{data.account_sid}/Balance.json",
                auth=(data.account_sid, data.auth_token)
            )
            if response.status_code == 200:
                balance_data = response.json()
                balance = float(balance_data.get("balance", 0))
                return {
                    "valid": True,
                    "balance": balance,
                    "currency": balance_data.get("currency", "USD"),
                    "message": "Twilio credentials verified"
                }
            elif response.status_code == 401:
                return {"valid": False, "message": "Invalid Account SID or Auth Token"}
            else:
                return {"valid": False, "message": f"Twilio returned status {response.status_code}"}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Twilio API timed out. Please try again.")
    except Exception as e:
        logger.error(f"Twilio verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify Twilio credentials")


@router.post("/settings/verify-elevenlabs")
async def verify_elevenlabs_credentials(
    data: ElevenLabsVerifyRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Verify ElevenLabs API key and return credit usage"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Try subscription endpoint first for credit info
            response = await client.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": data.api_key}
            )
            if response.status_code == 200:
                sub = response.json()
                char_count = sub.get("character_count", 0)
                char_limit = sub.get("character_limit", 1)
                remaining_pct = max(0, round(((char_limit - char_count) / char_limit) * 100)) if char_limit > 0 else 0
                return {
                    "valid": True,
                    "credits": {
                        "character_count": char_count,
                        "character_limit": char_limit,
                        "remaining_percent": remaining_pct,
                        "tier": sub.get("tier", "unknown")
                    },
                    "message": "ElevenLabs credentials verified"
                }
            elif response.status_code in (401, 403):
                # Try voices endpoint as a lighter check
                voice_resp = await client.get(
                    "https://api.elevenlabs.io/v1/voices",
                    headers={"xi-api-key": data.api_key}
                )
                if voice_resp.status_code == 200:
                    return {
                        "valid": True,
                        "credits": None,
                        "message": "ElevenLabs key verified (credit info requires 'user_read' permission)"
                    }
                return {"valid": False, "message": "Invalid ElevenLabs API key"}
            else:
                return {"valid": False, "message": f"ElevenLabs returned status {response.status_code}"}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="ElevenLabs API timed out. Please try again.")
    except Exception as e:
        logger.error(f"ElevenLabs verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify ElevenLabs credentials")


@router.post("/settings/integrations")
async def save_integrations(
    data: SaveIntegrationsRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Save user's BYOK integration credentials (encrypted)"""
    db = get_db()
    cipher = _get_cipher()
    user_id = current_user["user_id"]
    
    update_fields = {"byok_updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.twilio:
        if data.twilio.get("account_sid"):
            update_fields["twilio_account_sid"] = cipher.encrypt(data.twilio["account_sid"].encode()).decode()
        if data.twilio.get("auth_token"):
            update_fields["twilio_auth_token_enc"] = cipher.encrypt(data.twilio["auth_token"].encode()).decode()
        if data.twilio.get("phone_number"):
            update_fields["twilio_phone_number"] = data.twilio["phone_number"]
        update_fields["twilio_connected"] = True
    
    if data.elevenlabs:
        if data.elevenlabs.get("api_key"):
            update_fields["elevenlabs_api_key_enc"] = cipher.encrypt(data.elevenlabs["api_key"].encode()).decode()
        update_fields["elevenlabs_connected"] = True
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_fields}
    )
    
    return {"message": "Integration settings saved", "saved_at": update_fields["byok_updated_at"]}


@router.get("/settings/integrations/status")
async def get_integration_status(current_user: Dict = Depends(get_current_user)):
    """Check if user has configured BYOK credentials"""
    db = get_db()
    user = await db.users.find_one(
        {"user_id": current_user["user_id"]},
        {"_id": 0, "twilio_connected": 1, "elevenlabs_connected": 1, 
         "twilio_phone_number": 1, "byok_updated_at": 1}
    )
    return {
        "twilio_connected": user.get("twilio_connected", False) if user else False,
        "elevenlabs_connected": user.get("elevenlabs_connected", False) if user else False,
        "twilio_phone_number": user.get("twilio_phone_number") if user else None,
        "byok_updated_at": user.get("byok_updated_at") if user else None
    }


@router.get("/settings/integrations/balances")
async def get_integration_balances(current_user: Dict = Depends(get_current_user)):
    """Fetch real-time balances for user's BYOK Twilio and ElevenLabs accounts"""
    db = get_db()
    cipher = _get_cipher()
    user_id = current_user["user_id"]
    
    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "twilio_account_sid": 1, "twilio_auth_token_enc": 1,
         "elevenlabs_api_key_enc": 1, "twilio_connected": 1, "elevenlabs_connected": 1}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = {"twilio": None, "elevenlabs": None}
    
    # Check Twilio balance
    if user.get("twilio_connected") and user.get("twilio_account_sid") and user.get("twilio_auth_token_enc"):
        try:
            sid = cipher.decrypt(user["twilio_account_sid"].encode()).decode()
            token = cipher.decrypt(user["twilio_auth_token_enc"].encode()).decode()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Balance.json",
                    auth=(sid, token)
                )
                if resp.status_code == 200:
                    bal = resp.json()
                    balance = float(bal.get("balance", 0))
                    result["twilio"] = {
                        "balance": balance,
                        "currency": bal.get("currency", "USD"),
                        "low": balance < 10
                    }
                else:
                    result["twilio"] = {"error": "Invalid credentials or expired token", "low": False}
        except Exception as e:
            logger.error(f"Twilio balance check failed for user {user_id}: {e}")
            result["twilio"] = {"error": "Could not fetch Twilio balance", "low": False}
    
    # Check ElevenLabs credits
    if user.get("elevenlabs_connected") and user.get("elevenlabs_api_key_enc"):
        try:
            api_key = cipher.decrypt(user["elevenlabs_api_key_enc"].encode()).decode()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.elevenlabs.io/v1/user/subscription",
                    headers={"xi-api-key": api_key}
                )
                if resp.status_code == 200:
                    sub = resp.json()
                    char_count = sub.get("character_count", 0)
                    char_limit = sub.get("character_limit", 1)
                    remaining_pct = max(0, round(((char_limit - char_count) / char_limit) * 100)) if char_limit > 0 else 0
                    result["elevenlabs"] = {
                        "character_count": char_count,
                        "character_limit": char_limit,
                        "remaining_percent": remaining_pct,
                        "tier": sub.get("tier", "unknown"),
                        "low": remaining_pct < 20
                    }
                elif resp.status_code == 401 or resp.status_code == 403:
                    result["elevenlabs"] = {"error": "API key lacks permissions or is invalid. Ensure your key has 'user_read' permission.", "low": False}
                else:
                    result["elevenlabs"] = {"error": f"ElevenLabs returned status {resp.status_code}", "low": False}
        except Exception as e:
            logger.error(f"ElevenLabs balance check failed for user {user_id}: {e}")
            result["elevenlabs"] = {"error": "Could not fetch ElevenLabs credits"}
    
    return result
