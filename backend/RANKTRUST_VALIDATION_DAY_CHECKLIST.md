# RankTrust Validation Day — Morning Checklist
**Date:** _________________
**Mission (one sentence):** Determine whether a growth-based RankTrust opener creates more conversations than a merchant-services opener.

---

## ⏰ 9:00 AM — Deploy today's bundle (~3 minutes)

Run this on your VPS:

```bash
curl -L -o /tmp/ubp6.tgz <BUNDLE_URL_FROM_EMERGENT>
cd /var/www/dialgenix/backend && tar -xzvf /tmp/ubp6.tgz && PYTHONPATH=$PWD python3 tests/universal/test_campaign_session.py
```

**Expected:** 12 `PASS:` lines.

✅ Locks Control opener to: `"Who handles payment processing?"`
✅ Adds RankTrust Variant D forcing mechanism (`CampaignSession.start_forced`)
✅ Confirms 4 canned responses are loaded (SEO company / ranking question / number / robocall)

---

## ⏰ 9:15 AM — Build the test list (~15 minutes)

In **RankTrust**, filter:
- **Niche:** Dentists only (do NOT mix verticals)
- **GBP Rank:** 4-20
- **Pull:** 60 leads (you'll call 50 = 25 control + 25 RankTrust, +10 buffer for bad numbers)

Save the list as `dental_test_2026-06-16.csv` with columns: `lead_id, business_name, phone, gbp_rank`.

---

## ⏰ 9:30 AM — Wire Phase 2 Lite into server.py (~30 minutes)

Open `/var/www/dialgenix/backend/server.py` and apply the 3 integration points from `PHASE2_LITE_INTEGRATION.md`.

**For today's experiment, use the FORCED variant variant of integration point #1.** Split your 50 leads into two halves before dialing:

```python
# Day-1 experiment: lock variants instead of letting CampaignRouter rotate.
# First 25 leads → Control. Next 25 → RankTrust Variant D.

# Control half (25 calls):
session = CampaignSession.start_forced(
    lead_id=lead_id,
    lead_attrs={"niche": "dental"},
    campaign_id="merchant_services_default",
    variant_index=0,
)

# RankTrust half (25 calls):
session = CampaignSession.start_forced(
    lead_id=lead_id,
    lead_attrs={"gbp_rank": gbp_rank, "niche": "dental"},
    campaign_id="ranktrust_local_growth",
    variant_index=3,    # ← Variant D
)
```

Integration points #2 (objection intercept) and #3 (finalize / save report) are identical regardless of which campaign was selected.

**After wiring, restart and smoke-test:**
```bash
pm2 restart dialgenix-backend --update-env
pm2 logs dialgenix-backend --lines 30
```
Confirm: no exceptions, "online" status.

---

## ⏰ 10:00 AM — Place first 5 calls of each group (~30 minutes)

**5 Control + 5 RankTrust.** Listen live to at least 2-3 of each.

Watch for:
- AI says the correct opener
- Twilio doesn't crash
- `db.call_reports` gets a document per completed call

Verify after first 10 calls:
```bash
cd /var/www/dialgenix/backend
PYTHONPATH=$PWD python3 -c "
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
async def check():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ.get('DB_NAME', 'intentbrain')]
    n = await db.call_reports.count_documents({})
    print(f'call_reports documents: {n}')
asyncio.run(check())
"
```

Expected: `call_reports documents: 10` (or more).

---

## ⏰ 11:00 AM – 3:00 PM — Complete the 50 calls

Pace yourself. Take notes per call using the **Call Listening Template** (next file).

After every batch of 10 calls, run:
```bash
PYTHONPATH=$PWD python3 -m universal.reporting.analyze
```

Don't over-react to early numbers. Patterns emerge around call 30-40.

---

## ⏰ 4:00 PM — End-of-day analysis (~20 minutes)

```bash
cd /var/www/dialgenix/backend

# Full A/B view
PYTHONPATH=$PWD python3 -m universal.reporting.analyze

# Deep dive on RankTrust
PYTHONPATH=$PWD python3 -m universal.reporting.analyze --campaign ranktrust_local_growth

# Deep dive on Control
PYTHONPATH=$PWD python3 -m universal.reporting.analyze --campaign merchant_services_default
```

---

## ⏰ 4:30 PM — Decision Framework

Look at **only these 4 numbers** for each campaign:
1. Conversation Rate (engaged past opener)
2. Decision Maker Rate
3. Appointment Rate
4. Transfer Rate

**Success criteria:** RankTrust beats Control by **20%+** on Conversation Rate.

| Outcome | What it means | Next move |
|---|---|---|
| RankTrust +20%+ | Hypothesis confirmed | Scale to 200 calls next week, all RankTrust |
| RankTrust 0-20% better | Inconclusive | Re-run with Variant B as challenger to D |
| Control wins | Hypothesis falsified | Stop, listen to recordings, find the real opener |

---

## ❌ NOT TODAY

- [ ] MerchantBrain V2
- [ ] InsuranceBrain
- [ ] RoofingBrain
- [ ] Funding Score
- [ ] Workflow Score
- [ ] Another engine
- [ ] Another architecture refactor
- [ ] Another playbook module

If you catch yourself starting any of the above, stop. Today is validation day.

---

## 🚨 If something breaks

```bash
# Backend won't start after wiring?
tail -200 /var/log/supervisor/dialgenix-backend.err.log
# (or wherever pm2 writes errors — `pm2 logs dialgenix-backend --err`)

# Need to instantly revert Phase 2 Lite?
# Just remove the 3 code blocks you added to server.py.
# The new files stay on disk but become dormant (nothing imports them).
pm2 restart dialgenix-backend --update-env
```

Ping Emergent with the error log if stuck more than 15 minutes — the goal today is data, not debugging.
