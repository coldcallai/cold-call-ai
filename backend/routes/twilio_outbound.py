"""Outbound Human-Greeting Gate.

Strict rules enforced by this module (proven by tests/test_twilio_outbound_gate.py):

  1. calls.create() uses a URL callback (`url=`), NEVER inline TwiML.
  2. The AI opener is never embedded in the outbound call create() payload.
  3. /outbound/answer never speaks. It silently routes based on AMD AnsweredBy.
  4. /outbound/greeting silently <Gather>s for human speech (no Say, no Play).
  5. The opener is only played by /outbound/respond AFTER human speech is heard.
  6. ALL AI voice is ElevenLabs MP3 served via <Play https://.../api/tts/audio/{id}>.
     Twilio <Say> is NEVER used for AI voice; we hang up gracefully on TTS failure.
  7. Voicemail / IVR phrases short-circuit to a silent hangup. No opener.
  8. DNC requests write {phone_number, added_at, reason} to db.dnc_list.
  9. place_outbound_call() checks db.dnc_list BEFORE generating TTS / dialing.

Inbound legacy brain is intentionally untouched. After the opener plays, control
hands off to /api/twilio/inbound/respond via the next <Gather>.
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

logger = logging.getLogger(__name__)


# ============================================================
# Pluggable runtime state (set by setup_dependencies)
# ============================================================
class _State:
    db: Any = None
    twilio_client: Any = None
    eleven_client: Any = None
    synthesize_fn: Optional[Callable[[str, str], bytes]] = None
    voice_id: str = ""
    backend_url: str = ""
    from_number: str = ""
    # Path to a "kill switch" sentinel file. If this file exists on disk,
    # place_outbound_call() refuses to dial. Managed by scripts/deploy_preflight.sh
    # — the file is created when the structural self-test fails and removed
    # when it passes. This makes it impossible to accidentally ship a version
    # where the human-greeting gate is broken.
    kill_switch_path: str = ""
    # Path to the most recent self-test report (written by scripts/outbound_selftest.py).
    # Read-only metadata source for the /api/admin/outbound-status endpoint.
    selftest_report_path: str = ""
    # In-memory audio store: {audio_id: mp3_bytes}.
    # Production note: cleared on process restart; calls in flight will fail
    # gracefully (we hang up rather than fall back to robotic <Say>).
    audio_store: Dict[str, bytes] = {}


_state = _State()


def setup_dependencies(
    *,
    db: Any,
    twilio_client: Any,
    eleven_client: Any,
    synthesize_fn: Optional[Callable[[str, str], bytes]] = None,
    voice_id: str,
    backend_url: str,
    from_number: str,
    kill_switch_path: Optional[str] = None,
    selftest_report_path: Optional[str] = None,
) -> None:
    """Wire production clients into the outbound router. Idempotent."""
    _state.db = db
    _state.twilio_client = twilio_client
    _state.eleven_client = eleven_client
    _state.synthesize_fn = synthesize_fn or _default_eleven_synthesize
    _state.voice_id = voice_id
    _state.backend_url = backend_url.rstrip("/")
    _state.from_number = from_number
    # Default kill switch location: <backend_root>/OUTBOUND_DISABLED
    if kill_switch_path is None:
        kill_switch_path = os.environ.get(
            "OUTBOUND_KILL_SWITCH",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "OUTBOUND_DISABLED"),
        )
    _state.kill_switch_path = kill_switch_path
    if selftest_report_path is None:
        selftest_report_path = os.environ.get(
            "OUTBOUND_SELFTEST_REPORT", "/tmp/outbound_selftest_report.json"
        )
    _state.selftest_report_path = selftest_report_path


def is_outbound_disabled() -> bool:
    """True when the OUTBOUND_DISABLED sentinel file exists on disk."""
    return bool(_state.kill_switch_path) and os.path.isfile(_state.kill_switch_path)


def _default_eleven_synthesize(text: str, voice_id: str) -> bytes:
    """Default ElevenLabs synth path. Returns b"" on failure (caller must handle)."""
    client = _state.eleven_client
    if client is None:
        logger.error("ElevenLabs client not configured — cannot synthesize")
        _record_synth_event(success=False, latency_ms=0, error="client_not_configured")
        return b""
    import time as _time
    started = _time.monotonic()
    try:
        from elevenlabs.types import VoiceSettings  # type: ignore
        gen = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
        )
        out = b""
        for chunk in gen:
            out += chunk
        elapsed_ms = int((_time.monotonic() - started) * 1000)
        _record_synth_event(success=True, latency_ms=elapsed_ms, error=None)
        return out
    except Exception as e:  # pragma: no cover - network path
        elapsed_ms = int((_time.monotonic() - started) * 1000)
        logger.error(f"ElevenLabs synthesis failed: {e}")
        _record_synth_event(success=False, latency_ms=elapsed_ms, error=str(e)[:120])
        return b""


# ============================================================
# ElevenLabs health cache (in-memory; updated by every synth + light ping)
# ============================================================
class _ElevenHealth:
    last_synth_at: Optional[str] = None              # any attempt
    last_synth_latency_ms: int = 0
    last_synth_success: Optional[bool] = None
    last_successful_synth_at: Optional[str] = None
    last_error: Optional[str] = None
    last_ping_at: Optional[float] = None             # monotonic timestamp
    last_ping_reachable: Optional[bool] = None


_eleven_health = _ElevenHealth()
_MIN_PING_INTERVAL_SECONDS = 600   # 10 minutes — never hit ElevenLabs more than that from the status endpoint
_PING_TIMEOUT_SECONDS = 4


def _record_synth_event(*, success: bool, latency_ms: int, error: Optional[str]) -> None:
    """Called by _default_eleven_synthesize after every synth attempt."""
    now_iso = datetime.now(timezone.utc).isoformat()
    _eleven_health.last_synth_at = now_iso
    _eleven_health.last_synth_latency_ms = int(latency_ms or 0)
    _eleven_health.last_synth_success = bool(success)
    _eleven_health.last_error = error
    if success:
        _eleven_health.last_successful_synth_at = now_iso
        _eleven_health.last_ping_reachable = True


def _maybe_live_ping_elevenlabs() -> Optional[bool]:
    """Lightweight, rate-limited reachability check. Returns True/False or None
    if a recent successful synth event already proves reachability (no ping
    needed). NEVER does a synthesis — this is just a cheap voices.get_all() call.
    """
    import time as _time
    # If we had a successful synth in the last 10 minutes, the ElevenLabs API
    # is by definition reachable — skip the ping entirely.
    if _eleven_health.last_successful_synth_at:
        try:
            last_ok_dt = datetime.fromisoformat(_eleven_health.last_successful_synth_at)
            age = (datetime.now(timezone.utc) - last_ok_dt).total_seconds()
            if age < _MIN_PING_INTERVAL_SECONDS:
                return True
        except (TypeError, ValueError):
            pass

    # Rate-limit our own ping
    now_mono = _time.monotonic()
    if _eleven_health.last_ping_at is not None:
        if (now_mono - _eleven_health.last_ping_at) < _MIN_PING_INTERVAL_SECONDS:
            return _eleven_health.last_ping_reachable

    if _state.eleven_client is None:
        _eleven_health.last_ping_at = now_mono
        _eleven_health.last_ping_reachable = False
        return False

    try:
        # voices.get_all is a tiny GET — no synthesis, no audio bytes
        _ = _state.eleven_client.voices.get_all()
        reachable = True
    except Exception as e:  # pragma: no cover — network
        logger.warning(f"ElevenLabs live ping failed: {e}")
        reachable = False

    _eleven_health.last_ping_at = now_mono
    _eleven_health.last_ping_reachable = reachable
    return reachable


# ============================================================
# Speech classifier (pure function — heavily unit-tested)
# ============================================================
SpeechClass = Literal["human", "voicemail", "ivr", "dnc_request", "silence"]

_DNC_PATTERNS = [
    r"\bremove me\b",
    r"\btake me off\b",
    r"\bdo not call\b",
    r"\bdon'?t call\b",
    r"\bstop calling\b",
    r"\bno soliciting\b",
    r"\bnot interested.*remove\b",
    r"\bunsubscribe\b",
]

_VOICEMAIL_PATTERNS = [
    r"\bleave a message\b",
    r"\bafter the (tone|beep)\b",
    r"\bat the (tone|beep)\b",
    r"\b(you'?ve|you have) reached (the )?voicemail\b",
    r"\bvoicemail of\b",
    r"\bplease record your message\b",
    r"\bis (unavailable|not available) (right now|to take your call)\b",
    r"\bnot available to take your call\b",
]

_IVR_PATTERNS = [
    r"\bpress \d\b",
    r"\bfor (english|spanish|sales|billing|support|customer service)\b.*\bpress\b",
    r"\bmenu (has |options )?changed\b",
    r"\blisten carefully\b.*\bmenu\b",
    r"\bmain menu\b",
    r"\bif this is (a |an )?emergency\b",
    r"\bthank you for calling\b.*\b(press|menu|option)\b",
    r"\byour call (may be|is being) recorded\b",
    r"\b(dial|press) (zero|0) (to|for)\b",
]


def classify_speech(text: str) -> SpeechClass:
    """Classify caller speech. DNC > voicemail > ivr > human."""
    t = (text or "").strip().lower()
    if not t:
        return "silence"
    for p in _DNC_PATTERNS:
        if re.search(p, t):
            return "dnc_request"
    for p in _VOICEMAIL_PATTERNS:
        if re.search(p, t):
            return "voicemail"
    for p in _IVR_PATTERNS:
        if re.search(p, t):
            return "ivr"
    return "human"


# ============================================================
# DNC helpers
# ============================================================
async def is_on_dnc(db: Any, phone: str) -> bool:
    row = await db.dnc_list.find_one({"phone_number": phone})
    return row is not None


async def add_to_dnc(db: Any, phone: str, *, reason: str) -> None:
    await db.dnc_list.update_one(
        {"phone_number": phone},
        {"$set": {
            "phone_number": phone,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }},
        upsert=True,
    )


# ============================================================
# Outbound dialer entry point
# ============================================================
async def place_outbound_call(
    *,
    to_number: str,
    lead_id: str,
    campaign_id: str,
    variant_index: int,
    lead_attrs: Optional[Dict[str, Any]] = None,
    business_name: Optional[str] = None,
    experiment_tag: Optional[str] = None,
    opener_text_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Place an outbound call through the human-greeting gate.

    Returns:
      {"ok": True, "session_id": ..., "call_sid": ..., "opener_text": ...}
      {"ok": False, "skipped": "dnc"}                          # number on DNC
      {"ok": False, "error": "tts_failed"}                     # ElevenLabs unavailable

    If `opener_text_override` is provided, that exact string is used as the
    opener (no campaign session lookup). Used by the self-test script.
    """
    if _state.db is None or _state.twilio_client is None:
        raise RuntimeError("Outbound router not initialized — call setup_dependencies() first")

    # Hard safety gate — refuses to dial when the deploy pre-flight has marked
    # the system as broken. Created/removed by scripts/deploy_preflight.sh.
    if is_outbound_disabled():
        logger.error(
            f"[outbound] REFUSING to dial — kill switch present at {_state.kill_switch_path}. "
            "Run scripts/outbound_selftest.py and ensure exit 0 before re-enabling."
        )
        return {"ok": False, "blocked": "outbound_disabled", "kill_switch": _state.kill_switch_path}

    # Rule #9 — Skip DNC numbers BEFORE any TTS or Twilio spend
    if await is_on_dnc(_state.db, to_number):
        logger.info(f"[outbound] skipping {to_number} — on DNC list")
        return {"ok": False, "skipped": "dnc", "phone": to_number}

    if opener_text_override is not None:
        opener_text = opener_text_override
        session_context = {
            "campaign_id": campaign_id,
            "campaign_variant_index": variant_index,
            "campaign_variant_text": opener_text,
            "lead_source": "selftest",
            "lead_id": lead_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        # Build the campaign session (opener text)
        from universal.engines.campaign_session import CampaignSession  # local import
        session = CampaignSession.start_forced(
            lead_id=lead_id,
            lead_attrs=lead_attrs or {},
            campaign_id=campaign_id,
            variant_index=variant_index,
        )
        opener_text = session.opener_text
        session_context = session.session_context()

    # Pre-generate ElevenLabs MP3 for opener
    opener_bytes = _state.synthesize_fn(opener_text, _state.voice_id)
    if not opener_bytes:
        logger.error("[outbound] ElevenLabs synthesis failed — refusing to dial (no Say fallback)")
        return {"ok": False, "error": "tts_failed"}

    opener_audio_id = uuid.uuid4().hex
    _state.audio_store[opener_audio_id] = opener_bytes

    # Pre-generate the DNC acknowledgement clip (best-effort; we never fall back to <Say>)
    dnc_ack_text = "No problem. I'll add you to our do-not-call list right now. Have a good day."
    dnc_ack_bytes = _state.synthesize_fn(dnc_ack_text, _state.voice_id)
    dnc_ack_audio_id: Optional[str] = None
    if dnc_ack_bytes:
        dnc_ack_audio_id = uuid.uuid4().hex
        _state.audio_store[dnc_ack_audio_id] = dnc_ack_bytes

    session_id = uuid.uuid4().hex
    base = _state.backend_url
    answer_url = f"{base}/api/twilio/outbound/answer?session_id={session_id}"
    status_url = f"{base}/api/twilio/outbound/status?session_id={session_id}"

    # Rule #1 — URL callback, NEVER inline TwiML
    call = _state.twilio_client.calls.create(
        to=to_number,
        from_=_state.from_number,
        url=answer_url,
        method="POST",
        machine_detection="Enable",          # synchronous AMD; AnsweredBy in /answer form
        machine_detection_timeout=10,
        async_amd="false",
        status_callback=status_url,
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        status_callback_method="POST",
        record=True,
    )
    call_sid = getattr(call, "sid", None) or f"CA-{uuid.uuid4().hex[:30]}"

    await _state.db.outbound_sessions.insert_one({
        "session_id": session_id,
        "call_sid": call_sid,
        "lead_id": lead_id,
        "phone": to_number,
        "business_name": business_name,
        "campaign_id": campaign_id,
        "variant_index": variant_index,
        "opener_text": opener_text,
        "opener_audio_id": opener_audio_id,
        "dnc_ack_audio_id": dnc_ack_audio_id,
        "opener_played": False,
        "disposition": "PENDING",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "experiment": experiment_tag,
        "campaign_session": session_context,
    })

    logger.info(
        f"[outbound] placed call sid={call_sid} session={session_id} "
        f"campaign={campaign_id} variant={variant_index}"
    )
    return {
        "ok": True,
        "session_id": session_id,
        "call_sid": call_sid,
        "opener_text": opener_text,
    }



# ==================== RANKTRUST_VM_DROP_V1_CALLER ====================
async def place_voicemail_call(
    *,
    to_number: str,
    lead_id: str,
    campaign_id: str,
    call_id: str,
    voicemail_audio_url: str,
    business_name: Optional[str] = None,
) -> Dict[str, Any]:

    if _state.db is None or _state.twilio_client is None:
        raise RuntimeError(
            "Outbound router not initialized"
        )

    if is_outbound_disabled():
        return {
            "ok": False,
            "blocked": "outbound_disabled",
        }

    if (
        not voicemail_audio_url
        or not str(voicemail_audio_url).startswith(
            ("https://", "http://")
        )
    ):
        return {
            "ok": False,
            "error": "no_vm_audio",
        }

    if await is_on_dnc(
        _state.db,
        to_number,
    ):
        logger.info(
            f"[vm_outbound] skipping {to_number} — DNC"
        )
        return {
            "ok": False,
            "skipped": "dnc",
        }

    session_id = uuid.uuid4().hex

    answer_url = (
        f"{_state.backend_url}"
        f"/api/twilio/outbound/vm-answer"
        f"?session_id={session_id}"
    )

    status_url = (
        f"{_state.backend_url}"
        f"/api/twilio/outbound/vm-status"
        f"?session_id={session_id}"
    )

    # Final safety check immediately before Twilio spend.
    if is_outbound_disabled():
        return {
            "ok": False,
            "blocked": "outbound_disabled",
        }

    try:
        call = _state.twilio_client.calls.create(
            to=to_number,
            from_=_state.from_number,
            url=answer_url,
            method="POST",
            machine_detection="Enable",
            machine_detection_timeout=10,
            async_amd="false",
            status_callback=status_url,
            status_callback_event=[
                "initiated",
                "ringing",
                "answered",
                "completed",
            ],
            status_callback_method="POST",
            record=True,
        )

    except Exception as exc:
        logger.exception(
            "[vm_outbound] Twilio calls.create failed"
        )

        return {
            "ok": False,
            "error": "twilio_create_failed",
            "detail": str(exc)[:160],
        }

    call_sid = getattr(
        call,
        "sid",
        None,
    )

    if not call_sid:
        return {
            "ok": False,
            "error": "missing_call_sid",
        }

    await _state.db.outbound_sessions.insert_one({
        "session_id": session_id,
        "call_sid": call_sid,
        "call_id": call_id,
        "lead_id": lead_id,
        "phone": to_number,
        "business_name": business_name,
        "campaign_id": campaign_id,
        "voicemail_mode": True,
        "voicemail_audio_url": voicemail_audio_url,
        "voicemail_played": False,
        "disposition": "PENDING",
        "started_at": datetime.now(
            timezone.utc
        ).isoformat(),
    })

    return {
        "ok": True,
        "session_id": session_id,
        "call_sid": call_sid,
    }
# ================== END RANKTRUST_VM_DROP_V1_CALLER ==================


async def _set_disposition(call_sid: str, session_id: str, disposition: str, **extra: Any) -> None:
    update: Dict[str, Any] = {"disposition": disposition,
                              "last_event_at": datetime.now(timezone.utc).isoformat()}
    for k, v in extra.items():
        update[k] = v
    await _state.db.outbound_sessions.update_one(
        {"session_id": session_id},
        {"$set": update},
    )


def _twiml(response: VoiceResponse) -> Response:
    return Response(content=str(response), media_type="application/xml")


# ============================================================
# Twilio webhook router  (mounted at /api → /api/twilio/outbound/*)
# ============================================================
router = APIRouter(prefix="/twilio/outbound", tags=["twilio_outbound"])


@router.post("/answer")
async def outbound_answer(request: Request, session_id: str) -> Response:
    """First webhook fired by Twilio when the line opens. Decides voicemail vs human.

    Hard rule: this endpoint NEVER speaks.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "") or ""
    answered_by = (form.get("AnsweredBy") or "").lower()

    response = VoiceResponse()

    if answered_by.startswith("machine") or answered_by == "fax":
        # Voicemail / fax → silent hangup. No <Say>, no <Play>.
        await _set_disposition(call_sid, session_id, "VOICEMAIL", answered_by=answered_by)
        response.hangup()
        return _twiml(response)

    # Human or unknown → wait for them to greet us. Redirect to the silent gate.
    await _state.db.outbound_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"answered_at": datetime.now(timezone.utc).isoformat(),
                  "answered_by": answered_by or "unknown"}},
    )
    response.redirect(
        f"/api/twilio/outbound/greeting?session_id={session_id}",
        method="POST",
    )
    return _twiml(response)


@router.post("/greeting")
async def outbound_greeting(request: Request, session_id: str) -> Response:
    """Silent <Gather> waiting for the human to say something first.

    Hard rule: NO <Say>, NO <Play>. The AI never speaks until /respond hears a human.
    """
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        speech_timeout="auto",
        timeout=8,
        action=f"/api/twilio/outbound/respond?session_id={session_id}",
        method="POST",
    )
    # Intentionally empty — silent listening only.
    response.append(gather)
    # If they never say anything, hang up. NO robotic Say fallback.
    response.hangup()
    return _twiml(response)


@router.post("/respond")
async def outbound_respond(request: Request, session_id: str) -> Response:
    """Receives first human utterance. Classifies, then either plays opener
    (ElevenLabs <Play>) or short-circuits (voicemail/IVR/DNC) with a silent hangup.
    """
    form = await request.form()
    call_sid = form.get("CallSid", "") or ""
    speech = (form.get("SpeechResult") or "").strip()

    sess = await _state.db.outbound_sessions.find_one({"session_id": session_id})
    if not sess:
        # Unknown session — hang up silently
        r = VoiceResponse(); r.hangup()
        return _twiml(r)

    kind = classify_speech(speech)
    response = VoiceResponse()

    if kind in ("voicemail", "ivr"):
        await _set_disposition(call_sid, session_id, kind.upper(), caller_first_speech=speech)
        response.hangup()
        return _twiml(response)

    if kind == "dnc_request":
        phone = sess.get("phone") or ""
        if phone:
            await add_to_dnc(_state.db, phone, reason="caller_requested")
        await _set_disposition(call_sid, session_id, "DNC", caller_first_speech=speech)

        # Acknowledge via ElevenLabs if we pre-generated it; otherwise just hang up.
        ack_id = sess.get("dnc_ack_audio_id")
        if ack_id and ack_id in _state.audio_store:
            response.play(f"{_state.backend_url}/api/tts/audio/{ack_id}")
        # NEVER fall back to Twilio <Say>.
        response.hangup()
        return _twiml(response)

    if kind == "silence":
        # No speech captured — give them one more silent chance.
        gather = Gather(
            input="speech",
            speech_timeout="auto",
            timeout=6,
            action=f"/api/twilio/outbound/respond?session_id={session_id}",
            method="POST",
        )
        response.append(gather)
        response.hangup()
        return _twiml(response)

    # kind == "human" — play the opener (first turn only).
    if not sess.get("opener_played"):
        audio_id = sess.get("opener_audio_id")
        if not audio_id or audio_id not in _state.audio_store:
            logger.error(
                f"[outbound] opener audio missing for session={session_id} — hanging up "
                "(no robotic Say fallback)"
            )
            response.hangup()
            return _twiml(response)

        response.play(f"{_state.backend_url}/api/tts/audio/{audio_id}")
        await _state.db.outbound_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "opener_played": True,
                "first_human_speech": speech,
                "opener_played_at": datetime.now(timezone.utc).isoformat(),
                "disposition": "CONVERSATION",
            }},
        )

        # Hand off the rest of the conversation to the legacy inbound brain.
        gather = Gather(
            input="speech",
            speech_timeout="auto",
            timeout=6,
            action="/api/twilio/inbound/respond",
            method="POST",
        )
        response.append(gather)
        response.hangup()
        return _twiml(response)

    # Opener already played → straight handoff to legacy inbound respond.
    response.redirect("/api/twilio/inbound/respond", method="POST")
    return _twiml(response)



# ==================== RANKTRUST_VM_DROP_V1_ANSWER ====================
@router.post("/vm-answer")
async def outbound_vm_answer(
    request: Request,
    session_id: str,
) -> Response:

    form = await request.form()

    answered_by = (
        form.get("AnsweredBy")
        or "unknown"
    ).lower()

    sess = await _state.db.outbound_sessions.find_one({
        "session_id": session_id
    })

    response = VoiceResponse()

    if (
        not sess
        or not sess.get("voicemail_mode")
    ):
        response.hangup()
        return _twiml(response)

    audio_url = sess.get(
        "voicemail_audio_url"
    )

    if not audio_url:

        await _state.db.outbound_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "disposition": "VM_AUDIO_MISSING",
                "answered_by": answered_by,
            }},
        )

        response.hangup()
        return _twiml(response)

    if (
        answered_by.startswith("machine")
        or answered_by == "fax"
    ):
        disposition = "VOICEMAIL"
    else:
        disposition = "HUMAN_VM_PLAYED"

    response.play(audio_url)
    response.hangup()

    await _state.db.outbound_sessions.update_one(
        {"session_id": session_id},
        {"$set": {
            "answered_by": answered_by,
            "answered_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "voicemail_played": True,
            "disposition": disposition,
        }},
    )

    return _twiml(response)
# ================== END RANKTRUST_VM_DROP_V1_ANSWER ==================



# ==================== RANKTRUST_VM_DROP_V1_STATUS ====================
@router.post("/vm-status")
async def outbound_vm_status(
    request: Request,
    session_id: Optional[str] = None,
) -> Response:

    form = await request.form()

    call_sid = form.get("CallSid", "") or ""
    call_status = form.get("CallStatus", "") or ""
    answered_by = (
        form.get("AnsweredBy")
        or ""
    ).lower()

    duration = int(
        form.get("CallDuration", "0")
        or 0
    )

    q = (
        {"session_id": session_id}
        if session_id
        else {"call_sid": call_sid}
    )

    sess = await _state.db.outbound_sessions.find_one(q)

    if not sess:
        return Response(
            content="<Response/>",
            media_type="application/xml",
        )

    update = {
        "final_call_status": call_status,
        "duration_seconds": duration,
        "ended_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    if answered_by:
        update["answered_by"] = answered_by

    await _state.db.outbound_sessions.update_one(
        q,
        {"$set": update},
    )

    call_id = sess.get("call_id")

    if call_id:

        if call_status == "completed":
            final_status = "completed"

        elif call_status == "busy":
            final_status = "busy"

        elif call_status in (
            "no-answer",
            "canceled",
        ):
            final_status = "no_answer"

        else:
            final_status = "failed"

        await _state.db.calls.update_one(
            {"id": call_id},
            {"$set": {
                "status": final_status,
                "duration_seconds": duration,
                "ended_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "answered_by": (
                    answered_by
                    or sess.get("answered_by")
                ),
                "amd_status": (
                    answered_by
                    or sess.get("answered_by")
                ),
                "voicemail_dropped": bool(
                    sess.get("voicemail_played")
                ),
                "qualification_result.disposition":
                    sess.get("disposition")
                    or "PENDING",
            }},
        )

    return Response(
        content="<Response/>",
        media_type="application/xml",
    )
# ================== END RANKTRUST_VM_DROP_V1_STATUS ==================


@router.post("/status")
async def outbound_status(request: Request, session_id: Optional[str] = None) -> Response:
    """Final disposition webhook. Records call status + duration."""
    form = await request.form()
    call_sid = form.get("CallSid", "") or ""
    call_status = form.get("CallStatus", "") or ""
    answered_by = form.get("AnsweredBy", "") or ""
    duration = int(form.get("CallDuration", "0") or 0)

    update: Dict[str, Any] = {
        "final_call_status": call_status,
        "duration_seconds": duration,
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }
    if answered_by:
        update["answered_by"] = answered_by

    q = {"session_id": session_id} if session_id else {"call_sid": call_sid}
    await _state.db.outbound_sessions.update_one(q, {"$set": update})

    # Twilio expects an empty 200; return empty TwiML for safety.
    return Response(content="<Response/>", media_type="application/xml")


# ============================================================
# TTS audio streaming router  (mounted at /api → /api/tts/audio/{id})
# ============================================================
tts_router = APIRouter(prefix="/tts", tags=["tts"])


@tts_router.get("/audio/{audio_id}")
async def get_tts_audio(audio_id: str) -> Response:
    data = _state.audio_store.get(audio_id)
    if not data:
        raise HTTPException(status_code=404, detail="audio not found")
    return Response(
        content=data,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ============================================================
# Admin status router  (mounted at /api → /api/admin/outbound-status)
# Surfaces safe metadata about the dialer's safety state. NO secrets.
# ============================================================
admin_router = APIRouter(prefix="/admin", tags=["admin_outbound"])


def _read_selftest_report_safely(path: str) -> Dict[str, Any]:
    """Read only safe metadata from the self-test report. Never returns:
       - audio URLs (could leak the backend host),
       - phone numbers,
       - the structural sweep detail (could leak per-run setup phones).
       Only returns: passed, mode, finished_at/started_at, structural_passed.
    """
    import json
    safe: Dict[str, Any] = {
        "passed": None,
        "finished_at": None,
        "mode": None,
    }
    try:
        if not os.path.isfile(path):
            return safe
        with open(path, "r") as f:
            raw = json.load(f)
        # Whitelist only top-level scalars we can vouch for.
        if isinstance(raw, dict):
            if isinstance(raw.get("passed"), bool):
                safe["passed"] = raw["passed"]
            for key in ("finished_at", "started_at", "mode"):
                v = raw.get(key)
                if isinstance(v, str):
                    safe[key] = v
            # Prefer finished_at, fall back to started_at
            if safe.get("finished_at") is None and isinstance(safe.get("started_at"), str):
                safe["finished_at"] = safe["started_at"]
    except (OSError, ValueError):
        # Malformed or unreadable report — treat as unknown.
        pass
    safe.pop("started_at", None)
    return safe


@admin_router.get("/outbound-status")
async def outbound_status_admin() -> Dict[str, Any]:
    """Return safe metadata about whether outbound dialing is currently allowed.

    Read-only. Never exposes API keys, backend URLs with tokens, or raw
    provider responses. Designed for an admin dashboard / uptime monitor.
    """
    kill_path = _state.kill_switch_path or ""
    report_path = _state.selftest_report_path or ""
    kill_switch_present = bool(kill_path) and os.path.isfile(kill_path)

    report = _read_selftest_report_safely(report_path)
    last_passed = report.get("passed")  # True / False / None
    last_at = report.get("finished_at")

    # Decision matrix
    if kill_switch_present:
        can_live_dial = False
        reason = "OUTBOUND_DISABLED sentinel present — last deploy pre-flight failed."
    elif last_passed is None:
        can_live_dial = False
        reason = "No self-test report found — run scripts/deploy_preflight.sh first."
    elif last_passed is False:
        can_live_dial = False
        reason = "Last self-test reported passed=false — fix the regression and re-run."
    else:
        can_live_dial = True
        reason = "Self-test passed and no kill switch present — outbound dialing allowed."

    return {
        "kill_switch_present": kill_switch_present,
        "outbound_disabled": kill_switch_present,
        "last_selftest_at": last_at,
        "last_selftest_passed": last_passed,
        "last_selftest_report_path": report_path,
        "can_live_dial": can_live_dial,
        "reason": reason,
    }


# ----- ElevenLabs status (cached metadata, rate-limited optional ping) -----
_LATENCY_WARN_MS = 3000
_STALE_SUCCESS_WARN_SECONDS = 3600  # 1 hour


@admin_router.get("/elevenlabs-status")
async def elevenlabs_status_admin() -> Dict[str, Any]:
    """Return safe metadata about ElevenLabs health.

    Strategy:
      1. Primary signal — cached metadata from real production synth calls
         (`_default_eleven_synthesize` updates the cache on every attempt).
      2. Fallback signal — lightweight `voices.get_all()` ping, RATE-LIMITED to
         once per 10 minutes. NEVER triggers a synth.

    NEVER returns: API keys, voice IDs, raw provider responses, URLs with
    auth, raw exception tracebacks.
    """
    reachable = _maybe_live_ping_elevenlabs()
    last_success_iso = _eleven_health.last_successful_synth_at
    last_attempt_iso = _eleven_health.last_synth_at
    latency_ms = int(_eleven_health.last_synth_latency_ms or 0)

    # Decide status
    status = "unknown"
    reason = "No synthesis activity yet — ElevenLabs health unknown."
    if reachable is False:
        status = "down"
        reason = "ElevenLabs API is not reachable from this host."
    elif last_success_iso is None and reachable is True:
        status = "warn"
        reason = "API reachable but no successful synthesis has been recorded yet."
    elif last_success_iso is not None:
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(last_success_iso)).total_seconds()
        except (TypeError, ValueError):
            age = 0
        if age > _STALE_SUCCESS_WARN_SECONDS:
            status = "warn"
            reason = f"Last successful synthesis was over {int(age // 60)} minutes ago."
        elif latency_ms > _LATENCY_WARN_MS:
            status = "warn"
            reason = f"Last synthesis latency was {latency_ms}ms — above {_LATENCY_WARN_MS}ms threshold."
        else:
            status = "safe"
            reason = "ElevenLabs reachable and synthesizing within latency budget."

    # Build response — strict whitelist, no secrets, no voice IDs
    return {
        "api_reachable": bool(reachable) if reachable is not None else False,
        "last_synth_at": last_attempt_iso,
        "last_synth_latency_ms": latency_ms,
        "last_successful_synth_at": last_success_iso,
        "status": status,
        "reason": reason,
    }
