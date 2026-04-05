"""
Settings Routes Module
Contains settings, packs, account usage, and team management endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 7).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

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
