"""Outbound Human-Greeting Gate — REGRESSION TESTS.

These 9 tests are the contract for the outbound dialer. Production code must
satisfy ALL of them before any live prospect dials are placed.

Hard rules being enforced:
  1. Outbound call creation uses URL callback, NEVER inline TwiML opener.
  2. AI opener is never present in the initial outbound call TwiML.
  3. /outbound/answer never speaks (no <Say>, no <Play>).
  4. /outbound/answer only gathers silently / redirects silently.
  5. /outbound/greeting waits for human speech before opener (silent <Gather>).
  6. /outbound/greeting + /outbound/respond use ElevenLabs <Play>, never <Say>.
  7. Voicemail / IVR phrases classify as voicemail/ivr and do NOT start convo.
  8. DNC requests write to db.dnc_list.
  9. Dialer skips numbers already in db.dnc_list.
"""
from __future__ import annotations
import os
import sys
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

# Ensure the backend package is importable
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from routes import twilio_outbound  # noqa: E402


# ---------- Helpers ----------

def _twiml_root(xml_text: str) -> ET.Element:
    return ET.fromstring(xml_text)


def _twiml_has_say(xml_text: str) -> bool:
    return _twiml_root(xml_text).find(".//Say") is not None


def _twiml_has_play(xml_text: str) -> bool:
    return _twiml_root(xml_text).find(".//Play") is not None


def _twiml_gather(xml_text: str) -> Optional[ET.Element]:
    return _twiml_root(xml_text).find(".//Gather")


class FakeTwilioCall:
    def __init__(self, sid: str):
        self.sid = sid


class FakeTwilioCalls:
    def __init__(self):
        self.created_kwargs: List[Dict[str, Any]] = []

    def create(self, **kwargs):
        self.created_kwargs.append(kwargs)
        return FakeTwilioCall(sid=f"CA{uuid.uuid4().hex[:30]}")


class FakeTwilioClient:
    def __init__(self):
        self.calls = FakeTwilioCalls()


class FakeElevenLabsClient:
    """Returns deterministic non-empty MP3 bytes; tracks calls."""
    def __init__(self):
        self.invocations: List[Dict[str, Any]] = []

    def synthesize(self, text: str, voice_id: str) -> bytes:
        self.invocations.append({"text": text, "voice_id": voice_id})
        # Pseudo-MP3 bytes (header-ish) — enough to assert non-empty + streamed.
        return b"ID3\x04\x00\x00\x00\x00\x00\x00FAKE_MP3:" + text.encode()[:64]


# ---------- Fixtures ----------

@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    return client["intentbrain_test"]


@pytest.fixture
def fake_twilio():
    return FakeTwilioClient()


@pytest.fixture
def fake_eleven():
    return FakeElevenLabsClient()


@pytest.fixture
def app(db, fake_twilio, fake_eleven):
    """Build a minimal FastAPI app with ONLY the outbound router mounted under /api."""
    app = FastAPI()
    twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=fake_twilio,
        eleven_client=fake_eleven,
        synthesize_fn=fake_eleven.synthesize,
        voice_id="VOICE_TEST_001",
        backend_url="https://test.example.com",
        from_number="+15005550006",
    )
    app.include_router(twilio_outbound.router, prefix="/api")
    app.include_router(twilio_outbound.tts_router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


# ============================================================
# TEST 1 — Outbound call creation uses URL callback, not inline TwiML opener.
# ============================================================
@pytest.mark.asyncio
async def test_1_call_creation_uses_url_callback_not_inline_twiml(db, fake_twilio, fake_eleven, app):
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234567",
        lead_id="lead-001",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
        business_name="Test Dental",
    )
    assert result["ok"] is True
    assert len(fake_twilio.calls.created_kwargs) == 1
    kw = fake_twilio.calls.created_kwargs[0]

    # MUST use url callback
    assert "url" in kw and kw["url"], "calls.create must pass a url= callback"
    assert "/api/twilio/outbound/answer" in kw["url"]

    # MUST NOT use inline TwiML
    assert "twiml" not in kw, "calls.create MUST NOT pass inline twiml="

    # Status callback must point to outbound/status (not legacy)
    assert "/api/twilio/outbound/status" in kw["status_callback"]


