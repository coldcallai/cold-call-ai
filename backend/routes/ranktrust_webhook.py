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
import uuid
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
) -> Optional[str]:
    """Return the auth method used ('hmac' | 'token') or None on failure.

    Precedence matches original behavior:
      * If an X-RankTrust-Signature header is present AND a secret is configured,
        HMAC is the ONLY accepted method — token fallback is NOT tried.
      * Otherwise, if a shared token is configured, the token fallback is checked.
    """
    # Prefer HMAC when a signature header is provided AND a secret is configured.
    if signature_header and _state.handoff_secret:
        return "hmac" if _verify_hmac(raw_body, signature_header, _state.handoff_secret) else None
    # Fallback: shared token
    if _state.handoff_token:
        candidate = (token_query or token_header or "").strip()
        if candidate and hmac.compare_digest(candidate, _state.handoff_token):
            return "token"
    return None


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
    auth_method = _authorized(raw, x_ranktrust_signature, token, x_ranktrust_token)
    if auth_method is None:
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
        # Replay MUST include the previously stored scheduled_call_id (RankTrust contract §1).
        return _handoff_response(
            status=existing.get("status") or "queued",
            packet_id=packet.packet_id,
            scheduled_call_id=existing.get("scheduled_call_id"),
            replayed=True,
        )

    now = datetime.now(timezone.utc)
    phone = packet.business.phone

    # Decide initial status + assign a stable, unique scheduled_call_id up front.
    # Using uuid.uuid4() (not packet_id) so RankTrust can distinguish the dial job
    # from their own packet identifier.
    if phone:
        status = "queued"
        scheduled_call_id: Optional[str] = uuid.uuid4().hex
    else:
        status = "needs_phone"
        scheduled_call_id = None

    # Persist the handoff record — signature_verified + scheduled_call_id are
    # stored at the TOP LEVEL (RankTrust contract §3).
    record = {
        "packet_id": packet.packet_id,
        "received_at": now.isoformat(),
        "status": status,
        "signature_verified": (auth_method == "hmac"),
        "auth_method": auth_method,             # 'hmac' | 'token' — internal-only, safe
        "scheduled_call_id": scheduled_call_id,  # top-level (may be null on needs_phone)
        "business_name": packet.business.name,
        "business_industry": packet.business.industry,
        "business_phone": phone,
        "revenue_opportunity": packet.revenue_opportunity,
        "close_probability": packet.close_probability,
        "delay_seconds": packet.delay_seconds,
        # Store the full packet as an opaque blob for later use by the dialer /
        # in-call brain. NOTE: callback_token is stored ONLY server-side and
        # never returned by _public_view() or _handoff_response().
        "packet": _packet_to_dict(packet),
        "events": [
            {"at": now.isoformat(), "event": "received", "detail": f"status={status}"}
        ],
    }
    await _state.db.ranktrust_handoffs.insert_one(record)

    if status == "queued":
        target_at = now + timedelta(seconds=packet.delay_seconds)
        sched = {
            "packet_id": packet.packet_id,
            "scheduled_call_id": scheduled_call_id,   # linkage back to the handoff row
            "phone": phone,
            "target_at": target_at.isoformat(),
            "created_at": now.isoformat(),
            "status": "pending",
            "attempts": 0,
        }
        await _state.db.ranktrust_scheduled_calls.insert_one(sched)

    # If we can't dial, fire the callback right now.
    if status == "needs_phone":
        asyncio.create_task(_post_callback(
            packet_id=packet.packet_id,
            outcome="needs_phone",
            detail={"reason": "Handoff accepted but business.phone is missing."},
        ))

    return _handoff_response(
        status=status,
        packet_id=packet.packet_id,
        scheduled_call_id=scheduled_call_id,
        replayed=False,
    )


@router.get("/handoff/{packet_id}")
async def ranktrust_handoff_status(packet_id: str) -> Dict[str, Any]:
    if _state.db is None:
        raise HTTPException(status_code=503, detail="webhook not initialized")
    row = await _state.db.ranktrust_handoffs.find_one({"packet_id": packet_id})
    if not row:
        raise HTTPException(status_code=404, detail="packet not found")
    return _public_view(row, replayed=False)


# ============================================================
# Baseline Timeline (read-only diagnostic view)
# ============================================================
# Merges three collections into a single ordered stage-by-stage lifecycle:
#   * ranktrust_handoffs        (packet_received / queued / dial_placed / callback events)
#   * ranktrust_scheduled_calls (target_at / dialed_at)
#   * outbound_sessions         (answered / greeting_detected / call_ended)
#
# Never writes. Never touches secrets. Callback details are already redacted
# at write-time (stored detail is {outcome, status_code} or {outcome, error}).
_TIMELINE_STAGES_ORDER = [
    "packet_received",
    "packet_validated",
    "queued",
    "delay_target",
    "dial_started",
    "answered",
    "greeting_detected",
    "ai_conversation_started",
    "call_ended",
    "callback_sent",
]


