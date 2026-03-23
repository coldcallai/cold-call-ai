# ColdCall.ai - AI Cold Calling SaaS Platform

## Original Problem Statement
Build an AI cold calling machine that calls businesses, qualifies them, and routes qualified leads to different sales agents for payment processing.

## Product Vision
A vertical-agnostic B2B SaaS platform that:
1. Discovers high-intent leads via GPT-5.2 (businesses searching for competitor alternatives)
2. Executes AI cold calls to qualify leads using ElevenLabs TTS
3. Books qualified leads directly into sales agents' Calendly links
4. Tracks credits and subscription tiers for monetization

## User Personas
- **Sales Team Managers**: Need to scale outbound without hiring more SDRs
- **Small Business Owners**: Want affordable lead generation and qualification
- **Agencies**: Bring their own lead lists, need calling capacity

## Core Requirements

### Authentication (COMPLETED)
- [x] Email/Password registration and login with JWT tokens
- [x] Google OAuth via Emergent Auth integration
- [x] Session management with httpOnly cookies
- [x] Protected routes in React frontend
- [x] User credits tracking (lead_credits_remaining, call_credits_remaining)

### Pricing Model (COMPLETED - REVISED)
**Subscription Tiers:**
| Plan | Price | Leads/mo | Calls/mo | Features |
|------|-------|----------|----------|----------|
| Starter | $199 | 250 | 250 | CSV export, 1 user |
| Professional | $399 | 1,000 | 1,000 | Calendar booking, API, 5 users |
| Unlimited | $699 | 5,000 | Unlimited | Priority support, 5 team seats |
| Bring Your List | $349 | 0 | 1,500 | Unlimited CSV uploads, 3 users |

**Lead Packs (Auto-replenishing):**
- 500/mo: $59 ($0.118/lead)
- 1,500/mo: $149 ($0.099/lead)
- 5,000/mo: $399 ($0.079/lead)

**Call Packs (Overage protection):**
- 500 calls: $49 ($0.098/call)
- 2,000 calls: $149 ($0.0745/call)
- 5,000 calls: $299 ($0.0598/call)

**Top-up Packs (20% premium):**
- 100 Leads: $24
- 250 Leads: $55
- 100 Calls: $15

**Prepay Discounts:**
- Quarterly: 5% off
- Annual: 15% off

### Lead Discovery (COMPLETED)
- [x] GPT-5.2 powered intent search for high-buying-mode businesses
- [x] CSV upload for "Bring Your Own List" users
- [x] Lead status tracking (new, contacted, qualified, not_qualified, booked)
- [x] Intent signals storage

### AI Calling (PARTIALLY COMPLETED)
- [x] ElevenLabs TTS integration for realistic voice generation
- [x] Call simulation with GPT-5.2 conversation evaluation
- [ ] Twilio integration for real outbound calls (MOCKED)
- [x] Call transcripts storage
- [x] Qualification scoring (decision maker + interest level)

### Sales Pipeline (COMPLETED)
- [x] Kanban-style funnel dashboard
- [x] Lead status progression
- [x] Agent management with Calendly links
- [x] Booking workflow with email notifications

### Notifications (COMPLETED)
- [x] Resend email integration for qualified lead alerts
- [x] Meeting booked notifications
- [x] Webhook configuration UI

## Technical Architecture

### Stack
- **Frontend**: React 18, Tailwind CSS, Shadcn/UI, React Router
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB
- **Auth**: JWT + Emergent Google OAuth
- **AI**: GPT-5.2 via Emergent LLM Key
- **Voice**: ElevenLabs TTS
- **Email**: Resend

### Key Files
```
/app/
├── backend/
│   ├── server.py          # FastAPI app with all endpoints
│   ├── requirements.txt
│   └── .env               # MONGO_URL, EMERGENT_LLM_KEY, ELEVENLABS_API_KEY
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main routing, protected routes, dashboard components
│   │   ├── LandingPage.js # Public marketing page with pricing
│   │   ├── contexts/AuthContext.jsx
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       └── AuthCallback.jsx
│   └── .env               # REACT_APP_BACKEND_URL
```

### API Endpoints
- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/auth/session`, `/api/auth/logout`
- Leads: `/api/leads`, `/api/leads/gpt-intent-search`, `/api/leads/upload-csv`
- Calls: `/api/calls/simulate`, `/api/calls`
- TTS: `/api/tts/generate`, `/api/tts/voices`
- Packs: `/api/packs`, `/api/account/usage`, `/api/packs/purchase`
- Analytics: `/api/analytics/usage`, `/api/analytics/track`

## What's Been Implemented (December 2025)

### Session 1: Initial MVP
- Landing page with original 3-tier pricing
- Kanban sales funnel dashboard
- GPT-5.2 lead discovery
- CSV upload functionality
- Mock call simulation
- Resend email webhooks
- Basic credit packs UI

### Session 2 (Current): Auth & Pricing Overhaul
- Complete JWT authentication with email/password
- Emergent-managed Google OAuth integration
- Revised 4-tier pricing model ($199/$399/$699/$349)
- Auto-replenishing lead packs
- Call packs for overage protection
- Top-up packs at 20% premium
- ElevenLabs TTS integration for AI voice
- User credits tracking per account
- Protected routes in frontend
- **Usage Dashboard with credit consumption trends**
- **Usage analytics API with daily averages and suggestions**
- **Low-balance warnings and upgrade suggestions**

## Prioritized Backlog

### P0 - Critical
- [ ] Stripe Integration - Real checkout sessions for subscriptions and packs
- [ ] Credit deduction on usage (when discovering leads or making calls)

### P1 - High Priority
- [ ] Twilio Integration - Move from mocked to real outbound calls
- [ ] Multi-tenant data isolation - Scope leads/campaigns to user accounts
- [ ] Subscription tier enforcement - Limit features by plan

### P2 - Medium Priority
- [ ] Low-balance warnings in UI
- [ ] Usage analytics dashboard
- [ ] Auto-suggest plan upgrades based on top-up purchases

### P3 - Future
- [ ] Team seat management
- [ ] API rate limiting by tier
- [ ] Refactor App.js (2000+ lines) into smaller components

## Testing
- Backend: pytest suite at `/app/backend/tests/test_auth_and_api.py`
- Auth testing playbook: `/app/auth_testing.md`
- Test report: `/app/test_reports/iteration_1.json`
- Test user: test@example.com / Test123!

## 3rd Party Integrations Status
| Service | Status | Notes |
|---------|--------|-------|
| OpenAI GPT-5.2 | ✅ Active | Via Emergent LLM Key |
| Emergent Auth | ✅ Active | Google OAuth |
| ElevenLabs | ✅ Active | TTS voice generation |
| Resend | ⚠️ Requires Key | Email notifications |
| Stripe | ❌ Not Started | Payment processing |
| Twilio | ⚠️ Mocked | Real calls require credentials |
