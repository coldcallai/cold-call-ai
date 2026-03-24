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
- **Automatic credit deduction on lead discovery and AI calls**
- **Real-time sidebar credit balance updates**
- **402 Payment Required errors for insufficient credits**
- **Stripe Integration for subscriptions and credit packs**
- **Payment history tracking in database**
- **Checkout session polling for payment verification**
- **Admin account with unlimited credits for testing**
- **Compliance Layer (DNC management, number verification, pre-call checks)**
- **Twilio Integration for real outbound calls (LIVE)**
- **TwiML webhooks for AI conversation flow**
- **Call recording and status tracking**

### Session 3 (December 24, 2025): Real-Time AI Voice Conversations
- **Fixed Twilio Media Streams WebSocket connection** - Root cause was internal URL being used instead of external URL
- **Implemented Synthflow-style real-time AI calls** - Full bidirectional conversation pipeline
- **ElevenLabs TTS streaming to Twilio** - μ-law audio format for direct playback
- **WebSocket handler for Media Streams** - Handles connected, start, media, stop events
- **STT integration via OpenAI Whisper** - Transcribes caller audio for AI processing
- **GPT-5.2 response generation** - Context-aware sales conversation
- **Tested live calls** - Verified end-to-end flow with real phone calls

### Session 4 (December 24, 2025): Training & Onboarding Features
- **Custom Keywords up to 100** - Agents can add their own intent keywords for lead discovery
- **Preview Examples (Free)** - See sample leads before using credits
- **Keyword Persistence** - Keywords saved to user profile in database (survives refresh/logout)
- **Interactive Onboarding Guide** - 8-step walkthrough for new users covering:
  - Welcome, Keywords Setup, Preview Leads, Discover Real Leads, Create Campaign, Add Agents, Launch & Monitor, Completion
- **AI Help Chat Assistant** - GPT-powered chat that answers questions and guides users through:
  - Campaign setup, keyword selection, feature explanations, troubleshooting
  - Context-aware responses based on user's current page and account state
- **"Save Keywords" button** - Explicitly save keywords to profile

### Session 5 (December 24, 2025): Phone/Email Verification & AMD + Voicemail Drop
- **Phone Verification via Twilio Lookup API** ($0.005/lookup, cached 30 days)
  - Detects line type: mobile, landline, VoIP
  - Dial priority scoring (mobile=100, landline=60, voip=30)
  - Carrier name detection
- **Email Verification** (FREE)
  - Syntax validation, disposable domain detection, typo correction
  - Quality scoring and business vs personal classification
- **AMD (Answering Machine Detection)** - Detects human vs voicemail
  - Uses Twilio's AsyncAMD with DetectMessageEnd
  - Cost: ~$0.02 per call
- **Voicemail Drop** - Auto-drops pre-recorded VM when machine detected
  - Saves ~$0.14 per voicemail call (vs full AI processing)
  - Custom voicemail messages per campaign with variable substitution
  - Variables: {contact_name}, {business_name}, {company_name}
- **ROI Impact**: 56% cost reduction on calls (from $15 to $6.55 per 100 calls)
- **Configurable Response Wait Time** - Agents set how long AI waits for response (1-10 sec, default 4)

### Session 6 (December 24, 2025): ICP Scoring & Homepage AI Section
- **ICP (Ideal Customer Profile) Scoring** - Score leads 0-100 before dialing
  - Industry Fit (0-25 pts)
  - Company Size Fit (0-25 pts)
  - Intent Signal Strength (0-25 pts)
  - Contact Quality (0-25 pts)
- **Tier Classification**: A (80+), B (60-79), C (40-59), D (<40)
- **Rule-based scoring** (FREE) or **AI-powered scoring** (~$0.002/lead)
- **Batch scoring** - Score up to 100 leads at once
- **Dial Priority** - Combined score: 60% ICP + 40% phone verification
- **Homepage AI Capabilities Section** - Showcases:
  - Multi-turn conversations
  - CRM integration ready
  - Intelligent call routing
  - No-code setup
  - Live mockup showing "847 simultaneous calls"

