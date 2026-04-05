"""
Bookings Service Module
Contains booking-related business logic and helpers.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 7).
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


async def send_meeting_booked_notifications(lead: Dict, agent: Dict, user_id: str, booking_link: str):
    """Send notifications when a meeting is booked (background task)"""
    # This would integrate with email/SMS services
    logger.info(f"Meeting booked for lead {lead.get('business_name')} with agent {agent.get('name')}")
    # In production, this would send emails/SMS notifications
    pass