def _iso_or_none(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


def _elapsed_seconds(start_iso: Optional[str], stage_iso: Optional[str]) -> Optional[float]:
    if not start_iso or not stage_iso:
        return None
    try:
        start_dt = datetime.fromisoformat(start_iso)
        stage_dt = datetime.fromisoformat(stage_iso)
    except (TypeError, ValueError):
        return None
    return round((stage_dt - start_dt).total_seconds(), 3)


async def _build_timeline(packet_id: str) -> Optional[Dict[str, Any]]:
    """Return a merged, ordered lifecycle timeline for a packet.

    Returns None if the packet is unknown (endpoint will translate to 404).
    """
    handoff = await _state.db.ranktrust_handoffs.find_one({"packet_id": packet_id})
    if not handoff:
        return None

    sched = await _state.db.ranktrust_scheduled_calls.find_one({"packet_id": packet_id})
    session = await _state.db.outbound_sessions.find_one({"lead_id": f"ranktrust:{packet_id}"})

    events = handoff.get("events") or []
    received_at = _iso_or_none(handoff.get("received_at"))

    def _find_event(name: str) -> Optional[Dict[str, Any]]:
        return next((e for e in events if e.get("event") == name), None)

    def _find_callback_event() -> Optional[Dict[str, Any]]:
        for e in events:
            if e.get("event") in ("callback_posted", "callback_failed", "callback_skipped_no_url"):
                return e
        return None

    stages: List[Dict[str, Any]] = []

    def _add(stage: str, at: Optional[str], **detail: Any) -> None:
        if not at:
            return
        # Filter out None-valued detail fields for a clean readable payload
        clean_detail = {k: v for k, v in detail.items() if v is not None}
        stages.append({"stage": stage, "at": at, "detail": clean_detail})

    # 1. packet_received
    _add("packet_received", received_at, status="received")

    # 2. packet_validated — implicit: if the row exists, auth+Pydantic passed.
    _add("packet_validated", received_at,
         note="Auth (HMAC or token) accepted; Pydantic schema validated")

    # 3. queued — same moment as receipt (row was persisted).
    _add("queued", received_at,
         status=handoff.get("status"),
         delay_seconds=handoff.get("delay_seconds"))
    # 4. delay_target — the moment scheduler is allowed to dial.
    if sched:
        _add("delay_target", _iso_or_none(sched.get("target_at")),
             pending_for_seconds=handoff.get("delay_seconds"))

    # 5. dial_started
    dial_evt = _find_event("dial_placed")
    if dial_evt:
        _add("dial_started", _iso_or_none(dial_evt.get("at")),
             call_sid=(dial_evt.get("detail") or {}).get("call_sid"))

    # 6-9. answered / greeting_detected / ai_conversation_started / call_ended
    if session:
        _add("answered", _iso_or_none(session.get("answered_at")),
             answered_by=session.get("answered_by"))

        opener_played_at = _iso_or_none(session.get("opener_played_at"))
        _add("greeting_detected", opener_played_at,
             first_human_speech=session.get("first_human_speech"))
        _add("ai_conversation_started", opener_played_at,
             opener_text=session.get("opener_text"),
             disposition=session.get("disposition"))

        _add("call_ended", _iso_or_none(session.get("ended_at")),
             final_call_status=session.get("final_call_status"),
             duration_seconds=session.get("duration_seconds"),
             disposition=session.get("disposition"))

    # 10. callback_sent — any callback event (posted / failed / skipped).
    cb_evt = _find_callback_event()
    if cb_evt:
        _add("callback_sent", _iso_or_none(cb_evt.get("at")),
             event=cb_evt.get("event"),
             detail=cb_evt.get("detail"))

    # Attach elapsed_from_start_seconds
    for s in stages:
        s["elapsed_from_start_seconds"] = _elapsed_seconds(received_at, s["at"])

    # Stable order: primary key = _TIMELINE_STAGES_ORDER index; secondary = at.
    order_index = {name: i for i, name in enumerate(_TIMELINE_STAGES_ORDER)}
    stages.sort(key=lambda s: (order_index.get(s["stage"], 999), s["at"]))

    return {
        "packet_id": packet_id,
        "business_name": handoff.get("business_name"),
        "business_phone": handoff.get("business_phone"),
        "business_industry": handoff.get("business_industry"),
        "status": handoff.get("status"),
        "call_sid": handoff.get("call_sid") or (session or {}).get("call_sid"),
        "received_at": received_at,
        "delay_seconds": handoff.get("delay_seconds"),
        "timeline": stages,
    }


def _format_timeline_markdown(payload: Dict[str, Any]) -> str:
    """Copy-paste baseline block for debugging notes / chat sharing.

    Never includes secrets. Safe to paste into a public issue tracker.
    """
    lines: List[str] = []
    lines.append(f"# RankTrust → IntentBrain Baseline — `{payload.get('packet_id')}`")
    lines.append("")
    lines.append(f"- **Business:** {payload.get('business_name') or 'n/a'}"
                 f" ({payload.get('business_industry') or 'n/a'})")
    lines.append(f"- **Phone:** `{payload.get('business_phone') or 'n/a'}`")
    lines.append(f"- **Status:** `{payload.get('status') or 'unknown'}`")
    lines.append(f"- **Call SID:** `{payload.get('call_sid') or 'n/a'}`")
    lines.append(f"- **Received at:** `{payload.get('received_at') or 'n/a'}`")
    lines.append(f"- **Configured delay:** {payload.get('delay_seconds') or 'n/a'}s")
    lines.append("")
    lines.append("| # | Stage | Timestamp (UTC) | Elapsed from start (s) | Detail |")
    lines.append("|---|-------|-----------------|------------------------|--------|")
    for i, s in enumerate(payload.get("timeline") or [], start=1):
        detail = s.get("detail") or {}
        # Compact detail into `k=v` pairs so the whole line stays one row.
        detail_str = ", ".join(
            f"{k}=`{v}`" for k, v in detail.items()
            if v is not None and v != "" and v != []
        ) or "—"
        elapsed = s.get("elapsed_from_start_seconds")
        elapsed_str = f"{elapsed:.3f}" if isinstance(elapsed, (int, float)) else "—"
        lines.append(
            f"| {i} | `{s['stage']}` | `{s['at']}` | {elapsed_str} | {detail_str} |"
        )
    lines.append("")
    lines.append("_Generated by `GET /api/webhooks/ranktrust/timeline/{packet_id}?format=markdown`._")
    return "\n".join(lines)


@router.get("/timeline/{packet_id}")
async def ranktrust_timeline(
    packet_id: str,
    format: Optional[str] = Query(default=None),
) -> Any:
    """Read-only lifecycle timeline for a single RankTrust packet.

    - Default: JSON with an ordered `timeline` array.
    - `?format=markdown`: text/markdown baseline block for chat / debug notes.
    """
    if _state.db is None:
        raise HTTPException(status_code=503, detail="webhook not initialized")

    payload = await _build_timeline(packet_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="packet not found")

    if (format or "").lower() in ("md", "markdown"):
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=_format_timeline_markdown(payload),
            media_type="text/markdown; charset=utf-8",
        )
    return payload


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
    """Redact server-only fields (callback_token) before returning to the caller.

    Used by the debug GET /handoff/{packet_id} endpoint. The POST endpoint uses
    the stricter `_handoff_response` shape below.
    """
    packet = dict(record.get("packet") or {})
    packet.pop("callback_token", None)  # never echo
    return {
        "packet_id": record.get("packet_id"),
        "status": record.get("status"),
        "received_at": record.get("received_at"),
        "business_name": record.get("business_name"),
        "business_phone": record.get("business_phone"),
        "delay_seconds": record.get("delay_seconds"),
        "signature_verified": record.get("signature_verified"),
        "scheduled_call_id": scheduled_call_id if scheduled_call_id is not None else record.get("scheduled_call_id"),
        "replayed": replayed,
        "packet": packet,
    }


