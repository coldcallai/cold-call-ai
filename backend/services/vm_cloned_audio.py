"""Cloned-voice voicemail audio synthesis + persistence.

Design (production-safe, isolated):
  * When a campaign's voicemail_message is created/updated AND the campaign owner
    has a cloned voice, we synthesize the message via ElevenLabs and persist the
    MP3 to disk under `<backend>/vm_audio_cache/{campaign_id}.mp3`.
  * We store a `voicemail_audio_url` reference on the campaign row that Twilio
    can fetch during the AMD callback.
  * At AMD-callback time, `generate_voicemail_twiml()` returns <Play> using this
    URL. If no cloned URL is present OR the file has been lost, the caller falls
    back to `Polly.Matthew-Neural` <Say> (existing behavior — never regresses).

Hard rules:
  * This module NEVER touches the RankTrust webhook, the outbound gate, SMS,
    the funnel, or the retry cadence.
  * Failures are logged and non-fatal — the campaign save still succeeds; the
    Polly fallback then kicks in at dial time.
  * Placeholders like {business_name} in the message are stripped for the
    stored MP3 (single audio per campaign — no per-lead personalization).
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Storage layout matches the existing `inbound_audio_cache` convention.
_VM_AUDIO_DIR = Path(__file__).resolve().parent.parent / "vm_audio_cache"
_VM_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Same placeholder set the existing generate_voicemail_twiml understands.
_PLACEHOLDER_RE = re.compile(r"\{(business_name|contact_name|company_name)\}")


def vm_audio_path_for(campaign_id: str) -> Path:
    """Return the on-disk path where campaign_id's VM MP3 lives."""
    # Sanitize — never allow path traversal via a hostile campaign_id.
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(campaign_id))[:120]
    return _VM_AUDIO_DIR / f"{safe}.mp3"


def _bake_message(message: str, campaign: Dict[str, Any]) -> str:
    """Prepare the exact string sent to ElevenLabs.

    Because the audio is one-per-campaign (not per-lead), per-lead placeholders
    are stripped. `{company_name}` is filled in from the campaign since that
    IS campaign-scoped.
    """
    company_name = campaign.get("company_name") or "our team"
    text = message.replace("{company_name}", company_name)
    # Strip {business_name} / {contact_name} — they don't make sense in a
    # single-audio-per-campaign world.
    text = _PLACEHOLDER_RE.sub("", text)
    # Clean up double spaces / stray commas produced by the removal.
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+,", ",", text)
    return text.strip()


def _resolve_cloned_voice_id(
    db: Any,  # noqa: ANN401 — Motor db handle
    user_id: str,
    campaign: Dict[str, Any],
) -> Optional[str]:
    """Return the ElevenLabs voice_id to use, or None if no clone is available.

    Order of preference:
      1. Agent linked to the campaign has voice_type=='cloned' + cloned_voice_id
      2. First cloned voice owned by the user
    """
    return None  # actual async lookup happens in async wrapper below


async def resolve_cloned_voice_id(
    db: Any,
    user_id: str,
    campaign: Dict[str, Any],
) -> Optional[str]:
    """Async version — Motor collections are async-only."""
    # 1. Agent-linked cloned voice
    agent_id = campaign.get("agent_id")
    if agent_id:
        agent = await db.agents.find_one({"id": agent_id, "user_id": user_id})
        if agent and agent.get("voice_type") == "cloned" and agent.get("cloned_voice_id"):
            return agent["cloned_voice_id"]

    # 2. Fallback: first cloned voice owned by the user
    voice_doc = await db.cloned_voices.find_one({"user_id": user_id})
    if voice_doc and voice_doc.get("elevenlabs_voice_id"):
        return voice_doc["elevenlabs_voice_id"]

    return None


def synthesize_to_disk(
    *,
    eleven_client: Any,  # noqa: ANN401
    text: str,
    voice_id: str,
    out_path: Path,
) -> bool:
    """Synchronous ElevenLabs synth → MP3 on disk. Returns True on success."""
    if not eleven_client:
        logger.warning("[vm_cloned] ElevenLabs client not configured — skipping synth")
        return False
    if not text.strip():
        logger.warning("[vm_cloned] empty text — skipping synth")
        return False
    try:
        from elevenlabs.types import VoiceSettings  # type: ignore
        gen = eleven_client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
        )
        buf = b""
        for chunk in gen:
            buf += chunk
        if not buf:
            logger.error("[vm_cloned] ElevenLabs returned empty audio")
            return False
        out_path.write_bytes(buf)
        logger.info(f"[vm_cloned] wrote {len(buf)} bytes → {out_path}")
        return True
    except Exception as e:  # pragma: no cover — network path
        logger.error(f"[vm_cloned] ElevenLabs synth failed: {e!r}")
        return False


async def refresh_campaign_vm_audio(
    *,
    db: Any,
    eleven_client: Any,
    backend_public_url: str,
    campaign_id: str,
    user_id: str,
) -> Optional[str]:
    """Re-synthesize a campaign's VM audio and persist. Returns the served URL,
    or None if we couldn't produce audio (caller keeps the Polly fallback).

    Safe to call after every create/update of a campaign — cheap, isolated,
    non-fatal on any error.
    """
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": user_id})
    if not campaign:
        logger.warning(f"[vm_cloned] campaign {campaign_id} not found for user {user_id}")
        return None

    if not campaign.get("voicemail_enabled", True):
        # VM feature is off for this campaign — clear any stale reference.
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None}},
        )
        return None

    message = campaign.get("voicemail_message")
    if not message:
        # No custom message → default Polly path handles it. Clear ref.
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None}},
        )
        return None

    voice_id = await resolve_cloned_voice_id(db, user_id, campaign)
    if not voice_id:
        # User has no cloned voice → Polly fallback stays.
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None}},
        )
        return None

    baked = _bake_message(message, campaign)
    out_path = vm_audio_path_for(campaign_id)

    ok = synthesize_to_disk(
        eleven_client=eleven_client,
        text=baked,
        voice_id=voice_id,
        out_path=out_path,
    )
    if not ok:
        # Best-effort — don't crash the calling save endpoint.
        return None

    served_url = f"{backend_public_url.rstrip('/')}/api/vm-audio/{campaign_id}"
    await db.campaigns.update_one(
        {"id": campaign_id, "user_id": user_id},
        {"$set": {"voicemail_audio_url": served_url}},
    )
    logger.info(f"[vm_cloned] campaign {campaign_id} vm audio ready at {served_url}")
    return served_url


def read_vm_audio_bytes(campaign_id: str) -> Optional[bytes]:
    """Load a campaign's persisted VM MP3 from disk. None if not present."""
    p = vm_audio_path_for(campaign_id)
    if not p.is_file():
        return None
    try:
        return p.read_bytes()
    except OSError as e:
        logger.error(f"[vm_cloned] failed to read {p}: {e!r}")
        return None


def delete_vm_audio(campaign_id: str) -> None:
    """Best-effort delete for a campaign's persisted VM MP3."""
    p = vm_audio_path_for(campaign_id)
    try:
        if p.is_file():
            os.unlink(p)
    except OSError as e:
        logger.warning(f"[vm_cloned] failed to delete {p}: {e!r}")
