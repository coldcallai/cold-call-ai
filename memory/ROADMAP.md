# IntentBrain Implementation Roadmap

**Last updated:** June 15, 2026 (Phase 1 scaffold + MerchantBrain V1 content shipped to /app; awaiting VPS deploy + Gatekeeper V1 resend)
**Format:** Implementation-ready. Each phase lists the exact files to touch, the patch approach, and the VPS commands. PRD.md remains the spec/why; this is the how/when.

---

## PHASE 0 — Outstanding Production Bugs (do these BEFORE Phase 1 refactor)

### 0.1 — BUG #003: SMS booking delivery failure
**Status:** Root-caused June 13. Twilio error 30034 (A2P 10DLC not registered for +14044676189).
**Decision required from founder:**
- Option A — Switch SMS FROM to 888-513-1913 (only if toll-free SMS verification approved)
- Option B — Register A2P 10DLC for +14044676189 in Twilio Console (1-7 day review, ~$4/mo + $44 one-time)
- Option C — Hybrid (Option A immediate + Option B in parallel)

**Implementation when Option A is chosen:**
```bash
# 1. Confirm which env var controls SMS FROM
grep -E "TWILIO_SMS_FROM|TWILIO_NUMBER|TWILIO_FROM|INBOUND_SMS_FROM" /var/www/dialgenix/backend/.env

# 2. Update .env (replace +14044676189 with +18885131913)
# 3. Restart
pm2 restart dialgenix-backend --update-env

# 4. Verify by triggering a test SMS and checking Twilio dashboard for status=delivered
```

**Side fix already shipped June 13:** Removed "Sarah" from SMS body (`body = f"Hi! Thanks for calling IntentBrain. Book your demo here: {booking_url}"`).

### 0.2 — BUG #002: Conversation state leakage
**Symptom:** Agent loops back to "Thanks for calling IntentBrain…" after booking/qualification flows complete.
**Root cause hypothesis:** `last_stage` is being reset to `"greeting"` somewhere in the brain handler. Need to investigate `db.inbound_calls.update_one` calls that set `conversation_stage`.

**Implementation steps:**
```bash
# 1. Find every place conversation_stage gets written
grep -n '"conversation_stage"' /var/www/dialgenix/backend/server.py

# 2. Audit the legal state transition graph:
#    INTRO → DISCOVERY → QUALIFICATION → BOOKING → CONFIRMED → EXIT
#    (CONFIRMED and EXIT must be terminal — no transition back to INTRO)

# 3. Add a state-machine guard: refuse to write conversation_stage="greeting" 
#    if previous stage in {BOOKING, CONFIRMED, EXIT}

# 4. Write the patch as base64 + 1-liner deploy
```

### 0.3 — `.env` malformed lines (security)
Two keys printed to terminal during `source .env` because lines lacked `VAR=` prefix.
```bash
# Inspect (DO NOT paste values to chat)
grep -nE "^[^=#]+$" /var/www/dialgenix/backend/.env | grep -v "^#"

# Fix the offending lines (add VAR= prefix)
# Then rotate the keys that were exposed (Stripe + OpenAI)
```

---

## PHASE 1 — Refactor server.py into UniversalBrain Engines

**Decision (locked June 13, 2026):** Refactor BEFORE importing MerchantBrain content.
**Rationale:** Architecture mistakes are cheap to fix before content and expensive to fix after.
**Estimated effort:** 2-3 days.

### 1.0 — Create the directory skeleton
```bash
cd /var/www/dialgenix/backend
mkdir -p universal/engines
mkdir -p universal/state
mkdir -p universal/contracts
mkdir -p playbooks/merchant_brain
mkdir -p playbooks/roofing_brain   # stub
mkdir -p playbooks/insurance_brain # stub
mkdir -p playbooks/agency_brain    # stub
mkdir -p playbooks/dental_brain    # stub
mkdir -p playbooks/saas_brain      # stub
mkdir -p accounts                  # Layer 3 — per-ISO overrides
mkdir -p campaigns                 # Layer 4 — per-campaign sub-vertical
mkdir -p tests/universal
mkdir -p tests/playbooks
```

### 1.1 — Define the 10 Universal Engines (one file each, behavior-only)

