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
) -> None:
    """Wire production clients into the outbound router. Idempotent."""
    _state.db = db
    _state.twilio_client = twilio_client
    _state.eleven_client = eleven_client
    _state.synthesize_fn = synthesize_fn or _default_eleven_synthesize
    _state.voice_id = voice_id
    _state.backend_url = backend_url.rstrip("/")
    _state.from_number = from_number


def _default_eleven_synthesize(text: str, voice_id: str) -> bytes:
    """Default ElevenLabs synth path. Returns b"" on failure (caller must handle)."""
    client = _state.eleven_client
    if client is None:
        logger.error("ElevenLabs client not configured — cannot synthesize")
        return b""
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
        return out
    except Exception as e:  # pragma: no cover - network path
        logger.error(f"ElevenLabs synthesis failed: {e}")
        return b""


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
