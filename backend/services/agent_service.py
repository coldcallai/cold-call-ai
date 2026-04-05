"""
Agent Service Module
Contains agent-related business logic and voice helpers.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 4).
"""
import os
import base64
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


# ElevenLabs preset voices available for selection
ELEVENLABS_PRESET_VOICES = [
    {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "American, calm, professional"},
    {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "description": "American, confident, energetic"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "description": "American, soft, warm"},
    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "description": "American, well-rounded, calm"},
    {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "description": "American, emotional, engaging"},
    {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "description": "American, deep, narrative"},
    {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "description": "American, crisp, authoritative"},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "description": "American, deep, narrative"},
    {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "description": "American, raspy, casual"},
    {"id": "jBpfuIE2acCO8z3wKNLl", "name": "Gigi", "description": "American, expressive, animated"},
]


def get_preset_voices() -> List[Dict]:
    """Return list of available ElevenLabs preset voices"""
    return ELEVENLABS_PRESET_VOICES


async def get_user_cloned_voices(user_id: str) -> List[Dict]:
    """Get all cloned voices for a user"""
    db = get_db()
    voices = await db.cloned_voices.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(50)
    return voices


async def save_cloned_voice(
    user_id: str, 
    email: str,
    elevenlabs_voice_id: str, 
    name: str, 
    description: str
) -> Dict:
    """Save a new cloned voice to database"""
    import uuid
    db = get_db()
    
    cloned_voice_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "elevenlabs_voice_id": elevenlabs_voice_id,
        "name": name,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.cloned_voices.insert_one(cloned_voice_doc)
    return cloned_voice_doc


async def delete_cloned_voice_from_db(voice_id: str, user_id: str) -> Optional[Dict]:
    """Delete a cloned voice from database and return the voice doc"""
    db = get_db()
    
    voice = await db.cloned_voices.find_one({
        "id": voice_id,
        "user_id": user_id
    }, {"_id": 0})
    
    if not voice:
        return None
    
    # Delete from database
    await db.cloned_voices.delete_one({"id": voice_id, "user_id": user_id})
    
    # Update any agents using this voice to use default
    await db.agents.update_many(
        {"user_id": user_id, "cloned_voice_id": voice.get("elevenlabs_voice_id")},
        {"$set": {"voice_type": "preset", "cloned_voice_id": None, "cloned_voice_name": None}}
    )
    
    return voice


async def count_user_cloned_voices(user_id: str) -> int:
    """Count how many cloned voices a user has"""
    db = get_db()
    return await db.cloned_voices.count_documents({"user_id": user_id})


async def get_cloned_voice_by_elevenlabs_id(elevenlabs_voice_id: str, user_id: str) -> Optional[Dict]:
    """Get a cloned voice by its ElevenLabs ID"""
    db = get_db()
    return await db.cloned_voices.find_one({
        "elevenlabs_voice_id": elevenlabs_voice_id,
        "user_id": user_id
    }, {"_id": 0})


async def update_agent_voice_settings(
    agent_id: str,
    user_id: str,
    voice_type: str,
    voice_id: str,
    stability: float,
    similarity_boost: float,
    style: float
) -> Dict:
    """Update an agent's voice settings"""
    db = get_db()
    
    update_data = {
        "voice_type": voice_type,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style
        }
    }
    
    if voice_type == "preset":
        update_data["preset_voice_id"] = voice_id
        update_data["cloned_voice_id"] = None
        update_data["cloned_voice_name"] = None
    else:
        # Get cloned voice name
        cloned = await get_cloned_voice_by_elevenlabs_id(voice_id, user_id)
        if cloned:
            update_data["cloned_voice_id"] = voice_id
            update_data["cloned_voice_name"] = cloned.get("name")
    
    await db.agents.update_one(
        {"id": agent_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    return update_data
