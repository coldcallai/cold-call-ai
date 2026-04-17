"""
Billing/Subscriptions Routes Module
Contains Stripe subscription and billing endpoints.
Extracted from server.py as part of the Strangler Fig refactoring pattern (Phase 7).

NOTE: Stripe webhooks remain in server.py for stability.
"""
import os
import logging
import uuid
import stripe
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Form
from pydantic import BaseModel, Field

from services.auth_service import get_current_user, get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Billing"])

# Stripe configuration
stripe_api_key = os.environ.get("STRIPE_SECRET_KEY")
if stripe_api_key:
    stripe.api_key = stripe_api_key

# External service references (injected from main app)
_SUBSCRIPTION_PLANS = None
_get_or_create_stripe_customer = None
_get_or_create_stripe_price = None
_get_tier_features = None


def set_services(
    subscription_plans,
    get_or_create_stripe_customer_fn,
    get_or_create_stripe_price_fn,
    get_tier_features_fn
):
    """Inject service references from main app"""
    global _SUBSCRIPTION_PLANS, _get_or_create_stripe_customer, _get_or_create_stripe_price, _get_tier_features
    _SUBSCRIPTION_PLANS = subscription_plans
    _get_or_create_stripe_customer = get_or_create_stripe_customer_fn
    _get_or_create_stripe_price = get_or_create_stripe_price_fn
    _get_tier_features = get_tier_features_fn


# ============== SUBSCRIPTION FEATURES ==============

@router.get("/subscription/features")
async def get_subscription_features(current_user: Dict = Depends(get_current_user)):
    """Get features available for current user's subscription tier"""
    return _get_tier_features(current_user)


# ============== SUBSCRIPTION MANAGEMENT ==============

@router.post("/subscriptions/create")
async def create_subscription(
    request: Request,
    plan_id: str = Form(...),
    billing_cycle: str = Form("monthly"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a Stripe subscription with automatic recurring billing.
    Synthflow-style: auto-invoices on billing date, same-day recurring.
    """
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    if plan_id not in _SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    if billing_cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle")
    
    # Check if user already has active subscription
    if current_user.get("stripe_subscription_id"):
        try:
            existing_sub = stripe.Subscription.retrieve(current_user["stripe_subscription_id"])
            if existing_sub.status in ["active", "trialing"]:
                raise HTTPException(
                    status_code=400, 
                    detail="You already have an active subscription. Use the customer portal to manage it."
                )
        except stripe.error.StripeError:
            pass  # Subscription doesn't exist, proceed
    
    db = get_db()
    
    try:
        # Get or create Stripe customer
        customer_id = await _get_or_create_stripe_customer(current_user)
        
        # Get or create price
        price_id = await _get_or_create_stripe_price(plan_id, billing_cycle)
        
        # Build URLs
        origin = request.headers.get("origin", "https://intentbrain.ai")
        success_url = f"{origin}/app/settings?subscription=success"
        cancel_url = f"{origin}/app/packs?subscription=canceled"
        
        # Create checkout session for subscription
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                "metadata": {
                    "user_id": current_user["user_id"],
                    "plan_id": plan_id,
                    "billing_cycle": billing_cycle
                }
            },
            metadata={
                "user_id": current_user["user_id"],
                "plan_id": plan_id,
                "billing_cycle": billing_cycle,
                "type": "subscription"
            }
        )
        
        # Record pending subscription
        subscription_record = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "checkout_session_id": checkout_session.id,
            "plan_id": plan_id,
            "billing_cycle": billing_cycle,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscription_records.insert_one(subscription_record)
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions/portal")
async def get_customer_portal(
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get Stripe Customer Portal URL for managing subscription.
    Users can update payment method, cancel, or change plans here.
    """
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    customer_id = current_user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No payment profile found. Please subscribe first.")
    
    origin = request.headers.get("origin", "https://intentbrain.ai")
    return_url = f"{origin}/app/settings"
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        return {"portal_url": portal_session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to access billing portal")


@router.get("/subscriptions/current")
async def get_current_subscription(current_user: Dict = Depends(get_current_user)):
    """Get current subscription details"""
    if not stripe_api_key:
        return {"subscription": None, "message": "Stripe not configured"}
    
    subscription_id = current_user.get("stripe_subscription_id")
    if not subscription_id:
        return {
            "subscription": None,
            "tier": current_user.get("subscription_tier"),
            "status": current_user.get("subscription_status", "inactive")
        }
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Get upcoming invoice for next billing date
        upcoming_invoice = None
        try:
            upcoming = stripe.Invoice.upcoming(subscription=subscription_id)
            upcoming_invoice = {
                "amount_due": upcoming.amount_due / 100,
                "currency": upcoming.currency,
                "next_billing_date": datetime.fromtimestamp(upcoming.next_payment_attempt).isoformat() if upcoming.next_payment_attempt else None
            }
        except Exception:
            pass
        
        return {
            "subscription": {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "plan_id": subscription.metadata.get("plan_id"),
                "billing_cycle": subscription.metadata.get("billing_cycle", "monthly")
            },
            "upcoming_invoice": upcoming_invoice,
            "tier": current_user.get("subscription_tier"),
            "status": subscription.status
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving subscription: {e}")
        return {
            "subscription": None,
            "tier": current_user.get("subscription_tier"),
            "status": current_user.get("subscription_status", "inactive"),
            "error": str(e)
        }


@router.get("/subscriptions/invoices")
async def get_subscription_invoices(
    limit: int = 10,
    current_user: Dict = Depends(get_current_user)
):
    """Get invoice history for the customer"""
    if not stripe_api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    customer_id = current_user.get("stripe_customer_id")
    if not customer_id:
        return {"invoices": []}
    
    try:
        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=limit
        )
        
        return {
            "invoices": [{
                "id": inv.id,
                "number": inv.number,
                "status": inv.status,
                "amount_due": inv.amount_due / 100,
                "amount_paid": inv.amount_paid / 100,
                "currency": inv.currency,
                "created": datetime.fromtimestamp(inv.created).isoformat(),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url,
                "period_start": datetime.fromtimestamp(inv.period_start).isoformat() if inv.period_start else None,
                "period_end": datetime.fromtimestamp(inv.period_end).isoformat() if inv.period_end else None
            } for inv in invoices.data]
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")
