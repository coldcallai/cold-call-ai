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

## Completed (June 15, 2026) — Phase 1: UniversalBrain Refactor + MerchantBrain V1 (4 of 5 libraries)
- [x] **Schema locked** (`universal/contracts/{trigger,discovery,transfer,jargon,playbook}.py`):
      - `Trigger -> Objective -> Variations` (reactive, 1-5 variations, ≤30 words)
      - `DiscoveryQuestion` (proactive, primary + variations + softer_version + capture_slots + captures_enum)
      - `TransferDecision` (score-banded), `TransferSignal` (phrase → intent_delta)
      - `playbook_tags` field added everywhere (per founder request)
- [x] **10 Universal engines scaffolded** (`universal/engines/*.py`): Gatekeeper, Discovery, Objection, Qualification, IntentScoring, Callback, Appointment, Transfer, Memory, FollowUp — behavior-only, zero industry strings in conditionals
- [x] **ConversationState** with state-machine guard (`universal/state/conversation_state.py`) — fixes BUG #002 path: CONFIRMED/EXIT are terminal, illegal transitions raise
- [x] **Orchestrator** (`universal/orchestrator.py`) — feature-flagged via `UNIVERSAL_BRAIN_ENABLED=false`, does NOT touch existing server.py inline brain yet
- [x] **MerchantBrain V1 content modules** (`playbooks/merchant_brain/`) — **ALL 5 LIBRARIES SHIPPED (June 15, 2026)**:
      - Gatekeeper V1: **15 triggers** (What's this regarding? / We already have a processor / We handle that internally / Owner isn't available / Take a message / Just send an email / Sales call? / No sales calls / Call back later / Happy with processor / Who are you? / Who referred you? / Too busy / What do you want? / Not interested)
      - Decision Maker V1: 8 triggers
      - Workflow Discovery V1: 10 questions
      - Funding Discovery V1: 10 questions
      - Qualification V1: 8 questions
      - Transfer Logic V1: 3 score bands (0-59 Nurture / 60-79 Appointment / 80+ Live Transfer) + 13 signal boosts
      - Jargon Map V1: 25 entries (settlement_timing → "how quickly deposits hit your account", etc)
- [x] **4 health tests** (`tests/universal/`, `tests/playbooks/`): schema_lock, deletion_independence, no_industry_logic, merchant_brain_content. All PASS locally.
- [x] **Deploy bundle**: `/app/universal_brain_phase1.b64` (30 KB) + `/app/UNIVERSAL_BRAIN_PHASE1_DEPLOY.md` — non-breaking additive deploy to VPS

### Architectural achievements verified by tests:
- ✅ Universal engines run with NoopPlaybook (no MerchantBrain required)
- ✅ No vertical nouns appear in `if/elif/match` statements anywhere in `universal/`
- ✅ Locked schemas detect drift (added/removed fields fail the test)
- ✅ Zero jargon in spoken phrasings (Funding V1 rule enforced)

### Pending before Orchestrator can replace inline brain:
- [ ] Phase 2: wire `server.py` `/api/twilio/inbound/respond` to call `Orchestrator.handle_turn()` when `UNIVERSAL_BRAIN_ENABLED=true`
- [ ] Live-call regression against 888-513-1913
- [ ] Phase 3 prep: Account-layer substitution for `{agent_name}` / `{company_name}` (currently hard-coded as "Sarah" / "ABC Merchant Solutions" in `GK_WHO_ARE_YOU`)

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

### 🟠 P1 — Vertical Playbooks (template + niche)
**Architectural principle (added June 13, 2026):** Playbooks are structured as **universal templates** with **niche overrides**. The Deflection Intelligence Engine, Agent Brain Rules, and gatekeeper handling are shared infrastructure. Only the vertical-specific copy (industry framing, decision-maker title, pain points, pricing anchors) changes per niche.

#### 🏗️ Canonical Architecture (locked June 13, 2026)

```
IntentBrain Core (Universal Agent Brain)       ← Layer 1
├─ Gatekeeper Engine
├─ Discovery Engine
├─ Objection Engine
├─ Qualification Engine
├─ Intent Scoring Engine
├─ Callback Engine
├─ Appointment Engine
├─ Transfer Engine
├─ CRM Memory Engine
└─ Follow-Up Engine

         ↓ inherits ↓

Playbook Layer (Vertical Overrides)            ← Layer 2
├─ MerchantBrain
├─ RoofingBrain
├─ InsuranceBrain
├─ AgencyBrain
├─ DentalBrain
└─ SaaSBrain

         ↓ inherits ↓

Account Customization Layer                    ← Layer 3
(per-ISO / per-agent overrides — different offers, processors, pricing under same playbook)
e.g. MerchantBrain → David's Account (uses Priority, Paysafe, Shift4)
     MerchantBrain → Agent Smith's Account (uses Fiserv, Clearent, NMI)

         ↓ inherits ↓

Campaign Override Layer                        ← Layer 4 (added June 13, 2026)
(per-campaign sub-vertical targeting within an account)
e.g. MerchantBrain → David's Account → Dental Campaign (dental-specific objections, average ticket size)
     MerchantBrain → David's Account → Restaurant Campaign (tip handling, late-night surcharges)
     MerchantBrain → David's Account → Auto Repair Campaign (B2B mix, parts vs. labor pricing)
     MerchantBrain → David's Account → Retail Campaign (high card-present %, holiday surge)
```

