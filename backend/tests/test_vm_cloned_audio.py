"""Cloned-voice voicemail — TwiML branching, opaque-token persistence, retention.

Verifies:
  1. Placeholder stripping in _bake_message.
  2. Cloned voice present → mints uuid4.hex token, writes MP3 keyed by token,
     stores voicemail_audio_key + voicemail_audio_url on the campaign.
  3. No cloned voice → clears BOTH voicemail_audio_key AND voicemail_audio_url,
     deletes any previous file.
  4. TwiML: cloned-voice campaign → <Play>, non-cloned campaign → <Say>.
  5. Path sanitization: hostile keys can't escape the audio dir.
  6. Empty synth → no file, no partial DB update.
  7. read_vm_audio_bytes returns None for absent tokens.
  8. Regeneration mints a NEW token and DELETES the previous file (per-campaign retention).
  9. sweep_orphaned_vm_audio deletes files not referenced by any campaign.
 10. sweep_orphaned_vm_audio deletes files older than 30 days regardless of DB.

Never touches RankTrust webhook, SMS, funnel, retry cadence, or the
ElevenLabs Human-Greeting Gate. ElevenLabs is mocked.
"""
from __future__ import annotations

import os
import re
import sys
import time
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


HEX32 = re.compile(r"^[a-f0-9]{32}$")  # uuid4.hex shape


@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    return client["intentbrain_test_vm_cloned"]


@pytest.fixture
def fake_eleven_client():
    """Fake ElevenLabs client whose synth returns known bytes."""
    client = MagicMock()

    def _convert(**kwargs):
        yield b"ID3\x04\x00\x00\x00fake-mp3-header"
        yield b"AAA_body_bytes_for_" + kwargs["voice_id"].encode()[:16]

    client.text_to_speech.convert.side_effect = _convert
    return client


# --------- 1) Placeholder stripping ---------
def test_1_placeholder_stripping():
    from services.vm_cloned_audio import _bake_message
    msg = "Hi {contact_name}, this is a message for {business_name} from {company_name}."
    out = _bake_message(msg, {"company_name": "IntentBrain"},
                        agent_name="", callback_number_spoken="")
    assert "{contact_name}" not in out
    assert "{business_name}" not in out
    assert "IntentBrain" in out
    assert "  " not in out
    assert " ," not in out


# --------- 1b) 4-variable interpolation for cloned-voice bake ---------
def test_1b_four_variable_interpolation():
    from services.vm_cloned_audio import _bake_message
    msg = (
        "Hi, this is {agent_name} with {company_name}. Reach me at {callback_number}. "
        "Again, that's {callback_number}. Thanks."
    )
    out = _bake_message(
        msg,
        {"company_name": "RankTrust"},
        agent_name="David",
        callback_number_spoken="4 0 4, 5 5 5, 7 7 7 7",
    )
    assert "{agent_name}" not in out and "{company_name}" not in out
    assert "{callback_number}" not in out
    assert "David" in out
    assert "RankTrust" in out
    # Callback appears TWICE in the template — both instances must interpolate
    assert out.count("4 0 4, 5 5 5, 7 7 7 7") == 2


# --------- 1c) Bracket-style placeholder scrubbing (belt-and-suspenders) ---------
def test_1c_bracket_placeholder_scrubbed():
    from services.vm_cloned_audio import _bake_message
    msg = "Hi, this is [Your Name] with {company_name}. Call [Your Number]."
    out = _bake_message(msg, {"company_name": "RankTrust"},
                        agent_name="David", callback_number_spoken="404")
    # No square-bracket literals may survive into the baked text
    assert "[Your Name]" not in out
    assert "[Your Number]" not in out


