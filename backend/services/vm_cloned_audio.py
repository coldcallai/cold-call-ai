"""Cloned-voice voicemail audio synthesis + persistence.

Design (production-safe, isolated):
  * When a campaign's voicemail_message / voicemail_enabled / agent_id changes,
    we mint a fresh opaque token (uuid4.hex), synthesize the message via
    ElevenLabs, and persist the MP3 at:
        <backend>/vm_audio_cache/{token}.mp3
    The campaign row stores BOTH `voicemail_audio_key` (the token) and
    `voicemail_audio_url` (the derived public URL). The campaign_id is never
    exposed in the audio URL — Twilio only ever sees the opaque token.
  * On every regeneration, the OLD token's file is deleted before writing the
    new one (per-campaign retention).
  * On process startup, `sweep_orphaned_vm_audio()` deletes any files that are
    (a) not referenced by any campaign, or (b) older than 30 days.
  * At AMD-callback time, `generate_voicemail_twiml()` returns <Play> using the
    stored URL. If the file is missing / cloned voice absent, the caller falls
    back to Polly.Matthew-Neural <Say> — no regression.

Hard rules:
  * This module NEVER touches the RankTrust webhook, the outbound gate, SMS,
    the funnel, or the retry cadence.
  * Failures are logged and non-fatal — the campaign save always succeeds;
    the Polly fallback then kicks in at dial time.
  * Placeholders like {business_name} in the message are stripped for the
    stored MP3 (single audio per campaign — no per-lead personalization).
"""
from __future__ import annotations

import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

# Storage layout matches the existing `inbound_audio_cache` convention.
_VM_AUDIO_DIR = Path(__file__).resolve().parent.parent / "vm_audio_cache"
_VM_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Retention policy — belt-and-suspenders in case DB drifts.
_MAX_AGE_SECONDS = 30 * 24 * 3600  # 30 days

# Only hex-ish keys are legal (uuid4.hex is 32 lowercase hex chars).
# We validate BOTH on write and read so a hostile campaign_id / URL cannot
# escape the audio dir via traversal.
_TOKEN_RE = re.compile(r"^[a-zA-Z0-9]{16,64}$")

# Only per-lead placeholders are stripped from cloned-voice MP3s (one audio
# per campaign — per-lead variables can't be interpolated at synthesis time).
_PER_LEAD_PLACEHOLDER_RE = re.compile(r"\{(business_name|contact_name)\}")

# Any residual [bracket] or {brace} placeholder we didn't handle explicitly.
# Anything matching this must be scrubbed before synthesis so a broken template
# never gets spoken to a prospect.
_LEFTOVER_PLACEHOLDER_RE = re.compile(r"[\{\[][a-zA-Z_][a-zA-Z0-9_ ]*[\}\]]")


def _bake_message(
    message: str,
    campaign: Dict[str, Any],
    agent_name: str,
    callback_number_spoken: str,
) -> str:
    """Prepare the exact string sent to ElevenLabs.

    Campaign-scoped placeholders are interpolated:
      * {agent_name}       ← linked agent name (or profile fallback)
      * {company_name}     ← campaign.company_name
      * {callback_number}  ← spoken form of resolved callback number

    Per-lead placeholders ({business_name}, {contact_name}) are STRIPPED —
    the MP3 is generated once per campaign, not per lead.
    """
    company_name = campaign.get("company_name") or "our team"
    text = message
    text = text.replace("{company_name}", company_name)
    text = text.replace("{agent_name}", agent_name)
    text = text.replace("{callback_number}", callback_number_spoken or "")
    text = text.replace("for {business_name},", "")
    text = _PER_LEAD_PLACEHOLDER_RE.sub("", text)
    # Belt & suspenders: strip any leftover [bracket]/{brace} placeholders
    # so a broken template never gets baked into the MP3.
    text = _LEFTOVER_PLACEHOLDER_RE.sub("", text)

    # One conversational pause after the introduction.
    text = text.replace(
        "David with RankTrust. We ran",
        "David with RankTrust... We ran"
    )

    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+,", ",", text)
    return text.strip()


