"""Billing-related models and pricing constants"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid

from .enums import PackType


class PackPurchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pack_id: str
    pack_type: str
    quantity: int
    price: float
    purchased_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AccountUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    leads_remaining: int = 0
    calls_remaining: int = 0
    leads_used: int = 0
    calls_used: int = 0
    purchases: List[Dict] = []
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    industry: Optional[str] = None
    max_results: int = 10


class UsageEvent(BaseModel):
    event_type: str
    amount: int
    description: Optional[str] = None


# Subscription Plans
SUBSCRIPTION_PLANS = {
    # BYOL Plans (Bring Your Own List)
    "byol_starter": {
        "name": "BYOL Starter",
        "price": 199,
        "leads_per_month": 0,
        "calls_per_month": 250,
        "features": ["250 AI calls", "CSV upload", "Call recordings", "AI qualifying", "Auto booking", "7-day recordings"],
        "users": 1,
        "plan_type": "byol"
    },
    "byol_pro": {
        "name": "BYOL Pro",
        "price": 449,
        "leads_per_month": 0,
        "calls_per_month": 750,
        "features": ["750 AI calls", "CSV upload", "Call transcripts", "AI qualifying", "Auto booking", "30-day recordings", "Custom scripts"],
        "users": 3,
        "plan_type": "byol"
    },
    "byol_scale": {
        "name": "BYOL Scale",
        "price": 799,
        "leads_per_month": 0,
        "calls_per_month": 1500,
        "features": ["1,500 AI calls", "Unlimited CSV uploads", "Call transcripts", "AI qualifying", "Auto booking", "60-day recordings", "Custom scripts", "Priority support"],
        "users": 5,
        "plan_type": "byol"
    },
    # Full Service Plans (Lead Discovery + Calling)
    "discovery_starter": {
        "name": "Discovery Starter",
        "price": 399,
        "leads_per_month": 500,
        "calls_per_month": 250,
        "features": ["500 intent leads/mo", "250 AI calls", "Apollo.io lead discovery", "AI qualifying", "Auto booking", "7-day recordings"],
        "users": 1,
        "plan_type": "full_service"
    },
    "discovery_pro": {
        "name": "Discovery Pro",
        "price": 899,
        "leads_per_month": 1500,
        "calls_per_month": 750,
        "features": ["1,500 intent leads/mo", "750 AI calls", "Apollo.io lead discovery", "Call transcripts", "Auto booking", "30-day recordings", "Custom scripts"],
        "users": 3,
        "plan_type": "full_service"
    },
    "discovery_elite": {
        "name": "Discovery Elite",
        "price": 1599,
        "leads_per_month": 3000,
        "calls_per_month": 2000,
        "features": ["3,000 intent leads/mo", "2,000 AI calls", "Apollo.io lead discovery", "Call transcripts", "Auto booking", "90-day recordings", "Custom scripts", "Priority support", "5 team seats"],
        "users": 5,
        "plan_type": "full_service"
    },
    # Legacy/Test Plans
    "test_drive": {
        "name": "Test Drive",
        "price": 49,
        "leads_per_month": 0,
        "calls_per_month": 50,
        "features": ["50 AI calls", "Call recordings", "Basic dashboard", "CSV upload"],
        "users": 1,
        "is_test_plan": True
    },
    "payg": {
        "name": "Pay-as-you-go",
        "price": 0,
        "leads_per_month": 0,
        "calls_per_month": 0,
        "features": ["No monthly commitment", "Pay per call/lead", "Basic dashboard"],
        "users": 1,
        "credit_cost": {
            "per_lead": 0.25,
            "per_call": 0.50,
        }
    }
}

# Pay-as-you-go Credit Packs
PAYG_CREDIT_PACKS = [
    {"id": "payg_starter_10", "name": "Starter Pack", "leads": 25, "calls": 25, "price": 19, "per_lead": 0.38, "per_call": 0.38, "bonus": "Perfect for testing"},
    {"id": "payg_growth_50", "name": "Growth Pack", "leads": 100, "calls": 100, "price": 69, "per_lead": 0.35, "per_call": 0.35, "bonus": "10% savings"},
    {"id": "payg_scale_200", "name": "Scale Pack", "leads": 400, "calls": 400, "price": 249, "per_lead": 0.31, "per_call": 0.31, "bonus": "20% savings"},
]

# Lead Packs
LEAD_PACKS = [
    {"id": "leads_500", "name": "500 Leads", "quantity": 500, "price": 79, "type": "leads", "per_lead": 0.158},
    {"id": "leads_1500", "name": "1,500 Leads", "quantity": 1500, "price": 199, "type": "leads", "per_lead": 0.133},
    {"id": "leads_5000", "name": "5,000 Leads", "quantity": 5000, "price": 499, "type": "leads", "per_lead": 0.10},
]

# Call Packs
CALL_PACKS = [
    {"id": "calls_250", "name": "250 AI Calls", "quantity": 250, "price": 99, "type": "calls", "per_call": 0.396},
    {"id": "calls_500", "name": "500 AI Calls", "quantity": 500, "price": 179, "type": "calls", "per_call": 0.358},
    {"id": "calls_1000", "name": "1,000 AI Calls", "quantity": 1000, "price": 349, "type": "calls", "per_call": 0.349},
]

# Combo Packs
COMBO_PACKS = [
    {"id": "combo_starter", "name": "Starter Combo", "leads": 500, "calls": 250, "price": 99, "bonus": "Save $39"},
    {"id": "combo_growth", "name": "Growth Combo", "leads": 1000, "calls": 500, "price": 179, "bonus": "Save $99"},
    {"id": "combo_power", "name": "Power Combo", "leads": 2000, "calls": 1000, "price": 299, "bonus": "Save $148"},
]

# Top-up Packs
TOPUP_PACKS = [
    {"id": "topup_test_1", "name": "Test Pack (1 Lead)", "quantity": 1, "price": 1, "type": "topup", "credit_type": "leads", "per_unit": 1.00},
    {"id": "topup_100_leads", "name": "100 Leads Top-up", "quantity": 100, "price": 24, "type": "topup", "credit_type": "leads", "per_unit": 0.24},
    {"id": "topup_250_leads", "name": "250 Leads Top-up", "quantity": 250, "price": 55, "type": "topup", "credit_type": "leads", "per_unit": 0.22},
    {"id": "topup_100_calls", "name": "100 Calls Top-up", "quantity": 100, "price": 29, "type": "topup", "credit_type": "calls", "per_unit": 0.29},
]

# Annual Prepay Discounts
PREPAY_DISCOUNTS = {
    "quarterly": 0.05,
    "annual": 0.15
}
