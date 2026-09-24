"""Authenticated, campaign-scoped upload and explicit voice-agent generation for voicemail."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from services.auth_service import get_current_user, get_db
from services.vm_cloned_audio import (
    _delete_by_token, _mint_token, vm_audio_path_for, refresh_campaign_vm_audio,
)
import os

router = APIRouter(prefix="/campaigns", tags=["Campaign voicemail"])
MAX_MP3_BYTES = 12 * 1024 * 1024


def valid_mp3(data: bytes) -> bool:
    """Require an ID3 header or an MPEG Layer III sync frame near file start."""
    if len(data) < 1024:
        return False
    if data[:3] == b"ID3":
        return len(data) >= 10 and data[3] in (2, 3, 4)
    # An MP3 without ID3 can have a short metadata/junk preamble.
    for i in range(min(4096, len(data) - 3)):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            version = (data[i + 1] >> 3) & 3
            layer = (data[i + 1] >> 1) & 3
            bitrate_index = (data[i + 2] >> 4) & 15
            sample_rate_index = (data[i + 2] >> 2) & 3
            if version != 1 and layer == 1 and bitrate_index not in (0, 15) and sample_rate_index != 3:
                return True
    return False


@router.post("/{campaign_id}/voicemail-audio")
async def upload_voicemail_audio(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    selector = {"id": campaign_id, "user_id": current_user["user_id"]}
    campaign = await db.campaigns.find_one(selector, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.get("status") == "active":
        raise HTTPException(status_code=409, detail="Pause the campaign before replacing voicemail audio.")
    if not file.filename or not file.filename.lower().endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Choose an MP3 file.")
    if file.content_type not in ("audio/mpeg", "audio/mp3", "application/octet-stream", None):
        raise HTTPException(status_code=400, detail="Only MP3 audio is supported.")

    data = await file.read(MAX_MP3_BYTES + 1)
    if len(data) > MAX_MP3_BYTES:
        raise HTTPException(status_code=413, detail="MP3 must be 12 MB or smaller.")
    if not valid_mp3(data):
        raise HTTPException(status_code=400, detail="This file does not contain valid MP3 audio.")

    public_url = (os.environ.get("BACKEND_PUBLIC_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    if not public_url or not public_url.startswith("https://"):
        raise HTTPException(status_code=503, detail="Secure public audio URL is not configured.")

    token = _mint_token()
    path = vm_audio_path_for(token)
    tmp_path = path.with_suffix(".uploading")
    try:
        tmp_path.write_bytes(data)
        tmp_path.replace(path)
        served_url = f"{public_url}/api/vm-audio/{token}"
        result = await db.campaigns.update_one(
            {**selector, "status": {"$ne": "active"}},
            {"$set": {
                "voicemail_audio_url": served_url,
                "voicemail_audio_key": token,
                "voicemail_audio_locked": True,
                "voicemail_audio_source": "uploaded",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        if result.matched_count != 1:
            raise HTTPException(status_code=409, detail="Campaign changed while uploading; pause and retry.")
    except Exception:
        tmp_path.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
        raise

    old_token = campaign.get("voicemail_audio_key")
    if old_token != token:
        _delete_by_token(old_token)
    return {"ready": True, "voicemail_audio_url": served_url, "voicemail_audio_source": "uploaded"}


@router.post("/{campaign_id}/generate-voicemail")
async def generate_voicemail_using_agent(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Explicitly replace a prerecorded MP3 with the selected voice agent."""
    db = get_db()
    selector = {"id": campaign_id, "user_id": current_user["user_id"]}
    campaign = await db.campaigns.find_one(selector, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.get("status") == "active":
        raise HTTPException(status_code=409, detail="Pause the campaign before regenerating audio.")
    if not campaign.get("agent_id") or not campaign.get("voicemail_message"):
        raise HTTPException(status_code=400, detail="Select a Voice Agent and provide a voicemail script first.")
    from services.vm_cloned_audio import resolve_cloned_voice_id
    if not await resolve_cloned_voice_id(db, current_user["user_id"], campaign):
        raise HTTPException(status_code=400, detail="Selected Voice Agent has no usable ElevenLabs voice.")
    from server import eleven_client
    public_url = (os.environ.get("BACKEND_PUBLIC_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    if not public_url or not public_url.startswith("https://"):
        raise HTTPException(status_code=503, detail="Secure public audio URL is not configured.")
    url = await refresh_campaign_vm_audio(
        db=db, eleven_client=eleven_client, backend_public_url=public_url,
        campaign_id=campaign_id, user_id=current_user["user_id"], force=True,
    )
    if not url:
        raise HTTPException(status_code=502, detail="Voice Agent audio generation failed; existing audio was preserved.")
    return {"ready": True, "voicemail_audio_url": url, "voicemail_audio_source": "voice_agent"}
