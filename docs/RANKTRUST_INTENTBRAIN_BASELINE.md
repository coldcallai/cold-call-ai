# RankTrust → IntentBrain — Baseline Lifecycle Timeline

**Purpose.** Establish a canonical, timestamped record of the *first successful* end-to-end
`RankTrust → IntentBrain` packet dial. This becomes the permanent baseline for all future
debugging, latency regression checks, and performance optimization.

This document is **read-only diagnostic scaffolding**. It does not change any dialing
behavior, brain logic, or secret handling.

---

## 1. The canonical 10-stage sequence

Every packet that gets fully dialed passes through these 10 stages in this exact order:

| # | Stage                       | Source                              | When it fires                                                    |
|---|-----------------------------|-------------------------------------|------------------------------------------------------------------|
| 1 | `packet_received`           | `ranktrust_handoffs.received_at`    | HTTP body accepted by `/api/webhooks/ranktrust/handoff`.         |
| 2 | `packet_validated`          | Implicit @ receipt                  | HMAC / token auth + Pydantic schema both passed.                 |
| 3 | `queued`                    | Implicit @ receipt                  | Row persisted with `status='scheduled'`; ready for the scheduler.|
| 4 | `delay_target`              | `ranktrust_scheduled_calls.target_at`| Earliest moment the scheduler is allowed to dial (`received_at + delay_seconds`). |
| 5 | `dial_started`              | `ranktrust_handoffs.events[dial_placed]` | Scheduler invoked `place_outbound_call()` and Twilio returned a Call SID. |
| 6 | `answered`                  | `outbound_sessions.answered_at`     | Twilio `/outbound/answer` webhook fired; AMD reported `AnsweredBy`. |
| 7 | `greeting_detected`         | `outbound_sessions.opener_played_at`| First human utterance classified as `human` by the gate.         |
| 8 | `ai_conversation_started`   | `outbound_sessions.opener_played_at`| ElevenLabs opener MP3 played; control handed off to the brain.   |
| 9 | `call_ended`                | `outbound_sessions.ended_at`        | Twilio `status_callback` fired with `CallDuration` + final status. |
| 10 | `callback_sent`            | `ranktrust_handoffs.events[callback_*]` | POST back to RankTrust (`dial_placed` / `needs_phone` / `blocked_*` / `failed`). |

**Safety cap in effect.** For RankTrust-scheduled dials, `OUTBOUND_MAX_CALL_SECONDS`
(default `120`) is passed to Twilio as `time_limit`. If the AI conversation is still
active at that point, Twilio hard-ends the call and stage 9 fires with
`final_call_status='completed'` and `duration_seconds≈120`. This is expected and
protects against runaway AI-to-AI costs during early E2E validation.

---

## 2. How to capture your baseline

After you fire a test packet (`bash scripts/send_test_packet.sh`) and the call has
fully wrapped up (i.e. Twilio has fired the completion webhook), curl the timeline
endpoint on your VPS:

### 2a. Get the JSON structured timeline

```bash
BASE=https://your-vps.example.com
PACKET_ID=pkt-live-test-001

curl -sS "$BASE/api/webhooks/ranktrust/timeline/$PACKET_ID" | jq .
```

### 2b. Get the copy-paste markdown block for the project log

```bash
curl -sS "$BASE/api/webhooks/ranktrust/timeline/$PACKET_ID?format=markdown" \
  > "docs/baselines/${PACKET_ID}.md"
```

The markdown response is a single Markdown table you can paste directly into a chat
message, PR description, or debugging thread. It never contains callback tokens,
HMAC secrets, phone numbers of anyone other than the tested prospect, or backend URLs.

---

## 3. First-baseline template — *fill this in after your first live packet*

Once the first successful E2E test completes, paste the markdown output from
step 2b in this section. This becomes the reference point for every future
comparison.

```
> Replace this block with the output of:
>   curl -sS "$BASE/api/webhooks/ranktrust/timeline/$PACKET_ID?format=markdown"
```

### Expected shape (illustrative — replace with real numbers)

