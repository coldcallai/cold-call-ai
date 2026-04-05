"""
Lead Service Module
Contains lead-related business logic and helper functions.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 3).
"""
import os
import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

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


def get_dial_recommendation(verification: Dict) -> str:
    """
    Generate a dial recommendation based on phone verification results.
    """
    line_type = verification.get("line_type", "unknown")
    is_valid = verification.get("is_valid", True)
    
    if not is_valid:
        return "Do not dial - invalid number"
    
    if line_type in ["mobile", "cellphone", "wireless"]:
        return "Priority dial - mobile numbers have highest answer rates"
    elif line_type in ["landline", "fixedline", "fixed"]:
        return "Standard dial - landline numbers have moderate answer rates"
    elif line_type in ["voip", "non-fixed voip", "virtual"]:
        return "Low priority - VoIP numbers may be spam filters or virtual"
    else:
        return "Unknown line type - proceed with caution"


async def log_usage_event(user_id: str, event_type: str, amount: int, credits_after: int):
    """
    Log a credit usage event for analytics tracking.
    """
    db = get_db()
    await db.usage_events.insert_one({
        "user_id": user_id,
        "event_type": event_type,
        "amount": amount,
        "credits_after": credits_after,
        "created_at": datetime.now(timezone.utc).isoformat()
    })


def generate_csv_content(leads: List[Dict], fieldnames: List[str]) -> str:
    """
    Generate CSV content from a list of leads.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for lead in leads:
        row = {}
        for field in fieldnames:
            value = lead.get(field, '')
            if isinstance(value, list):
                value = '; '.join(str(v) for v in value)
            row[field] = value
        writer.writerow(row)
    
    output.seek(0)
    return output.getvalue()


def parse_csv_leads(content: bytes, user_id: str) -> tuple:
    """
    Parse CSV content and return list of lead dicts and errors.
    Returns: (created_leads, errors)
    """
    import uuid
    
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    created_leads = []
    errors = []
    
    for idx, row in enumerate(reader):
        try:
            # Map common column names
            business_name = (
                row.get('business_name') or 
                row.get('company') or 
                row.get('name') or 
                row.get('Business Name') or 
                row.get('Company')
            )
            phone = (
                row.get('phone') or 
                row.get('Phone') or 
                row.get('phone_number') or 
                row.get('Phone Number')
            )
            email = row.get('email') or row.get('Email') or row.get('email_address')
            contact_name = (
                row.get('contact_name') or 
                row.get('contact') or 
                row.get('Contact') or 
                row.get('Contact Name')
            )
            industry = row.get('industry') or row.get('Industry')
            company_size = row.get('company_size') or row.get('size') or row.get('Company Size')
            
            if not business_name or not phone:
                errors.append(f"Row {idx + 1}: Missing business_name or phone")
                continue
            
            lead_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "business_name": business_name,
                "phone": phone,
                "email": email,
                "contact_name": contact_name,
                "industry": industry,
                "company_size": company_size,
                "source": "csv_upload",
                "status": "new",
                "intent_signals": ["Uploaded from CSV"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            created_leads.append(lead_data)
            
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
    
    return created_leads, errors