# ============================================================
# TEST 2 — AI opener is never present in the initial outbound call TwiML.
# ============================================================
@pytest.mark.asyncio
async def test_2_no_opener_in_initial_call_request(db, fake_twilio, fake_eleven, app):
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234568",
        lead_id="lead-002",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    assert result["ok"] is True
    opener = result["opener_text"].lower()
    kw = fake_twilio.calls.created_kwargs[0]

    # Twilio.calls.create must NOT contain the opener anywhere
    serialized = " ".join(str(v) for v in kw.values()).lower()
    assert opener not in serialized, "Opener text must NEVER appear in the outbound call create() payload"

    # And no <Say>/<Play> embedded
    assert "<say" not in serialized
    assert "<play" not in serialized


# ============================================================
# TEST 3 — /outbound/answer does not speak.
# TEST 4 — /outbound/answer only gathers silently (no Say, no Play).
# ============================================================
@pytest.mark.asyncio
async def test_3_and_4_answer_does_not_speak(db, fake_twilio, fake_eleven, client):
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234569",
        lead_id="lead-003",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    session_id = result["session_id"]
    call_sid = result["call_sid"]

    # Simulate Twilio AMD result: human
    resp = client.post(
        f"/api/twilio/outbound/answer?session_id={session_id}",
        data={"CallSid": call_sid, "AnsweredBy": "human"},
    )
    assert resp.status_code == 200
    xml = resp.text

    # Hard rules
    assert not _twiml_has_say(xml), "/answer MUST NOT emit <Say>"
    assert not _twiml_has_play(xml), "/answer MUST NOT emit <Play> (no AI speech before human greets us)"

    # Must redirect to /greeting silently
    root = _twiml_root(xml)
    redirect = root.find(".//Redirect")
    assert redirect is not None, "/answer must <Redirect> to /greeting"
    assert "/api/twilio/outbound/greeting" in (redirect.text or "")


# ============================================================
# TEST 5 — /outbound/greeting waits for human speech before opener.
# TEST 6 (part A) — /outbound/greeting uses ElevenLabs <Play>, never Twilio <Say>.
# ============================================================
@pytest.mark.asyncio
async def test_5_and_6a_greeting_silent_gather_no_say(db, fake_twilio, fake_eleven, client):
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234570",
        lead_id="lead-004",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    session_id = result["session_id"]
    call_sid = result["call_sid"]

    resp = client.post(
        f"/api/twilio/outbound/greeting?session_id={session_id}",
        data={"CallSid": call_sid},
    )
    assert resp.status_code == 200
    xml = resp.text

    # NO speech at all in the greeting waiting state
    assert not _twiml_has_say(xml), "/greeting MUST NEVER emit <Say>"
    assert not _twiml_has_play(xml), "/greeting MUST NOT play opener before human speech"

    # Must contain a Gather waiting for speech
    gather = _twiml_gather(xml)
    assert gather is not None, "/greeting MUST contain a <Gather>"
    assert gather.get("input", "").startswith("speech"), "<Gather> must accept speech input"
    assert gather.get("speechTimeout") == "auto", "<Gather speechTimeout='auto'> required"
    action = gather.get("action") or ""
    assert "/api/twilio/outbound/respond" in action

    # Gather must have NO Say/Play children — silent wait
    assert gather.find("./Say") is None
    assert gather.find("./Play") is None


# ============================================================
# TEST 6 (part B) — /outbound/respond plays opener via ElevenLabs <Play>, never <Say>.
# ============================================================
@pytest.mark.asyncio
async def test_6b_respond_plays_elevenlabs_never_says(db, fake_twilio, fake_eleven, client):
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234571",
        lead_id="lead-005",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    session_id = result["session_id"]
    call_sid = result["call_sid"]

    # Human says "hello"
    resp = client.post(
        f"/api/twilio/outbound/respond?session_id={session_id}",
        data={"CallSid": call_sid, "SpeechResult": "Hello, this is Sarah."},
    )
    assert resp.status_code == 200
    xml = resp.text

    # MUST be ElevenLabs <Play>, never <Say>
    assert not _twiml_has_say(xml), "/respond MUST NEVER emit Twilio <Say> for AI voice"
    assert _twiml_has_play(xml), "/respond MUST emit ElevenLabs <Play> for the opener"

    # The Play URL must point at our streaming TTS endpoint
    play = _twiml_root(xml).find(".//Play")
    play_url = (play.text or "").strip()
    assert "/api/tts/audio/" in play_url

    # And the audio_id served from that URL must be fetchable + non-empty MP3
    audio_id = play_url.rsplit("/", 1)[-1]
    audio_resp = client.get(f"/api/tts/audio/{audio_id}")
    assert audio_resp.status_code == 200
    assert audio_resp.headers["content-type"].startswith("audio/mpeg")
    assert len(audio_resp.content) > 0