| # | File | Responsibility |
|---|------|----------------|
| 1 | `universal/engines/gatekeeper.py` | Detect deflection type, classify intent, pivot to intelligence capture |
| 2 | `universal/engines/discovery.py` | Open the call, identify business, find decision maker |
| 3 | `universal/engines/objection.py` | Generic objection-handling state machine (selects objective → variation) |
| 4 | `universal/engines/qualification.py` | BANT/pain matrix flow control (does NOT contain industry questions) |
| 5 | `universal/engines/intent_scoring.py` | The math: applies weights from playbook to signals, updates score |
| 6 | `universal/engines/callback.py` | Parse callback time, persist `scheduled_callbacks`, background worker dispatch |
| 7 | `universal/engines/appointment.py` | Calendly link dispatch, SMS booking flow, appointment confirmation |
| 8 | `universal/engines/transfer.py` | Live transfer logic (warm/cold), routing rules, agent availability check |
| 9 | `universal/engines/memory.py` | `call_intelligence` CRUD, conversation summaries, name-drop lookups |
| 10 | `universal/engines/follow_up.py` | Nurture drip orchestration, SEND_EMAIL_AND_CALL scheduling |

### 1.2 — Define the contracts (interfaces between Universal and Playbook)

`universal/contracts/playbook.py` — abstract base classes the Playbook layer must implement:
```python
class Playbook(ABC):
    @abstractmethod
    def get_triggers(self) -> list[Trigger]: ...
    @abstractmethod
    def get_qualification_fields(self) -> list[QualField]: ...
    @abstractmethod
    def get_intent_weights(self) -> dict[str, int]: ...
    @abstractmethod
    def get_industry_knowledge(self) -> IndustryKB: ...
    @abstractmethod
    def get_transfer_rules(self) -> list[TransferRule]: ...
```

`universal/contracts/trigger.py` — the Trigger dataclass matching the schema in PRD §"MerchantBrain Content Schema":
```python
@dataclass
class Variation:
    text: str

@dataclass
class Objective:
    name: str
    intent_delta: int
    next_state: str
    variations: list[Variation]

@dataclass
class Trigger:
    id: str
    matches: list[str]  # phrase patterns
    possible_meanings: list[str]
    objectives: dict[str, Objective]
```

### 1.3 — Define `conversation_state` (the single source of truth)

`universal/state/conversation_state.py` — the dataclass MongoDB persists:
```python
@dataclass
class ConversationState:
    call_sid: str
    stage: str               # INTRO | DISCOVERY | QUALIFICATION | BOOKING | CONFIRMED | EXIT
    decision_maker_known: bool = False
    decision_maker_name: str | None = None
    pain_known: bool = False
    callback_known: bool = False
    transfer_eligible: bool = False
    intent_score: int = 0
    # ...all the boolean checklist items from PRD §Gatekeeper Success Score
```

### 1.4 — Extract existing logic from `server.py` lines ~11648-11720
The current brain handler currently mixes:
- Fast-path lookup
- Follow-up wrapper
- OpenAI brain call
- Action routing (collect_email / transfer_human / end_call / continue)
- TwiML Gather assembly

**Refactor target:** each of those moves into its respective engine. `server.py` becomes a thin orchestrator that just routes Twilio webhook → engine pipeline → TwiML.

### 1.5 — Architectural health tests (must pass before merging Phase 1)
```bash
# Test 1: No industry-specific business logic in universal/
python3 tests/universal/test_no_industry_logic.py

# Test 2: Delete MerchantBrain and Universal still runs
python3 tests/universal/test_deletion_independence.py

# Test 3: All 10 engines pass their unit tests
pytest tests/universal/
```

### 1.6 — Deploy Phase 1
```bash
cd /var/www/dialgenix/backend
git checkout -b phase1-universal-refactor
# (engine files created, server.py thinned)
pm2 restart dialgenix-backend
pm2 logs dialgenix-backend --lines 50 --nostream | grep -E "Engine|prewarm|complete"
# Live smoke test: call 888-513-1913, confirm all existing flows still work
```

---

## PHASE 2 — Build MerchantBrain (the first Playbook)

**Prerequisite:** Phase 1 health tests all green.
**Estimated effort:** 2-3 days (content import + playbook glue).

### 2.1 — Founder authoring (IN PROGRESS — June 15, 2026)
Founder is manually authoring/editing all MerchantBrain responses offline. Content will arrive as:
- Gatekeeper Library (deflection responses with objective tags)
- Decision Maker Library
- Processor Objections (Square / Clover / Toast / Fiserv / etc.)
- Funding / Workflow / Statement-review conversations
- Transfer Triggers
- Intent Scoring Rules