def _mint_token() -> str:
    """Return a fresh opaque 32-char lowercase-hex token."""
    return uuid.uuid4().hex


def vm_audio_path_for(token: str) -> Path:
    """Return the on-disk path for a given opaque token.

    Rejects anything that doesn't match _TOKEN_RE — returns a path under the
    audio dir with a `_invalid_` prefix so any read/write fails safely.
    """
    if not isinstance(token, str) or not _TOKEN_RE.match(token):
        return _VM_AUDIO_DIR / "_invalid_token.mp3"
    return _VM_AUDIO_DIR / f"{token}.mp3"


def _bake_message_legacy(message: str, campaign: Dict[str, Any]) -> str:
    """Deprecated shim — retained ONLY so test_1 (which imports _bake_message
    directly with a 2-arg signature) still passes without a rewrite.
    New callers use the 4-arg _bake_message above.
    """
    return _bake_message(message, campaign, agent_name="", callback_number_spoken="")


async def resolve_cloned_voice_id(
    db: Any,
    user_id: str,
    campaign: Dict[str, Any],
) -> Optional[str]:
    """Return the ElevenLabs voice_id to use, or None.

    Preference order:
      1. Agent linked to the campaign has voice_type=='cloned' + cloned_voice_id
      2. First cloned voice owned by the user
    """
    agent_id = campaign.get("agent_id")
    if agent_id:
        agent = await db.agents.find_one({"id": agent_id, "user_id": user_id})
        if agent and agent.get("voice_type") == "cloned" and agent.get("cloned_voice_id"):
            return agent["cloned_voice_id"]

        logger.warning(
            f"[vm_cloned] linked agent {agent_id} has no usable cloned voice"
        )
        return None

    # FAIL CLOSED: voicemail campaigns must use the exact cloned voice
    # attached to their selected agent. Never guess or use an arbitrary
    # first cloned voice from the account.
    logger.error(
        "[vm_cloned] campaign has no linked agent_id; refusing arbitrary voice fallback"
    )
    return None


async def resolve_agent_name_for_bake(
    db: Any, user_id: str, campaign: Dict[str, Any]
) -> str:
    """Same source-of-truth as server.resolve_agent_name, kept here so this
    module has no dependency on server.py."""
    agent_id = campaign.get("agent_id")
    if agent_id:
        agent = await db.agents.find_one({"id": agent_id, "user_id": user_id})
        if agent and agent.get("name"):
            return str(agent["name"]).strip()
    user = await db.users.find_one({"user_id": user_id}) if user_id else None
    if user:
        for key in ("name", "full_name", "display_name"):
            if user.get(key):
                return str(user[key]).strip()
    return "your account rep"


async def resolve_callback_for_bake(
    db: Any, user_id: str, campaign: Dict[str, Any]
) -> Optional[str]:
    """Same fallback chain as server.resolve_callback_number, without importing
    server.py. Returns the raw phone; caller normalizes for speech.

    Order: campaign.callback_number → user.phone_number → env TWILIO_PHONE_NUMBER.
    """
    n = campaign.get("callback_number")
    if n and str(n).strip():
        return str(n).strip()
    user = await db.users.find_one({"user_id": user_id}) if user_id else None
    if user and user.get("phone_number"):
        return str(user["phone_number"]).strip()
    env_num = os.environ.get("TWILIO_PHONE_NUMBER")
    return env_num if env_num else None


