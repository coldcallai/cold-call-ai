# IntentBrain.ai - PRD

## Original Problem Statement
Build an AI cold calling machine that calls businesses, qualifies them, and routes qualified leads to different sales agents for payment processing.

## Current Status: LAUNCH READY
- Platform fully functional at https://intentbrain.ai
- ElevenLabs Scale ($330/mo, 2M credits)
- Stripe live payments working
- Both phone numbers (404 + 888) active with natural AI voice
- SSL configured, DNS propagated

## Architecture
- **Frontend:** React 18, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, Motor (async MongoDB)
- **Voice Pipeline:** Twilio → FastAPI WebSocket → GPT-5.2 → ElevenLabs Flash v2
- **Payments:** Stripe live
- **Pricing:** BYOK model

## Pricing
| Plan | Price |
|---|---|
| Test Drive | $49/mo |
| Review Requests | $49/mo (add-on) |
| BYOL Starter | $199/mo |
| BYOL Pro | $449/mo |
| BYOL Scale | $799/mo |
| Discovery Starter | $399/mo |
| Discovery Pro | $899/mo |
| Discovery Elite | $1,599/mo |
| Receptionist Lite | $49/mo |
| Receptionist Pro | $99/mo |
| Receptionist Plus | $199/mo |

## Domains
- Primary: https://intentbrain.ai (live, SSL)
- Legacy: https://dialgenix.ai (still works, same server)

## Completed (June 12, 2026) — BUG #004 Latency Eliminated
- [x] **Fast-path cache** for AI identity probes (29 phrases): bypasses OpenAI (~3000ms → <5ms) — `_BRAIN_FAST_PATH_CACHE` in `server.py` lines ~125
- [x] **Auto-followup wrapper** (`_ensure_followup`): appends "Want a quick demo?" when brain text doesn't end with "?" — kills silent dead-end after brain answers
- [x] **Audio prewarm at startup** (background async task, semaphore=4): pre-generates ElevenLabs audio for all 27+ fast-path responses on boot — `prewarm_fast_path_audio` startup hook
- [x] **Reverted `speech_timeout=1.5` → `"auto"`**: saves ~800ms of dead air vs 1.5s wait
- [x] **Shortened fast-path responses to ≤12 words**: halves ElevenLabs gen time
- [x] **"Sarah" identity leak fixed** in `cache_inbound_audio()` greeting — agent is now neutral "I'm your AI assistant"
- [x] **Removed "who built you" from prompt_injection guard** — was returning dismissive "I can't provide internal system information"
- [x] **Removed "are you a bot" from OFF list** — now routed to fast-path
- [x] **Added 8 Spanish/language fast-path entries**: "do you speak spanish", "habla espanol", "what languages do you support", etc.
- [x] **Result: All identity probes ~800ms total perceived latency (102ms backend)** — indistinguishable from live human rep

### Verified via live calls to 888-513-1913:
- "who built you?" → `FAST_PATH hit + cache_hit=True` (102ms backend)
- "are you a bot?" → `FAST_PATH hit + cache_hit=True`
- "do you speak spanish?" → `FAST_PATH hit + cache_hit=True`
- "what languages do you support?" → `FAST_PATH hit + cache_hit=True`

### Files touched (on VPS `/var/www/dialgenix/backend/`):
- `server.py` — Multiple patches v3, v4, v5 (backed up as `.py.bak.<timestamp>`)
- `inbound_audio_cache/` — 27 cached `.b64` files now present

## Completed (April 28, 2026)
- [x] **Inbound 888 agent pricing fix**: Replaced wrong "$199/$499" tiers with correct Discovery Starter $399, Pro $899, Elite $1,599
- [x] **Qualifying question added**: AI now asks "How many leads/calls per month?" before quoting price
- [x] **BYOL/Discovery branch**: Vague callers ("small/exploring") routed to "Do you have your own list, or need us to find them?" → BYOL ($199/$449/$799) or Discovery
- [x] **$49 starter fallback**: All Discovery quotes now end with "We also have a starter package at $49 — want me to walk you through that?" → Test Drive
- [x] **Reduced speech sensitivity**: All inbound `Gather` blocks `speech_timeout='auto'` → `speech_timeout=2`, `timeout=5→8`
- [x] **Call Me button error handling**: Maps Twilio error codes (21211/21214/21215/21610/401) to friendly messages
- [x] Stale audio cache cleared so VPS regenerates with new pricing copy
- [x] New audio keys: `qualify_volume`, `qualify_byol_or_discovery`, `pricing_starter/pro/elite/overview`, `pricing_test_drive`, `pricing_byol_starter/pro/scale`