**Four-Layer Inheritance Model:**
1. **Universal Brain** — built once, shared by all (10 engines, *behavior only, zero industry nouns*)
2. **Playbook Brain** (e.g., MerchantBrain) — industry knowledge, industry objections, industry qualification, industry scoring weights
3. **Account Customization** — per-ISO/per-agent offer copy, processor preferences, pricing anchors
4. **Campaign Override** — per-campaign sub-vertical targeting within an account (e.g., dental vs. restaurant vs. auto repair, all running under one MerchantBrain account)

#### 📝 MerchantBrain Content Schema (added June 15, 2026)

**The N responses per trigger are NOT alternatives — they are objective-paths.** MerchantBrain selects which response to use by inspecting `conversation_state` and choosing the objective that fills the highest-priority missing field.

**Canonical schema per trigger (objection/deflection/statement):**
```yaml
trigger: "We already have a processor"
possible_meanings:
  - SCREENING
  - INTERNAL_MANAGEMENT
  - GENUINE_INCUMBENT
  - BRUSH_OFF
objectives:
  DECISION_MAKER_DISCOVERY:
    intent_delta: 0
    next_state: DECISION_MAKER_DISCOVERY
    variations:
      - "That makes sense. Who typically oversees that relationship?"
      - "Got it. Is that something the owner handles personally?"
      - "Who usually evaluates those options when they come up?"
  PAIN_DISCOVERY:
    intent_delta: +10
    next_state: PAIN_DISCOVERY
    variations:
      - "What do you think they like most about the current setup?"
      - "Has that arrangement been working about the way they'd hoped?"
  CALLBACK:
    intent_delta: +5
    next_state: CALLBACK_SCHEDULED
    variations:
      - "When is usually the best time to catch them?"
      - "What's the best way to reach them?"
  TRANSFER:
    intent_delta: +50
    next_state: TRANSFERRING
    variations:
      - "Is there a chance I could get 60 seconds with them now?"
      - "Would it help if I held while you check?"
```

**Rule:** 2-3 natural variations per objective. NOT 20. The AI picks the **objective** from state; within the objective, it picks one variation (round-robin or random) to avoid sounding scripted.

**Why 2-3, not 20:** Elite reps don't memorize 300 objections × 20 responses. They think *"What do I need next?"* — pick objective → speak naturally. The library should mirror that, not become an unmaintainable spreadsheet.

**Selection logic (UniversalBrain — owns the behavior):**
```
1. Read current conversation_state (e.g. {decision_maker_known: false, pain_known: false, ...})
2. Match trigger from playbook
3. Pick the objective that fills the highest-priority missing slot
4. Emit the response for that objective
5. Update state + intent_score per objective's metadata
```

**Forbidden pattern (do not implement):**
```python
random.choice(responses)   # ❌ AI script reader, not Agent Brain
```

**Required pattern:**
```python
objective = decide_objective(state, trigger.objectives)   # ✅ Agent Brain
response = trigger.objectives[objective].response
```

When founder ships the 10-response sets, **each response will be tagged with the objective it serves**, not just listed as alternatives.


Every pull request must answer exactly ONE of: **UniversalBrain / Playbook / Account / Campaign**. No "A + B". No multi-layer answers. If it can't be answered in one letter, the change is wrong.

#### 🚨 Binding Architectural Rule: "UniversalBrain owns behavior. Playbooks own domain knowledge."

**Refined June 13, 2026** (from prior wording "no industry nouns" — too strict, since industry strings can legitimately appear as *data*):

UniversalBrain MUST NOT contain industry-specific **business logic**. Industry strings appearing as *data* are fine; industry strings appearing in *conditionals* are violations.

**✅ Allowed in UniversalBrain** (industry as data):
```python
lead = {"industry": "merchant_services"}   # Data — OK
def score(lead, weights): ...              # Behavior — OK
```

**❌ Forbidden in UniversalBrain** (industry as logic):
```python
if processor == "Square":          # ❌ belongs in MerchantBrain
    increase_intent_score()

if industry == "roofing":          # ❌ belongs in RoofingBrain
    ask_storm_question()

if vertical == "dental":           # ❌ belongs in DentalBrain
    ask_insurance_acceptance()
```

**Why the wording matters:** "No industry nouns" would forbid even harmless data tagging. The real boundary is **behavior vs. domain knowledge**:
- UniversalBrain owns: state machines, scoring math, callback scheduling, transfer logic, memory I/O, prompt orchestration
- Playbooks own: industry questions, industry objections, industry scoring weights, industry-specific response copy

#### 🧪 Future Architectural Health Test

**Six months from now, ask:** *"Could you delete MerchantBrain entirely and have IntentBrain still run?"*

- ✅ **Healthy architecture:** Yes. It would still call, qualify, schedule, transfer, remember, and follow up — just without any merchant-services-specific knowledge. Generic placeholders ("Hi, I'm calling to learn about your business") would fill in.
- ❌ **Leaky architecture:** No. Core calling logic breaks because merchant logic leaked into UniversalBrain.

If a future code change ever causes core engines to fail when a playbook is removed → the boundary has been violated and needs immediate refactoring before the next vertical is added.

#### Why MerchantBrain is *content*, not *code* (architectural goal)