**Each trigger arrives in the canonical schema** (see PRD §"MerchantBrain Content Schema"):
- 2-3 variations per objective (NOT 20)
- Each response tagged with objective it serves

### 2.2 — Import content into MerchantBrain playbook structure
```
playbooks/merchant_brain/
├── __init__.py            # MerchantBrain class implements Playbook ABC
├── triggers.yaml          # all triggers (gatekeeper + objection + statement)
├── qualification.yaml     # monthly_volume, avg_ticket, max_ticket, cp_pct, current_processor
├── intent_weights.yaml    # per-signal score weights
├── industry_kb.md         # Clover, Square, Toast, Fiserv, Cash Discounting, Schedule A, etc.
├── transfer_rules.yaml    # when to escalate to human
└── opening_scripts.yaml   # niche-specific openers
```

### 2.3 — Wire MerchantBrain into the router
```python
# universal/orchestrator.py
def get_playbook(account_id: str, campaign_id: str | None) -> Playbook:
    # Layer 2 selection — for now hardcoded to MerchantBrain
    return MerchantBrain(account_id, campaign_id)
```

### 2.4 — Test MerchantBrain in isolation
```bash
pytest tests/playbooks/test_merchant_brain.py
# Specifically test:
#   - All triggers parse and load
#   - All objectives have 2-3 variations
#   - No variation > 25 words
#   - Intent weights sum sanely (no negative-total scenarios)
```

### 2.5 — Deploy Phase 2
```bash
# Once content is imported + tested
pm2 restart dialgenix-backend
# Live call test against 888-513-1913 using merchant-services-flavored questions
```

---

## PHASE 3 — Account Customization Layer (Layer 3)

**Prerequisite:** MerchantBrain shipped and validated on live calls.
**Estimated effort:** 1 day.

### 3.1 — Account model
```python
# accounts/account.py
@dataclass
class Account:
    account_id: str
    playbook_id: str            # "merchant_brain"
    overrides: dict             # JSON Patch–style overrides
    preferred_processors: list[str]   # e.g. ["Priority", "Paysafe", "Shift4"]
    pricing_anchors: dict       # e.g. {"savings_threshold": 0.20}
    offer_copy: dict            # custom offer wording
```

### 3.2 — Override resolution at runtime
```python
# universal/orchestrator.py
def resolve(trigger_id, state, account, campaign):
    base = playbook.triggers[trigger_id]
    if account: base = apply_overrides(base, account.overrides)
    if campaign: base = apply_overrides(base, campaign.overrides)
    return select_objective(base, state)
```

### 3.3 — Deploy Phase 3
```bash
# Seed first account (David)
python3 -c "from accounts.seeds import seed_david_account; seed_david_account()"
pm2 restart dialgenix-backend
```

---

## PHASE 4 — Campaign Override Layer (Layer 4)

**Prerequisite:** Account layer working with at least one account.
**Estimated effort:** 1 day.

### 4.1 — Campaign model — same pattern as Account, scoped per-campaign within an Account
```python
@dataclass
class Campaign:
    campaign_id: str
    account_id: str
    sub_vertical: str           # "dental" | "restaurant" | "auto_repair" | "retail"
    overrides: dict
```

### 4.2 — Sub-vertical-specific overrides
Example: `MerchantBrain → David Account → Dental Campaign`
```yaml
sub_vertical: dental
overrides:
  qualification.avg_ticket_anchor: 250    # dental practices have higher tickets
  triggers.WE_USE_SQUARE.objectives.PAIN_DISCOVERY.variations:
    - "Are you handling insurance claims through Square as well, or separately?"
```

### 4.3 — Deploy Phase 4
```bash
python3 -c "from campaigns.seeds import seed_dental_campaign; seed_dental_campaign(david_account_id)"
pm2 restart dialgenix-backend
```

---

## PHASE 5 — Deflection Intelligence Engine (Gatekeeper Engine v2)

**Prerequisite:** Phases 1-4 complete (engine extraction done).
**Estimated effort:** 1-2 days.
**Reference:** PRD §"Gatekeeper / Callback Flow" + §"Agent Brain Rules"

### 5.1 — MongoDB collection
```python
# Create call_intelligence collection with indexes
await db.call_intelligence.create_index([("call_sid", 1)], unique=True)
await db.call_intelligence.create_index([("lead_id", 1)])
await db.call_intelligence.create_index([("next_action_at", 1)])
```