## Completed (April 22, 2026)
- [x] **Lead Discovery → Funnel bug FIXED**: Modular `routes/leads.py` was saving discovered leads with `user_id=None` and without `campaign_id`, making them invisible to Funnel (which filters by user_id)
- [x] Added `/api/leads/backfill-orphans` endpoint (one-click repair for existing orphan leads)
- [x] Added "Fix Missing Leads" button in Funnel page (calls backfill)
- [x] Fixed `.model_dump()` crash on dict in server.py gpt_intent_search
- [x] Added `campaign_id` to `GPTIntentSearchRequest` + `LeadDiscoveryRequest` in routes/leads.py
- [x] Ensured `user_id` is stamped on every lead created via `/leads/discover` and `/leads/gpt-intent-search` in both monolith and modular routes

## Completed (April 17, 2026)
- [x] Full rebrand DialGenix → IntentBrain (143+ references)
- [x] New circular logo (hero, navbar, sidebar, login, SEO pages)
- [x] intentbrain.ai domain + SSL
- [x] ElevenLabs Scale upgrade (2M credits)
- [x] Inbound audio regenerated (9 clips, IntentBrain)
- [x] Landing page demo audio regenerated (3 clips)
- [x] Both Twilio numbers configured
- [x] Toll-free verification submitted
- [x] Hero section redesigned (big centered logo)
- [x] All CTAs → pricing (not Calendly)
- [x] PAYG removed, Review Requests add-on added
- [x] BYOL credit packs blocked
- [x] Industry script templates (10 total)
- [x] Campaign Dial Settings
- [x] CSV parser fixed
- [x] BYOK Setup Wizard + Credit Alerts
- [x] Getting Started: ElevenLabs step + FTC/DNC instructions

## Backlog
### 🔴 P0 — Open Bugs (next session priority)
- [ ] **BUG #002 — Conversation state leakage**: Agent loops back to "Thanks for calling IntentBrain..." after booking/qualification. Need to lock stages BOOKING → CONFIRMED → EXIT (no return to greeting).
- [ ] **BUG #003 — Booking SMS not arriving**: `/api/twilio/inbound/sms-number` endpoint exists but deliveries unverified. Add structured logging around Twilio SMS dispatch (parsed phone, Twilio SID, API response, delivery status).

### 🟠 P1 — Coverage Expansion (post-bugs)
- [ ] Expand fast-path with core product features: "live transfers", "voicemail drops", "CRM integration", "Calendly integration", "outbound calling", "do you integrate with HubSpot/Salesforce"
- [ ] Add proper "do you support X" Q&A to brain prompt so legitimate product questions don't get classified as OFF_TOPIC

### 🟠 P1 — Gatekeeper / Callback Flow (NEW — added June 13, 2026)
**Renamed June 13: Deflection Intelligence Engine** — core IntentBrain infrastructure that every vertical playbook will inherit.

---

#### Agent Brain Rules (binding — drive every implementation decision)

**Rule #1 — Reframe the gatekeeper:**
The gatekeeper's primary job is to **protect time**, NOT to reject merchant services. Every prompt, classifier, and pivot script must treat the gatekeeper as a *time guardian*, not an obstacle.

**Rule #2 — Never try to "close" a gatekeeper.**
The goal of any gatekeeper interaction is intelligence capture. Any ONE of the following is a WIN:
- Decision-maker name
- Decision-maker title
- Best callback time
- Direct extension / email
- Transfer to DM

The AI must NEVER pitch product/pricing to a gatekeeper. If pitched at, defer back to intelligence questions.