# ============================================================
# TEST 7 — Voicemail / IVR phrases classify as voicemail/ivr and do NOT start conversation.
# ============================================================
@pytest.mark.asyncio
async def test_7_voicemail_and_ivr_do_not_start_conversation(db, fake_twilio, fake_eleven, client):
    # --- A: AMD says machine_end_beep at /answer ---
    r1 = await twilio_outbound.place_outbound_call(
        to_number="+15551234572", lead_id="lead-006",
        campaign_id="ranktrust_local_growth", variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    resp = client.post(
        f"/api/twilio/outbound/answer?session_id={r1['session_id']}",
        data={"CallSid": r1["call_sid"], "AnsweredBy": "machine_end_beep"},
    )
    xml = resp.text
    assert not _twiml_has_say(xml)
    assert not _twiml_has_play(xml)
    assert _twiml_root(xml).find(".//Hangup") is not None, "Machine → must <Hangup>"

    # Confirm the session is logged as VOICEMAIL
    sess = await db.outbound_sessions.find_one({"session_id": r1["session_id"]})
    assert sess["disposition"] == "VOICEMAIL"

    # --- B: IVR phrase reaches /respond ("press 1 for sales") ---
    r2 = await twilio_outbound.place_outbound_call(
        to_number="+15551234573", lead_id="lead-007",
        campaign_id="ranktrust_local_growth", variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    resp = client.post(
        f"/api/twilio/outbound/respond?session_id={r2['session_id']}",
        data={"CallSid": r2["call_sid"], "SpeechResult":
              "Thank you for calling. For sales press 1. For billing press 2."},
    )
    xml = resp.text
    assert not _twiml_has_play(xml), "IVR detection must NOT play the opener"
    assert not _twiml_has_say(xml)
    assert _twiml_root(xml).find(".//Hangup") is not None

    sess = await db.outbound_sessions.find_one({"session_id": r2["session_id"]})
    assert sess["disposition"] == "IVR"
    assert sess["opener_played"] is False

    # --- C: Voicemail phrase reaches /respond ("please leave a message after the tone") ---
    r3 = await twilio_outbound.place_outbound_call(
        to_number="+15551234574", lead_id="lead-008",
        campaign_id="ranktrust_local_growth", variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    resp = client.post(
        f"/api/twilio/outbound/respond?session_id={r3['session_id']}",
        data={"CallSid": r3["call_sid"], "SpeechResult":
              "You have reached the voicemail of Dr Smith. Please leave a message after the tone."},
    )
    xml = resp.text
    assert not _twiml_has_play(xml)
    assert not _twiml_has_say(xml)
    sess = await db.outbound_sessions.find_one({"session_id": r3["session_id"]})
    assert sess["disposition"] == "VOICEMAIL"
    assert sess["opener_played"] is False


# ============================================================
# TEST 8 — DNC request writes to db.dnc_list.
# ============================================================
@pytest.mark.asyncio
async def test_8_dnc_request_writes_to_dnc_list(db, fake_twilio, fake_eleven, client):
    phone = "+15551234575"
    result = await twilio_outbound.place_outbound_call(
        to_number=phone, lead_id="lead-009",
        campaign_id="ranktrust_local_growth", variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    session_id = result["session_id"]
    call_sid = result["call_sid"]

    # Caller asks to be removed
    resp = client.post(
        f"/api/twilio/outbound/respond?session_id={session_id}",
        data={"CallSid": call_sid, "SpeechResult": "Please take me off your list, do not call again."},
    )
    assert resp.status_code == 200
    xml = resp.text
    # No robotic Say even on DNC ack
    assert not _twiml_has_say(xml), "DNC ack must use ElevenLabs <Play>, never Twilio <Say>"
    assert _twiml_root(xml).find(".//Hangup") is not None

    # DNC row written
    dnc = await db.dnc_list.find_one({"phone_number": phone})
    assert dnc is not None
    assert dnc["reason"] == "caller_requested"

    # Disposition logged
    sess = await db.outbound_sessions.find_one({"session_id": session_id})
    assert sess["disposition"] == "DNC"


# ============================================================
# TEST 9 — Dialer skips numbers already in db.dnc_list.
# ============================================================
@pytest.mark.asyncio
async def test_9_dialer_skips_dnc_numbers(db, fake_twilio, fake_eleven, app):
    bad = "+15559999999"
    await db.dnc_list.insert_one({"phone_number": bad, "added_at": "2026-01-01T00:00:00Z", "reason": "prior_request"})

    result = await twilio_outbound.place_outbound_call(
        to_number=bad, lead_id="lead-skip",
        campaign_id="ranktrust_local_growth", variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    assert result["ok"] is False
    assert result["skipped"] == "dnc"
    # No Twilio call placed
    assert len(fake_twilio.calls.created_kwargs) == 0
    # No TTS generated (don't waste credits)
    assert len(fake_eleven.invocations) == 0


# ============================================================
# Bonus — speech classifier unit coverage
# ============================================================
def test_classify_speech_human_vs_machine():
    classify = twilio_outbound.classify_speech
    assert classify("Hello, this is Sarah") == "human"
    assert classify("Hi there") == "human"
    assert classify("Yeah this is John") == "human"

    assert classify("Please leave a message after the tone") == "voicemail"
    assert classify("You have reached the voicemail of doctor smith") == "voicemail"
    assert classify("At the beep please record your message") == "voicemail"

    assert classify("For sales press 1, for billing press 2") == "ivr"
    assert classify("Thank you for calling. Please listen carefully as our menu has changed") == "ivr"
    assert classify("If this is an emergency please hang up and dial 911") == "ivr"

    assert classify("Remove me from your list") == "dnc_request"
    assert classify("Do not call this number again") == "dnc_request"
    assert classify("Take me off your call list") == "dnc_request"
    assert classify("Stop calling me") == "dnc_request"

    assert classify("") == "silence"
    assert classify("   ") == "silence"


# ============================================================
# TEST 10 — Kill switch sentinel file blocks dialing.
# This is the deploy-time safety gate: when scripts/deploy_preflight.sh detects
# a structural self-test failure it writes the OUTBOUND_DISABLED file, and the
# router refuses to place any outbound call until the file is removed.
# ============================================================
@pytest.mark.asyncio
async def test_10_kill_switch_blocks_outbound(tmp_path, db, fake_twilio, fake_eleven):
    kill_file = tmp_path / "OUTBOUND_DISABLED"
    kill_file.write_text("selftest failed at 2026-02-25T19:00:00Z\nexit_code=1\n")

    twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=fake_twilio,
        eleven_client=fake_eleven,
        synthesize_fn=fake_eleven.synthesize,
        voice_id="VOICE_TEST_001",
        backend_url="https://test.example.com",
        from_number="+15005550006",
        kill_switch_path=str(kill_file),
    )

    assert twilio_outbound.is_outbound_disabled() is True

    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234599",
        lead_id="lead-blocked",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    assert result["ok"] is False
    assert result["blocked"] == "outbound_disabled"
    # No Twilio call, no ElevenLabs spend
    assert len(fake_twilio.calls.created_kwargs) == 0
    assert len(fake_eleven.invocations) == 0

    # Removing the sentinel re-enables dialing
    kill_file.unlink()
    assert twilio_outbound.is_outbound_disabled() is False
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551234599",
        lead_id="lead-allowed",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "dental"},
    )
    assert result["ok"] is True


def test_classify_speech_human_vs_machine_DUPLICATE_GUARD():
    # Sentinel — ensures the file order didn't get jumbled by an edit.
    assert callable(twilio_outbound.classify_speech)
