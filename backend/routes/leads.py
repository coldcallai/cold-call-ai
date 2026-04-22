"""
Leads Routes Module
Contains all lead-related API endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 3).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from services.auth_service import get_current_user, get_db
from services.lead_service import (
    get_dial_recommendation,
    log_usage_event,
    generate_csv_content,
    parse_csv_leads,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/leads", tags=["Leads"])

# External service references (injected from main app)
_ai_service = None
_compliance_service = None
_icp_service = None
_crm_service = None
_get_tier_features = None
_check_subscription_limit = None


def set_services(ai_service, compliance_service, icp_service, crm_service, get_tier_features_fn, check_subscription_limit_fn):
    """Inject service references from main app"""
    global _ai_service, _compliance_service, _icp_service, _crm_service, _get_tier_features, _check_subscription_limit
    _ai_service = ai_service
    _compliance_service = compliance_service
    _icp_service = icp_service
    _crm_service = crm_service
    _get_tier_features = get_tier_features_fn
    _check_subscription_limit = check_subscription_limit_fn


# ============== ENUMS ==============
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    BOOKED = "booked"


# ============== REQUEST/RESPONSE MODELS ==============
class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    business_name: str
    contact_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: str = "manual"
    intent_signals: List[str] = []
    status: LeadStatus = LeadStatus.NEW
    qualification_score: Optional[int] = None
    is_decision_maker: Optional[bool] = None
    interest_level: Optional[int] = None
    line_type: Optional[str] = None
    carrier: Optional[str] = None
    phone_verified: bool = False
    icp_score: Optional[int] = None
    icp_breakdown: Optional[Dict[str, Any]] = None
    dial_priority: Optional[int] = None
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


class LeadDiscoveryRequest(BaseModel):
    search_query: str = "credit card processing"
    location: Optional[str] = None
    industry: Optional[str] = None
    max_results: int = 10
    campaign_id: Optional[str] = None


class GPTIntentSearchRequest(BaseModel):
    search_query: str
    location: Optional[str] = None
    industry: Optional[str] = None
    max_results: int = 10
    custom_keywords: Optional[List[str]] = None
    campaign_id: Optional[str] = None
    exclude_industries: Optional[List[str]] = None


class PreviewLeadsRequest(BaseModel):
    search_query: str
    location: Optional[str] = None
    industry: Optional[str] = None
    custom_keywords: Optional[List[str]] = None
    exclude_industries: Optional[List[str]] = None


class BulkVerifyRequest(BaseModel):
    lead_ids: Optional[List[str]] = None
    verify_all_unverified: bool = False


class BatchICPScoreRequest(BaseModel):
    lead_ids: List[str]
    use_ai: bool = False
    icp_config: Optional[Dict[str, Any]] = None


# ============== LEAD DISCOVERY ENDPOINTS ==============

@router.post("/preview-examples")
async def preview_lead_examples(
    request: PreviewLeadsRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Preview example leads based on keywords WITHOUT using credits.
    Returns 3 sample leads to show what kind of results the search would produce.
    """
    custom_keywords = None
    if request.custom_keywords:
        custom_keywords = [kw.strip() for kw in request.custom_keywords[:100] if kw and kw.strip()]
    
    preview_leads = await _ai_service.gpt_intent_search(
        query=request.search_query,
        industry=request.industry,
        location=request.location,
        max_results=3,
        custom_keywords=custom_keywords,
        exclude_industries=request.exclude_industries
    )
    
    return {
        "preview": True,
        "count": len(preview_leads),
        "message": "These are example leads based on your keywords. Run a full search to discover and save leads.",
        "example_leads": preview_leads,
        "keywords_used": custom_keywords[:10] if custom_keywords else ["Using default keywords"]
    }


