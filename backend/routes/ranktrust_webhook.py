"""RankTrust → IntentBrain Handoff Webhook.

Endpoint contract:
    POST /api/webhooks/ranktrust/handoff
    Body: HandoffPacket (JSON)
    Auth: HMAC-SHA256 preferred (X-RankTrust-Signature: sha256=<hex>),
          token fallback (?token=... or X-RankTrust-Token header).

Flow:
    1. Verify auth.
    2. Validate + store the packet in db.ranktrust_handoffs (idempotent on packet_id).
    3. If business.phone is missing → status='needs_phone'. Callback RankTrust
       with the reason. No dial scheduled.
    4. Else → persist a ranktrust_scheduled_calls row with target_at = now + delay_seconds.
    5. A background scheduler polls every 30s. When target_at ≤ now it invokes
       place_outbound_call() — which respects the OUTBOUND_DISABLED kill switch
       and db.dnc_list. Whatever happens, RankTrust gets a callback POST back.

Hard rules:
    * Never enables outbound dialing on its own — everything routes through
      routes.twilio_outbound.place_outbound_call which is gated by the kill
      switch + DNC.
    * Never logs secrets, HMAC keys, or raw callback tokens.
    * Malformed / unauthenticated requests never touch the DB.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field, HttpUrl, field_validator

logger = logging.getLogger(__name__)


# ============================================================
# Pluggable state (wired by server.py at startup)
# ============================================================
class _State:
    db: Any = None
    handoff_secret: str = ""           # HMAC secret
    handoff_token: str = ""            # Shared-token fallback
    callback_url_default: str = ""     # env fallback for RankTrust callback
    callback_token_default: str = ""
    poll_seconds: int = 30
    _scheduler_task: Optional[asyncio.Task] = None
    _scheduler_stop: Optional[asyncio.Event] = None


_state = _State()


def setup_dependencies(
    *,
    db: Any,
    handoff_secret: str = "",
    handoff_token: str = "",
    callback_url_default: str = "",
    callback_token_default: str = "",
    poll_seconds: int = 30,
) -> None:
    """Wire the router. Idempotent."""
    _state.db = db
    _state.handoff_secret = handoff_secret or ""
    _state.handoff_token = handoff_token or ""
    _state.callback_url_default = (callback_url_default or "").rstrip("/")
    _state.callback_token_default = callback_token_default or ""
    _state.poll_seconds = max(1, int(poll_seconds))


# ============================================================
# Packet schema
# ============================================================
E164 = re.compile(r"^\+[1-9]\d{7,14}$")


class BusinessInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)   # E.164 when present
    website: Optional[str] = Field(None, max_length=500)

    @field_validator("phone")
    @classmethod
    def _phone_e164(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip()
        if not E164.match(v):
            raise ValueError("phone must be E.164 (e.g. +14045551234)")
        return v


class SalesScript(BaseModel):
    opener: str = Field(..., min_length=1, max_length=2000)
    key_points: List[str] = Field(default_factory=list, max_length=25)
    call_to_action: Optional[str] = Field(None, max_length=500)


class Objection(BaseModel):
    objection: str = Field(..., max_length=500)
    response: str = Field(..., max_length=2000)


class HandoffPacket(BaseModel):
    packet_id: str = Field(..., min_length=1, max_length=200)
    business: BusinessInfo
    revenue_opportunity: Optional[float] = None
    close_probability: Optional[float] = None
    best_offer: Optional[str] = Field(None, max_length=500)
    sales_script: SalesScript
    objections: List[Objection] = Field(default_factory=list, max_length=25)
    conversation_strategy: Optional[str] = Field(None, max_length=5000)
    delay_seconds: int = Field(default=300)
    callback_url: Optional[HttpUrl] = None
    callback_token: Optional[str] = Field(None, max_length=500)

    @field_validator("delay_seconds")
    @classmethod
    def _delay_range(cls, v: int) -> int:
        if v < 60 or v > 86400:
            raise ValueError("delay_seconds must be between 60 and 86400")
        return v

    @field_validator("close_probability")
    @classmethod
    def _prob_range(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if v < 0.0 or v > 1.0:
            raise ValueError("close_probability must be between 0 and 1")
        return v


# ============================================================
# Auth
# ============================================================
def _verify_hmac(raw_body: bytes, signature_header: str, secret: str) -> bool:
    """`X-RankTrust-Signature: sha256=<hex>`. Constant-time compare."""
    if not signature_header or not secret:
        return False
    sig = signature_header.strip()
    if sig.startswith("sha256="):
        sig = sig[len("sha256="):]
    try:
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    except Exception:  # pragma: no cover
        return False
    return hmac.compare_digest(expected, sig)


def _authorized(
    raw_body: bytes,
    signature_header: Optional[str],
    token_query: Optional[str],
    token_header: Optional[str],
) -> bool:
    # Prefer HMAC when a signature header is provided AND a secret is configured.
    if signature_header and _state.handoff_secret:
        return _verify_hmac(raw_body, signature_header, _state.handoff_secret)
    # Fallback: shared token
    if _state.handoff_token:
        candidate = (token_query or token_header or "").strip()
        if candidate and hmac.compare_digest(candidate, _state.handoff_token):
            return True
    return False


# ============================================================
# Router
# ============================================================
router = APIRouter(prefix="/webhooks/ranktrust", tags=["ranktrust_webhook"])


@router.post("/handoff")
async def ranktrust_handoff(
    request: Request,
    token: Optional[str] = Query(default=None),
    x_ranktrust_signature: Optional[str] = Header(default=None),
    x_ranktrust_token: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if _state.db is None:
        raise HTTPException(status_code=503, detail="webhook not initialized")

    raw = await request.body()
    if not _authorized(raw, x_ranktrust_signature, token, x_ranktrust_token):
        # Never disclose which method failed
        raise HTTPException(status_code=401, detail="unauthorized")

    # Parse + validate
    try:
        import json as _json
        payload = _json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="body must be valid JSON")

    try:
        packet = HandoffPacket(**payload)
    except Exception as e:
        # Pydantic validation error — surface a safe summary, not secrets
        raise HTTPException(status_code=422, detail=str(e)[:500])

    # Idempotency: if we've already seen this packet_id, return the stored row.
    existing = await _state.db.ranktrust_handoffs.find_one({"packet_id": packet.packet_id})
    if existing:
        # Never echo callback_token / any secret field
        return _public_view(existing, replayed=True)

    now = datetime.now(timezone.utc)
    phone = packet.business.phone

    # Decide initial status
    if not phone:
        status = "needs_phone"
        scheduled_call_id = None
    else:
        status = "scheduled"

    # Persist the handoff record
    record = {
        "packet_id": packet.packet_id,
        "received_at": now.isoformat(),
        "status": status,
        "business_name": packet.business.name,
        "business_industry": packet.business.industry,
        "business_phone": phone,
        "revenue_opportunity": packet.revenue_opportunity,
        "close_probability": packet.close_probability,
        "delay_seconds": packet.delay_seconds,
        # Store the full packet as an opaque blob for later use by the dialer /
        # in-call brain. NOTE: callback_token is stored ONLY server-side and
        # never returned by _public_view().
        "packet": _packet_to_dict(packet),
        "events": [
            {"at": now.isoformat(), "event": "received", "detail": f"status={status}"}
        ],
    }
    await _state.db.ranktrust_handoffs.insert_one(record)

    scheduled_call_id: Optional[str] = None
    if status == "scheduled":
        target_at = now + timedelta(seconds=packet.delay_seconds)
        sched = {
            "packet_id": packet.packet_id,
            "phone": phone,
            "target_at": target_at.isoformat(),
            "created_at": now.isoformat(),
            "status": "pending",
            "attempts": 0,
        }
        await _state.db.ranktrust_scheduled_calls.insert_one(sched)
        scheduled_call_id = str(sched.get("_id") or packet.packet_id)

    # If we can't dial, fire the callback right now.
    if status == "needs_phone":
        asyncio.create_task(_post_callback(
            packet_id=packet.packet_id,
            outcome="needs_phone",
            detail={"reason": "Handoff accepted but business.phone is missing."},
        ))

    return _public_view(record, replayed=False, scheduled_call_id=scheduled_call_id)


@router.get("/handoff/{packet_id}")
async def ranktrust_handoff_status(packet_id: str) -> Dict[str, Any]:
    if _state.db is None:
        raise HTTPException(status_code=503, detail="webhook not initialized")
    row = await _state.db.ranktrust_handoffs.find_one({"packet_id": packet_id})
    if not row:
        raise HTTPException(status_code=404, detail="packet not found")
    return _public_view(row, replayed=False)


# ============================================================
# Helpers
# ============================================================
def _packet_to_dict(p: HandoffPacket) -> Dict[str, Any]:
    """Serialize the packet for storage. HttpUrl → str."""
    d = p.model_dump()
    if d.get("callback_url") is not None:
        d["callback_url"] = str(d["callback_url"])
    return d


def _public_view(record: Dict[str, Any], *, replayed: bool, scheduled_call_id: Optional[str] = None) -> Dict[str, Any]:
    """Redact server-only fields (callback_token) before returning to the caller."""
    packet = dict(record.get("packet") or {})
    packet.pop("callback_token", None)  # never echo
    return {
        "packet_id": record.get("packet_id"),
        "status": record.get("status"),
        "received_at": record.get("received_at"),
        "business_name": record.get("business_name"),
        "business_phone": record.get("business_phone"),
        "delay_seconds": record.get("delay_seconds"),
        "scheduled_call_id": scheduled_call_id,
        "replayed": replayed,
        "packet": packet,
    }


async def _post_callback(
    *,
    packet_id: str,
    outcome: str,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """POST the result back to RankTrust. Uses packet-level callback_url +
    callback_token when present, else falls back to env defaults."""
    if _state.db is None:
        return

    row = await _state.db.ranktrust_handoffs.find_one({"packet_id": packet_id})
    if not row:
        logger.warning(f"[ranktrust] callback requested for unknown packet_id={packet_id}")
        return

    packet_data = row.get("packet") or {}
    url = packet_data.get("callback_url") or _state.callback_url_default
    token = packet_data.get("callback_token") or _state.callback_token_default

    if not url:
        # Nothing to post to — record locally and move on.
        await _state.db.ranktrust_handoffs.update_one(
            {"packet_id": packet_id},
            {"$push": {"events": {
                "at": datetime.now(timezone.utc).isoformat(),
                "event": "callback_skipped_no_url",
                "detail": {"outcome": outcome},
            }}},
        )
        return

    body = {
        "packet_id": packet_id,
        "outcome": outcome,
        "detail": detail or {},
        "at": datetime.now(timezone.utc).isoformat(),
    }
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            success = 200 <= resp.status_code < 300
            log_detail = {"outcome": outcome, "status_code": resp.status_code}
    except Exception as e:
        logger.warning(f"[ranktrust] callback POST failed for packet_id={packet_id}: {e!r}")
        success = False
        log_detail = {"outcome": outcome, "error": str(e)[:200]}

    await _state.db.ranktrust_handoffs.update_one(
        {"packet_id": packet_id},
        {"$push": {"events": {
            "at": datetime.now(timezone.utc).isoformat(),
            "event": "callback_posted" if success else "callback_failed",
            "detail": log_detail,
        }}},
    )


# ============================================================
# Scheduler
# ============================================================
async def scheduler_tick_once(now_dt: Optional[datetime] = None) -> Dict[str, Any]:
    """Process all due scheduled calls. Returns a stats dict for tests."""
    if _state.db is None:
        return {"processed": 0}

    now_dt = now_dt or datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    stats = {"processed": 0, "dialed": 0, "blocked": 0, "failed": 0, "needs_phone": 0}

    cursor = _state.db.ranktrust_scheduled_calls.find({
        "status": "pending",
        "target_at": {"$lte": now_iso},
    })
    docs = await cursor.to_list(length=200)

    for job in docs:
        packet_id = job["packet_id"]
        phone = job.get("phone")
        stats["processed"] += 1

        # Claim the job atomically
        claim = await _state.db.ranktrust_scheduled_calls.update_one(
            {"packet_id": packet_id, "status": "pending"},
            {"$set": {"status": "dialing", "started_at": now_iso},
             "$inc": {"attempts": 1}},
        )
        if claim.modified_count == 0:
            continue

        if not phone:
            stats["needs_phone"] += 1
            await _finalize_job(packet_id, terminal_status="needs_phone",
                                outcome="needs_phone", detail={"reason": "no phone"})
            continue

        # Load the packet to build the opener + business context
        handoff = await _state.db.ranktrust_handoffs.find_one({"packet_id": packet_id})
        packet = (handoff or {}).get("packet") or {}
        opener = ((packet.get("sales_script") or {}).get("opener") or "").strip()
        business_name = (packet.get("business") or {}).get("name")

        if not opener:
            stats["failed"] += 1
            await _finalize_job(packet_id, terminal_status="failed",
                                outcome="failed",
                                detail={"reason": "packet has no sales_script.opener"})
            continue

        # Dial through the outbound gate — kill switch + DNC still hard-govern
        try:
            from routes import twilio_outbound as _twilio_outbound
            result = await _twilio_outbound.place_outbound_call(
                to_number=phone,
                lead_id=f"ranktrust:{packet_id}",
                campaign_id="ranktrust_handoff",
                variant_index=0,
                lead_attrs={"source": "ranktrust_handoff", "packet_id": packet_id},
                business_name=business_name,
                experiment_tag="ranktrust_handoff",
                opener_text_override=opener,
            )
        except Exception as e:  # pragma: no cover
            stats["failed"] += 1
            logger.error(f"[ranktrust] place_outbound_call raised for {packet_id}: {e!r}")
            await _finalize_job(packet_id, terminal_status="failed",
                                outcome="failed",
                                detail={"reason": "dial_exception"})
            continue

        if not result.get("ok"):
            if result.get("blocked") == "outbound_disabled":
                stats["blocked"] += 1
                await _finalize_job(
                    packet_id,
                    terminal_status="blocked_outbound_disabled",
                    outcome="blocked_outbound_disabled",
                    detail={"reason": "kill switch present"},
                )
            elif result.get("skipped") == "dnc":
                stats["blocked"] += 1
                await _finalize_job(
                    packet_id,
                    terminal_status="blocked_dnc",
                    outcome="blocked_dnc",
                    detail={"reason": "phone on DNC list"},
                )
            else:
                stats["failed"] += 1
                # Redact anything sensitive in `result` — only surface documented keys
                safe = {k: result.get(k) for k in ("ok", "blocked", "skipped", "error") if k in result}
                await _finalize_job(packet_id, terminal_status="failed",
                                    outcome="failed", detail=safe)
            continue

        stats["dialed"] += 1
        call_sid = result.get("call_sid")
        await _state.db.ranktrust_scheduled_calls.update_one(
            {"packet_id": packet_id},
            {"$set": {"status": "dialed", "call_sid": call_sid,
                      "dialed_at": datetime.now(timezone.utc).isoformat()}},
        )
        await _state.db.ranktrust_handoffs.update_one(
            {"packet_id": packet_id},
            {"$set": {"status": "dialed", "call_sid": call_sid},
             "$push": {"events": {
                 "at": datetime.now(timezone.utc).isoformat(),
                 "event": "dial_placed",
                 "detail": {"call_sid": call_sid},
             }}},
        )
        # Terminal outcomes (voicemail / IVR / DNC / conversation) will be
        # posted by the outbound gate's status webhook + a separate reconciler.
        # For now we notify RankTrust the dial was placed.
        asyncio.create_task(_post_callback(
            packet_id=packet_id, outcome="dial_placed",
            detail={"call_sid": call_sid, "business_name": business_name},
        ))

    return stats


async def _finalize_job(packet_id: str, *, terminal_status: str, outcome: str, detail: Dict[str, Any]) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    await _state.db.ranktrust_scheduled_calls.update_one(
        {"packet_id": packet_id},
        {"$set": {"status": terminal_status, "finished_at": now_iso}},
    )
    await _state.db.ranktrust_handoffs.update_one(
        {"packet_id": packet_id},
        {"$set": {"status": terminal_status},
         "$push": {"events": {"at": now_iso, "event": terminal_status, "detail": detail}}},
    )
    await _post_callback(packet_id=packet_id, outcome=outcome, detail=detail)


async def _scheduler_loop() -> None:  # pragma: no cover — background task
    stop = _state._scheduler_stop
    while stop is None or not stop.is_set():
        try:
            await scheduler_tick_once()
        except Exception as e:
            logger.error(f"[ranktrust] scheduler tick error: {e!r}")
        try:
            await asyncio.wait_for(asyncio.sleep(_state.poll_seconds), timeout=_state.poll_seconds + 1)
        except asyncio.TimeoutError:
            pass


def start_scheduler() -> None:
    """Start the background poller. Idempotent."""
    if _state._scheduler_task and not _state._scheduler_task.done():
        return
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    _state._scheduler_stop = asyncio.Event()
    _state._scheduler_task = loop.create_task(_scheduler_loop())
    logger.info(f"[ranktrust] scheduler started (poll every {_state.poll_seconds}s)")


def stop_scheduler() -> None:  # pragma: no cover — process shutdown
    if _state._scheduler_stop:
        _state._scheduler_stop.set()
