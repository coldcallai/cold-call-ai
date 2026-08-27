# RANKTRUST_CAMPAIGN_RUNNER_V1

from __future__ import annotations

import asyncio
import logging
import os
import socket
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from services.campaign_service import get_db

from services.campaign_runner_service import (
    claim_next_lead,
    peek_next_lead,
    release_claim,
    recover_stale_claims,
    create_call_record,
    mark_call_placed,
    mark_call_failed,
    mark_lead_attempted,
    ensure_runner_indexes,
)

from services.vm_cloned_audio import (
    ensure_lead_vm_audio,
    vm_audio_path_for,
)

from routes import twilio_outbound


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)

log = logging.getLogger("campaign_runner")

POLL_SECONDS = float(
    os.getenv(
        "CAMPAIGN_RUNNER_POLL_INTERVAL_SECONDS",
        "5",
    )
)

CLAIM_TTL_SECONDS = int(
    os.getenv(
        "CLAIM_TTL_SECONDS",
        "120",
    )
)

DRY_RUN = (
    os.getenv(
        "RUNNER_DRY_RUN",
        "true",
    ).lower()
    == "true"
)

WORKER_ID = (
    os.getenv("WORKER_ID")
    or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
)


def pace_seconds(
    calls_per_hour: int,
) -> float:

    if calls_per_hour <= 0:
        return float("inf")

    return 3600.0 / float(
        calls_per_hour
    )


def local_window(
    campaign: Dict[str, Any],
    now_utc: Optional[datetime] = None,
):

    timezone_name = str(
        campaign.get("timezone")
        or ""
    ).strip()

    if not timezone_name:
        return (
            False,
            "timezone_missing",
            None,
        )

    try:
        tz = ZoneInfo(
            timezone_name
        )

    except ZoneInfoNotFoundError:
        return (
            False,
            "timezone_invalid",
            None,
        )

    now_utc = (
        now_utc
        or datetime.now(
            timezone.utc
        )
    )

    local = now_utc.astimezone(
        tz
    )

    calling_days = [
        str(day).lower()[:3]
        for day in (
            campaign.get(
                "calling_days"
            )
            or []
        )
    ]

    today = (
        local.strftime("%a")
        .lower()[:3]
    )

    if today not in calling_days:
        return (
            False,
            "outside_calling_day",
            local,
        )

    try:
        start_hour, start_minute = [
            int(x)
            for x in str(
                campaign[
                    "calling_hours_start"
                ]
            ).split(":", 1)
        ]

        end_hour, end_minute = [
            int(x)
            for x in str(
                campaign[
                    "calling_hours_end"
                ]
            ).split(":", 1)
        ]

    except Exception:
        return (
            False,
            "calling_window_invalid",
            local,
        )

    current_minutes = (
        local.hour * 60
        + local.minute
    )

    start_minutes = (
        start_hour * 60
        + start_minute
    )

    end_minutes = (
        end_hour * 60
        + end_minute
    )

    if not (
        start_minutes
        <= current_minutes
        < end_minutes
    ):
        return (
            False,
            "outside_calling_hours",
            local,
        )

    return (
        True,
        "ok",
        local,
    )


def period_bounds(
    campaign: Dict[str, Any],
    now_utc: Optional[datetime] = None,
):

    tz = ZoneInfo(
        campaign["timezone"]
    )

    now_utc = (
        now_utc
        or datetime.now(
            timezone.utc
        )
    )

    local = now_utc.astimezone(
        tz
    )

    day_start = local.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    hour_start = local.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    return (
        day_start.astimezone(
            timezone.utc
        ).isoformat(),
        hour_start.astimezone(
            timezone.utc
        ).isoformat(),
    )


