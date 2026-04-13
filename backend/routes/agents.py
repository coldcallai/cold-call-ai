"""
Agents Routes Module
Contains all agent-related API endpoints including voice cloning.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 4).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel, Field

from services.auth_service import get_current_user, get_db
from services.agent_service import (
    get_preset_voices,
    get_user_cloned_voices,
    save_cloned_voice,
    delete_cloned_voice_from_db,
    count_user_cloned_voices,
    get_cloned_voice_by_elevenlabs_id,
    update_agent_voice_settings,
    ELEVENLABS_PRESET_VOICES,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Agents"])

# External service references (injected from main app)
_eleven_client = None
_check_subscription_limit = None
_get_tier_features = None
_VoiceSettings = None


def set_services(eleven_client, check_subscription_limit_fn, get_tier_features_fn, VoiceSettings):
    """Inject service references from main app"""
    global _eleven_client, _check_subscription_limit, _get_tier_features, _VoiceSettings
    _eleven_client = eleven_client
    _check_subscription_limit = check_subscription_limit_fn
    _get_tier_features = get_tier_features_fn
    _VoiceSettings = VoiceSettings


# ============== MODELS ==============
class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    calendly_api_token: Optional[str] = None
    calendly_event_type_uri: Optional[str] = None
    is_active: bool = True
    max_daily_calls: int = 50
    assigned_leads: int = 0
    booked_meetings: int = 0
    use_case: str = "sales_cold_calling"
    system_prompt: Optional[str] = None
    voice_type: str = "preset"
    preset_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel by default
    cloned_voice_id: Optional[str] = None
    cloned_voice_name: Optional[str] = None
    voice_settings: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    calendly_link: str
    calendly_api_token: Optional[str] = None
    max_daily_calls: int = 50
    use_case: str = "sales_cold_calling"
    system_prompt: Optional[str] = None
    voice_type: str = "preset"
    preset_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    voice_settings: Optional[Dict[str, Any]] = None


# ============== AGENT CRUD ENDPOINTS ==============

@router.get("/agents", response_model=List[Agent])
async def get_agents(current_user: Dict = Depends(get_current_user)):
    """Get agents belonging to the current user"""
    db = get_db()
    agents = await db.agents.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(100)
    return agents


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, current_user: Dict = Depends(get_current_user)):
    """Get a specific agent (must belong to current user)"""
    db = get_db()
    agent = await db.agents.find_one({"id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/agents", response_model=Agent)
async def create_agent(agent: AgentCreate, current_user: Dict = Depends(get_current_user)):
    """Create a new agent owned by the current user"""
    db = get_db()
    
    # Check subscription tier limits for agents
    limit_check = await _check_subscription_limit(current_user, "agents")
    if not limit_check["allowed"]:
        raise HTTPException(status_code=403, detail=limit_check["reason"])
    
    agent_obj = Agent(**agent.model_dump(), user_id=current_user["user_id"])
    await db.agents.insert_one(agent_obj.model_dump())
    return agent_obj


@router.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    """Update an agent (must belong to current user)"""
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.agents.update_one(
        {"id": agent_id, "user_id": current_user["user_id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = await db.agents.find_one({"id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    return agent


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete an agent (must belong to current user)"""
    db = get_db()
    result = await db.agents.delete_one({"id": agent_id, "user_id": current_user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}


# ============== VOICE MANAGEMENT ENDPOINTS ==============

@router.get("/voices/presets")
async def get_preset_voices_endpoint(current_user: Dict = Depends(get_current_user)):
    """Get list of available ElevenLabs preset voices"""
    return {"voices": get_preset_voices()}


@router.get("/voices/cloned")
async def get_cloned_voices(current_user: Dict = Depends(get_current_user)):
    """Get user's cloned voices"""
    voices = await get_user_cloned_voices(current_user["user_id"])
    return {"voices": voices}


@router.post("/voices/clone")
async def clone_voice(
    files: List[UploadFile] = File(...),
    voice_name: str = Form(...),
    description: str = Form(""),
    current_user: Dict = Depends(get_current_user)
):
    """
    Clone a voice using ElevenLabs IVC (Instant Voice Cloning).
    Requires 1-5 audio files (MP3, WAV) totaling at least 30 seconds.
    """
    if not _eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured. Add ELEVENLABS_API_KEY to .env")
    
    if len(files) < 1 or len(files) > 5:
        raise HTTPException(status_code=400, detail="Please upload 1-5 audio files")
    
    # Check subscription tier (voice cloning is a premium feature)
    tier = current_user.get("subscription_tier")
    if tier not in ["pro", "unlimited", "enterprise"]:
        raise HTTPException(
            status_code=403, 
            detail="Voice cloning is available on Pro and higher plans. Please upgrade to use this feature."
        )
    
    # Check if user already has max cloned voices (limit to 5)
    existing_count = await count_user_cloned_voices(current_user["user_id"])
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 cloned voices allowed. Please delete one before creating a new one.")
    
    try:
        # Prepare files for ElevenLabs
        file_tuples = []
        for file in files:
            content = await file.read()
            file_tuples.append((file.filename, content))
        
        # Clone voice using ElevenLabs IVC
        voice = _eleven_client.clone(
            name=f"{voice_name}_{current_user['user_id'][:8]}",
            description=description or f"Cloned voice for {current_user['email']}",
            files=file_tuples
        )
        
        # Save to database
        cloned_voice_doc = await save_cloned_voice(
            user_id=current_user["user_id"],
            email=current_user["email"],
            elevenlabs_voice_id=voice.voice_id,
            name=voice_name,
            description=description
        )
        
        logger.info(f"Voice cloned successfully for user {current_user['user_id']}: {voice.voice_id}")
        
        return {
            "message": "Voice cloned successfully",
            "voice_id": voice.voice_id,
            "name": voice_name,
            "id": cloned_voice_doc["id"]
        }
        
    except Exception as e:
        logger.error(f"Voice cloning failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@router.delete("/voices/cloned/{voice_id}")
async def delete_cloned_voice(voice_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete a cloned voice"""
    voice = await delete_cloned_voice_from_db(voice_id, current_user["user_id"])
    
    if not voice:
        raise HTTPException(status_code=404, detail="Cloned voice not found")
    
    # Try to delete from ElevenLabs
    if _eleven_client and voice.get("elevenlabs_voice_id"):
        try:
            _eleven_client.voices.delete(voice["elevenlabs_voice_id"])
        except Exception as e:
            logger.warning(f"Failed to delete voice from ElevenLabs: {e}")
    
    return {"message": "Cloned voice deleted"}


@router.post("/voices/preview")
async def preview_voice(
    text: str = Form(...),
    voice_id: str = Form(...),
    current_user: Dict = Depends(get_current_user)
):
    """Generate a voice preview sample"""
    if not _eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")
    
    try:
        import base64
        
        audio_generator = _eleven_client.text_to_speech.convert(
            text=text[:500],  # Limit preview text
            voice_id=voice_id,
            model_id="eleven_flash_v2",
            voice_settings=_VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.3,
                use_speaker_boost=True
            )
        )
        
        # Collect audio data
        audio_data = b""
        for chunk in audio_generator:
            audio_data += chunk
        
        # Return as base64
        audio_b64 = base64.b64encode(audio_data).decode()
        
        return {
            "audio": f"data:audio/mpeg;base64,{audio_b64}",
            "text": text[:500]
        }
        
    except Exception as e:
        logger.error(f"Voice preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice preview failed: {str(e)}")


@router.put("/agents/{agent_id}/voice")
async def update_agent_voice(
    agent_id: str,
    voice_type: str = Form(...),
    voice_id: str = Form(...),
    stability: float = Form(0.5),
    similarity_boost: float = Form(0.75),
    style: float = Form(0.3),
    current_user: Dict = Depends(get_current_user)
):
    """Update an agent's voice settings"""
    db = get_db()
    
    agent = await db.agents.find_one({"id": agent_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if voice_type != "preset":
        # Verify cloned voice belongs to user
        cloned = await get_cloned_voice_by_elevenlabs_id(voice_id, current_user["user_id"])
        if not cloned:
            raise HTTPException(status_code=400, detail="Cloned voice not found")
    
    await update_agent_voice_settings(
        agent_id=agent_id,
        user_id=current_user["user_id"],
        voice_type=voice_type,
        voice_id=voice_id,
        stability=stability,
        similarity_boost=similarity_boost,
        style=style
    )
    
    return {"message": "Agent voice updated", "voice_type": voice_type, "voice_id": voice_id}