def _normalize_phone_for_speech(phone: Optional[str]) -> str:
    """Same rendering as server.normalize_phone_for_speech, duplicated to
    keep this module self-contained."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        a, b, c = digits[:3], digits[3:6], digits[6:]
        return f"{' '.join(a)}, {' '.join(b)}, {' '.join(c)}"
    return ", ".join(" ".join(digits[i:i + 3]) for i in range(0, len(digits), 3))


def synthesize_to_disk(
    *,
    eleven_client: Any,
    text: str,
    voice_id: str,
    out_path: Path,
    model_id: str = "eleven_v3",
    stability: float = 0.50,
    similarity_boost: float = 0.75,
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
            model_id=model_id,
            voice_settings=VoiceSettings(
                stability=stability,
            ),
        )
        buf = b""
        for chunk in gen:
            buf += chunk
        if not buf:
            logger.error("[vm_cloned] ElevenLabs returned empty audio")
            return False
        out_path.write_bytes(buf)

        logger.info(f"[vm_cloned] wrote {out_path.stat().st_size} bytes → {out_path.name}")
        return True
    except Exception as e:  # pragma: no cover — network path
        logger.error(f"[vm_cloned] ElevenLabs synth failed: {e!r}")
        return False


def _delete_by_token(token: Optional[str]) -> None:
    """Best-effort delete for a persisted audio token."""
    if not token:
        return
    p = vm_audio_path_for(token)
    try:
        if p.is_file():
            os.unlink(p)
            logger.info(f"[vm_cloned] deleted stale audio {p.name}")
    except OSError as e:
        logger.warning(f"[vm_cloned] failed to delete {p}: {e!r}")



async def ensure_lead_vm_audio(
    *,
    db: Any,
    eleven_client: Any,
    backend_public_url: str,
    campaign: Dict[str, Any],
    lead: Dict[str, Any],
    user_id: str,
) -> Optional[str]:
    import hashlib

    campaign_id = str(campaign.get("id") or "")
    lead_id = str(lead.get("id") or "")
    message = campaign.get("voicemail_message") or ""

    if not campaign_id or not lead_id:
        return None
    if not campaign.get("voicemail_enabled", True):
        return None
    if "{business_name}" not in message:
        return None

    business_name = str(lead.get("business_name") or "").strip()
    if not business_name:
        return None

    voice_id = await resolve_cloned_voice_id(db, user_id, campaign)
    if not voice_id:
        return None

    agent_name = await resolve_agent_name_for_bake(db, user_id, campaign)
    raw_callback = await resolve_callback_for_bake(db, user_id, campaign)
    callback_spoken = _normalize_phone_for_speech(raw_callback) if raw_callback else ""

    personalized_message = message.replace("{business_name}", business_name)

    baked = _bake_message(
        personalized_message,
        campaign,
        agent_name=agent_name,
        callback_number_spoken=callback_spoken,
    )

    synthesis_text = (
        "[calm, confident, grounded, masculine, conversational, restrained]\n\n"
        + baked.replace(
            "If you'd like to see what we found,",
            "[direct, helpful, matter-of-fact]\n\nIf you'd like to see what we found,",
            1,
        )
    )

    fingerprint = hashlib.sha256(
        "|".join([
            campaign_id,
            lead_id,
            voice_id,
            business_name,
            baked,
            "v3_restrained_055_080",
        ]).encode("utf-8")
    ).hexdigest()

    existing = await db.lead_vm_audio.find_one(
        {
            "campaign_id": campaign_id,
            "lead_id": lead_id,
            "user_id": user_id,
        },
        {"_id": 0},
    )

    if (
        existing
        and existing.get("fingerprint") == fingerprint
        and existing.get("voicemail_audio_url")
    ):
        return existing["voicemail_audio_url"]

    old_key = existing.get("voicemail_audio_key") if existing else None
    new_token = _mint_token()
    out_path = vm_audio_path_for(new_token)

    ok = synthesize_to_disk(
        eleven_client=eleven_client,
        text=synthesis_text,
        voice_id=voice_id,
        out_path=out_path,
        model_id="eleven_v3",
        stability=0.55,
        similarity_boost=0.80,
    )
    if not ok:
        return None

    served_url = f"{backend_public_url.rstrip('/')}/api/vm-audio/{new_token}"

    await db.lead_vm_audio.update_one(
        {
            "campaign_id": campaign_id,
            "lead_id": lead_id,
            "user_id": user_id,
        },
        {
            "$set": {
                "campaign_id": campaign_id,
                "lead_id": lead_id,
                "user_id": user_id,
                "business_name": business_name,
                "fingerprint": fingerprint,
                "voicemail_audio_url": served_url,
                "voicemail_audio_key": new_token,
            }
        },
        upsert=True,
    )

    if old_key and old_key != new_token:
        _delete_by_token(old_key)

    return served_url

async def refresh_campaign_vm_audio(
    *,
    db: Any,
    eleven_client: Any,
    backend_public_url: str,
    campaign_id: str,
    user_id: str,
) -> Optional[str]:
    """Re-synthesize a campaign's VM audio and persist under a FRESH token.

    Returns the new served URL, or None if no cloned-voice audio should exist
    (caller keeps the Polly fallback). Idempotent — safe to call after every
    create/update. Always mints a new token so old URLs stop working.
    """
    campaign = await db.campaigns.find_one({"id": campaign_id, "user_id": user_id})
    if not campaign:
        logger.warning(f"[vm_cloned] campaign {campaign_id} not found for user {user_id}")
        return None

    if campaign.get("voicemail_audio_locked"):
        locked_url = campaign.get("voicemail_audio_url")
        locked_key = campaign.get("voicemail_audio_key")
        if locked_url and locked_key:
            logger.info(
                f"[vm_cloned] campaign {campaign_id} audio is LOCKED; preserving existing asset"
            )
            return locked_url

    old_key = campaign.get("voicemail_audio_key")

    def _clear_ref_and_delete_old() -> None:
        # Fire-and-return helper used by every "no cloned audio wanted" branch.
        _delete_by_token(old_key)

    if not campaign.get("voicemail_enabled", True):
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None, "voicemail_audio_key": None}},
        )
        _clear_ref_and_delete_old()
        return None

    message = campaign.get("voicemail_message")
    if not message:
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None, "voicemail_audio_key": None}},
        )
        _clear_ref_and_delete_old()
        return None

    voice_id = await resolve_cloned_voice_id(db, user_id, campaign)
    if not voice_id:
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None, "voicemail_audio_key": None}},
        )
        _clear_ref_and_delete_old()
        return None

    # Resolve campaign-scoped variables BEFORE synthesis. If callback number
    # can't be resolved, refuse to generate audio — a placeholder like
    # "{callback_number}" must never be baked into a real voicemail MP3.
    agent_name = await resolve_agent_name_for_bake(db, user_id, campaign)
    raw_callback = await resolve_callback_for_bake(db, user_id, campaign)
    callback_spoken = _normalize_phone_for_speech(raw_callback) if raw_callback else ""

    if "{callback_number}" in message and not raw_callback:
        logger.warning(
            f"[vm_cloned] refusing to synth for {campaign_id}: message references "
            f"{{callback_number}} but no callback number is resolvable"
        )
        await db.campaigns.update_one(
            {"id": campaign_id, "user_id": user_id},
            {"$set": {"voicemail_audio_url": None, "voicemail_audio_key": None}},
        )
        _clear_ref_and_delete_old()
        return None

    baked = _bake_message(
        message, campaign,
        agent_name=agent_name,
        callback_number_spoken=callback_spoken,
    )

    # Natural RankTrust voicemail opening.
    baked = baked.replace(
        "Hi, this is David with RankTrust.",
        "Hi, this is David with Ranktrust."
    )

    baked = baked.replace(
        "Rank Trust",
        "Ranktrust"
    )
    new_token = _mint_token()
    out_path = vm_audio_path_for(new_token)

    logger.info(
        f"[vm_cloned] SYNTH_CHECK campaign={campaign_id} voice_id={voice_id}"
    )

    synthesis_text = baked

    ok = synthesize_to_disk(
        eleven_client=eleven_client,
        text=synthesis_text,
        voice_id=voice_id,
        out_path=out_path,
        model_id="eleven_v3",
        stability=0.50,
        similarity_boost=0.86,
    )
    if not ok:
        # Leave the campaign's old key untouched — the old audio (if any) still
        # plays. Do NOT partially update the row.
        return None

    served_url = f"{backend_public_url.rstrip('/')}/api/vm-audio/{new_token}"
    await db.campaigns.update_one(
        {"id": campaign_id, "user_id": user_id},
        {"$set": {"voicemail_audio_url": served_url,
                  "voicemail_audio_key": new_token}},
    )
    # Per-campaign retention: delete previous file AFTER the row points at the new one.
    _delete_by_token(old_key)

    logger.info(f"[vm_cloned] campaign {campaign_id} vm audio ready ({len(new_token)}-char token)")
    return served_url


def read_vm_audio_bytes(token: str) -> Optional[bytes]:
    """Load a persisted VM MP3 by its opaque token. None if not present."""
    p = vm_audio_path_for(token)
    if not p.is_file():
        return None
    try:
        return p.read_bytes()
    except OSError as e:
        logger.error(f"[vm_cloned] failed to read {p}: {e!r}")
        return None


async def sweep_orphaned_vm_audio(db: Any) -> Dict[str, int]:
    """One-shot retention sweep. Safe to run on startup.

    Deletes any MP3 in vm_audio_cache/ that is:
      (a) not referenced by any campaign's voicemail_audio_key, OR
      (b) older than _MAX_AGE_SECONDS regardless of DB reference.
    Returns {'scanned': N, 'deleted_orphans': X, 'deleted_expired': Y}.
    """
    stats = {"scanned": 0, "deleted_orphans": 0, "deleted_expired": 0}

    # Collect all currently-referenced tokens.
    # Preserve both campaign-level and lead-specific voicemail audio.
    live_tokens: Set[str] = set()

    cursor = db.campaigns.find(
        {"voicemail_audio_key": {"$ne": None}},
        {"voicemail_audio_key": 1, "_id": 0},
    )
    async for row in cursor:
        key = row.get("voicemail_audio_key")
        if isinstance(key, str) and _TOKEN_RE.match(key):
            live_tokens.add(key)

    lead_cursor = db.lead_vm_audio.find(
        {"voicemail_audio_key": {"$ne": None}},
        {"voicemail_audio_key": 1, "_id": 0},
    )
    async for row in lead_cursor:
        key = row.get("voicemail_audio_key")
        if isinstance(key, str) and _TOKEN_RE.match(key):
            live_tokens.add(key)

    now = time.time()
    if not _VM_AUDIO_DIR.is_dir():
        return stats

    for entry in _VM_AUDIO_DIR.iterdir():
        if not entry.is_file() or entry.suffix != ".mp3":
            continue
        stats["scanned"] += 1
        token = entry.stem
        try:
            age = now - entry.stat().st_mtime
        except OSError:
            continue

        if age > _MAX_AGE_SECONDS:
            try:
                entry.unlink()
                stats["deleted_expired"] += 1
                logger.info(f"[vm_cloned] retention expired: deleted {entry.name} (age={int(age)}s)")
            except OSError as e:
                logger.warning(f"[vm_cloned] retention delete failed for {entry}: {e!r}")
            continue

        if token not in live_tokens:
            try:
                entry.unlink()
                stats["deleted_orphans"] += 1
                logger.info(f"[vm_cloned] orphan: deleted {entry.name}")
            except OSError as e:
                logger.warning(f"[vm_cloned] orphan delete failed for {entry}: {e!r}")

    logger.info(f"[vm_cloned] sweep complete: {stats}")
    return stats