| # | Stage                        | Timestamp (UTC)             | Elapsed (s) | Notes                                    |
|---|------------------------------|-----------------------------|-------------|------------------------------------------|
| 1 | `packet_received`            | `2026-02-XXTHH:MM:SS+00:00` | 0.000       | HMAC verified                            |
| 2 | `packet_validated`           | same as (1)                 | 0.000       | Pydantic pass                            |
| 3 | `queued`                     | same as (1)                 | 0.000       | Row persisted                            |
| 4 | `delay_target`               | `+300s later`               | 300.000     | Configured `delay_seconds`               |
| 5 | `dial_started`               | just after (4)              | 300.x       | Twilio returned Call SID                 |
| 6 | `answered`                   | ~1–3s after (5)             | ~302        | `AnsweredBy=human`                       |
| 7 | `greeting_detected`          | ~1–4s after (6)             | ~305        | First human utterance                    |
| 8 | `ai_conversation_started`    | same as (7)                 | ~305        | Opener MP3 played                        |
| 9 | `call_ended`                 | conversation end / 120s cap | ≤ (8)+120   | `final_call_status=completed`            |
| 10| `callback_sent`              | immediately after (5) or (9)| ~301 or (9)+ε | Callback POST returned 2xx             |

---

## 4. Interpreting the numbers

- **Stages 1–3** should share the same timestamp (they are three semantic points
  around the same DB insert).
- **Stage 4** should be `packet.delay_seconds` after stage 1. If it drifts, your
  scheduler poll interval (`poll_seconds`, default 30) is the ceiling on jitter.
- **Stage 5 elapsed** minus **stage 4 elapsed** must be `< poll_seconds`. Values
  significantly larger indicate a stalled scheduler loop.
- **Stage 6 - stage 5** is Twilio's connect + AMD time — normal range is 3–10s
  for landlines, 1–4s for mobiles.
- **Stage 7 - stage 6** is how long the callee took to say hello. Under 5s is healthy.
- **Stage 9 - stage 8** is the length of the actual AI conversation. If this equals
  `OUTBOUND_MAX_CALL_SECONDS` (default 120), the safety cap terminated the call.
- **Stage 10** may fire *before* stage 9 (we notify RankTrust `dial_placed` as soon
  as the Call SID is returned; the terminal disposition callback is a separate future
  event that will be added when the reconciler ships).

---

## 5. Debugging failure modes

If a stage is **missing** from your timeline, the packet stopped there. Use this
mapping to jump straight to the failing subsystem:

| Missing stage             | Likely cause                                              |
|---------------------------|-----------------------------------------------------------|
| `packet_received`         | Auth failed (bad HMAC / token) — request never persisted. |
| `queued`                  | `business.phone` was null → `status=needs_phone`.         |
| `delay_target`            | Same as `queued` (no scheduled call row created).         |
| `dial_started`            | Kill switch present, phone on DNC, or scheduler stopped.  |
| `answered`                | Twilio never called `/outbound/answer` (webhook URL wrong).|
| `greeting_detected`       | AMD said machine, or human never spoke inside 8s.         |
| `ai_conversation_started` | Opener MP3 missing from `_state.audio_store` (process restart between dial and answer). |
| `call_ended`              | Twilio `status_callback` misconfigured; the call may still be in progress. |
| `callback_sent`           | `callback_url` missing AND no `RANKTRUST_CALLBACK_URL` env fallback set. |

---

## 6. Security guarantees of the timeline endpoint

- **Read-only.** `GET /api/webhooks/ranktrust/timeline/{packet_id}` never writes.
- **No secrets.** `callback_token`, HMAC secret, and any `Authorization` header we
  sent are stripped at *write* time. The stored `callback_posted` event detail is
  strictly `{outcome, status_code}` or `{outcome, error}`.
- **No auth required for reads** by design — the endpoint is intentionally usable
  from a debugging shell on the VPS. If you expose it externally, protect it at the
  ingress layer (VPN, IP allowlist, or basic auth in your reverse proxy). Do not
  add auth to the endpoint itself unless we also add it to `/handoff/{packet_id}`.

---

## 7. Change log

- **2026-02-XX** — Baseline scaffolding introduced. Endpoint + markdown formatter
  + pytest coverage added. No behavior changes to the outbound gate, scheduler,
  or callback path.
