"""Day-1 RankTrust Validation Dialer.

Standalone script — does NOT modify server.py.
Reads dental_test.csv, dials 50 calls (25 control + 25 RankTrust Variant D),
tags each call doc with campaign_session context for later analysis.

Usage:
    cd /var/www/dialgenix/backend
    PYTHONPATH=$PWD python3 run_dental_experiment.py --csv /tmp/dental_test.csv

After all calls complete (next day), run:
    PYTHONPATH=$PWD python3 generate_dental_reports.py
"""
from __future__ import annotations
import argparse
import asyncio
import csv
import os
import sys
import time
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from twilio.rest import Client as TwilioClient

from universal.engines.campaign_session import CampaignSession


# Read from env (same as server.py)
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "intentbrain")
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM = os.environ.get("TWILIO_OUTBOUND_FROM") or os.environ.get("TWILIO_PHONE_NUMBER")
BACKEND_URL = os.environ["BACKEND_URL"]


def build_twiml(opener_text: str, callback_url: str) -> str:
    """Inline TwiML: AI says the campaign opener, then hands to the existing
    respond handler for the rest of the conversation."""
    # Escape XML special chars in opener
    safe = (opener_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="{callback_url}/api/twilio/inbound/respond" method="POST" speechTimeout="auto" timeout="6">
        <Say voice="Polly.Joanna-Neural">{safe}</Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">No worries, I'll try you again another time. Have a great day.</Say>
    <Hangup/>
</Response>"""


async def dial_one(*, twilio: TwilioClient, db, lead: dict, campaign_id: str, variant_index: int) -> dict:
    session = CampaignSession.start_forced(
        lead_id=lead["lead_id"],
        lead_attrs={"gbp_rank": int(lead.get("gbp_rank") or 0), "niche": "dental"},
        campaign_id=campaign_id,
        variant_index=variant_index,
    )

    twiml = build_twiml(session.opener_text, BACKEND_URL)
    status_cb = f"{BACKEND_URL}/api/twilio/status"

    try:
        call = twilio.calls.create(
            to=lead["phone"],
            from_=TWILIO_FROM,
            twiml=twiml,
            status_callback=status_cb,
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            record=True,
        )
        # Tag the call doc — written to BOTH collections so analyzer can find it
        await db.calls.update_one(
            {"twilio_sid": call.sid},
            {"$set": {
                "twilio_sid": call.sid,
                "lead_id": lead["lead_id"],
                "business_name": lead.get("business_name"),
                "phone": lead["phone"],
                "campaign_session": session.session_context(),
                "experiment": "ranktrust_validation_2026-06-24",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        # Also seed inbound_calls so the respond handler has a doc to update
        await db.inbound_calls.update_one(
            {"call_sid": call.sid},
            {"$set": {
                "call_sid": call.sid,
                "lead_id": lead["lead_id"],
                "campaign_session": session.session_context(),
                "experiment": "ranktrust_validation_2026-06-24",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "conversation_stage": "post_opener",
            }},
            upsert=True,
        )
        print(f"  ✓ {lead['business_name'][:30]:30}  {campaign_id[:12]:12}  v{variant_index}  sid={call.sid}")
        return {"call_sid": call.sid, "lead_id": lead["lead_id"], "ok": True}
    except Exception as e:
        print(f"  ✗ {lead['business_name'][:30]:30}  ERROR: {e}")
        return {"lead_id": lead["lead_id"], "ok": False, "error": str(e)}


async def run(csv_path: str, control_count: int, ranktrust_count: int, dry_run: bool):
    twilio = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    leads = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(row)
    if not leads:
        print("No leads in CSV.")
        return

    print(f"Loaded {len(leads)} leads from {csv_path}.")
    print(f"Plan: {control_count} Control + {ranktrust_count} RankTrust = {control_count + ranktrust_count} total")
    print(f"From number: {TWILIO_FROM}")
    if dry_run:
        print("\n--- DRY RUN — no calls placed ---")
        for i, lead in enumerate(leads[: control_count + ranktrust_count]):
            cid = "merchant_services_default" if i < control_count else "ranktrust_local_growth"
            vidx = 0 if i < control_count else 3
            s = CampaignSession.start_forced(
                lead_id=lead["lead_id"], lead_attrs={"gbp_rank": int(lead.get("gbp_rank") or 0)},
                campaign_id=cid, variant_index=vidx,
            )
            print(f"  [{i+1:02d}] {lead['business_name'][:30]:30} {cid[:12]:12} v{vidx} opener=\"{s.opener_text[:60]}...\"")
        return

    # Confirm
    print("\nType 'DIAL' to begin placing real calls: ", end="")
    sys.stdout.flush()
    if input().strip() != "DIAL":
        print("Aborted.")
        return

    # Control half
    print(f"\n=== CONTROL — {control_count} calls ===")
    for i, lead in enumerate(leads[:control_count]):
        await dial_one(twilio=twilio, db=db, lead=lead,
                       campaign_id="merchant_services_default", variant_index=0)
        time.sleep(8)  # 8s between dials — keeps Twilio happy, avoids queue

    # RankTrust half (Variant D)
    print(f"\n=== RANKTRUST VARIANT D — {ranktrust_count} calls ===")
    for i, lead in enumerate(leads[control_count : control_count + ranktrust_count]):
        await dial_one(twilio=twilio, db=db, lead=lead,
                       campaign_id="ranktrust_local_growth", variant_index=3)
        time.sleep(8)

    print(f"\n✓ All {control_count + ranktrust_count} dials initiated. Monitor via Twilio console + db.calls collection.")


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
