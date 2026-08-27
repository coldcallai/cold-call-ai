from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from pymongo import ReturnDocument
from services.campaign_service import get_db


async def claim_next_lead(
    campaign_id: str,
    user_id: str,
    worker_id: str,
    claim_ttl_seconds: int = 120,
    canary_lead_id: Optional[str] = None,
    canary_phone: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    db = get_db()
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    expires = (
        now + timedelta(seconds=claim_ttl_seconds)
    ).isoformat()

    clauses = [
        {"user_id": user_id},
        {"$or": [
            {"campaign_id": campaign_id},
            {"assigned_campaigns": campaign_id},
        ]},
        {"phone": {"$exists": True, "$nin": [None, ""]}},
        {"dialed_campaigns": {"$ne": campaign_id}},
        {"$or": [
            {"claimed_by": {"$exists": False}},
            {"claimed_by": None},
            {"claim_expires_at": {"$lt": now_iso}},
        ]},
    ]

    if canary_lead_id:
        clauses.append({"id": canary_lead_id})

    if canary_phone:
        clauses.append({"phone": canary_phone})

    return await db.leads.find_one_and_update(
        {"$and": clauses},
        {"$set": {
            "claimed_by": worker_id,
            "claimed_at": now_iso,
            "claim_expires_at": expires,
            "updated_at": now_iso,
        }},
        sort=[
            ("dial_priority", -1),
            ("created_at", 1),
        ],
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )


async def peek_next_lead(
    campaign_id: str,
    user_id: str,
    canary_lead_id: Optional[str] = None,
    canary_phone: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    db = get_db()

    clauses = [
        {"user_id": user_id},
        {"$or": [
            {"campaign_id": campaign_id},
            {"assigned_campaigns": campaign_id},
        ]},
        {"phone": {"$exists": True, "$nin": [None, ""]}},
        {"dialed_campaigns": {"$ne": campaign_id}},
    ]

    if canary_lead_id:
        clauses.append({"id": canary_lead_id})

    if canary_phone:
        clauses.append({"phone": canary_phone})

    cursor = db.leads.find(
        {"$and": clauses},
        {"_id": 0},
    ).sort([
        ("dial_priority", -1),
        ("created_at", 1),
    ]).limit(1)

    rows = await cursor.to_list(1)

    return rows[0] if rows else None


async def release_claim(
    lead_id: str,
    worker_id: str,
    reason: Optional[str] = None,
) -> None:

    db = get_db()

    update = {
        "claimed_by": None,
        "claimed_at": None,
        "claim_expires_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if reason:
        update["last_claim_release_reason"] = reason

    await db.leads.update_one(
        {
            "id": lead_id,
            "claimed_by": worker_id,
        },
        {"$set": update},
    )


async def recover_stale_claims() -> int:

    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    result = await db.leads.update_many(
        {
            "claimed_by": {"$nin": [None, ""]},
            "claim_expires_at": {"$lt": now_iso},
        },
        {
            "$set": {
                "claimed_by": None,
                "claimed_at": None,
                "claim_expires_at": None,
            }
        },
    )

    return int(result.modified_count)


async def create_call_record(
    user_id: str,
    campaign_id: str,
    lead_id: str,
    agent_id: Optional[str],
    worker_id: str,
) -> str:

    import uuid

    db = get_db()
    call_id = str(uuid.uuid4())

    previous = await db.calls.count_documents(
        {
            "campaign_id": campaign_id,
            "lead_id": lead_id,
        }
    )

    await db.calls.insert_one(
        {
            "id": call_id,
            "user_id": user_id,
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "agent_id": agent_id,
            "status": "pending",
            "duration_seconds": 0,
            "voicemail_dropped": False,
            "worker_id": worker_id,
            "attempt_number": previous + 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "qualification_result": {
                "mode": "voicemail_drop",
                "attempt_number": previous + 1,
            },
        }
    )

    return call_id


async def mark_call_placed(
    call_id: str,
    session_id: str,
    call_sid: str,
) -> None:

    db = get_db()

    await db.calls.update_one(
        {"id": call_id},
        {
            "$set": {
                "status": "in_progress",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "twilio_sid": call_sid,
                "session_id": session_id,
            }
        },
    )


async def mark_call_failed(
    call_id: str,
    error: str,
) -> None:

    db = get_db()

    await db.calls.update_one(
        {"id": call_id},
        {
            "$set": {
                "status": "failed",
                "error": error,
                "ended_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


async def mark_lead_attempted(
    lead_id: str,
    campaign_id: str,
    worker_id: str,
) -> None:

    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()

    await db.leads.update_one(
        {
            "id": lead_id,
            "claimed_by": worker_id,
        },
        {
            "$inc": {
                "attempt_count": 1,
            },
            "$addToSet": {
                "dialed_campaigns": campaign_id,
            },
            "$set": {
                "last_attempted_at": now_iso,
                "claimed_by": None,
                "claimed_at": None,
                "claim_expires_at": None,
                "updated_at": now_iso,
            },
        },
    )


async def ensure_runner_indexes() -> None:

    db = get_db()

    await db.leads.create_index([
        ("user_id", 1),
        ("campaign_id", 1),
        ("dial_priority", -1),
    ])

    await db.leads.create_index([
        ("claimed_by", 1),
        ("claim_expires_at", 1),
    ])

    await db.calls.create_index([
        ("campaign_id", 1),
        ("started_at", -1),
    ])

    await db.calls.create_index([
        ("campaign_id", 1),
        ("lead_id", 1),
    ])

    await db.outbound_sessions.create_index(
        "session_id",
        unique=True,
    )

    await db.outbound_sessions.create_index(
        "call_sid"
    )
