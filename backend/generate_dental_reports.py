"""Generate CallReports from completed dental experiment calls.

Reads db.calls + db.inbound_calls (where the respond handler stored conversation),
builds CallReport per call, writes to db.call_reports.

Usage:
    cd /var/www/dialgenix/backend
    PYTHONPATH=$PWD python3 generate_dental_reports.py
"""
from __future__ import annotations
import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from universal.engines.campaign_session import CampaignSession


EXPERIMENT_TAG = "ranktrust_validation_2026-06-24"


async def run():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "intentbrain")]

    n_built = 0
    n_skipped = 0

    async for call_doc in db.calls.find({"experiment": EXPERIMENT_TAG}, {"_id": 0}):
        sid = call_doc["twilio_sid"]
        ctx = call_doc.get("campaign_session")
        if not ctx:
            n_skipped += 1
            continue
        session = CampaignSession.rehydrate(ctx)

        # Pull conversation + status from inbound_calls
        ibc = await db.inbound_calls.find_one({"call_sid": sid}, {"_id": 0}) or {}

        # Construct legacy_call_doc combining what both collections know
        legacy = {
            "decision_maker_name": ibc.get("decision_maker_name"),
            "current_processor": ibc.get("current_processor"),
            "intent_score": ibc.get("intent_score", 0),
            "appointment_booked": ibc.get("appointment_booked") or ibc.get("demo_sms_sent_at") is not None,
            "transferred": ibc.get("transferred"),
            "conversation_stage": ibc.get("conversation_stage") or call_doc.get("status"),
            "outcome": ibc.get("outcome"),
            # The respond handler stores {caller, timestamp} per turn
            "turns": [
                {"role": "user", "text": t.get("caller", "")}
                for t in (ibc.get("conversation") or [])
                if t.get("caller")
            ],
        }
        report = await session.finalize(
            call_sid=sid, legacy_call_doc=legacy,
            reports_collection=db.call_reports,
        )
        # Override duration from Twilio's actual reported number
        if call_doc.get("duration"):
            await db.call_reports.update_one(
                {"call_sid": sid},
                {"$set": {"duration_seconds": int(call_doc["duration"])}},
            )
        n_built += 1
        print(f"  ✓ {sid}  campaign={report.campaign_id}  variant={report.campaign_variant_index}  outcome={report.outcome}  engaged={report.engaged_past_opener}")

    print(f"\nBuilt {n_built} reports. Skipped {n_skipped} (no campaign_session).")
    print("\nNow run:")
    print("  PYTHONPATH=$PWD python3 -m universal.reporting.analyze")
    print("  PYTHONPATH=$PWD python3 -m universal.reporting.analyze --campaign ranktrust_local_growth")


if __name__ == "__main__":
    asyncio.run(run())