If MerchantBrain v1 ships as a collection of:
- Questions (qualifying / discovery prompts)
- Responses (objection handlers, deflection pivots)
- Scoring rules (weights per signal)
- Industry knowledge (processor names, terminology, pricing models)
- Transfer rules (when to escalate to human)

…stored as **structured data** (JSON / Markdown / DB rows) rather than custom Python code, then every subsequent playbook (RoofingBrain, InsuranceBrain, etc.) becomes a *content authoring job*, not an engineering job. That's the 10x leverage win.

#### Refactor-First Decision (confirmed June 13, 2026)
> "Architecture mistakes are cheap to fix before content and expensive to fix after content."

**Sequencing:**
1. ✅ **FIRST:** Extract existing inline brain logic from `server.py` lines ~11648-11720 into the 10 universal engines
2. ✅ **THEN:** Build MerchantBrain as the first playbook on the clean architecture
3. ✅ **THEN:** Import all manually-authored MerchantBrain responses
4. ✅ **THEN:** Add Account Customization layer
5. ✅ **THEN:** Add Campaign Override layer (or stub it in advance as a placeholder, even if unused for v1)

**Rationale:** Importing 5,000 lines of MerchantBrain content into the current monolithic structure would hardwire merchant logic into core logic. Six months later, RoofingBrain / InsuranceBrain / AgencyBrain would each require ripping that out. The refactor is 2-3 days of work that saves 2-3 weeks per future vertical.

#### Three-Layer Inheritance Model (DEPRECATED — superseded by 4-layer above):
1. **Universal Brain** — built once, shared by all
2. **Playbook Brain** (e.g., MerchantBrain) — industry knowledge, industry objections, industry qualification, industry scoring weights
3. **Account Customization** — per-ISO/per-agent offer copy, processor preferences, pricing anchors

#### What stays UNIVERSAL (never vertical-specific):
- ✅ Deflection Detection
- ✅ Callback Scheduling
- ✅ Gatekeeper Classification
- ✅ Decision-Maker Identification
- ✅ CRM Memory
- ✅ Follow-Up Logic
- ✅ Conversation Summaries
- ✅ Intent Scoring Framework (the math; the weights per signal are universal)
- ✅ Transfer Framework

#### What a Playbook contains (and ONLY this):
| Layer | Example: MerchantBrain |
|---|---|
| Industry Knowledge | Clover, Square, Toast, Fiserv, Paysafe, Shift4, NMI, Cash Discounting, Dual Pricing, Level 2/3, Funding, Residuals, Schedule A |
| Industry Objections | "Already have a processor", "Friend handles processing", "We already reviewed rates", "We use Square/Clover" |
| Industry Qualification | Monthly volume, Average ticket, Max ticket, Card-present %, Current processor |
| Industry Scoring | Intent Score, Savings Score, Workflow Score, Funding Score |

Universal engine asks the question. Playbook supplies the *content* of the question/response. Example:
- Universal Gatekeeper Engine detects: "We already have a processor"
- MerchantBrain override response: industry-specific pivot referencing rate comparisons / Schedule A
- RoofingBrain override response: industry-specific pivot referencing storm season / supplier pricing
- AgencyBrain override response: industry-specific pivot referencing campaign performance

**Same framework. Different responses.**

#### Naming conventions
- **Internal (code)**: `UniversalBrain`, `MerchantBrain`, `RoofingBrain`, `InsuranceBrain`, `AgencyBrain`, `DentalBrain`, `SaaSBrain`
- **External (customer-facing)**: "IntentBrain Merchant Services **Playbook**" — *"Playbook"* reads better to customers than *"Brain"*

#### Why this matters
Building five separate vertical systems = five separate maintenance nightmares, five prompt trees, five qualification engines, five duplicate gatekeeper logics that drift apart over time. Build the engines once → 10x leverage on every future vertical → consistent quality across all niches → faster vertical rollout (a new vertical becomes ~2 days of *content* work, not 2 weeks of engineering).

#### Playbook Roadmap
- [ ] **MerchantBrain** (Merchant Services) — 🔨 IN PROGRESS by founder, all agent responses being authored/edited manually before code import
- [ ] AgencyBrain (Agencies) — future
- [ ] RoofingBrain (Roofing) — future
- [ ] InsuranceBrain (Insurance) — future
- [ ] DentalBrain (Dental practices) — future
- [ ] SaaSBrain (SaaS sales) — future

**Each playbook will include:**
- Discovery script (opener + qualifying questions) — *industry-specific copy only*
- Qualification logic (BANT / pain matrix) — *industry-specific fields only*
- Objection handlers — *industry-specific copy only*
- Gatekeeper deflection responses (uses universal engine, supplies industry-specific pivot copy)
- Vertical-specific intent score weights (e.g., MerchantBrain weights "monthly volume" heavily; RoofingBrain weights "storm damage" heavily)

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

## Completed (Feb 25, 2026) — Outbound Human-Greeting Gate (Phases A-E) ✅
**Fix:** Outbound AI was speaking before the human said "hello" and was sometimes falling back to robotic Twilio `<Say>`. Now structurally impossible.

