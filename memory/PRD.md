# DialGenix.ai (Rebranding to IntentBrain.ai) - PRD

## Original Problem Statement
Build an AI cold calling machine that calls businesses, qualifies them, and routes qualified leads to different sales agents for payment processing.

## Current Status: PRE-LAUNCH (Ready for signups)
- Platform fully functional, users can sign up and explore
- AI calling blocked until ElevenLabs upgraded (8 credits remaining, resets May 5)
- Stripe live payments connected and working
- Domain: dialgenix.ai (rebranding to intentbrain.ai pending)

## Architecture
- **Frontend:** React 18, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, Motor (async MongoDB)
- **Voice Pipeline:** Twilio → FastAPI WebSocket → GPT-5.2 → ElevenLabs Flash v2
- **Payments:** Stripe (live key on VPS as STRIPE_API_KEY)
- **Pricing:** BYOK model (users bring own Twilio + ElevenLabs keys)

## Pricing (Aligned Landing Page + Backend — April 15, 2026)
| Plan | Price | Type |
|---|---|---|
| Test Drive | $49/mo | Entry |
| Review Requests | $49/mo | Add-on |
| BYOL Starter | $199/mo (250 calls) | BYOL |
| BYOL Pro | $449/mo (750 calls) | BYOL |
| BYOL Scale | $799/mo (1,500 calls) | BYOL |
| Discovery Starter | $399/mo | Full Service |
| Discovery Pro | $899/mo | Full Service |
| Discovery Elite | $1,599/mo | Full Service |
| Receptionist Lite | $49/mo | Inbound |
| Receptionist Pro | $99/mo | Inbound |
| Receptionist Plus | $199/mo | Inbound |

**PAYG removed.** BYOL users cannot purchase credit packs — must upgrade tier.

## Getting Started Checklist (7 steps)
1. Connect Twilio Voice
2. Connect ElevenLabs Voice (NEW)
3. Set Up Calendly Booking
4. Complete Compliance Setup (with FTC/DNC instructions for B2C)
5. Create Your First Agent
6. Create a Campaign
7. Connect CRM (Optional)

## Industry Script Templates (10 total)
- Sales / Cold Calling (generic)
- Lead Generation Agency
- Digital Marketing Agency
- Insurance Sales
- Solar Sales
- Roofing / Home Services
- Credit Card Processing
- Appointment Setter
- Receptionist
- Customer Service

## Completed Features (April 15, 2026)
- [x] All landing page CTAs go to pricing (not Calendly)
- [x] PAYG removed, replaced with Review Requests add-on
- [x] Pricing alignment (landing page = backend = Stripe)
- [x] Landing page → Stripe checkout flow
- [x] BYOL credit packs blocked
- [x] ElevenLabs added to Getting Started checklist
- [x] FTC/DNC detailed instructions for B2C
- [x] CSV parser fixed (BOM, whitespace, mixed case)
- [x] Inbound AI webhook configured
- [x] 6 new industry script templates
- [x] Campaign Dial Settings
- [x] ElevenLabs Flash v2 switch
- [x] Inbound audio disk caching
- [x] BYOK Setup Wizard
- [x] Credit Alert Banner
- [x] GitHub repo private, Twilio token rotated

## Backlog

### P0 - Before Launch
- [ ] Upgrade ElevenLabs to Scale ($330/mo)
- [ ] Test Stripe post-payment redirect
- [ ] IntentBrain.ai rebrand

### P1 - High Priority
- [ ] Verify CSV upload works on live site
- [ ] Voice Cloning UI verification

### P2 - Medium Priority
- [ ] Predictive dialer
- [ ] Open Dental RPA integration
- [ ] Monolith refactoring

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
| ElevenLabs | 8 credits left | VPS .env |
| Twilio | Active (token rotated) | VPS .env |
| Stripe | Active (live key) | VPS .env as STRIPE_API_KEY |
