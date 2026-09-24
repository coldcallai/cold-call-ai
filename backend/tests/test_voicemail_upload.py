"""Unit tests for campaign-scoped prerecorded voicemail upload and source selection."""
from __future__ import annotations

import io
import os
import sys
from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers
from mongomock_motor import AsyncMongoMockClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routes import voicemail_upload as vu
from services.vm_cloned_audio import refresh_campaign_vm_audio, resolve_cloned_voice_id

# Small, header-valid MP3 fixture. Decoding is intentionally not part of unit tests.
FAKE_MP3 = b"ID3\\x04\\x00\\x00\\x00\\x00\\x00\\x00".decode("unicode_escape").encode("latin1") + b"X" * 1200


@pytest.fixture
def db():
    return AsyncMongoMockClient()["vm_uploaded_tests"]


@pytest.fixture
def setup_audio(monkeypatch, tmp_path, db):
    monkeypatch.setattr(vu, "get_db", lambda: db)
    monkeypatch.setattr(vu, "vm_audio_path_for", lambda token: tmp_path / f"{token}.mp3")
    monkeypatch.setattr(vu, "_delete_by_token", lambda key: None)
    monkeypatch.setenv("BACKEND_PUBLIC_URL", "https://example.test")
    return db, tmp_path


def upload(filename="approved.mp3", data=FAKE_MP3, content_type="audio/mpeg"):
    return UploadFile(
        file=io.BytesIO(data), filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def test_mp3_header_validation():
    assert vu.valid_mp3(FAKE_MP3)
    assert not vu.valid_mp3(b"not an MP3" * 200)
    assert not vu.valid_mp3(b"ID3\\x04\\x00".decode("unicode_escape").encode("latin1"))


@pytest.mark.asyncio
async def test_campaign_upload_retains_exact_bytes_and_ownership(setup_audio):
    db, audio_dir = setup_audio
    await db.campaigns.insert_one({
        "id": "owned", "user_id": "alice", "status": "paused",
        "voicemail_audio_key": None, "voicemail_audio_url": None,
    })
    result = await vu.upload_voicemail_audio(
        "owned", upload(), current_user={"user_id": "alice"},
    )
    assert result["voicemail_audio_source"] == "uploaded"
    saved = await db.campaigns.find_one({"id": "owned"})
    assert saved["voicemail_audio_locked"] is True
    assert (audio_dir / (saved["voicemail_audio_key"] + ".mp3")).read_bytes() == FAKE_MP3

    with pytest.raises(HTTPException) as exc:
        await vu.upload_voicemail_audio(
            "owned", upload(), current_user={"user_id": "bob"},
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_rejects_invalid_file_and_active_campaign(setup_audio):
    db, _ = setup_audio
    await db.campaigns.insert_one({"id": "active", "user_id": "alice", "status": "active"})
    with pytest.raises(HTTPException) as exc:
        await vu.upload_voicemail_audio("active", upload(), current_user={"user_id": "alice"})
    assert exc.value.status_code == 409

    await db.campaigns.insert_one({"id": "paused", "user_id": "alice", "status": "paused"})
    with pytest.raises(HTTPException) as exc:
        await vu.upload_voicemail_audio(
            "paused", upload(filename="not-mp3.txt"), current_user={"user_id": "alice"},
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_locked_uploaded_audio_not_regenerated(db):
    await db.campaigns.insert_one({
        "id": "one", "user_id": "alice", "voicemail_audio_locked": True,
        "voicemail_audio_key": "12345678123456781234567812345678",
        "voicemail_audio_url": "https://example.test/api/vm-audio/12345678123456781234567812345678",
        "voicemail_message": "approved",
    })
    fake_eleven = MagicMock()
    url = await refresh_campaign_vm_audio(
        db=db, eleven_client=fake_eleven,
        backend_public_url="https://example.test",
        campaign_id="one", user_id="alice",
    )
    assert url.endswith("12345678123456781234567812345678")
    fake_eleven.text_to_speech.convert.assert_not_called()


@pytest.mark.asyncio
async def test_voice_agent_can_resolve_preset_or_cloned(db):
    await db.agents.insert_many([
        {"id": "preset", "user_id": "alice", "voice_type": "preset", "preset_voice_id": "james"},
        {"id": "clone", "user_id": "alice", "voice_type": "cloned", "cloned_voice_id": "david"},
    ])
    assert await resolve_cloned_voice_id(db, "alice", {"agent_id": "preset"}) == "james"
    assert await resolve_cloned_voice_id(db, "alice", {"agent_id": "clone"}) == "david"
    assert await resolve_cloned_voice_id(db, "bob", {"agent_id": "preset"}) is None