# --------- 2) refresh: cloned voice present → token minted, MP3 written, URL stored ---------
@pytest.mark.asyncio
async def test_2_refresh_writes_mp3_and_sets_url_with_opaque_token(
    db, fake_eleven_client, tmp_path, monkeypatch
):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    user_id = "u-test-1"
    campaign_id = "cmp-cloned-1"
    await db.campaigns.insert_one({
        "id": campaign_id, "user_id": user_id,
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
    assert url is not None
    # URL uses an opaque hex token, NOT the campaign_id
    assert campaign_id not in url
    token = url.rsplit("/", 1)[-1]
    assert HEX32.match(token), f"expected 32-char hex token, got {token!r}"

    # MP3 written to disk at token.mp3 (not campaign_id.mp3)
    on_disk = tmp_path / f"{token}.mp3"
    assert on_disk.is_file()
    assert on_disk.read_bytes().startswith(b"ID3")
    assert not (tmp_path / f"{campaign_id}.mp3").exists(), "must not write by campaign_id"

    # Campaign row updated with BOTH fields
    row = await db.campaigns.find_one({"id": campaign_id})
    assert row["voicemail_audio_url"] == url
    assert row["voicemail_audio_key"] == token


# --------- 3) refresh: no cloned voice → clears BOTH fields + deletes prior file ---------
@pytest.mark.asyncio
async def test_3_no_cloned_voice_clears_url_and_key(
    db, fake_eleven_client, tmp_path, monkeypatch
):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    user_id = "u-test-2"
    campaign_id = "cmp-polly-only"
    # Simulate a previous cloned-voice audio: file on disk + key on row
    stale_token = "a" * 32
    stale_path = tmp_path / f"{stale_token}.mp3"
    stale_path.write_bytes(b"stale-bytes")
    await db.campaigns.insert_one({
        "id": campaign_id, "user_id": user_id,
        "voicemail_enabled": True,
        "voicemail_message": "Hi, this is a test.",
        "voicemail_audio_url": f"https://intentbrain.ai/api/vm-audio/{stale_token}",
        "voicemail_audio_key": stale_token,
    })
    # NOTE: no cloned_voices row for this user

    url = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=fake_eleven_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    assert url is None
    row = await db.campaigns.find_one({"id": campaign_id})
    assert row["voicemail_audio_url"] is None
    assert row["voicemail_audio_key"] is None
    # Stale file cleaned up
    assert not stale_path.exists(), "stale audio file should have been deleted"


# --------- 4) TwiML branching: cloned → <Play>, non-cloned → <Say> ---------
def test_4_twiml_uses_play_when_audio_url_present():
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

    xml_cloned = _twiml({"voicemail_audio_url": "https://intentbrain.ai/api/vm-audio/deadbeef" * 4})
    assert "<Play>" in xml_cloned
    assert "<Say" not in xml_cloned

    xml_polly = _twiml({"voicemail_audio_url": None})
    assert "<Say" in xml_polly
    assert "Polly.Matthew-Neural" in xml_polly
    assert "<Play>" not in xml_polly


# --------- 5) Path sanitization: hostile tokens can't escape the dir ---------
def test_5_path_sanitization(tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    # Traversal attempts fall into an inert sentinel path
    for hostile in ("../../etc/passwd", "..", "", "/etc/hosts", "a" * 5000):
        p = vm_mod.vm_audio_path_for(hostile)
        assert str(p).startswith(str(tmp_path))
        assert "/etc/passwd" not in str(p)
        assert "/etc/hosts" not in str(p)


# --------- 6) Empty synth output → no file, no partial DB update ---------
@pytest.mark.asyncio
async def test_6_empty_synth_leaves_no_file_and_no_row_update(db, tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    empty_client = MagicMock()
    empty_client.text_to_speech.convert.side_effect = lambda **kw: iter([])

    user_id = "u-test-6"
    campaign_id = "cmp-empty"
    await db.campaigns.insert_one({
        "id": campaign_id, "user_id": user_id,
        "voicemail_enabled": True,
        "voicemail_message": "hello",
    })
    await db.cloned_voices.insert_one({
        "id": "v-6", "user_id": user_id, "elevenlabs_voice_id": "vX",
    })

    url = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=empty_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    assert url is None
    # No file, no ghost token on the row
    assert not any(tmp_path.iterdir())
    row = await db.campaigns.find_one({"id": campaign_id})
    assert row.get("voicemail_audio_url") in (None, "")
    assert row.get("voicemail_audio_key") in (None, "")


# --------- 7) read_vm_audio_bytes returns None for absent tokens ---------
def test_7_read_missing_returns_none(tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)
    # Well-formed hex, but no file on disk
    assert vm_mod.read_vm_audio_bytes("f" * 32) is None
    # Malformed token also returns None (rejected by _TOKEN_RE)
    assert vm_mod.read_vm_audio_bytes("..") is None
    assert vm_mod.read_vm_audio_bytes("") is None


# --------- 8) Regeneration mints a NEW token and DELETES the old file ---------
@pytest.mark.asyncio
async def test_8_regeneration_deletes_old_file(db, fake_eleven_client, tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    user_id = "u-test-8"
    campaign_id = "cmp-regen"
    await db.campaigns.insert_one({
        "id": campaign_id, "user_id": user_id,
        "voicemail_enabled": True,
        "voicemail_message": "first version",
    })
    await db.cloned_voices.insert_one({
        "id": "v-8", "user_id": user_id, "elevenlabs_voice_id": "voice_regen",
    })

    url_1 = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=fake_eleven_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    token_1 = url_1.rsplit("/", 1)[-1]
    assert (tmp_path / f"{token_1}.mp3").is_file()

    # Simulate a message update → refresh again
    await db.campaigns.update_one(
        {"id": campaign_id}, {"$set": {"voicemail_message": "second version"}}
    )
    url_2 = await vm_mod.refresh_campaign_vm_audio(
        db=db, eleven_client=fake_eleven_client,
        backend_public_url="https://intentbrain.ai",
        campaign_id=campaign_id, user_id=user_id,
    )
    token_2 = url_2.rsplit("/", 1)[-1]

    # New token differs
    assert token_1 != token_2
    # New file exists
    assert (tmp_path / f"{token_2}.mp3").is_file()
    # Old file was deleted (per-campaign retention)
    assert not (tmp_path / f"{token_1}.mp3").exists(), \
        "regeneration must delete the previous token's file"

    # Row reflects the new token
    row = await db.campaigns.find_one({"id": campaign_id})
    assert row["voicemail_audio_key"] == token_2


# --------- 9) sweep deletes orphan files (no campaign references them) ---------
@pytest.mark.asyncio
async def test_9_sweep_deletes_orphans(db, tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    # 3 files on disk. 1 referenced, 2 orphans.
    live_token = "a" * 32
    orphan_1  = "b" * 32
    orphan_2  = "c" * 32
    (tmp_path / f"{live_token}.mp3").write_bytes(b"live")
    (tmp_path / f"{orphan_1}.mp3").write_bytes(b"orphan_1")
    (tmp_path / f"{orphan_2}.mp3").write_bytes(b"orphan_2")

    await db.campaigns.insert_one({
        "id": "cmp-live", "user_id": "u-9",
        "voicemail_audio_key": live_token,
    })

    stats = await vm_mod.sweep_orphaned_vm_audio(db)
    assert stats["scanned"] == 3
    assert stats["deleted_orphans"] == 2
    assert stats["deleted_expired"] == 0
    assert (tmp_path / f"{live_token}.mp3").is_file()
    assert not (tmp_path / f"{orphan_1}.mp3").exists()
    assert not (tmp_path / f"{orphan_2}.mp3").exists()


# --------- 10) sweep deletes files older than 30 days regardless of DB ---------
@pytest.mark.asyncio
async def test_10_sweep_deletes_expired_even_if_referenced(db, tmp_path, monkeypatch):
    from services import vm_cloned_audio as vm_mod
    monkeypatch.setattr(vm_mod, "_VM_AUDIO_DIR", tmp_path)

    token = "d" * 32
    p = tmp_path / f"{token}.mp3"
    p.write_bytes(b"ancient")
    # Backdate mtime by 40 days
    ancient_ts = time.time() - (40 * 24 * 3600)
    os.utime(p, (ancient_ts, ancient_ts))

    await db.campaigns.insert_one({
        "id": "cmp-ancient", "user_id": "u-10",
        "voicemail_audio_key": token,
    })

    stats = await vm_mod.sweep_orphaned_vm_audio(db)
    assert stats["deleted_expired"] == 1
    assert not p.exists()