**Rule #3 — Score every gatekeeper interaction.**
After every gatekeeper turn, the call must be re-scored. The score feeds the Merchant Services Intent Score (and every future vertical's intent score):

| Signal | Points |
|--------|--------|
| Decision-maker name obtained | +15 |
| Direct extension obtained | +25 |
| Email obtained | +15 |
| Best callback time | +10 |
| Transferred to DM | +50 |
| Hard block (no info captured) | -20 |

---

**Philosophy:** The gold isn't the callback — it's the *information*. Even a "rejected" call can score 65 if we extract the right intel.

**Pipeline:**
```
Detect Deflection → Classify Type → Capture Intelligence → Score Intent → Schedule Next Best Action
```

**Deflection Categories (enum):**
- `OWNER_BUSY` — try callback at suggested time
- `OWNER_UNAVAILABLE` — capture best time + decision-maker name
- `NO_COLD_CALLS` — pivot to ask for decision-maker name, best time, processor name
- `SEND_EMAIL` — capture email recipient name + their direct phone, schedule SEND_EMAIL_AND_CALL with waitDays=2
- `GATEKEEPER_BLOCK` — capture as much intel as possible before hangup
- `CALL_BACK_LATER` — schedule callback at requested time
- `SCREENING` ("just tell me what you want") — pivot, then capture decision maker / title / email
- `NOT_INTERESTED` — capture WHY (current processor, contract end date, pain points)
- `ALREADY_HAVE_PROCESSOR` — capture processor name, contract end date, satisfaction level (high-value lead nurture pipeline)
- `UNKNOWN` — fallback to brain freeform

**Intelligence Capture Schema (`call_intelligence` collection):**
```json
{
  "call_sid": "...",
  "lead_id": "...",
  "deflection_type": "NO_COLD_CALLS",
  "decision_maker_name": "Tom",
  "decision_maker_title": "Owner",
  "decision_maker_email": "tom@business.com",
  "decision_maker_direct_phone": "+1...",
  "best_callback_time": "Tuesday 10:00",
  "current_processor": "Square",
  "contract_end_date": "2026-12-01",
  "next_action": "CALL_BACK",
  "next_action_at": "2026-06-17T15:00:00Z",
  "wait_days": 0,
  "gatekeeper_first_name": "Susan"   // for next-call name-drop ("Susan suggested...")
}
```

**Intent Score Points:**
| Signal | Points |
|--------|--------|
| Decision maker name | +15 |
| Email obtained | +10 |
| Best callback time | +10 |
| Direct extension/phone | +25 |
| Email request from gatekeeper | +15 |
| Transferred to DM | +50 |
| Current processor mentioned | +10 |
| Contract end date | +20 |
| Hard block (no info captured) | -20 |

**Gatekeeper Success Score** (boolean checklist tracked per call):
- `decision_maker_name_obtained`
- `email_obtained`
- `best_time_obtained`
- `processor_mentioned`
- `gatekeeper_name_obtained` (for warm follow-up)

→ A call that didn't book a demo can still be a *successful* call.

**Next Best Action Engine (rules table):**
| Deflection Type | Next Action | Default Wait |
|----|----|----|
| OWNER_BUSY | CALL_BACK | 1 day |
| OWNER_UNAVAILABLE | CALL_BACK | use captured best_callback_time |
| NO_COLD_CALLS | SEND_EMAIL_AND_CALL | 3 days |
| SEND_EMAIL | SEND_EMAIL_AND_CALL | 2 days |
| GATEKEEPER_BLOCK | CALL_BACK | 5 days (different time of day) |
| CALL_BACK_LATER | CALL_BACK | use captured time |
| SCREENING | EMAIL_THEN_CALL | 1 day |
| NOT_INTERESTED | NURTURE_DRIP | 30 days |
| ALREADY_HAVE_PROCESSOR | NURTURE_DRIP | until contract_end_date - 60 days |

**Next-call Name-drop Logic:**
On callback, if `gatekeeper_first_name` AND `decision_maker_name` exist, opening line becomes:
> *"Hi [DM_name], this is [AI_name]. I was speaking with [Gatekeeper_name] earlier and she suggested [best_time] would be the best time to reach you."*

**Estimated effort:** 1-2 days (was half-day for basic callback)
- Day 1: Deflection classifier (LLM-driven w/ structured output), intelligence capture state machine, MongoDB collection + indexes, intent score function
- Day 2: Next Best Action engine, background scheduler/dialer worker, name-drop on outbound, dashboard UI for call_intelligence

**Why P1 priority:** Core IntentBrain infrastructure. Every future vertical playbook (merchant services, roofing, insurance, agencies, dental) inherits the same engine. Building this once = 10x leverage.

### P0 - Before Monday Launch
- [ ] Practice setup walkthrough
- [ ] Test CSV upload on live
- [ ] Test Stripe post-payment redirect

### P1
- [ ] Predictive dialer
- [ ] Open Dental RPA integration

### P2
- [ ] Calendly Webhook Sync
- [ ] Payment Overlay Platform

## VPS Deployment
```
cd /var/www/dialgenix && git pull origin main && cd frontend && npm run build --legacy-peer-deps && cd ../backend && pm2 restart dialgenix-backend
```