@router.post("/discover")
async def discover_leads(request: LeadDiscoveryRequest, current_user: Dict = Depends(get_current_user)):
    """Discover new leads using AI-powered research (legacy endpoint)"""
    db = get_db()
    user_id = current_user["user_id"]
    
    discovered = await _ai_service.gpt_intent_search(
        query=request.search_query,
        location=request.location,
        max_results=request.max_results
    )
    
    created_leads = []
    for biz in discovered:
        lead_data = Lead(
            user_id=user_id,
            business_name=biz.get("name", "Unknown Business"),
            phone=biz.get("phone", ""),
            source="ai_discovery",
            intent_signals=biz.get("intent_signals", ["credit_card_processing_intent"])
        )
        lead_dict = lead_data.model_dump()
        if request.campaign_id:
            lead_dict["campaign_id"] = request.campaign_id
        await db.leads.insert_one(lead_dict)
        created_leads.append(lead_dict)
    
    return {
        "discovered": len(created_leads),
        "leads": created_leads
    }


@router.post("/gpt-intent-search")
async def gpt_intent_search(
    request: GPTIntentSearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Discover leads using GPT-5.2 powered intent search (deducts lead credits)"""
    db = get_db()
    user_id = current_user["user_id"]
    leads_requested = request.max_results
    leads_remaining = current_user.get("lead_credits_remaining", 0)
    
    # Check subscription tier limits
    limit_check = await _check_subscription_limit(current_user, "leads", leads_requested)
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    # Validate custom keywords based on tier
    features = _get_tier_features(current_user)
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
    
    discovered = await _ai_service.gpt_intent_search(
        query=request.search_query,
        industry=request.industry,
        location=request.location,
        max_results=request.max_results,
        custom_keywords=custom_keywords,
        exclude_industries=request.exclude_industries
    )
    
    created_leads = []
    skipped_duplicates = 0
    for biz in discovered:
        phone = (biz.get("phone") or "").strip()
        biz_name = biz.get("name", "Unknown Business")
        
        # Dedupe: skip if this user already has a lead with same phone OR same business name
        if phone or biz_name:
            dupe_query = {"user_id": user_id}
            or_conditions = []
            if phone:
                or_conditions.append({"phone": phone})
            if biz_name and biz_name != "Unknown Business":
                or_conditions.append({"business_name": biz_name})
            if or_conditions:
                dupe_query["$or"] = or_conditions
                existing = await db.leads.find_one(dupe_query, {"_id": 0, "id": 1})
                if existing:
                    skipped_duplicates += 1
                    continue
        
        lead_data = Lead(
            user_id=user_id,
            business_name=biz_name,
            phone=phone,
            email=biz.get("email"),
            source="gpt_intent_search",
            intent_signals=biz.get("intent_signals", [])
        )
        lead_dict = lead_data.model_dump()
        if request.campaign_id:
            lead_dict["campaign_id"] = request.campaign_id
        await db.leads.insert_one(lead_dict)
        created_leads.append(lead_dict)
    
    leads_discovered = len(created_leads)
    
    # Deduct credits
    if leads_discovered > 0:
        new_balance = leads_remaining - leads_discovered
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"lead_credits_remaining": -leads_discovered},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        await log_usage_event(
            user_id=user_id,
            event_type="lead_discovery",
            amount=leads_discovered,
            credits_after=new_balance
        )
    
    return {
        "discovered": leads_discovered,
        "skipped_duplicates": skipped_duplicates,
        "source": "gpt_intent_search",
        "leads": created_leads,
        "credits_used": leads_discovered,
        "credits_remaining": leads_remaining - leads_discovered
    }


# ============== BACKFILL / ORPHAN LEAD REPAIR ==============

class BackfillOrphanRequest(BaseModel):
    campaign_id: Optional[str] = None  # If provided, assign orphan leads to this campaign


@router.post("/backfill-orphans")
async def backfill_orphan_leads(
    request: BackfillOrphanRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Repair leads that were saved without user_id or campaign_id due to old bug.
    - Assigns user_id = current user to any lead missing user_id that was created via discovery sources.
    - Optionally assigns provided campaign_id to leads with missing/null campaign_id.
    Safe to run multiple times.
    """
    db = get_db()
    user_id = current_user["user_id"]
    
    # Step 1: adopt orphan discovery leads (no user_id at all) created in the last 30 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    adopt_query = {
        "$or": [{"user_id": {"$exists": False}}, {"user_id": None}],
        "source": {"$in": ["gpt_intent_search", "ai_discovery"]},
        "created_at": {"$gte": cutoff}
    }
    adopt_result = await db.leads.update_many(
        adopt_query,
        {"$set": {"user_id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Step 2: optionally assign a campaign to this user's leads that have none
    campaign_assigned = 0
    if request.campaign_id:
        # Verify campaign belongs to user
        campaign = await db.campaigns.find_one(
            {"id": request.campaign_id, "user_id": user_id}, {"_id": 0}
        )
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_query = {
            "user_id": user_id,
            "$or": [{"campaign_id": {"$exists": False}}, {"campaign_id": None}, {"campaign_id": ""}]
        }
        campaign_result = await db.leads.update_many(
            campaign_query,
            {"$set": {"campaign_id": request.campaign_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        campaign_assigned = campaign_result.modified_count
    
    # Stats for confirmation
    total_user_leads = await db.leads.count_documents({"user_id": user_id})
    
    return {
        "success": True,
        "adopted_orphan_leads": adopt_result.modified_count,
        "assigned_to_campaign": campaign_assigned,
        "total_leads_for_user": total_user_leads,
        "message": f"Adopted {adopt_result.modified_count} orphan leads. Assigned {campaign_assigned} to campaign."
    }



@router.post("/deduplicate")
async def deduplicate_leads(current_user: Dict = Depends(get_current_user)):
    """
    Remove duplicate leads for current user.
    Groups by phone number (primary) and business_name (fallback).
    Keeps the oldest lead in each group, deletes the rest.
    Leads in non-'new' status are preserved.
    """
    db = get_db()
    user_id = current_user["user_id"]
    
    # Fetch all user leads sorted by created_at ascending (oldest first)
    leads = await db.leads.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(50000)
    
    seen_phones = {}
    seen_names = {}
    to_delete = []
    
    for lead in leads:
        lead_id = lead.get("id")
        phone = (lead.get("phone") or "").strip()
        name = (lead.get("business_name") or "").strip().lower()
        status = lead.get("status", "new")
        
        # Never delete leads that have been actioned (contacted/qualified/booked/etc.)
        if status != "new":
            if phone:
                seen_phones[phone] = lead_id
            if name:
                seen_names[name] = lead_id
            continue
        
        is_dup = False
        if phone and phone in seen_phones:
            is_dup = True
        elif name and name in seen_names and name != "unknown business":
            is_dup = True
        
        if is_dup:
            to_delete.append(lead_id)
        else:
            if phone:
                seen_phones[phone] = lead_id
            if name:
                seen_names[name] = lead_id
    
    deleted_count = 0
    if to_delete:
        result = await db.leads.delete_many({
            "user_id": user_id,
            "id": {"$in": to_delete},
            "status": "new"
        })
        deleted_count = result.deleted_count
    
    remaining = await db.leads.count_documents({"user_id": user_id})
    
    return {
        "success": True,
        "duplicates_removed": deleted_count,
        "remaining_leads": remaining,
        "message": f"Removed {deleted_count} duplicate leads. {remaining} unique leads remain."
    }


# ============== LEADS CRUD ==============

@router.get("", response_model=List[Lead])
async def get_leads(
    status: Optional[LeadStatus] = None,
    limit: int = Query(100, le=500),
    skip: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Get leads belonging to the current user"""
    db = get_db()
    query = {"user_id": current_user["user_id"]}
    if status:
        query["status"] = status
    
    leads = await db.leads.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return leads


@router.get("/export-csv")
async def export_leads_csv(
    status: Optional[LeadStatus] = None, 
    line_type: Optional[str] = Query(default=None, description="Filter by line type: mobile, landline, voip"),
    current_user: Dict = Depends(get_current_user)
):
    """Export leads to CSV (only user's own leads)."""
    db = get_db()
    features = _get_tier_features(current_user)
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
    
    fieldnames = ['business_name', 'contact_name', 'phone', 'email', 'status', 'line_type', 'carrier', 'source', 'intent_signals', 'qualification_score', 'created_at']
    csv_content = generate_csv_content(leads, fieldnames)
    
    filename_parts = ["leads"]
    if line_type:
        filename_parts.append(line_type)
    if status:
        filename_parts.append(status)
    filename_parts.append(datetime.now().strftime('%Y%m%d_%H%M%S'))
    filename = "_".join(filename_parts) + ".csv"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export-mobile-csv")
async def export_mobile_leads_csv(
    status: Optional[LeadStatus] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Export only mobile phone leads to CSV."""
    db = get_db()
    features = _get_tier_features(current_user)
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
    
    fieldnames = ['phone', 'business_name', 'contact_name', 'email', 'carrier', 'status', 'qualification_score']
    csv_content = generate_csv_content(leads, fieldnames)
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mobile_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/phone-stats")
async def get_lead_phone_stats(current_user: Dict = Depends(get_current_user)):
    """Get statistics about lead phone types."""
    db = get_db()
    user_id = current_user["user_id"]
    
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$line_type", "count": {"$sum": 1}}}
    ]
    
    results = await db.leads.aggregate(pipeline).to_list(100)
    
    stats = {"mobile": 0, "landline": 0, "voip": 0, "unknown": 0, "total": 0}
    
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


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific lead (must belong to current user)"""
    db = get_db()
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("", response_model=Lead)
async def create_lead(lead: LeadCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new lead owned by the current user"""
    db = get_db()
    lead_obj = Lead(**lead.model_dump(), user_id=current_user["user_id"])
    await db.leads.insert_one(lead_obj.model_dump())
    return lead_obj


@router.post("/{lead_id}/verify-phone")
async def verify_lead_phone(lead_id: str, current_user: Dict = Depends(get_current_user)):
    """Verify a lead's phone number and update with line type."""
    db = get_db()
    user_id = current_user["user_id"]
    
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    phone = lead.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")
    
    verification = await _compliance_service.verify_number(phone)
    
    update_data = {
        "line_type": verification.get("line_type", "unknown"),
        "carrier": verification.get("carrier"),
        "phone_verified": verification.get("is_valid", False),
        "dial_priority": verification.get("dial_priority", 50),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.leads.update_one({"id": lead_id, "user_id": user_id}, {"$set": update_data})
    
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


@router.post("/verify-phones-bulk")
async def verify_leads_phones_bulk(request: BulkVerifyRequest, current_user: Dict = Depends(get_current_user)):
    """Bulk verify phone numbers for multiple leads."""
    db = get_db()
    user_id = current_user["user_id"]
    
    query = {"user_id": user_id}
    
    if request.lead_ids:
        query["id"] = {"$in": request.lead_ids}
    elif request.verify_all_unverified:
        query["phone_verified"] = {"$ne": True}
    else:
        raise HTTPException(status_code=400, detail="Provide lead_ids or set verify_all_unverified=true")
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(500)
    
    if not leads:
        return {"message": "No leads to verify", "verified": 0}
    
    results = {"total": len(leads), "verified": 0, "mobile": 0, "landline": 0, "voip": 0, "unknown": 0, "failed": 0}
    
    for lead in leads:
        phone = lead.get("phone")
        if not phone:
            results["failed"] += 1
            continue
        
        try:
            verification = await _compliance_service.verify_number(phone)
            line_type = verification.get("line_type", "unknown")
            
            update_data = {
                "line_type": line_type,
                "carrier": verification.get("carrier"),
                "phone_verified": verification.get("is_valid", False),
                "dial_priority": verification.get("dial_priority", 50),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.leads.update_one({"id": lead["id"], "user_id": user_id}, {"$set": update_data})
            
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


@router.put("/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str, 
    updates: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Update a lead (must belong to current user)"""
    db = get_db()
    user_id = current_user["user_id"]
    
    current_lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if not current_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    old_status = current_lead.get("status")
    new_status = updates.get("status")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.leads.update_one({"id": lead_id, "user_id": user_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    
    # Auto-push to CRM when lead becomes qualified
    if new_status == "qualified" and old_status != "qualified":
        features = _get_tier_features(current_user)
        if features.get("crm_integration") and _crm_service:
            background_tasks.add_task(_crm_service.auto_push_qualified_lead, user_id, lead)
            logger.info(f"Queued CRM push for qualified lead {lead_id}")
    
    return lead


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a lead (must belong to current user)"""
    db = get_db()
    result = await db.leads.delete_one({"id": lead_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}


@router.post("/upload-csv")
async def upload_leads_csv(file: UploadFile = File(...), current_user: Dict = Depends(get_current_user)):
    """Upload leads from CSV file (Bring Your Own List)"""
    db = get_db()
    features = _get_tier_features(current_user)
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
        created_leads, errors = parse_csv_leads(content, user_id)
        
        # Insert all leads
        if created_leads:
            await db.leads.insert_many(created_leads)
        
        return {
            "uploaded": len(created_leads),
            "errors": len(errors),
            "error_details": errors[:10] if errors else [],
            "message": f"Successfully uploaded {len(created_leads)} leads"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


# ============== ICP SCORING ENDPOINTS ==============

@router.post("/{lead_id}/icp-score")
async def score_lead_icp(
    lead_id: str,
    use_ai: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """Score a single lead based on ICP (Ideal Customer Profile)."""
    db = get_db()
    features = _get_tier_features(current_user)
    
    if not features.get("icp_scoring"):
        raise HTTPException(status_code=403, detail="ICP scoring is not available on your plan. Upgrade to Starter or higher.")
    
    if use_ai and not features.get("ai_icp_scoring"):
        raise HTTPException(status_code=403, detail="AI-powered ICP scoring requires Professional or higher plan.")
    
    lead = await db.leads.find_one({"id": lead_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if use_ai:
        score_result = await _icp_service.score_lead_with_ai(lead)
    else:
        score_result = await _icp_service.score_lead(lead)
    
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {
            "icp_score": score_result["total_score"],
            "icp_breakdown": score_result["breakdown"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"lead_id": lead_id, "business_name": lead.get("business_name"), **score_result}


@router.post("/batch-icp-score")
async def batch_score_leads_icp(request: BatchICPScoreRequest, current_user: Dict = Depends(get_current_user)):
    """Score multiple leads for ICP fit."""
    features = _get_tier_features(current_user)
    
    if not features.get("icp_scoring"):
        raise HTTPException(status_code=403, detail="ICP scoring is not available on your plan. Upgrade to Starter or higher.")
    
    if request.use_ai and not features.get("ai_icp_scoring"):
        raise HTTPException(status_code=403, detail="AI-powered ICP scoring requires Professional or higher plan.")
    
    if len(request.lead_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 leads per batch")
    
    results = await _icp_service.batch_score_leads(request.lead_ids, request.icp_config, request.use_ai)
    
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


@router.get("/by-icp-score")
async def get_leads_by_icp_score(
    min_score: int = Query(0, ge=0, le=100),
    tier: Optional[str] = Query(None, description="A, B, C, or D"),
    limit: int = Query(50, le=200),
    current_user: Dict = Depends(get_current_user)
):
    """Get leads sorted by ICP score (highest first)."""
    db = get_db()
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