### 5.2 — Deflection classifier (LLM-driven w/ structured output)
```python
# universal/engines/gatekeeper.py
async def classify_deflection(speech: str) -> DeflectionResult:
    # Use OpenAI structured output (JSON schema) → DeflectionType enum
    # No "Sarah" or industry-noun bias in the prompt
```

### 5.3 — Intelligence capture state machine
Implements the 10 deflection categories + their objective trees from PRD.

### 5.4 — Next Best Action engine
Implements the rules table from PRD §"Next Best Action Engine".

### 5.5 — Background scheduler/dialer worker
```python
# universal/workers/callback_dispatcher.py
# Runs every 5 minutes
# Finds call_intelligence rows where next_action_at <= now AND next_action == "CALL_BACK"
# Triggers Twilio outbound dial with name-drop opening
```

### 5.6 — Name-drop integration
On outbound callback, opener uses:
> "Hi {decision_maker_name}, this is {ai_name}. I was speaking with {gatekeeper_first_name} earlier and she suggested {best_callback_time} would be the best time to reach you."

### 5.7 — Dashboard UI for call_intelligence
React component showing:
- All intel captured per call
- Gatekeeper Success Score
- Next action queue
- Intent score timeline

### 5.8 — Deploy Phase 5
```bash
pm2 restart dialgenix-backend
# Live test: call gatekeeper-style answer to AI, verify intel captured
```

---

## PHASE 6 — Frontend / Public Site polish (already in progress)

- [x] Removed "Sarah" from landing page (June 13, 2026 — patched `out/index.html`)
- [ ] Rebuild frontend from updated source (when source has new "Experience a Real AI Sales Conversation" copy)
- [ ] Verify all CTAs route to `/pricing` (not Calendly directly)
- [ ] Ensure data-testid attributes on every interactive element

```bash
cd /var/www/intentbrain-frontend && npm run build && pm2 restart cold-call-ai
```

---

## PHASE 7+ — Future Playbooks (content-only work after Phases 1-5)

Once UniversalBrain + Account + Campaign layers are stable:
- [ ] RoofingBrain (storm season, supplier pricing)
- [ ] InsuranceBrain (policy renewals, premiums)
- [ ] AgencyBrain (campaign performance, retainers)
- [ ] DentalBrain (insurance, recall lists)
- [ ] SaaSBrain (contract renewals, seat expansion)

Each new playbook = ~2 days of *content authoring*, not engineering.

---

## Standing Rules (apply to every phase)

1. **One layer per PR.** Every PR must answer exactly ONE of: UniversalBrain / Playbook / Account / Campaign. No multi-layer answers.
2. **UniversalBrain owns behavior. Playbooks own domain knowledge.** No industry-specific business logic in UniversalBrain. Industry strings as data = OK, industry strings in conditionals = forbidden.
3. **Health test:** Could MerchantBrain be deleted and IntentBrain still run? Must always be "yes."
4. **MerchantBrain ships as content, not code.** New playbooks are content authoring jobs, not engineering jobs.
5. **2-3 variations per objective.** Never 20. Elite reps don't memorize 300×20.
6. **Never `random.choice(responses)`.** Always select objective from state, then pick variation.
7. **Never close a gatekeeper.** Gatekeeper interactions are intelligence capture only.
8. **Patch via base64 1-liners.** VPS terminal mangles multi-line heredocs. Local script → base64 → `echo ... | base64 -d > /tmp/patch.py && python3 /tmp/patch.py && pm2 restart dialgenix-backend --update-env`.

---

## Implementation Order Summary

```
PHASE 0  — Fix open prod bugs (SMS, state leakage, .env)
PHASE 1  — Refactor: extract 10 universal engines
PHASE 2  — Import MerchantBrain content (founder authoring now)
PHASE 3  — Add Account layer
PHASE 4  — Add Campaign layer
PHASE 5  — Build Deflection Intelligence Engine v2 (gatekeeper)
PHASE 6  — Frontend polish + rebuild
PHASE 7+ — Future vertical playbooks (content only)
```

**Do NOT begin Phase 1 until Phase 0 production bugs are fixed.**
**Do NOT begin Phase 2 until Phase 1 health tests are green.**
**Do NOT begin Phases 3-5 until Phase 2 ships and live-call-tested.**
