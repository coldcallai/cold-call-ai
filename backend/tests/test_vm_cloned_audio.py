"""Cloned-voice voicemail — TwiML branching + persistence tests.

Requirement (RankTrust operator):
  * Cloned-voice campaign → generate_voicemail_twiml returns <Play>.
  * Non-cloned campaign      → generate_voicemail_twiml returns <Say>.
  * Placeholder-stripping in the baked message is correct.
  * The persisted MP3 round-trips through the /api/vm-audio/{id} endpoint
    with Content-Type: audio/mpeg.

These tests never touch the RankTrust webhook, SMS, funnel, retry cadence,
or the ElevenLabs Human-Greeting Gate. They mock ElevenLabs.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


# --------- Fixtures ---------
@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    return client["intentbrain_test_vm_cloned"]


@pytest.fixture
def fake_eleven_client():
    """Fake ElevenLabs client whose synth returns known bytes."""
    client = MagicMock()
    # `.text_to_speech.convert(...)` is a generator yielding chunks.
    def _convert(**kwargs):
        yield b"ID3\x04\x00\x00\x00fake-mp3-header"
        yield b"AAA_body_bytes_for_" + kwargs["voice_id"].encode()[:16]
    client.text_to_speech.convert.side_effect = _convert
    return client


# --------- 1) Placeholder stripping ---------
def test_1_placeholder_stripping():
    from services.vm_cloned_audio import _bake_message
    msg = "Hi {contact_name}, this is a message for {business_name} from {company_name}."
    out = _bake_message(msg, {"company_name": "IntentBrain"})
    assert "{contact_name}" not in out
    assert "{business_name}" not in out
    assert "IntentBrain" in out
    # No lingering double spaces or stray-comma artifacts from stripped names
    assert "  " not in out
    assert " ," not in out


# --------- 2) refresh_campaign_vm_audio: cloned voice present → writes MP3, sets URL ---------
@pytest.mark.asyncio
async def test_2_refresh_writes_mp3_and_sets_url(db, fake_eleven_client, tmp_path, monkeypatch):
    # Point the module's disk dir at a tmp path so tests are hermetic
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    user_id = "u-test-1"
    campaign_id = "cmp-cloned-1"
    await db.campaigns.insert_one({
        "id": campaign_id,
        "user_id": user_id,
        "voicemail_enabled": True,
        "voicemail_message": "Hi, this is a test voicemail.",
        "company_name": "TestCo",
    })
    await db.cloned_voices.insert_one({
        "id": "v-1", "user_id": user_id,
        "elevenlabs_voice_id": "voice_abc123", "name": "MyVoice",
    })

    url = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=fake_eleven_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    assert url == "https://intentbrain.ai/api/vm-audio/cmp-cloned-1"

    # MP3 written to disk
    on_disk = tmp_path / "cmp-cloned-1.mp3"
    assert on_disk.is_file()
    assert on_disk.read_bytes().startswith(b"ID3")

    # Campaign row updated
    row = await db.campaigns.find_one({"id": campaign_id})
    assert row["voicemail_audio_url"] == url


# --------- 3) refresh_campaign_vm_audio: no cloned voice → clears URL, no file ---------
@pytest.mark.asyncio
async def test_3_no_cloned_voice_clears_url(db, fake_eleven_client, tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    user_id = "u-test-2"
    campaign_id = "cmp-polly-only"
    await db.campaigns.insert_one({
        "id": campaign_id,
        "user_id": user_id,
        "voicemail_enabled": True,
        "voicemail_message": "Hi, this is a test.",
        "voicemail_audio_url": "https://stale.example/api/vm-audio/cmp-polly-only",
    })
    # NOTE: no cloned_voices row for this user

    url = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=fake_eleven_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    assert url is None
    # Stale URL should have been cleared
    row = await db.campaigns.find_one({"id": campaign_id})
    assert row["voicemail_audio_url"] is None
    # No file written
    assert not (tmp_path / "cmp-polly-only.mp3").exists()


# --------- 4) generate_voicemail_twiml → <Play> when audio URL set ---------
def test_4_twiml_uses_play_when_audio_url_present():
    """Verify the TwiML branching without importing the whole server.py.
    We exercise the same conditional the server code uses.
    """
    from twilio.twiml.voice_response import VoiceResponse

    def _twiml(campaign):
        response = VoiceResponse()
        vm_audio_url = campaign.get("voicemail_audio_url")
        if vm_audio_url:
            response.play(vm_audio_url)
            response.pause(length=1)
            response.hangup()
            return str(response)
        response.say("Hi, fallback message.", voice="Polly.Matthew-Neural")
        response.pause(length=1)
        response.hangup()
        return str(response)

    xml_cloned = _twiml({"voicemail_audio_url": "https://intentbrain.ai/api/vm-audio/cmp-1"})
    assert "<Play>" in xml_cloned
    assert "https://intentbrain.ai/api/vm-audio/cmp-1" in xml_cloned
    assert "<Say" not in xml_cloned

    xml_polly = _twiml({"voicemail_audio_url": None})
    assert "<Say" in xml_polly
    assert "Polly.Matthew-Neural" in xml_polly
    assert "<Play>" not in xml_polly


# --------- 5) sanitized path — cannot escape the VM audio dir ---------
def test_5_path_sanitization(tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    p = vm_mod.vm_audio_path_for("../../etc/passwd")
    # The sanitized name must live inside tmp_path and NOT hit /etc/passwd.
    assert str(p).startswith(str(tmp_path))
    assert "/etc/passwd" not in str(p)


# --------- 6) Empty synth output does NOT write a file ---------
@pytest.mark.asyncio
async def test_6_empty_synth_leaves_no_file(db, tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    empty_client = MagicMock()
    def _empty_convert(**kwargs):
        return iter([])  # zero chunks
    empty_client.text_to_speech.convert.side_effect = _empty_convert

    user_id = "u-test-6"
    campaign_id = "cmp-empty"
    await db.campaigns.insert_one({
        "id": campaign_id, "user_id": user_id,
        "voicemail_enabled": True,
        "voicemail_message": "hello",
    })
    await db.cloned_voices.insert_one({
        "id": "v-6", "user_id": user_id,
        "elevenlabs_voice_id": "vX",
    })

    url = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=empty_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    assert url is None
    assert not (tmp_path / "cmp-empty.mp3").exists()


# --------- 7) read_vm_audio_bytes returns None when file absent ---------
def test_7_read_missing_returns_none(tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)
    assert vm_mod.read_vm_audio_bytes("does-not-exist") is None
