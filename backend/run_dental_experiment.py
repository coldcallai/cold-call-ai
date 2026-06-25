"""Day-1 RankTrust Validation Dialer — uses the Outbound Human-Greeting Gate.

Hard rules now enforced upstream (in backend/routes/twilio_outbound.py):
  * Twilio call is created with `url=...` (NOT inline TwiML).
  * AI never speaks until the prospect says "hello" (silent <Gather> gate).
  * Voicemail/IVR/AMD short-circuits to silent hangup.
  * Opener is ElevenLabs MP3 via <Play>. Twilio <Say> is NEVER used for AI voice.
  * DNC numbers are skipped here (and via add_to_dnc on caller request).

Usage:
    cd /var/www/dialgenix/backend
    PYTHONPATH=$PWD python3 run_dental_experiment.py --csv /tmp/dental_test.csv

After all calls complete, run:
    PYTHONPATH=$PWD python3 generate_dental_reports.py
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from twilio.rest import Client as TwilioClient
from elevenlabs import ElevenLabs

# Load .env BEFORE importing routes (which reads env at setup time)
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Ensure backend root is importable when run as a script
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from routes import twilio_outbound  # noqa: E402
from universal.engines.campaign_session import CampaignSession  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("dental_dialer")


def _env(key: str, *, required: bool = True, default: str | None = None) -> str:
    v = os.environ.get(key, default)
    if required and not v:
        raise SystemExit(f"Missing required env var: {key}")
    return v or ""


def _build_clients():
    mongo_url = _env("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "intentbrain")
    twilio_sid = _env("TWILIO_ACCOUNT_SID")
    twilio_token = _env("TWILIO_AUTH_TOKEN")
    twilio_from = os.environ.get("TWILIO_OUTBOUND_FROM") or os.environ.get("TWILIO_PHONE_NUMBER")
    if not twilio_from:
        raise SystemExit("Missing TWILIO_OUTBOUND_FROM (or TWILIO_PHONE_NUMBER)")
    backend_url = _env("BACKEND_URL")
    eleven_key = _env("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"  # Rachel default

    db = AsyncIOMotorClient(mongo_url)[db_name]
    twilio_client = TwilioClient(twilio_sid, twilio_token)
    eleven_client = ElevenLabs(api_key=eleven_key)

    twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=twilio_client,
        eleven_client=eleven_client,
        synthesize_fn=None,  # default ElevenLabs MP3 generator
        voice_id=voice_id,
        backend_url=backend_url,
        from_number=twilio_from,
    )
    log.info(f"Dialer ready. from={twilio_from} backend_url={backend_url} voice_id={voice_id}")
    return db


async def dial_one(*, lead: dict, campaign_id: str, variant_index: int, experiment_tag: str) -> dict:
    """Place one outbound call through the gate."""
    phone = lead["phone"]
    biz = lead.get("business_name") or "(unknown)"
    lead_attrs = {"gbp_rank": int(lead.get("gbp_rank") or 0), "niche": "dental"}

    result = await twilio_outbound.place_outbound_call(
        to_number=phone,
        lead_id=lead["lead_id"],
        campaign_id=campaign_id,
        variant_index=variant_index,
        lead_attrs=lead_attrs,
        business_name=biz,
        experiment_tag=experiment_tag,
    )

    if result.get("ok"):
        log.info(f"  ✓ {biz[:30]:30}  {campaign_id[:24]:24}  v{variant_index}  sid={result['call_sid']}")
    elif result.get("skipped") == "dnc":
        log.warning(f"  ⏭  {biz[:30]:30}  SKIPPED (on DNC list)  {phone}")
    else:
        log.error(f"  ✗ {biz[:30]:30}  FAILED  result={result}")
    return result


async def run(csv_path: str, control_count: int, ranktrust_count: int, dry_run: bool):
    db = _build_clients()

    leads: list[dict] = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)

    total = control_count + ranktrust_count
    if not leads:
        log.error("No leads in CSV.")
        return

    log.info(f"Loaded {len(leads)} leads. Plan: {control_count} Control + {ranktrust_count} RankTrust = {total} total")

    if dry_run:
        log.info("--- DRY RUN — no calls placed ---")
        for i, lead in enumerate(leads[:total]):
            cid = "merchant_services_default" if i < control_count else "ranktrust_local_growth"
            vidx = 0 if i < control_count else 3
            s = CampaignSession.start_forced(
                lead_id=lead["lead_id"],
                lead_attrs={"gbp_rank": int(lead.get("gbp_rank") or 0)},
                campaign_id=cid,
                variant_index=vidx,
            )
            print(f"  [{i+1:02d}] {lead['business_name'][:30]:30} {cid[:24]:24} v{vidx} opener=\"{s.opener_text[:60]}...\"")
        return

    print("\nType 'DIAL' to begin placing real calls: ", end="")
    sys.stdout.flush()
    if input().strip() != "DIAL":
        print("Aborted.")
        return

    experiment_tag = "ranktrust_validation_2026-06-25"

    log.info(f"=== CONTROL — {control_count} calls ===")
    for lead in leads[:control_count]:
        await dial_one(lead=lead, campaign_id="merchant_services_default",
                       variant_index=0, experiment_tag=experiment_tag)
        time.sleep(8)

    log.info(f"=== RANKTRUST VARIANT D — {ranktrust_count} calls ===")
    for lead in leads[control_count:total]:
        await dial_one(lead=lead, campaign_id="ranktrust_local_growth",
                       variant_index=3, experiment_tag=experiment_tag)
        time.sleep(8)

    log.info(f"✓ All {total} dials initiated. Monitor Twilio + db.outbound_sessions.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to dental_test.csv")
    ap.add_argument("--control", type=int, default=25, help="Control call count")
    ap.add_argument("--ranktrust", type=int, default=25, help="RankTrust call count")
    ap.add_argument("--dry-run", action="store_true", help="Show plan without dialing")
    args = ap.parse_args()
    asyncio.run(run(args.csv, args.control, args.ranktrust, args.dry_run))


if __name__ == "__main__":
    main()
