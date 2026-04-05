"""
Campaigns Routes Module
Contains all campaign-related API endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 5).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Form
from pydantic import BaseModel, Field
from enum import Enum

from services.auth_service import get_current_user, get_db
from services.campaign_service import (
    get_campaign_leads,
    update_lead_dial_priority,
    DEFAULT_FOLLOWUP_SETTINGS,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

# External service references (injected from main app)
_check_subscription_limit = None
_get_tier_features = None
_icp_service = None


def set_services(check_subscription_limit_fn, get_tier_features_fn, icp_service):
    """Inject service references from main app"""
    global _check_subscription_limit, _get_tier_features, _icp_service
    _check_subscription_limit = check_subscription_limit_fn
    _get_tier_features = get_tier_features_fn
    _icp_service = icp_service


# ============== ENUMS ==============
class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


# ============== MODELS ==============
class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
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
    voicemail_enabled: bool = True
    voicemail_message: Optional[str] = None
    response_wait_seconds: int = 4
    company_name: Optional[str] = None
    icp_config: Optional[Dict[str, Any]] = None
    min_icp_score: int = 0
    followup_settings: Optional[Dict[str, Any]] = None
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
    response_wait_seconds: int = 4
    company_name: Optional[str] = None
    icp_config: Optional[Dict[str, Any]] = None
    min_icp_score: int = 0


# ============== CAMPAIGN CRUD ENDPOINTS ==============

@router.get("", response_model=List[Campaign])
async def get_campaigns(current_user: Dict = Depends(get_current_user)):
    """Get campaigns belonging to the current user"""
    db = get_db()
    campaigns = await db.campaigns.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(100)
    return campaigns


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific campaign (must belong to current user)"""
    db = get_db()
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("", response_model=Campaign)
async def create_campaign(campaign: CampaignCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new campaign owned by the current user"""
    db = get_db()
    
    # Check subscription tier limits for campaigns
    limit_check = await _check_subscription_limit(current_user, "campaigns")
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    # Check feature access for voicemail drop
    features = _get_tier_features(current_user)
    campaign_data = campaign.model_dump()
    
    if campaign_data.get("voicemail_enabled") and not features.get("voicemail_drop"):
        raise HTTPException(
            status_code=403, 
            detail="Voicemail drop is not available on your plan. Upgrade to Starter or higher to use this feature."
        )
    
    campaign_obj = Campaign(**campaign_data, user_id=current_user["user_id"])
    await db.campaigns.insert_one(campaign_obj.model_dump())
    return campaign_obj


@router.put("/{campaign_id}", response_model=Campaign)
async def update_campaign(campaign_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """Update a campaign (must belong to current user)"""
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.campaigns.update_one(
        {"id": campaign_id, "user_id": current_user["user_id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": current_user["user_id"]}, {"_id": 0})
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a campaign (must belong to current user)"""
    db = get_db()
    result = await db.campaigns.delete_one({"id": campaign_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign deleted"}


# ============== CAMPAIGN STATUS ENDPOINTS ==============

@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Start a campaign (must belong to current user)"""
    db = get_db()
    result = await db.campaigns.update_one(
        {"id": campaign_id, "user_id": current_user["user_id"]},
        {"$set": {"status": CampaignStatus.ACTIVE, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign started", "status": "active"}


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, current_user: Dict = Depends(get_current_user)):
    """Pause a campaign (must belong to current user)"""
    db = get_db()
    result = await db.campaigns.update_one(
        {"id": campaign_id, "user_id": current_user["user_id"]},
        {"$set": {"status": CampaignStatus.PAUSED, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"message": "Campaign paused", "status": "paused"}


# ============== ICP SCORING ENDPOINTS ==============

@router.post("/{campaign_id}/score-all-leads")
async def score_campaign_leads(
    campaign_id: str,
    use_ai: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """
    Score all leads assigned to a campaign based on campaign's ICP config.
    Updates dial priority for optimal calling order.
    """
    db = get_db()
    user_id = current_user["user_id"]
    
    # Multi-tenancy: Verify campaign belongs to current user
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": user_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get leads assigned to this campaign
    leads = await get_campaign_leads(campaign_id, user_id)
    
    if not leads:
        return {"message": "No leads assigned to this campaign", "scored_count": 0}
    
    lead_ids = [lead["id"] for lead in leads]
    icp_config = campaign.get("icp_config")
    
    results = await _icp_service.batch_score_leads(lead_ids, icp_config, use_ai)
    
    # Calculate dial priority combining ICP score and phone verification
    for result in results:
        await update_lead_dial_priority(result["lead_id"], user_id, result["total_score"])
    
    return {
        "campaign_id": campaign_id,
        "scored_count": len(results),
        "message": "Leads scored and dial priority updated",
        "average_score": sum(r["total_score"] for r in results) / len(results) if results else 0
    }


# ============== FOLLOW-UP SETTINGS ENDPOINTS ==============

@router.put("/{campaign_id}/followup-settings")
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
    db = get_db()
    
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


@router.get("/{campaign_id}/followup-settings")
async def get_campaign_followup_settings(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get follow-up settings for a campaign"""
    db = get_db()
    
    campaign = await db.campaigns.find_one({
        "id": campaign_id,
        "user_id": current_user["user_id"]
    }, {"_id": 0, "followup_settings": 1, "id": 1, "name": 1})
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "campaign_id": campaign["id"],
        "campaign_name": campaign.get("name"),
        "settings": campaign.get("followup_settings") or DEFAULT_FOLLOWUP_SETTINGS
    }
