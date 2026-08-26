# Phase 2 Lite — Integration Guide

## What this is
The minimum production wiring needed to test the RankTrust vs Merchant Services
opener hypothesis with real calls. **Legacy brain is not touched.** Three
integration points in `server.py`, each ~5 lines.

## What this is NOT
- ❌ Replacing the legacy inline brain
- ❌ Wiring the new Orchestrator into the conversation
- ❌ Modifying MerchantBrain, UniversalBrain, Decision Maker, Workflow, Funding,
       Qualification, or Transfer Logic
- ❌ MerchantBrain V2

If any of the above starts happening, stop and revert.

---

## Integration Points

### Point 1 — Outbound dial start
Where the existing code initiates an outbound call and decides what the AI
will say first.

```python
# at the top of server.py
from universal.engines.campaign_session import CampaignSession

# wherever you currently kick off an outbound call:
async def start_outbound_call(lead_id: str, phone: str, lead_attrs: dict):
    # === PHASE 2 LITE: opener selection ===
    session = CampaignSession.start(lead_id=lead_id, lead_attrs=lead_attrs)
    opener_text = session.opener_text

    # Persist the session context onto the call doc so the end-of-call
    # webhook can rehydrate it. Use your existing outbound_calls collection.
    await db.outbound_calls.insert_one({
        "lead_id": lead_id,
        "phone": phone,
        "started_at": datetime.now(timezone.utc),
        "campaign_session": session.session_context(),
    })
    # =====================================

    # …existing Twilio dial logic, but instead of the hard-coded opener,
    # pass `opener_text` into the first TwiML <Say> / ElevenLabs prefetch.
```

`lead_attrs` should include whatever data your scraper already collects.
Minimum: `{"gbp_rank": 8}` (RankTrust auto-discovery output).

**Failure modes already handled:**
- No `gbp_rank` → falls back to `merchant_services_default` opener
- `gbp_rank` outside 4-20 → falls back to control opener
- Multiple campaigns match → most-specific rule-count wins (deterministic tiebreak by lead_id hash)

---

### Point 2 — Optional caller-utterance intercept (RankTrust objection responses)
This is the **only** place Phase 2 Lite touches the live conversation. It runs
**before** the legacy brain processes each caller turn. If the caller says
something the campaign has a canned response for, we say that and return —
otherwise we hand control to the legacy brain unchanged.

```python
# in your /api/twilio/.../respond handler, ABOVE the existing legacy brain call:

# === PHASE 2 LITE: campaign objection intercept ===
session_ctx = (call_doc or {}).get("campaign_session")
if session_ctx:
    session = CampaignSession.rehydrate(session_ctx)
    canned = session.check_objection(caller_speech)
    if canned:
        # speak it and return — skip the legacy brain for THIS turn only
        return twilio_say_and_gather(canned)
# =================================================

# …existing legacy brain logic continues here, untouched
```

What this gives you on day one:
- "How did you find my ranking?" → friendly canned response
- "Where did you get my number?" → transparency response
- "Is this a robocall?" → calm answer + open question

That's it. Three phrases. No conversational logic added.

---

### Point 3 — Call-end finalize (the report)
Where you currently handle Twilio's call-status callback (the `completed`
event). After your existing cleanup, build and persist the CallReport.

```python
# in your /api/twilio/call-status webhook, after existing logic:

# === PHASE 2 LITE: persist CallReport ===
session_ctx = (call_doc or {}).get("campaign_session")
if session_ctx:
    session = CampaignSession.rehydrate(session_ctx)
    await session.finalize(
        call_sid=call_sid,
        legacy_call_doc=call_doc,           # your existing outbound_calls doc
        reports_collection=db.call_reports, # new collection, MongoDB auto-creates
    )
# ========================================
```

This writes one document per call into `db.call_reports`. The `analyze.py` CLI
already reads that collection.

`legacy_call_doc` is your existing call document. The adapter looks for these
fields (all optional, missing fields default cleanly):
- `decision_maker_name`, `current_processor`
- `intent_score`
- `appointment_booked`, `transferred`, `outcome`
- `conversation_stage` / `status`
- `turns` or `transcript` (list of `{role, text}` or `{speaker, said}`)

The richer `legacy_call_doc.turns` is, the richer the report — but even with
an empty turns list you still get the campaign attribution, opener variant,
engaged_past_opener (boolean), DM reached, and outcome.

---

## After integration: testing the experiment

```bash
# After 50+ calls have run:
cd /var/www/dialgenix/backend
PYTHONPATH=$PWD python3 -m universal.reporting.analyze --campaign ranktrust_local_growth
```

Outputs the side-by-side variant performance you saw in the hypothetical
dashboard — but on real data.

```bash
# Compare RankTrust vs Merchant Services baseline:
PYTHONPATH=$PWD python3 -m universal.reporting.analyze
```

Outputs the A/B campaign comparison at the bottom.

---

## Rollback

If anything is off, the entire Phase 2 Lite layer is removable by reverting
the three insertion points. The new files (`universal/engines/campaign_session.py`,
`playbooks/campaigns/*`) stay on disk but are dormant — nothing imports them
unless `server.py` does.

```python
# Complete rollback = remove the three Phase 2 Lite code blocks from server.py
# No DB cleanup needed; the call_reports collection is independent.
```

---

## What we learn after 50-100 calls

Per your spec:
| Question | Answered by |
|---|---|
| Will RankTrust open more conversations than merchant processing? | `Conversation Rate` per campaign |
| Which RankTrust variant wins? | `Variant Performance` table |
| What are real merchants saying? | `Top Merchant Phrases` |
| What objections matter most? | `Top Objection Phrases` |
| Should we ship `DM_ALREADY_HAVE_SEO_COMPANY` next? | Frequency in `Top Objection Phrases` |
| Should we kill, iterate, or scale RankTrust? | All of the above |

This is the smallest possible step that produces the data needed to answer
the next strategic question. Nothing else.
