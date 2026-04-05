"""
Bookings Routes Module
Contains all booking-related API endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 7).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum

from services.auth_service import get_current_user, get_db
from services.booking_service import send_meeting_booked_notifications

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/bookings", tags=["Bookings"])

# External service references (injected from main app)
_get_tier_features = None
_calendly_service = None
_LeadStatus = None


def set_services(get_tier_features_fn, calendly_service, LeadStatus):
    """Inject service references from main app"""
    global _get_tier_features, _calendly_service, _LeadStatus
    _get_tier_features = get_tier_features_fn
    _calendly_service = calendly_service
    _LeadStatus = LeadStatus


# ============== ENUMS ==============
class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELED = "canceled"
    NO_SHOW = "no_show"


# ============== MODELS ==============
class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    lead_id: str
    agent_id: str
    campaign_id: Optional[str] = None
    booking_link: str
    lead_name: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_email: Optional[str] = None
    agent_name: Optional[str] = None
    scheduled_time: Optional[str] = None
    calendly_event_uri: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BookMeetingRequest(BaseModel):
    lead_id: str
    agent_id: str
    campaign_id: Optional[str] = None
    notes: Optional[str] = None


# ============== BOOKING ENDPOINTS ==============

@router.post("")
async def book_meeting(
    request: BookMeetingRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Book a meeting with an agent for a qualified lead - generates personalized Calendly link"""
    db = get_db()
    user_id = current_user["user_id"]
    
    # Check feature access - calendar booking requires Professional+
    features = _get_tier_features(current_user)
    if not features.get("calendar_booking"):
        raise HTTPException(
            status_code=403,
            detail="Calendar booking integration requires Professional plan or higher."
        )
    
    # Multi-tenancy: Verify lead and agent belong to current user
    lead = await db.leads.find_one({"id": request.lead_id, "user_id": user_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if _LeadStatus and lead.get("status") != _LeadStatus.QUALIFIED:
        raise HTTPException(status_code=400, detail="Lead is not qualified for booking")
    
    agent = await db.agents.find_one({"id": request.agent_id, "user_id": user_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Generate personalized booking link with lead data pre-filled
    personalized_link = _calendly_service.generate_booking_link(
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
            "status": "booked",
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


@router.get("")
async def get_bookings(
    status: Optional[BookingStatus] = None,
    agent_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Get all bookings for the current user"""
    db = get_db()
    query = {"user_id": current_user["user_id"]}
    if status:
        query["status"] = status
    if agent_id:
        query["agent_id"] = agent_id
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return bookings


@router.get("/{booking_id}")
async def get_booking(booking_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific booking"""
    db = get_db()
    booking = await db.bookings.find_one(
        {"id": booking_id, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status: BookingStatus,
    scheduled_time: Optional[str] = None,
    calendly_event_uri: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Update booking status (e.g., when meeting is confirmed via Calendly webhook)"""
    db = get_db()
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


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: str,
    reason: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Cancel a booking"""
    db = get_db()
    booking = await db.bookings.find_one(
        {"id": booking_id, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Update booking status to canceled
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "status": BookingStatus.CANCELED,
            "cancel_reason": reason,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update lead status back to qualified
    await db.leads.update_one(
        {"id": booking["lead_id"], "user_id": current_user["user_id"]},
        {"$set": {
            "status": "qualified",
            "booking_id": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Booking canceled", "booking_id": booking_id}