def _handoff_response(*, status: str, packet_id: str,
                     scheduled_call_id: Optional[str], replayed: bool) -> Dict[str, Any]:
    """Strict RankTrust POST /handoff response contract.

    Contract (v2):
      {"status": "queued" | "needs_phone",
       "packet_id": "<from payload>",
       "scheduled_call_id": "<uuid hex>" | null}

    Also emits `replayed: bool` — RankTrust ignores extra keys but this is
    useful for their operators when eyeballing responses.
    """
    return {
        "status": status,
        "packet_id": packet_id,
        "scheduled_call_id": scheduled_call_id,
        "replayed": replayed,
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

        # Dial through the outbound gate — kill switch + DNC still hard-govern.
        # Attach a runaway-cost cap: Twilio HARD-ENDS this call after
        # OUTBOUND_MAX_CALL_SECONDS (default 120s). Applies to RankTrust
        # handoffs only — legacy Phase D / dental dialer paths pass no cap.
        try:
            max_seconds_env = os.environ.get("OUTBOUND_MAX_CALL_SECONDS", "120")
            max_call_seconds = int(max_seconds_env) if max_seconds_env else 120
            if max_call_seconds <= 0:
                max_call_seconds = 120
        except (TypeError, ValueError):
            max_call_seconds = 120

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
                max_call_seconds=max_call_seconds,
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