**Shipped:**
- `backend/routes/twilio_outbound.py` — NEW router with 5 endpoints:
  - `POST /api/twilio/outbound/answer` — AMD `AnsweredBy` gate. Silent `<Redirect>` for human/unknown, silent `<Hangup/>` for machine_*/fax. **Never emits Say/Play.**
  - `POST /api/twilio/outbound/greeting` — Silent `<Gather input="speech" speechTimeout="auto">`. **Empty Gather body** — no Say/Play children.
  - `POST /api/twilio/outbound/respond` — Classifies first utterance (`classify_speech`). Voicemail/IVR → silent hangup. DNC request → write `db.dnc_list` + optional ElevenLabs ack via `<Play>` + hangup. Human → emit `<Play>{backend_url}/api/tts/audio/{id}</Play>` (opener) then handoff `<Gather action="/api/twilio/inbound/respond">`.
  - `POST /api/twilio/outbound/status` — Final disposition writer.
  - `GET /api/tts/audio/{id}` — Streams ElevenLabs MP3 bytes from in-memory `audio_store` (media_type=audio/mpeg).
- `backend/routes/twilio_outbound.py::place_outbound_call()` — Dialer entry point. Checks `db.dnc_list` BEFORE generating TTS/dialing. Creates Twilio call with `url=` callback (NEVER inline TwiML), `machine_detection="Enable"`, async_amd="false". Persists session in `db.outbound_sessions`.
- `backend/tests/test_twilio_outbound_gate.py` — 9 regression tests + 1 classifier unit test. **All 10 pass.** Tests enforce:
  1. URL callback, not inline TwiML
  2. Opener never in initial create() payload
  3. /answer never speaks
  4. /answer only redirects silently
  5. /greeting waits for human speech (silent Gather)
  6. ElevenLabs `<Play>` is used; Twilio `<Say>` never used for AI voice
  7. Voicemail/IVR classified → silent hangup, opener NOT played
  8. DNC request writes to `db.dnc_list`
  9. Dialer skips DNC numbers BEFORE Twilio/ElevenLabs calls
- `backend/server.py` — additive mount block after `app.include_router(api_router)`. **Legacy inbound brain untouched.**
- `backend/run_dental_experiment.py` — rewritten to use `twilio_outbound.place_outbound_call()`. Inline TwiML eliminated.
- `backend/conftest.py` + `backend/tests/__init__.py` — pytest path setup so `universal/` resolves correctly.

**Verified by testing agent (iteration_19):** 9/9 pytest, 6/6 live HTTP smoke checks, legacy inbound endpoints still 200.

**Open follow-up (non-blocking):**
- Set `BACKEND_URL` in `/app/backend/.env` (or VPS .env) so `<Play>` URLs are absolute — currently empty, mount log shows `backend_url=MISSING`. Twilio still resolves relative paths against the webhook host.

## Completed (Feb 25, 2026) — Outbound Pre-flight Self-Test ✅
**Purpose:** Regression-safe pre-flight before every prospect batch. Verifies all 9 hard rules of the gate without burning Twilio minutes or ElevenLabs credits.

**Shipped:**
- `backend/scripts/outbound_selftest.py` — single-file pre-flight. Runs in two modes:
  - **Structural (default):** Fakes Twilio + ElevenLabs. Exercises every outbound endpoint via `httpx.AsyncClient` + `ASGITransport` against the real router code. Validates TwiML structure, classifier, DNC write+skip, opener exact phrasing. 10 checks total.
  - **`--dial` (live):** Places ONE real Twilio call to `888-513-1913` (or `--phone`). Pins the opener to: `Hi, this is Sarah. Quick question — who handles patient payment workflows for the practice?`. Polls `db.outbound_sessions` for opener_played / final disposition.
- **Hard rule enforced in script:** if structural checks fail, the script REFUSES to place a live dial (`Structural checks FAILED — refusing to place live dial.`).
- **Report:** Console pass/fail + `/tmp/outbound_selftest_report.json` with call SID, endpoint path, disposition, ElevenLabs audio URL per check, and `say_detected` flag per check.
- **Idempotent:** unique per-run setup phone (`+1555111{uuid}`), try/finally cleanup, and broader regex sweep of any `+1555111\d{7}` residue from prior runs. Verified across 3 consecutive runs with zero DB residue (iteration_21).
- `routes/twilio_outbound.py::place_outbound_call()` — added `opener_text_override` kwarg so the self-test can pin the founder phrasing without going through CampaignSession.

**Verified by testing agent (iteration_21):** 3/3 consecutive runs exit 0, 10/10 checks each, pytest 9/9, legacy inbound endpoints still defined.

**Operator usage on VPS:**
```
cd /var/www/dialgenix/backend
PYTHONPATH=$PWD python3 scripts/outbound_selftest.py            # structural only
PYTHONPATH=$PWD python3 scripts/outbound_selftest.py --dial     # also dials 888-513-1913
# exit 0 → safe to dial prospects; exit 1 → DO NOT DIAL
```

## Completed (Feb 25, 2026) — Deploy-Time Safety Gate ✅
**Purpose:** Make it IMPOSSIBLE to accidentally redeploy a version where the outbound gate is broken. Three layers:

**1. Runtime kill switch (`routes/twilio_outbound.py`)**
- New: `is_outbound_disabled()` reads a sentinel file (default `<backend>/OUTBOUND_DISABLED`, overridable via env `OUTBOUND_KILL_SWITCH`).
- `place_outbound_call()` checks it FIRST. If present → returns `{"ok": False, "blocked": "outbound_disabled"}`. **Zero Twilio/ElevenLabs spend** while disabled.
- New regression test `test_10_kill_switch_blocks_outbound` proves it (now 11 tests total).

