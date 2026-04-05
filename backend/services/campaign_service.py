"""
Campaign Service Module
Contains campaign-related business logic and helpers.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 5).
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB connection (lazy initialization)
_db = None

def get_db():
    """Get MongoDB database instance"""
    global _db
    if _db is None:
        mongo_url = os.environ['MONGO_URL']
        is_localhost = 'localhost' in mongo_url or '127.0.0.1' in mongo_url
        if is_localhost:
            client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000
            )
        else:
            client = AsyncIOMotorClient(
                mongo_url,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000
            )
        _db = client[os.environ['DB_NAME']]
    return _db


# Default follow-up settings
DEFAULT_FOLLOWUP_SETTINGS = {
    "enabled": True,
    "no_answer_retry_enabled": True,
    "no_answer_retry_count": 3,
    "no_answer_retry_delay_hours": 24,
    "voicemail_followup_enabled": True,
    "voicemail_followup_delay_hours": 48,
    "sequence_id": None
}


async def get_campaign_leads(campaign_id: str, user_id: str) -> List[Dict]:
    """Get leads assigned to a campaign"""
    db = get_db()
    leads = await db.leads.find(
        {"user_id": user_id, "$or": [
            {"campaign_id": campaign_id},
            {"assigned_campaigns": campaign_id}
        ]},
        {"_id": 0, "id": 1}
    ).to_list(500)
    return leads


async def update_lead_dial_priority(lead_id: str, user_id: str, icp_score: int) -> None:
    """Update a lead's dial priority based on ICP score and phone verification"""
    db = get_db()
    lead = await db.leads.find_one({"id": lead_id, "user_id": user_id}, {"_id": 0})
    if lead:
        phone_priority = lead.get("verification", {}).get("dial_priority", 50)
        # Combined priority: 60% ICP + 40% phone quality
        dial_priority = int(icp_score * 0.6 + phone_priority * 0.4)
        
        await db.leads.update_one(
            {"id": lead_id, "user_id": user_id},
            {"$set": {"dial_priority": dial_priority}}
        )


async def auto_schedule_followup(call_id: str, outcome: str, user_id: str) -> None:
    """
    Automatically schedule follow-up based on call outcome.
    This is called as a background task after calls complete.
    """
    db = get_db()
    
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
        "status": "pending"
    })
    if existing:
        logger.info(f"Lead {call['lead_id']} already has pending follow-up")
        return
    
    # Determine follow-up type and delay
    import uuid
    followup_doc = None
    
    if outcome == "no_answer" and settings.get("no_answer_retry_enabled", True):
        # Check retry count
        retry_count = await db.calls.count_documents({
            "lead_id": call["lead_id"],
            "campaign_id": call["campaign_id"],
            "status": "no_answer"
        })
        
        if retry_count < settings.get("no_answer_retry_count", 3):
            delay_hours = settings.get("no_answer_retry_delay_hours", 24)
            scheduled_time = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
            
            followup_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "lead_id": call["lead_id"],
                "campaign_id": call["campaign_id"],
                "call_id": call_id,
                "type": "no_answer_retry",
                "status": "pending",
                "scheduled_at": scheduled_time.isoformat(),
                "retry_number": retry_count + 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
    
    elif outcome == "voicemail" and settings.get("voicemail_followup_enabled", True):
        delay_hours = settings.get("voicemail_followup_delay_hours", 48)
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
        
        followup_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "lead_id": call["lead_id"],
            "campaign_id": call["campaign_id"],
            "call_id": call_id,
            "type": "voicemail_followup",
            "status": "pending",
            "scheduled_at": scheduled_time.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    if followup_doc:
        await db.followups.insert_one(followup_doc)
        logger.info(f"Scheduled {followup_doc['type']} for lead {call['lead_id']}")


# Import timedelta for the auto_schedule_followup function
from datetime import timedelta
