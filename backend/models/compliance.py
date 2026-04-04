"""Compliance-related models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


class DNCSuppression(BaseModel):
    """Do Not Call suppression list entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str
    reason: str
    source: str
    added_by: Optional[str] = None
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NumberVerification(BaseModel):
    """Phone number verification result"""
    phone_number: str
    is_valid: bool
    line_type: str
    is_business: bool
    carrier: Optional[str] = None
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComplianceCheck(BaseModel):
    """Pre-call compliance check result"""
    phone_number: str
    is_allowed: bool
    reasons: List[str] = []
    checks_performed: List[str] = []
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AICallScript(BaseModel):
    """AI call script with compliance disclosure"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    disclosure: str
    greeting: str
    value_proposition: str
    qualification_questions: List[str]
    objection_handlers: Dict[str, str]
    booking_script: str
    dnc_script: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComplianceAcknowledgment(BaseModel):
    version: str
    acknowledged_items: List[str]


# Default compliant AI call script
DEFAULT_AI_SCRIPT = {
    "disclosure": "Hi, this is an AI assistant calling on behalf of {company_name}. This is an automated business call.",
    "greeting": "Is this {contact_name} at {business_name}?",
    "value_proposition": "I'm reaching out because we help businesses like yours {value_prop}. Many companies in your industry are seeing {benefit}.",
    "qualification_questions": [
        "Are you the person who handles {decision_area} for your business?",
        "Is this something your company is currently exploring?",
        "What's your timeline for making a decision on this?"
    ],
    "objection_handlers": {
        "not_interested": "I understand. Before I go, may I ask what solution you're currently using?",
        "bad_time": "No problem. When would be a better time to have a brief conversation?",
        "send_info": "Absolutely. What email should I send that to?",
        "already_have": "Great. How's that working out for you? Any challenges?"
    },
    "booking_script": "Excellent! I'd like to connect you with one of our specialists. They can show you exactly how this works. Do you have 15 minutes this week for a quick call?",
    "dnc_script": "No problem at all. I'll make sure you don't receive any more calls from us. Have a great day!"
}