**2. Deploy preflight wrapper (`backend/scripts/deploy_preflight.sh`)**
- Runs `scripts/outbound_selftest.py` (structural only, never `--dial`).
- Exit 0 → removes `OUTBOUND_DISABLED`, prints `OUTBOUND SELF-TEST PASSED — live dialing allowed`.
- Exit 1 → writes `OUTBOUND_DISABLED` with `selftest_failed`/`exit_code`/`at` timestamp, prints the EXACT mandated banner: `OUTBOUND SELF-TEST FAILED — LIVE DIALING DISABLED`, exits 1.
- **No secrets ever printed.** `set -u` only — no `set -x`. No `cat`/`echo`/`grep`/`printenv` on .env.
- Fail-closed if selftest script itself is missing.
- Operator escape hatch: `FORCE_ENABLE=1 bash scripts/deploy_preflight.sh` (loud, still surfaces exit 1).

**3. GitHub Action (`.github/workflows/outbound_preflight.yml`)**
- Triggers on push/PR touching outbound surface.
- Runs `pytest tests/test_twilio_outbound_gate.py` then `bash scripts/deploy_preflight.sh`.
- Uses **mongomock fallback** when `MONGO_URL` unset → hermetic CI, no production DB access.
- **No secrets referenced** in `env:` blocks (no `secrets.TWILIO_*`, no `secrets.ELEVENLABS_*`).
- Uploads `/tmp/outbound_selftest_report.json` as artifact on every run.

**Verified by testing agent (iteration_22):**
- ✅ 11/11 pytest pass
- ✅ PASS path: exit 0, kill switch removed, "PASSED" banner
- ✅ FAIL path: exit 1, kill switch written with timestamp, EXACT banner "OUTBOUND SELF-TEST FAILED — LIVE DIALING DISABLED"
- ✅ Runtime enforcement: with sentinel present, `place_outbound_call` returns blocked with zero API calls
- ✅ mongomock fallback works when MONGO_URL unset (verified by moving .env aside)
- ✅ No secrets leaked (no `set -x`, no `--dial` anywhere, no `secrets.*` in YAML)
- ✅ Legacy `/api/twilio/inbound*` endpoints still at server.py:11226+ — untouched
- ✅ Idempotency: 3 consecutive deploy_preflight runs exit 0, zero DNC residue

**Operator usage on VPS post-deploy:**
```
cd /var/www/dialgenix/backend
bash scripts/deploy_preflight.sh && pm2 restart dialgenix-backend
# If structural fails, OUTBOUND_DISABLED is written and the dialer refuses every dial
# until the sentinel is removed (auto by next successful preflight, or manually after fix).
```

## Completed (Feb 25, 2026) — Admin Status Endpoint ✅
**`GET /api/admin/outbound-status`** — surfaces the outbound dialer's safety state for the admin UI / uptime monitors. No SSH required.

**Response shape (7 keys, no secrets):**
```json
{
  "kill_switch_present": true,
  "outbound_disabled": true,
  "last_selftest_at": "2026-02-25T19:43:37Z",
  "last_selftest_passed": true,
  "last_selftest_report_path": "/tmp/outbound_selftest_report.json",
  "can_live_dial": false,
  "reason": "OUTBOUND_DISABLED sentinel present — last deploy pre-flight failed."
}
```

**Hard-coded leak guards (verified by tests + by hand-crafted leak curl):**
- Whitelist reader pulls ONLY `passed`, `finished_at`, `mode` from the report.
- Strips: `checks`, `phone`, `elevenlabs_audio_url`, all raw provider data.
- Never reads `.env`, never exposes API keys / URLs with tokens.

**Decision matrix:**
| State | `can_live_dial` |
|---|---|
| Sentinel present | **false** (sentinel wins regardless of report) |
| No report file | **false** |
| Report passed=false | **false** |
| Report missing/malformed | **false** |
| Report passed=true + no sentinel | **true** |

**Tests:** 5 new (`test_11a..e`) — sentinel blocks, passing allows, missing blocks, failing blocks, malformed treated as unknown. Total suite now **16/16 passing**.

**Verified by testing agent (iteration_23):** All 5 live scenarios curl-verified, hand-crafted leak test passes (phone numbers, API keys, BACKEND_URL, raw provider response, audio URLs, checks array — none leak through), runtime-state consistency confirmed.

**Operator note:** endpoint is intentionally unauthenticated (read-only metadata, no secrets). In production, reverse-proxy auth layer fronts the admin surface.

## Completed (Feb 26, 2026) — AI Operations Center foundation ✅
**Purpose:** Replace the one-off banner idea with the foundation of an Ops dashboard. Every future engine plugs into the same UI via a single reusable contract.

**Shipped:**
- `frontend/src/components/StatusCard.jsx` — reusable health card. Polls every 30s, pauses while tab hidden, refreshes on tab refocus. Maps `{safe, warn, down, unknown}` → `{emerald, amber, rose, slate}` styling. Props: `{title, icon, fetchStatus, intervalMs, testId, helpHref}`. Exposes `formatRelativeTime` helper.
- `frontend/src/components/cards/OutboundDialerStatusCard.jsx` — first concrete card. Polls `/api/admin/outbound-status`, translates response into the StatusCard contract.
- `frontend/src/pages/OpsCenterPage.jsx` — `/app/ops` page with a `cards` array. **Adding a new engine card = 1 component + 1 array entry.** Header `AI Operations Center` with Activity icon, sub-copy *"Live health of every engine that powers IntentBrain. Cards auto-refresh every 30 seconds."*
- `frontend/src/App.js` — route `/app/ops` registered inside the protected layout.
- `frontend/src/components/Sidebar.jsx` — sidebar entry "Ops Center" with Activity icon (between Analytics and CRM Integrations).

