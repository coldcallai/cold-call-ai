"""
Authentication Service Module
Contains password hashing, session management, and user authentication helpers.
Extracted from server.py as part of the Strangler Fig refactoring pattern.
"""
import os
import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'intentbrain_default_secret_key')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Security bearer
security = HTTPBearer(auto_error=False)

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


# ============== PASSWORD UTILITIES ==============
def hash_password(password: str) -> str:
    """
    Hash password using PBKDF2-SHA256 with random salt.
    Format: salt$hash
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against stored hash.
    Returns True if password matches, False otherwise.
    """
    try:
        salt, hash_hex = hashed.split('$')
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == hash_hex
    except Exception:
        return False


# ============== SESSION MANAGEMENT ==============
async def create_session(user_id: str, expires_days: int = 7) -> str:
    """
    Create a new session for a user.
    Returns the session token.
    """
    db = get_db()
    session_token = f"sess_{uuid.uuid4().hex}"
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=expires_days),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    return session_token


async def get_session_from_token(token: str) -> Optional[Dict]:
    """
    Get user from session token.
    Returns user document if valid, None if invalid or expired.
    """
    db = get_db()
    session_doc = await db.user_sessions.find_one({"session_token": token})
    if not session_doc:
        return None
    
    # Check expiration
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Get user
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    return user_doc


async def delete_session(session_token: str) -> bool:
    """Delete a session token. Returns True if deleted."""
    db = get_db()
    result = await db.user_sessions.delete_one({"session_token": session_token})
    return result.deleted_count > 0


# ============== AUTHENTICATION DEPENDENCIES ==============
async def get_current_user(
    request: Request, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """
    Get current user from session - checks cookies first, then Authorization header.
    Raises HTTPException 401 if not authenticated.
    """
    session_token = None
    
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Fall back to Authorization header
    if not session_token and credentials:
        session_token = credentials.credentials
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_session_from_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user


async def get_optional_user(
    request: Request, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """
    Get current user if authenticated, otherwise return None.
    Does not raise exception for unauthenticated requests.
    """
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


# ============== PHONE UTILITIES ==============
def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    # Remove all non-digit characters except leading +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    # If no + prefix and 10 digits, assume US number
    if not cleaned.startswith('+') and len(cleaned) == 10:
        cleaned = '+1' + cleaned
    elif not cleaned.startswith('+') and len(cleaned) == 11 and cleaned.startswith('1'):
        cleaned = '+' + cleaned
    return cleaned