async def quota_and_pace_ok(
    db,
    campaign: Dict[str, Any],
):

    calls_per_hour = int(
        campaign.get(
            "calls_per_hour"
        )
        or 0
    )

    calls_per_day = int(
        campaign.get(
            "calls_per_day"
        )
        or 0
    )

    if (
        calls_per_hour <= 0
        or calls_per_day <= 0
    ):
        return (
            False,
            "call_limits_invalid",
        )

    day_start, hour_start = (
        period_bounds(
            campaign
        )
    )

    placed_filter = {
        "campaign_id":
            campaign["id"],

        "twilio_sid": {
            "$exists": True,
            "$nin": [None, ""],
        },
    }

    day_count = (
        await db.calls.count_documents({
            **placed_filter,
            "started_at": {
                "$gte": day_start
            },
        })
    )

    hour_count = (
        await db.calls.count_documents({
            **placed_filter,
            "started_at": {
                "$gte": hour_start
            },
        })
    )

    if day_count >= calls_per_day:
        return (
            False,
            "daily_quota_reached",
        )

    if hour_count >= calls_per_hour:
        return (
            False,
            "hourly_quota_reached",
        )

    latest = await db.calls.find_one(
        placed_filter,
        {
            "_id": 0,
            "started_at": 1,
        },
        sort=[
            ("started_at", -1)
        ],
    )

    if (
        latest
        and latest.get(
            "started_at"
        )
    ):

        try:
            last = datetime.fromisoformat(
                latest[
                    "started_at"
                ]
            )

            if last.tzinfo is None:
                last = last.replace(
                    tzinfo=timezone.utc
                )

            elapsed = (
                datetime.now(
                    timezone.utc
                )
                - last.astimezone(
                    timezone.utc
                )
            ).total_seconds()

            required_gap = pace_seconds(
                calls_per_hour
            )

            if elapsed < required_gap:
                return (
                    False,
                    "paced_wait",
                )

        except Exception:

            return (
                False,
                "last_dial_timestamp_invalid",
            )

    canary_phase = int(
        campaign.get(
            "canary_phase"
        )
        or 0
    )

    if canary_phase > 0:

        unique_leads = (
            await db.calls.distinct(
                "lead_id",
                placed_filter,
            )
        )

        if (
            len(unique_leads)
            >= canary_phase
        ):
            return (
                False,
                "canary_limit_reached",
            )

    return (
        True,
        "ok",
    )


async def existing_audio_url(
    db,
    campaign: Dict[str, Any],
    lead: Dict[str, Any],
) -> Optional[str]:

    personalized = await db.lead_vm_audio.find_one(
        {
            "campaign_id": campaign["id"],
            "lead_id": lead["id"],
            "user_id": campaign["user_id"],
        },
        {"_id": 0},
    )

    if personalized:
        url = personalized.get(
            "voicemail_audio_url"
        )

        key = personalized.get(
            "voicemail_audio_key"
        )

        if (
            url
            and key
            and vm_audio_path_for(
                str(key)
            ).is_file()
        ):
            return str(url)

    url = campaign.get(
        "voicemail_audio_url"
    )

    key = campaign.get(
        "voicemail_audio_key"
    )

    if (
        url
        and key
        and vm_audio_path_for(
            str(key)
        ).is_file()
    ):
        return str(url)

    return None


async def get_live_audio(
    db,
    eleven_client,
    campaign: Dict[str, Any],
    lead: Dict[str, Any],
) -> Optional[str]:

    existing = await existing_audio_url(
        db,
        campaign,
        lead,
    )

    if existing:
        return existing

    message = (
        campaign.get(
            "voicemail_message"
        )
        or ""
    )

    if "{business_name}" not in message:
        return None

    backend_url = (
        os.getenv(
            "BACKEND_PUBLIC_URL"
        )
        or os.getenv(
            "REACT_APP_BACKEND_URL"
        )
        or "https://intentbrain.ai"
    )

    return await ensure_lead_vm_audio(
        db=db,
        eleven_client=eleven_client,
        backend_public_url=backend_url,
        campaign=campaign,
        lead=lead,
        user_id=campaign["user_id"],
    )


async def process_campaign_dry_run(
    db,
    campaign: Dict[str, Any],
) -> None:

    campaign_id = campaign.get("id")
    user_id = campaign.get("user_id")

    if (
        not campaign_id
        or not user_id
        or campaign.get("status") != "active"
    ):
        return

    if not campaign.get("voicemail_enabled"):
        log.info(
            "DRY RUN campaign=%s skipped=not_voicemail_campaign",
            campaign_id,
        )
        return

    if twilio_outbound.is_outbound_disabled():
        log.warning(
            "DRY RUN campaign=%s skipped=outbound_disabled",
            campaign_id,
        )
        return

    ok, reason, local = local_window(
        campaign
    )

    if not ok:
        log.info(
            "DRY RUN campaign=%s skipped=%s",
            campaign_id,
            reason,
        )
        return

    ok, reason = await quota_and_pace_ok(
        db,
        campaign,
    )

    if not ok:
        log.info(
            "DRY RUN campaign=%s skipped=%s",
            campaign_id,
            reason,
        )
        return

    canary_phase = int(
        campaign.get("canary_phase")
        or 0
    )

    canary_lead_id = campaign.get(
        "canary_lead_id"
    )

    canary_phone = campaign.get(
        "canary_phone"
    )

    if (
        canary_phase == 1
        and not canary_lead_id
        and not canary_phone
    ):
        log.error(
            "DRY RUN campaign=%s skipped=canary_target_missing",
            campaign_id,
        )
        return

    lead = await peek_next_lead(
        campaign_id,
        user_id,
        canary_lead_id=(
            canary_lead_id
            if canary_phase == 1
            else None
        ),
        canary_phone=(
            canary_phone
            if canary_phase == 1
            else None
        ),
    )

    if not lead:
        log.info(
            "DRY RUN campaign=%s no_eligible_lead",
            campaign_id,
        )
        return

    audio = await existing_audio_url(
        db,
        campaign,
        lead,
    )

    log.info(
        "DRY RUN campaign=%s lead=%s "
        "local=%s audio_ready=%s "
        "pace_seconds=%.1f NO_TWILIO_CALL",
        campaign_id,
        lead.get("id"),
        local.isoformat()
        if local
        else None,
        bool(audio),
        pace_seconds(
            int(
                campaign.get(
                    "calls_per_hour"
                )
                or 0
            )
        ),
    )