**Card contract for future engines** — implement an async function returning:
```js
{
  status: 'safe' | 'warn' | 'down' | 'unknown',
  label:  'SAFE' | ...,
  reason: string,
  metrics: [{ label, value }, ...]
}
```
Render with `<StatusCard title=... icon=... fetchStatus=... testId=... />`. That's it.

**Planned future cards (documented in OpsCenterPage.jsx, NOT built):**
- ElevenLabs (API reachable, voice latency, last synth)
- OpenAI (API reachable, model, last completion)
- Twilio (Voice, SMS, webhook health)
- Prospecting Engine (last run, prospects loaded, dedup complete)
- Campaign Engine (active campaign, calls today, transfers, DNC count)
- UniversalBrain (active brain, version, loaded successfully)
- System Health (backend online, DB connected, queue healthy)

**Verified by testing agent (iteration_24):**
- ✅ 11/11 acceptance criteria
- ✅ SAFE state (data-status="safe", badge "SAFE", all 4 metrics populated)
- ✅ DISABLED state (data-status="down", badge "DISABLED", sentinel reflected)
- ✅ Manual Refresh fires `GET /api/admin/outbound-status`
- ✅ Responsive grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`)
- ✅ No secrets in frontend bundle (`REACT_APP_BACKEND_URL` only)
- ✅ All interactive + info elements carry unique `data-testid` per platform rules

## Completed (Feb 26, 2026) — Ops Center: ElevenLabs card (second proof-of-pattern) ✅
**Backend `GET /api/admin/elevenlabs-status`** — strict 6-key whitelist response:
```json
{
  "api_reachable": true,
  "last_synth_at": "...",
  "last_synth_latency_ms": 420,
  "last_successful_synth_at": "...",
  "status": "safe|warn|down|unknown",
  "reason": "..."
}
```
**No secrets exposed.** No `api_key`, no `voice_id`, no `xi-api-key`, no `bearer`, no raw provider responses.

**Strategy: cache-first, no synth on poll.**
- Primary: `_record_synth_event()` is called inside `_default_eleven_synthesize` after every production synth attempt (success + failure), updating an in-memory `_ElevenHealth` cache with `last_synth_at`, `last_synth_latency_ms`, `last_successful_synth_at`.
- Fallback: `_maybe_live_ping_elevenlabs()` — cheap `voices.get_all()` call, **rate-limited to once per 10 minutes** (`_MIN_PING_INTERVAL_SECONDS=600`). Short-circuits entirely when a recent successful synth proves reachability.
- **Never synthesizes audio on poll.** `test_12e` wires an exploding `synth_fn` that would fail if invoked — confirmed by 21/21 tests + 10 rapid live curls producing zero synth log entries.

**Status mapping:**
- `safe`: API reachable, recent success within 1h, latency < 3000ms
- `warn`: API reachable but no synth yet, OR synth stale > 1h, OR latency > 3000ms
- `down`: API unreachable
- `unknown`: insufficient data

**Frontend `ElevenLabsStatusCard.jsx`** — 55-line wrapper around the reusable `StatusCard`. Displays: API reachable / Last synth / Last latency / Last success. Polls every 30s, same as Outbound card. Latency display guards 0 → `—` so the card doesn't show misleading `0 ms` before any synth has happened.

**Ops Center now displays 2 cards side-by-side:** Outbound Dialer + ElevenLabs. Adding the 3rd card (OpenAI / Twilio / Prospecting / Campaign Engine / UniversalBrain / System Health) is one ~50-line component + one entry in the `cards` array.

**5 new tests (12a–12e). Total suite now 21/21.**
- `12a` safe after successful synth (no live ping issued — cache wins)
- `12b` down when API unreachable
- `12c` warn on high latency
- `12d` response contains no secrets (api_key, xi-api-key, voice_id, bearer, sk-, authorization, .env — all forbidden)
- `12e` no synth loop: 20 rapid polls → 0 synth invocations + voices.get_all called ≤1×

**Verified by testing agent (iteration_25):** 100% backend + 100% frontend; all acceptance criteria pass.

## Completed (Feb 26, 2026) — Deploy preflight venv autodetection (P0 fix) ✅
**Reported by operator on VPS:** `ModuleNotFoundError: No module named 'fastapi'` when running `bash scripts/deploy_preflight.sh`. System `python3` lacks the app deps; pm2 runs the backend from a virtualenv.

**Fixed:** `deploy_preflight.sh` now auto-detects a python interpreter that has `fastapi` AND `twilio` importable. Search order:
1. `$OUTBOUND_PYTHON` env override
2. `backend/venv/bin/python{3,}` + `backend/.venv/bin/python{3,}`
3. `<repo_root>/venv/bin/python{3,}` + `<repo_root>/.venv/bin/python{3,}`
4. System `python3` / `python`

If none qualify → writes `OUTBOUND_DISABLED` with first-line tag `selftest_python_missing`, prints the FATAL hint (`pm2 describe dialgenix-backend | grep exec interpreter`), prints the mandated banner, exits 1. Fail-closed contract preserved.

Probe redirects BOTH stdout AND stderr to `/dev/null` — zero info leakage.

**Verified by testing agent (iteration_26):**
- ✅ Happy path auto-detects `/root/.venv/bin/python3`, exit 0, PASSED banner
- ✅ `OUTBOUND_PYTHON` override honored
- ✅ Fail-closed path writes correct sentinel + mandated banner + exit 1
- ✅ Secret hygiene intact (no `set -x`, no `--dial`, no `.env` reads)
- ✅ Full deploy chain E2E green (pytest 21/21, backend restart, both admin endpoints HTTP 200)
- ✅ `install_mount_block.py` idempotent (re-run prints "Already installed")

## Completed (Feb 26, 2026) — Phase D operator wrapper ✅
**`scripts/run_selftest.sh`** — one-line invocation for both structural pre-flight and Phase D live dial. Single source of truth for python detection (refactored out into `scripts/_lib_python_finder.sh`, now consumed by both `deploy_preflight.sh` and `run_selftest.sh`).

**Behavior:**
- `bash scripts/run_selftest.sh` → structural mode, no live dial.
- `bash scripts/run_selftest.sh --dial` → live call (only when YOU type `--dial`).
- All operator args pass through verbatim. `--dial` is **NEVER auto-injected** by the wrapper.
- Exits with the SAME code as `outbound_selftest.py` (verified with stub-at-exit-7).
- Prints which python was selected so you always know what just ran.
- Fails closed (exit 1, no live call attempted) if no fastapi-capable python is found — even when operator passes `--dial`.

**Verified by testing agent (iteration_27):** 10/10 cases pass.
- ✅ deploy_preflight refactor preserves identical behavior
- ✅ Structural mode prints correct banners, exit 0
- ✅ Stub-replaced selftest confirms argv = `[]` without --dial, `[--dial, --phone, +18885131913]` with operator args, `[--foo, bar]` for arbitrary args
- ✅ Exit 7 propagated (no normalization)
- ✅ Fail-closed when no usable python — `--dial` never reaches anything
- ✅ Probe suppresses stdout+stderr; zero secret leakage
- ✅ Shared finder requires BACKEND_DIR (graceful FATAL if missing)
- ✅ Full E2E chain green (preflight → run_selftest → backend restart → `/api/admin/outbound-status` 200 → pytest 21/21)

## Completed (Mar 4, 2026) — RankTrust → IntentBrain Handoff Webhook (Phase 3) ✅
**`POST /api/webhooks/ranktrust/handoff`** — receives RankTrust AI Call Packages, stores them, schedules the AI call after `delay_seconds`, dials via the outbound gate, and POSTs the result back to RankTrust.

**Auth:** HMAC-SHA256 preferred (`X-RankTrust-Signature: sha256=<hex>` with `RANKTRUST_HANDOFF_SECRET`), token fallback (`?token=` OR `X-RankTrust-Token` header with `RANKTRUST_HANDOFF_TOKEN`). Constant-time compare via `hmac.compare_digest`. Fails 401 when nothing is configured (fail-closed).

**Packet schema (Pydantic-validated):**
```json
{
  "packet_id": "unique-id",
  "business": {"name": "...", "industry": "...", "phone": "+1E164", "website": "..."},
  "revenue_opportunity": 45000.0,
  "close_probability": 0.62,
  "best_offer": "...",
  "sales_script": {"opener": "...", "key_points": [...], "call_to_action": "..."},
  "objections": [{"objection": "...", "response": "..."}],
  "conversation_strategy": "...",
  "delay_seconds": 300,
  "callback_url": "https://...",
  "callback_token": "..."
}
```

**Flow:**
1. Verify auth → 401 on failure (no DB write).
2. Validate + persist to `db.ranktrust_handoffs` (idempotent on `packet_id`).
3. Missing phone → `status='needs_phone'`, immediate callback with reason, no scheduled call. **Non-crashing** (RankTrust can hand off packets even before every prospect has clean phone data.)
4. Valid phone → persist `db.ranktrust_scheduled_calls` row with `target_at = now + delay_seconds`.
5. Background scheduler polls every 30s. When due, claims the job atomically, calls `place_outbound_call()` — respects `OUTBOUND_DISABLED` sentinel + `db.dnc_list`.
6. Outcomes: `dial_placed`, `blocked_outbound_disabled`, `blocked_dnc`, `needs_phone`, `failed`. Every terminal outcome fires a callback to RankTrust.

**Callback contract:** POST JSON `{packet_id, outcome, detail, at}` with `Authorization: Bearer <callback_token>`. Packet-level `callback_url`/`callback_token` override env `.env` defaults. **Body never contains** `callback_token` or HMAC secret (only the Authorization header carries the bearer).

**Hard gates preserved:**
- `OUTBOUND_DISABLED` kill switch → scheduler still claims job but `place_outbound_call` refuses; RankTrust gets `blocked_outbound_disabled` callback.
- `db.dnc_list` → `blocked_dnc` callback.
- Callback body: strict allowlist, redacts `callback_token`.
- Public GET response: `_public_view()` explicitly pops `callback_token`.

**12 regression tests. 33/33 combined with outbound gate suite.**

**Verified by testing agent (iteration_28):** 100% backend. Live auth gate returns 401 fail-closed with zero DB writes when secrets unconfigured. No secret leakage in logs. Legacy `/api/twilio/inbound*` + `/api/tts/generate` untouched.

**Operator env vars to configure for production:**
```
RANKTRUST_HANDOFF_SECRET=<random 32+ char>   # HMAC secret (preferred)
RANKTRUST_HANDOFF_TOKEN=<random 32+ char>    # Shared-token fallback
RANKTRUST_CALLBACK_URL=https://ranktrust.io/api/webhooks/intentbrain   # server-side default
RANKTRUST_CALLBACK_TOKEN=<random 32+ char>   # server-side default
```

## Completed (Mar 4, 2026) — E2E test helper: `send_test_packet.sh` ✅
**Purpose:** operator-friendly one-liner to fire a real RankTrust handoff packet from the VPS without manual HMAC math or secret handling.

**`backend/scripts/send_test_packet.sh`:**
- Sources the shared `_lib_python_finder.sh` (same venv autodetect as deploy_preflight.sh)
- Uses `python-dotenv` to read `RANKTRUST_HANDOFF_SECRET` / `RANKTRUST_HANDOFF_TOKEN` from `.env` (never `cat`/`echo`/`grep`)
- Builds a canonical test packet: business_name=`IntentBrain Demo AI`, phone=`+18885131913` (operator's demo-AI-answered line), delay=60s, unique `test-e2e-<epoch>-<uuid8>` packet_id
- HMAC-signs when secret present, else `?token=` fallback
- Prints ONLY response status + JSON. Zero secret / HMAC-hex leakage
- Flags: `--phone`, `--delay`, `--url`

**Verified by testing agent (iteration_29):**
- ✅ 33/33 pytest regression still green
- ✅ Fails-closed with clear FATAL when no secret configured; zero HTTP request, zero DB write
- ✅ HMAC happy path → HTTP 200 + `status="scheduled"` + `scheduled_call_id` + zero secret leakage
- ✅ Token fallback path → HTTP 200 (known limitation: uvicorn access log captures query string — documented)
- ✅ Back-to-back runs generate unique packet_ids; `replayed=false` each time
- ✅ Rows correctly appear in `db.ranktrust_handoffs` (status=scheduled) + `db.ranktrust_scheduled_calls` (status=pending)
- ✅ Cleanup via `python-dotenv unset_key` returns webhook to 401 fail-closed

**Operator usage on VPS (after configuring `RANKTRUST_HANDOFF_SECRET`):**
```
bash /var/www/dialgenix/backend/scripts/send_test_packet.sh                # +18885131913, delay 60
bash scripts/send_test_packet.sh --phone +1XXXXXXXXXX --delay 300
curl -s http://localhost:8001/api/webhooks/ranktrust/handoff/<packet_id> | python3 -m json.tool
```

## VPS Deployment
```
cd /var/www/dialgenix && git pull origin main && cd frontend && npm run build --legacy-peer-deps && cd ../backend && bash scripts/deploy_preflight.sh && pm2 restart dialgenix-backend
```



## Completed (Feb 2026) — RankTrust → IntentBrain Baseline Timeline (Read-Only Diagnostic)
- [x] Added `GET /api/webhooks/ranktrust/timeline/{packet_id}` — merges `ranktrust_handoffs`,
      `ranktrust_scheduled_calls`, and `outbound_sessions` into a single ordered lifecycle
      with 10 canonical stages: `packet_received`, `packet_validated`, `queued`, `delay_target`,
      `dial_started`, `answered`, `greeting_detected`, `ai_conversation_started`, `call_ended`,
      `callback_sent`. Each stage carries ISO timestamp + `elapsed_from_start_seconds`.
- [x] Added `?format=markdown` variant returning a copy-paste baseline table for chat/PR notes.
      No secrets, no callback_tokens, no HMAC values ever emitted (redacted at write time).
- [x] Read-only + additive: no writes, no legacy brain edits, no new features, no behavior
      changes to outbound gate / scheduler / callback path.
- [x] Docs at `/app/docs/RANKTRUST_INTENTBRAIN_BASELINE.md` — sequence explanation, capture
      instructions (curl one-liners), interpretation guide, failure-mode → subsystem mapping,
      baseline template to fill in after first live E2E.
- [x] pytest coverage (43/43 passing): 404 on unknown packet, partial pre-dial timeline,
      full happy-path with monotonic timestamps + canonical stage ordering, markdown format
      secret-leak assertion.

**Operator usage on VPS (after live E2E completes):**
```
BASE=https://intentbrain.ai
PACKET_ID=pkt-live-test-001
curl -sS "$BASE/api/webhooks/ranktrust/timeline/$PACKET_ID" | jq .
curl -sS "$BASE/api/webhooks/ranktrust/timeline/$PACKET_ID?format=markdown" \
  > docs/baselines/${PACKET_ID}.md
```

## Scope Freeze (still in effect, Feb 2026)
Development is frozen until user completes:
1. Phase D live self-test on VPS (`bash scripts/run_selftest.sh --dial`)
2. RankTrust E2E packet (`bash scripts/send_test_packet.sh`) + baseline capture via timeline endpoint
3. Rotation of leaked OpenAI + Stripe API keys

Post-unfreeze priority order:
1. SerpAPI live prospecting (replace mock data)
2. Stripe Live mode toggle
3. 3–5 agency validation sessions
4. Phase 2 UniversalBrain wiring
