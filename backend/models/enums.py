"""Enumeration types for the application"""
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    BOOKED = "booked"

class CallStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    UNLIMITED = "unlimited"
    BYL = "byl"  # Bring Your List

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class FollowUpReason(str, Enum):
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    CALLBACK_REQUESTED = "callback_requested"
    NURTURE = "nurture"
    RETRY = "retry"
    SEQUENCE = "sequence"

class FollowUpStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SKIPPED = "skipped"

class PackType(str, Enum):
    LEADS = "leads"
    CALLS = "calls"
    TOPUP = "topup"

class CRMProvider(str, Enum):
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    PIPEDRIVE = "pipedrive"