async def run_dry_run_loop() -> None:

    db = get_db()

    # Initialize only enough outbound state
    # for kill-switch checks.
    twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=object(),
        eleven_client=None,
        voice_id="",
        backend_url=(
            os.getenv("BACKEND_PUBLIC_URL")
            or "https://intentbrain.ai"
        ),
        from_number="DRY_RUN",
    )

    await ensure_runner_indexes()

    recovered = await recover_stale_claims()

    log.info(
        "RANKTRUST CAMPAIGN RUNNER DRY RUN "
        "worker=%s recovered_stale_claims=%s",
        WORKER_ID,
        recovered,
    )

    campaigns = await db.campaigns.find(
        {
            "status": "active",
        },
        {
            "_id": 0,
        },
    ).to_list(100)

    log.info(
        "DRY RUN active_campaigns=%s",
        len(campaigns),
    )

    for campaign in campaigns:
        await process_campaign_dry_run(
            db,
            campaign,
        )

    log.info(
        "DRY RUN COMPLETE — NO TWILIO CALLS CREATED"
    )


# Main entry point moved to bottom after live-canary functions.


async def initialize_live_outbound(db):

    from twilio.rest import Client
    from elevenlabs import ElevenLabs

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not sid or not token or not from_number:
        raise RuntimeError(
            "Twilio environment incomplete"
        )

    twilio_client = Client(
        sid,
        token,
    )

    eleven_key = os.getenv(
        "ELEVENLABS_API_KEY"
    )

    eleven_client = (
        ElevenLabs(api_key=eleven_key)
        if eleven_key
        else None
    )

    backend_url = (
        os.getenv("BACKEND_PUBLIC_URL")
        or os.getenv("REACT_APP_BACKEND_URL")
        or "https://intentbrain.ai"
    )

    twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=twilio_client,
        eleven_client=eleven_client,
        voice_id="",
        backend_url=backend_url,
        from_number=from_number,
    )

    return eleven_client


async def select_live_canary(
    db,
    campaign: Dict[str, Any],
):

    campaign_id = campaign.get("id")
    user_id = campaign.get("user_id")

    if campaign.get("status") != "active":
        return None, "campaign_not_active"

    if not campaign.get("voicemail_enabled"):
        return None, "not_voicemail_campaign"

    if int(campaign.get("canary_phase") or 0) != 1:
        return None, "live_v1_requires_canary_phase_1"

    canary_lead_id = campaign.get(
        "canary_lead_id"
    )

    canary_phone = campaign.get(
        "canary_phone"
    )

    if not canary_lead_id or not canary_phone:
        return None, "canary_target_missing"

    if twilio_outbound.is_outbound_disabled():
        return None, "outbound_disabled"

    ok, reason, _ = local_window(
        campaign
    )

    if not ok:
        return None, reason

    ok, reason = await quota_and_pace_ok(
        db,
        campaign,
    )

    if not ok:
        return None, reason

    lead = await peek_next_lead(
        campaign_id,
        user_id,
        canary_lead_id=canary_lead_id,
        canary_phone=canary_phone,
    )

    if not lead:
        return None, "controlled_canary_not_found"

    if (
        lead.get("id") != canary_lead_id
        or lead.get("phone") != canary_phone
    ):
        return None, "canary_identity_mismatch"

    return lead, "ok"