### Session 7 (December 2025): Multi-Tenant Data Isolation
- **Complete multi-tenant data isolation** - All user data is now scoped by user_id
- **Secured endpoints**: Leads, Campaigns, Agents, Calls, Webhooks, Dashboard Stats
- **Cross-user access protection** - Returns 404 (not 403) to prevent data leakage
- **All CRUD operations secured** - Create, Read, Update, Delete filtered by user_id
- **31 backend tests passing** - Full coverage of isolation scenarios
- **Test users created**: User A (test@example.com) and User B (test_user_b@example.com)

### Session 8 (December 2025): Subscription Tier Enforcement & Features
- **Subscription tier feature flags** - TIER_FEATURES dict with limits for free/starter/professional/unlimited/byl
- **Monthly usage tracking** - get_monthly_usage() tracks leads and calls per billing month
- **Feature access checks** - check_subscription_limit() enforces limits on leads, calls, campaigns, agents
- **CSV export/upload enforcement** - Blocked for free users, allowed for higher tiers
- **ICP scoring enforcement** - Basic scoring for Starter+, AI scoring for Professional+
- **Low balance notifications** - Automatic email alerts when credits drop below threshold
- **ICP configuration UI** - Added to campaign creation form (target industries, company sizes, roles)
- **16 subscription tier tests passing**
- **New endpoint**: GET /api/subscription/features - Returns user's tier limits and usage

## Prioritized Backlog

### P0 - Critical
- [x] ~~Stripe Integration - Real checkout sessions for subscriptions and packs~~ ✅ DONE
- [x] ~~Twilio Media Streams WebSocket - Real-time AI conversations~~ ✅ DONE
- [x] ~~Custom Keywords (up to 100) for lead discovery~~ ✅ DONE
- [x] ~~In-App Training Guide & Help Chat~~ ✅ DONE
- [x] ~~Phone Verification (Twilio Lookup)~~ ✅ DONE
- [x] ~~AMD + Voicemail Drop~~ ✅ DONE
- [x] ~~ICP Scoring~~ ✅ DONE

### P1 - High Priority
- [x] ~~Multi-tenant data isolation - Scope leads/campaigns to user accounts~~ ✅ DONE (December 2025)
- [x] ~~Subscription tier enforcement - Limit features by plan~~ ✅ DONE (December 2025)
- [x] ~~Low balance notification system~~ ✅ DONE (December 2025)
- [x] ~~ICP configuration UI in campaign form~~ ✅ DONE (December 2025)
- [ ] Improve STT accuracy - Consider Deepgram for lower latency

### P2 - Medium Priority
- [ ] Low-balance email notifications
- [ ] Auto-suggest plan upgrades based on top-up purchases
- [ ] Stripe recurring subscriptions (currently one-time payments)

### P3 - Future
- [ ] Team seat management
- [ ] API rate limiting by tier
- [ ] Refactor App.js (2000+ lines) into smaller components
- [ ] Calendar integration for auto-booking qualified leads

## Testing
- Backend: pytest suite at `/app/backend/tests/test_auth_and_api.py`
- Multi-tenant isolation tests: `/app/backend/tests/test_multi_tenant_isolation.py` (31 tests)
- Subscription tier tests: `/app/backend/tests/test_subscription_tiers.py` (16 tests)
- Auth testing playbook: `/app/auth_testing.md`
- Test reports: `/app/test_reports/iteration_1.json`, `/app/test_reports/iteration_2.json`
- Test users:
  - User A (admin): test@example.com / Test123!
  - User B (free): test_user_b@example.com / Test456!

## 3rd Party Integrations Status
| Service | Status | Notes |
|---------|--------|-------|
| OpenAI GPT-5.2 | ✅ Active | Via Emergent LLM Key |
| OpenAI Whisper | ✅ Active | STT for caller audio |
| Emergent Auth | ✅ Active | Google OAuth |
| ElevenLabs | ✅ Active | TTS voice generation, μ-law output |
| Stripe | ✅ Active | Test keys, checkout working |
| Twilio | ✅ Active | Live outbound calls + Media Streams |
| Resend | ⚠️ Requires Key | Email notifications |
