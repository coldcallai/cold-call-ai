# DialGenix.ai (Rebranding to IntentBrain.ai) - PRD

## Original Problem Statement
Build an AI cold calling machine that calls businesses, qualifies them, and routes qualified leads to different sales agents for payment processing.

## Current Status: PRE-LAUNCH
- Platform fully functional
- Domain: dialgenix.ai (rebranding to intentbrain.ai pending)
- ElevenLabs: 8 credits remaining, resets May 5 or upgrade to Scale ($330/mo)
- All voice now uses eleven_flash_v2 (2x more efficient)
- Stripe live payments connected and working

## Architecture
- **Frontend:** React 18, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, Motor (async MongoDB)
- **Voice Pipeline:** Twilio → FastAPI WebSocket → GPT-5.2 → ElevenLabs Flash v2
- **Payments:** Stripe (live key configured on VPS)
- **Pricing:** BYOK model (users bring own Twilio + ElevenLabs keys)

## Pricing (Aligned Landing Page + Backend)
| Plan | Price |
|---|---|
| Pay-as-you-go | $0/mo + $0.50/call |
| Test Drive | $49/mo |
| BYOL Starter | $199/mo (250 calls) |
| BYOL Pro | $449/mo (750 calls) |
| BYOL Scale | $799/mo (1,500 calls) |
| Discovery Starter | $399/mo |
| Discovery Pro | $899/mo |
| Discovery Elite | $1,599/mo |
| Receptionist Lite | $49/mo |
| Receptionist Pro | $99/mo |
| Receptionist Plus | $199/mo |

**BYOL users cannot purchase credit packs** — must upgrade tier for more calls.

## Completed Features (April 2026)
- [x] BYOK Setup Wizard (4-step guided onboarding)
- [x] Credit Alert Banner (Twilio <$10, ElevenLabs <20%)
- [x] ElevenLabs Flash v2 (switched from multilingual_v2)
- [x] Inbound audio disk caching
- [x] Campaign Dial Settings (calls/day, calls/hour, time, days)
- [x] BYOL credit packs blocked (frontend + backend)
- [x] Pricing alignment (landing page = backend = Stripe)
- [x] Landing page → Stripe checkout flow
- [x] CSV parser improved (accepts multiple column name formats)
- [x] Agency/sales team campaign script (7-state flow)
- [x] FAQ: "Is there a free trial or demo available?"
- [x] GitHub repo set to private
- [x] Twilio auth token rotated

## Backlog

### P0 - Before Launch
- [ ] Test Stripe post-payment redirect (use test key)
- [ ] IntentBrain.ai rebrand (domain purchased)
- [ ] CSV upload errors on live site debugging

### P1 - High Priority
- [ ] Industry script template library
- [ ] Voice Cloning UI integration verification

### P2 - Medium Priority
- [ ] Predictive dialer (parallel calling)
- [ ] Open Dental RPA integration
- [ ] Monolith refactoring (server.py 12,700+ lines)

### P3 - Future
- [ ] Calendly Webhook Sync
- [ ] Payment Overlay Platform

## VPS Deployment
```
cd /var/www/dialgenix && git pull origin main && cd frontend && npm run build --legacy-peer-deps && cd ../backend && pm2 restart dialgenix-backend
```

## 3rd Party Integrations
| Service | Status | Key Location |
|---|---|---|
| OpenAI GPT-5.2 | Active | Emergent LLM Key |
| ElevenLabs | Active (8 credits) | VPS .env |
| Twilio | Active (token rotated) | VPS .env |
| Stripe | Active (live key) | VPS .env as STRIPE_API_KEY |
