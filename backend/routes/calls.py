"""
Calls Routes Module
Contains call-related API endpoints (READ operations and analytics).
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 6).

NOTE: This module handles READ operations and analytics only.
Twilio webhooks, call initiation (/calls/initiate), and realtime WebSocket
remain in server.py due to their complexity and tight coupling with Twilio services.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum

from services.auth_service import get_current_user, get_db
from services.call_service import calculate_analytics

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Calls"])

# External service references (injected from main app)
_get_tier_features = None
_twilio_service = None
_twilio_phone_number = None
_recording_service = None


def set_services(get_tier_features_fn, twilio_service, twilio_phone_number, recording_service):
    """Inject service references from main app"""
    global _get_tier_features, _twilio_service, _twilio_phone_number, _recording_service
    _get_tier_features = get_tier_features_fn
    _twilio_service = twilio_service
    _twilio_phone_number = twilio_phone_number
    _recording_service = recording_service


# ============== ENUMS ==============
class CallStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"


# ============== MODELS ==============
class Call(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    lead_id: str
    campaign_id: str
    agent_id: Optional[str] = None
    status: CallStatus = CallStatus.PENDING
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_seconds: int = 0
    recording_url: Optional[str] = None
    recording_sid: Optional[str] = None
    transcript: Optional[Any] = None  # Can be string or list of dicts
    full_transcript: Optional[str] = None
    transcript_segments: Optional[List[Dict]] = None
    transcription_status: Optional[str] = None
    qualification_result: Optional[Dict[str, Any]] = None
    twilio_sid: Optional[str] = None
    answered_by: Optional[str] = None
    amd_status: Optional[str] = None
    amd_duration_ms: Optional[int] = None
    voicemail_dropped: bool = False
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== TWILIO STATUS ENDPOINT ==============

@router.get("/calls/twilio-status")
async def get_twilio_status():
    """Check if Twilio is configured"""
    return {
        "configured": _twilio_service.is_configured if _twilio_service else False,
        "phone_number": _twilio_phone_number[:6] + "****" if _twilio_phone_number else None
    }


# ============== CALLS CRUD ENDPOINTS ==============

@router.get("/calls", response_model=List[Call])
async def get_calls(
    status: Optional[CallStatus] = None,
    campaign_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Get calls belonging to the current user"""
    db = get_db()
    user_id = current_user["user_id"]
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    if campaign_id:
        query["campaign_id"] = campaign_id
    
    calls = await db.calls.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return calls


@router.get("/calls/{call_id}", response_model=Call)
async def get_call(call_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific call (must belong to current user)"""
    db = get_db()
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


# ============== ANALYTICS ENDPOINT ==============

@router.get("/analytics")
async def get_analytics(
    range: str = Query("7d", regex="^(7d|30d|90d|all)$"),
    current_user: Dict = Depends(get_current_user)
):
    """Get call analytics for the current user"""
    return await calculate_analytics(current_user["user_id"], range)


# ============== AMD STATUS ENDPOINT ==============

@router.get("/calls/{call_id}/amd-status")
async def get_call_amd_status(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get AMD (Answering Machine Detection) status for a specific call"""
    db = get_db()
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


# ============== RECORDING & TRANSCRIPTION ENDPOINTS ==============

@router.get("/calls/{call_id}/recording")
async def get_call_recording(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get call recording details and playback URL.
    Requires Starter tier or higher.
    """
    features = _get_tier_features(current_user)
    if not features.get("call_recording"):
        raise HTTPException(
            status_code=403,
            detail="Call recording requires Starter plan or higher."
        )
    
    db = get_db()
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


@router.get("/calls/{call_id}/transcript")
async def get_call_transcript(
    call_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get call transcript (full text and timestamped segments).
    Requires Professional tier or higher.
    """
    features = _get_tier_features(current_user)
    if not features.get("call_transcription"):
        raise HTTPException(
            status_code=403,
            detail="Call transcription requires Professional plan or higher."
        )
    
    db = get_db()
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


@router.post("/calls/{call_id}/transcribe")
async def request_transcription(
    call_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Request transcription for a call recording.
    Useful if automatic transcription failed or was not triggered.
    """
    features = _get_tier_features(current_user)
    if not features.get("call_transcription"):
        raise HTTPException(
            status_code=403,
            detail="Call transcription requires Professional plan or higher."
        )
    
    db = get_db()
    call = await db.calls.find_one({"id": call_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.get("recording_sid"):
        raise HTTPException(status_code=400, detail="No recording available for this call")
    
    if call.get("transcription_status") == "processing":
        return {"message": "Transcription already in progress", "status": "processing"}
    
    # Process in background
    if _recording_service:
        background_tasks.add_task(
            _recording_service.process_call_recording,
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
