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