async def process_live_canary(
    db,
    eleven_client,
    campaign: Dict[str, Any],
) -> str:

    lead, reason = await select_live_canary(
        db,
        campaign,
    )

    if not lead:
        log.info(
            "LIVE CANARY campaign=%s skipped=%s",
            campaign.get("id"),
            reason,
        )
        return reason

    campaign_id = campaign["id"]
    user_id = campaign["user_id"]

    if twilio_outbound.is_outbound_disabled():
        return "outbound_disabled"

    claimed = await claim_next_lead(
        campaign_id,
        user_id,
        WORKER_ID,
        claim_ttl_seconds=CLAIM_TTL_SECONDS,
        canary_lead_id=campaign["canary_lead_id"],
        canary_phone=campaign["canary_phone"],
    )

    if not claimed:
        return "canary_claim_failed"

    call_id = None

    try:
        audio_url = await get_live_audio(
            db,
            eleven_client,
            campaign,
            claimed,
        )

        if not audio_url:
            await release_claim(
                claimed["id"],
                WORKER_ID,
                "no_vm_audio",
            )
            return "no_vm_audio"

        call_id = await create_call_record(
            user_id,
            campaign_id,
            claimed["id"],
            campaign.get("agent_id"),
            WORKER_ID,
        )

        fresh = await db.campaigns.find_one(
            {
                "id": campaign_id,
                "user_id": user_id,
            },
            {
                "_id": 0,
                "status": 1,
                "canary_phase": 1,
                "canary_lead_id": 1,
                "canary_phone": 1,
            },
        )

        if (
            not fresh
            or fresh.get("status") != "active"
            or int(fresh.get("canary_phase") or 0) != 1
            or fresh.get("canary_lead_id") != claimed["id"]
            or fresh.get("canary_phone") != claimed["phone"]
        ):
            await mark_call_failed(
                call_id,
                "canary_state_changed",
            )

            await release_claim(
                claimed["id"],
                WORKER_ID,
                "canary_state_changed",
            )

            return "canary_state_changed"

        if twilio_outbound.is_outbound_disabled():

            await mark_call_failed(
                call_id,
                "outbound_disabled",
            )

            await release_claim(
                claimed["id"],
                WORKER_ID,
                "outbound_disabled",
            )

            return "outbound_disabled"

        result = await twilio_outbound.place_voicemail_call(
            to_number=claimed["phone"],
            lead_id=claimed["id"],
            campaign_id=campaign_id,
            call_id=call_id,
            voicemail_audio_url=audio_url,
            business_name=claimed.get("business_name"),
        )

        if result.get("skipped") == "dnc":
            await db.calls.delete_one(
                {"id": call_id}
            )

            await release_claim(
                claimed["id"],
                WORKER_ID,
                "dnc",
            )

            return "dnc"

        if not result.get("ok"):

            error = (
                result.get("error")
                or result.get("blocked")
                or "place_failed"
            )

            await mark_call_failed(
                call_id,
                error,
            )

            await release_claim(
                claimed["id"],
                WORKER_ID,
                error,
            )

            return error

        await mark_call_placed(
            call_id,
            result["session_id"],
            result["call_sid"],
        )

        await mark_lead_attempted(
            claimed["id"],
            campaign_id,
            WORKER_ID,
        )

        await db.campaigns.update_one(
            {
                "id": campaign_id,
                "user_id": user_id,
            },
            {
                "$inc": {
                    "total_calls": 1
                }
            },
        )

        log.info(
            "LIVE CANARY PLACED campaign=%s lead=%s call_sid=%s",
            campaign_id,
            claimed["id"],
            result["call_sid"],
        )

        return "placed"

    except Exception as exc:

        log.exception(
            "LIVE CANARY ERROR campaign=%s lead=%s",
            campaign_id,
            claimed.get("id"),
        )

        if call_id:
            await mark_call_failed(
                call_id,
                "runner_error:"
                + type(exc).__name__,
            )

        await release_claim(
            claimed["id"],
            WORKER_ID,
            "runner_error",
        )

        return "runner_error"


async def run_live_canary_once() -> None:

    db = get_db()
    eleven_client = await initialize_live_outbound(db)

    await ensure_runner_indexes()

    campaigns = await db.campaigns.find(
        {
            "status": "active",
            "canary_phase": 1,
        },
        {
            "_id": 0,
        },
    ).to_list(20)

    if len(campaigns) != 1:
        raise RuntimeError(
            f"Expected exactly 1 active canary campaign, found {len(campaigns)}"
        )

    result = await process_live_canary(
        db,
        eleven_client,
        campaigns[0],
    )

    print("LIVE CANARY RESULT:", result)


if __name__ == "__main__":

    if DRY_RUN:
        asyncio.run(
            run_dry_run_loop()
        )

    else:
        if os.getenv("RUN_LIVE_CANARY") != "YES":
            raise RuntimeError(
                "LIVE MODE BLOCKED. "
                "Set RUN_LIVE_CANARY=YES explicitly."
            )

        asyncio.run(
            run_live_canary_once()
        )
