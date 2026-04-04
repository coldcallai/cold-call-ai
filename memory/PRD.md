# DialGenix.ai - AI Cold Calling SaaS Platform

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

### Session 9 (December 2025): Calendly Integration & Auto-Booking
- **CalendlyService** - Full service class for Calendly API integration (booking links, availability, events)
- **Personalized booking links** - Auto-generates Calendly links pre-filled with lead name, email, phone
- **Booking model** - New data model to track meeting bookings with status (pending/confirmed/cancelled/completed)
- **Booking CRUD endpoints**:
  - POST /api/bookings - Create booking with personalized link
  - GET /api/bookings - List user's bookings
  - GET /api/bookings/{id} - Get specific booking
  - PUT /api/bookings/{id}/status - Update booking status
  - DELETE /api/bookings/{id} - Cancel booking (reverts lead to qualified)
- **Calendly webhook** - POST /api/calendly/webhook handles invitee.created and invitee.canceled events
- **Agent model enhanced** - Added calendly_api_token, calendly_event_type_uri, booked_meetings fields
- **Email notifications** - Booking emails now include personalized Calendly link button
- **Feature gated** - Calendar booking requires Professional plan or higher
- **Bookings Dashboard UI** - Full-featured frontend page with:
  - Stats cards (total, pending, confirmed, completed, cancelled)
  - Filter by status and agent
  - Search by lead name/email/phone
  - Copy/Open booking links
  - Cancel bookings with confirmation
  - Calendly connection status indicator
- **Enhanced BookingDialog** - Shows personalized link preview with pre-filled lead data
- **New navigation item** - Bookings page added to sidebar

### Session 10 (December 2025): Call Recording & Transcription
- **CallRecordingService** - Full service for recording storage and Whisper transcription
- **Object Storage Integration** - Uses Emergent object storage for audio file storage
- **Whisper Transcription** - OpenAI Whisper API for accurate speech-to-text
- **Call Model Enhanced** - Added recording_url, recording_sid, full_transcript, transcript_segments, transcription_status
- **Tiered Feature Access**:
  - Free: No recordings
  - Starter ($199): Recordings, 7-day retention, no transcription
  - Professional ($399): Recordings, 30-day retention, full transcription
  - Unlimited ($699): Recordings, 90-day retention, full transcription
- **Recording Endpoints**:
  - GET /api/calls/{id}/recording - Get recording details
  - GET /api/calls/{id}/recording/stream - Stream audio for playback
  - GET /api/calls/{id}/transcript - Get full transcript with timestamps
  - POST /api/calls/{id}/transcribe - Request transcription for a call
  - POST /api/twilio/recording - Enhanced webhook for auto-processing recordings
- **Enhanced Call History UI**:
  - Play/Pause recording buttons in table
  - Recording badge indicator
  - Feature availability badges (Recordings, Transcripts)
  - Full transcript view with timestamped segments
  - Request transcription button

### Session 11 (December 2025): Pay-as-you-go Pricing Tier
- **New PAYG Tier** - $0/month, pay only for usage
  - $0.50 per AI call
  - $0.25 per lead discovered
  - 3-day call recording retention
  - CSV export/upload included
  - Basic ICP scoring
- **PAYG Credit Packs**:
  - Starter Pack: $19 for 25 leads + 25 calls ($0.38 each)
  - Growth Pack: $69 for 100 leads + 100 calls ($0.35 each, 10% savings)
  - Scale Pack: $249 for 400 leads + 400 calls ($0.31 each, 20% savings)
- **New API Endpoints**:
  - GET /api/pricing/plans - Public pricing information
  - GET /api/payg/packs - Available credit packs
  - POST /api/payg/purchase - Purchase credit pack
  - POST /api/payg/upgrade - Upgrade from free trial to PAYG
  - GET /api/payg/balance - Check credit balance and history
- **Landing Page Updated** - PAYG option prominently displayed with "No Commitment" badge
- **Competitive Positioning**: Now competes with Bland AI for low-volume users

### Session 12 (December 2025): CRM Integrations
- **CRMIntegrationService** - Universal CRM service supporting 3 providers:
  - GoHighLevel (GHL)
  - Salesforce
  - HubSpot
- **Secure Credential Storage** - API keys encrypted using Fernet encryption from JWT secret
- **Feature Access**:
  - Free/Starter/PAYG: No CRM access
  - Professional/Unlimited/BYL: Full CRM integration
- **Auto-Push on Qualification** - When a lead status changes to "qualified", automatically pushed to all connected CRMs as background task
- **New Database Collections**:
  - crm_credentials: Stores encrypted API keys per user/provider
  - crm_lead_push_logs: Audit trail of all CRM pushes
- **CRM API Endpoints**:
  - GET /api/crm/status - Get all CRM connection statuses
  - POST /api/crm/connect - Connect CRM with API key
  - POST /api/crm/disconnect/{provider} - Disconnect a CRM
  - GET /api/crm/push-logs - Get CRM push history
  - POST /api/crm/push-lead/{provider} - Manual lead push
  - GET /api/crm/oauth/callback - OAuth callback handler
- **CRM Integrations UI Page** (`/app/integrations`):
  - 3 provider cards with status, connect/disconnect buttons
  - "How it works" info banner
  - Recent Lead Syncs table with push history
  - Upgrade prompt for non-Professional users
- **Tests**: 16 CRM integration tests passing (`/app/backend/tests/test_crm_integration.py`)

### Session 13 (December 2025): Enhanced TCPA Compliance
- **Calling Hours Enforcement** - TCPA-compliant 8am-9pm local time restriction:
  - Area code to timezone mapping for 200+ US area codes
  - State identification from phone number
  - Automatic local time calculation
  - Clear "next allowed time" when blocked
- **State-Specific Restrictions** - Stricter than federal requirements:
  - Texas: 9am-9pm (SB 140)
  - Connecticut: 9am-8pm
  - Florida, Georgia, Louisiana, Massachusetts, Oklahoma, Rhode Island, Washington, Wisconsin: 8am-8pm
  - Pennsylvania: 9am-9pm
- **National DNC Registry Integration** (Real Phone Validation API):
  - National DNC Registry check
  - State DNC Registry check
  - **TCPA Litigator detection** (blocks known lawsuit-happy numbers)
  - Cell phone detection
  - 30-day caching per FTC requirements
  - Bulk upload endpoint for FTC data imports
- **Tiered DNC Allowances** (included in subscription):
  - Free: 50 checks/month (internal only)
  - PAYG: 100 checks/month + $0.015/overage
  - Starter: 500 checks/month + $0.012/overage
  - Professional: 2,000 checks/month + $0.01/overage
  - Unlimited: Unlimited checks
  - BYL: 1,500 checks/month + $0.01/overage
- **DNC Usage Tracking** - Monthly usage tracked per user with overage billing
- **Enhanced Compliance Endpoints**:
  - GET /api/compliance/status - TCPA configuration + DNC usage stats
  - GET /api/compliance/calling-hours/{phone} - Check calling window
  - GET /api/compliance/national-dnc/{phone} - Check National + State DNC + Litigator
  - POST /api/compliance/national-dnc/upload - Bulk DNC list import
- **7 Pre-Call Checks**: calling_hours, internal_dnc, national_dnc, state_dnc, litigator, number_verification, call_frequency
- **Tests**: 24 TCPA compliance tests passing (`/app/backend/tests/test_tcpa_compliance.py`)

### Session 14 (December 2025): Zero-Cost DNC Compliance Solution
- **DNC Management Admin UI** (`/app/dnc`) - Full-featured compliance dashboard:
  - National DNC List card with upload, stats, refresh status
  - TCPA Litigators card with add/upload/remove functionality
  - Internal DNC List card (auto-managed from call opt-outs)
  - Critical refresh reminder alerts (31-day FTC requirement)
- **FTC Data Integration**:
  - POST /api/compliance/dnc/upload-ftc - Bulk import FTC DNC data files
  - GET /api/compliance/dnc/stats - DNC database statistics
  - GET /api/compliance/dnc/refresh-reminder - 31-day refresh reminder
  - Supports FTC standard format (.txt, .csv with 10-digit numbers)
- **TCPA Litigator Management**:
  - POST /api/compliance/litigators/upload - Bulk import litigator list
  - POST /api/compliance/litigators/add - Add single litigator
  - GET /api/compliance/litigators - List all litigators
  - DELETE /api/compliance/litigators/{phone} - Remove litigator
  - GET /api/compliance/litigators/info - Litigator protection guide
  - Automatic blocking of calls to known TCPA plaintiffs
- **FTC Data Instructions Tab** - Step-by-step guide to download free FTC DNC data
- **Cost**: $0/month (uses free FTC data + Twilio Lookup already included)

### Session 15 (December 2025): Compliance Setup & Acknowledgment System
- **Compliance Setup Page** (`/app/compliance`) - Guided onboarding for TCPA compliance:
  - B2B vs B2C calling mode selection with clear cost differences
  - B2B: $0 cost, no FTC registration (recommended)
  - B2C: FTC registration required, DNC data purchase ($82-$22k/year)
  - 4 acknowledgment checkboxes (DNC responsibility, TCPA rules, calling hours, litigator risk)
  - Progress tracking (0-100%)
  - Compliance checklist with actionable items
- **User Compliance Fields** added to User model:
  - compliance_acknowledged (bool)
  - compliance_acknowledged_at (timestamp)
  - compliance_acknowledged_version (string)
  - ftc_san (FTC Subscription Account Number for B2C)
  - calling_mode ("b2b" or "b2c")
- **Compliance Endpoints**:
  - GET /api/compliance/acknowledgment - Get acknowledgment status
  - POST /api/compliance/acknowledge - Submit acknowledgment
  - GET /api/compliance/setup-guide - Get checklist and guides
- **Compliance Audit Trail** - All acknowledgments logged for legal protection
- **Resources Section** - FAQ accordion with B2B/B2C explanation, penalties, AI disclosure info

### Session 16 (December 2025): Setup Instructions & Onboarding Wizard
- **Getting Started Page** (`/app/getting-started`) - Permanent setup checklist:
  - Progress tracking with percentage (0-100%)
  - 5 required + 1 optional setup steps with expand/collapse instructions
  - Step-by-step guidance with "Go to Setup" navigation buttons
  - "Calling Features Locked" warning when setup incomplete
  - "You're All Set!" success banner when all required steps complete
  - External links to Twilio Console, Calendly for account creation
- **Setup Wizard Modal** - First-login guided setup:
  - Appears automatically for new users (setup_wizard_completed=false)
  - Step-by-step walkthrough of all 5 required setup tasks
  - Shows completion status (Completed/Pending badge) for each step
  - Can be skipped with toast notification pointing to Getting Started page
  - Minimizable to continue working while keeping wizard accessible
  - Progress bar showing overall setup completion
- **Call Blocking Feature** - Blocks AI calls until setup complete:
  - FunnelPage and LeadDiscovery simulateCall checks setup status
  - Shows toast with "Go to Setup" action when blocked
  - Uses `can_make_calls` flag from /api/setup/status
- **Setup Status API Endpoints**:
  - GET /api/setup/status - Returns all steps with completion status
  - GET /api/setup/can-call - Quick check for call gating
  - POST /api/user/setup-wizard-complete - Mark wizard as done
- **Required Setup Steps Tracked**:
  1. Twilio Voice connection (env vars or settings)
  2. Calendly booking links (via agents with calendly_link)
  3. Compliance acknowledgment (compliance_acknowledged=true)
  4. First agent created (agents collection count)
  5. First campaign created (campaigns collection count)
- **Tests**: 24 setup status tests passing (`/app/backend/tests/test_setup_status.py`)

### Session 17 (December 2025): Synthflow-style Free Trial
- **Time-based Free Trial** - 15 minutes of call time (no credit card required):
  - New users get `trial_minutes_total: 15.0` instead of lead/call credits
  - `trial_seconds_used` tracks actual call duration consumed
  - `trial_expired` flag marks when trial is exhausted
  - `subscription_status: "trialing"` for trial users
- **Trial Status API** - Real-time trial tracking:
  - GET /api/user/trial-status - Returns trial info (is_trial, trial_active, minutes_remaining, etc.)
  - GET /api/auth/me - Now includes `trial_status` object in response
  - Paid users get `is_trial: false`, `minutes_remaining: -1` (unlimited)
- **Call Duration Tracking** - Automatic deduction on call completion:
  - Twilio status webhook (`/api/twilio/status`) deducts call duration from trial
  - `deduct_trial_time()` helper updates `trial_seconds_used` and `trial_expired`
- **Call Blocking** - Trial users blocked when expired:
  - `/api/calls/initiate` returns 402 with upgrade message for expired trials
  - `/api/calls/simulate` also checks trial status before allowing calls
- **TrialBanner Component** - Dynamic UI based on trial state:
  - Info (cyan): >7 minutes remaining - "Free Trial: X min of call time remaining"
  - Warning (amber): 3-7 minutes - "Trial running low"
  - Critical (red pulsing): <3 minutes - "Trial Almost Over!"
  - Expired (red): "Free Trial Expired" with prominent "Upgrade Now" button
  - Progress bar showing usage percentage
  - Paid users do not see any trial banner
- **Tests**: 8 trial feature tests passing (`/app/backend/tests/test_trial_features.py`)

### Session 18 (December 2025): Phone Verification for Trial Abuse Prevention
- **SMS Phone Verification** - Required for ALL trial users (email/password AND OAuth):
  - POST /api/auth/send-verification - Sends 6-digit SMS code via Twilio
  - POST /api/auth/verify-phone - Validates code and returns verification token
  - POST /api/auth/verify-phone-oauth - Completes verification for logged-in OAuth users
  - Codes expire after 10 minutes, max 5 attempts
  - 1-minute cooldown between resend requests
- **Trial Phone Number Tracking** - `trial_phone_numbers` collection:
  - Each phone can only be used for ONE free trial
  - Blocks same phone from creating multiple trial accounts
  - Stores user_id, email, and timestamp for audit trail
- **Updated Registration Flow (Email/Password)**:
  - Step 1: Enter name, email, phone, password
  - Step 2: Enter 6-digit SMS code
  - Step 3: Account created with verified phone
- **OAuth Users Also Require Phone Verification**:
  - PhoneVerificationModal appears after OAuth login if phone not verified
  - User must verify phone before accessing any trial features
  - Call initiation blocked with 403 error until phone verified
- **User Model Updates**:
  - `phone_number` - Verified phone stored on user
  - `phone_verified` - Boolean flag for verification status
- **API Updates**:
  - `/api/user/trial-status` includes `phone_verification_required` flag
  - `/api/calls/initiate` and `/api/calls/simulate` check `phone_verified` for trial users

## Prioritized Backlog

### P0 - Critical
- [x] ~~Stripe Integration - Real checkout sessions for subscriptions and packs~~ ✅ DONE
- [x] ~~Twilio Media Streams WebSocket - Real-time AI conversations~~ ✅ DONE
- [x] ~~Custom Keywords (up to 100) for lead discovery~~ ✅ DONE
- [x] ~~In-App Training Guide & Help Chat~~ ✅ DONE
- [x] ~~Phone Verification (Twilio Lookup)~~ ✅ DONE
- [x] ~~AMD + Voicemail Drop~~ ✅ DONE
- [x] ~~ICP Scoring~~ ✅ DONE
- [x] ~~Setup Instructions / Onboarding Wizard~~ ✅ DONE (December 2025)
- [x] ~~Synthflow-style Free Trial (15 minutes of call time)~~ ✅ DONE (December 2025)
- [x] ~~ElevenLabs Voice Cloning~~ ✅ DONE (March 2026) - Clone custom voices for AI agents

### P1 - High Priority
- [x] ~~Multi-tenant data isolation - Scope leads/campaigns to user accounts~~ ✅ DONE (December 2025)
- [x] ~~Subscription tier enforcement - Limit features by plan~~ ✅ DONE (December 2025)
- [x] ~~Low balance notification system~~ ✅ DONE (December 2025)
- [x] ~~ICP configuration UI in campaign form~~ ✅ DONE (December 2025)
- [x] ~~Calendar/Calendly integration for auto-booking~~ ✅ DONE (December 2025)
- [x] ~~CRM Integrations (GoHighLevel, Salesforce, HubSpot)~~ ✅ DONE (December 2025)
- [x] ~~Phone Verify Button - Individual & bulk verify with line type filter~~ ✅ DONE (December 2025)
- [ ] Improve STT accuracy - Consider Deepgram for lower latency

### P2 - Medium Priority
- [ ] Connect real Stripe checkout for PAYG credit packs (Blocked: waiting for domain + Stripe approval)
- [ ] Low-balance email notifications
- [ ] Auto-suggest plan upgrades based on top-up purchases
- [ ] Stripe recurring subscriptions (currently one-time payments)
- [ ] Domain setup for dialgenix.ai

### P3 - Future
- [ ] **Multi-language support** (50+ languages like Synthflow) - Currently English only
- [ ] **Bulk Voice Assignment** - Assign same cloned voice to multiple agents at once
- [ ] Team seat management
- [ ] API rate limiting by tier
- [ ] Refactor App.js (2000+ lines) into smaller components
- [ ] Two-party call recording disclosure (state-specific)
- [ ] Consent tracking system (TCPA express written consent)
- [ ] Parallel dialing (Orum-style)
- [ ] Call Analytics Dashboard
- [ ] A/B testing for call scripts
- [x] ~~Automated Follow-Up Calls~~ ✅ DONE (March 2026)

## Testing
- Backend: pytest suite at `/app/backend/tests/test_auth_and_api.py`
- Multi-tenant isolation tests: `/app/backend/tests/test_multi_tenant_isolation.py` (31 tests)
- Subscription tier tests: `/app/backend/tests/test_subscription_tiers.py` (16 tests)
- CRM integration tests: `/app/backend/tests/test_crm_integration.py` (16 tests)
- TCPA compliance tests: `/app/backend/tests/test_tcpa_compliance.py` (24 tests)
- Setup status tests: `/app/backend/tests/test_setup_status.py` (24 tests)
- Phone verification tests: `/app/backend/tests/test_phone_verification.py` (12 tests)
- Trial features tests: `/app/backend/tests/test_trial_features.py` (8 tests)
- Voice cloning tests: `/app/backend/tests/test_voice_cloning.py` (10 tests)
- Voice preview tests: `/app/backend/tests/test_voice_preview.py` (8 tests)
- Auth testing playbook: `/app/auth_testing.md`
- Test reports: `/app/test_reports/iteration_1.json` through `/app/test_reports/iteration_9.json`
- Test users:
  - User A (admin): test@example.com / Test123!
  - User B (free): test_user_b@example.com / Test456!
  - Starter user: test_starter_1ea49b76@example.com / Test123!
  - Trial users (for testing trial states):
    - Fresh trial: trial_fresh_befc8abc@test.com / Test123!
    - Low trial (5 min): trial_low_355019df@test.com / Test123!
    - Critical trial (2 min): trial_critical_a44e1a05@test.com / Test123!
    - Expired trial: trial_test_1774537902@test.com / Test123!

## 3rd Party Integrations Status
| Service | Status | Notes |
|---------|--------|-------|
| OpenAI GPT-5.2 | ✅ Active | Via Emergent LLM Key |
| OpenAI Whisper | ✅ Active | STT for caller audio |
| Emergent Auth | ✅ Active | Google OAuth |
| ElevenLabs | ✅ Active | TTS voice generation, μ-law output, Voice Cloning (IVC) |
| Stripe | ✅ Active | Test keys, checkout working |
| Twilio | ✅ Active | Live outbound calls + Media Streams |
| Resend | ⚠️ Requires Key | Email notifications |
| GoHighLevel | ✅ Ready | CRM integration - requires user API key |
| Salesforce | ✅ Ready | CRM integration - requires user API key |
| HubSpot | ✅ Ready | CRM integration - requires user API key |
| Real Phone Validation | ⚠️ Ready | DNC Plus API - configure DNC_API_KEY |

### Session 10 (March 2026): Voice Cloning Integration
- **ElevenLabs Voice Cloning (IVC)** - Clone custom voices for AI agents (Synthflow/Bland AI parity)
  - Upload 1-5 audio samples (MP3/WAV, 30+ seconds total)
  - Pro+ subscription required for voice cloning
  - Maximum 5 cloned voices per user
  - Voice tuning controls: Stability, Similarity, Style
- **Voice Cloning UI Components**:
  - `VoiceCloneModal` - Upload audio samples, name voice, clone via ElevenLabs API
  - `VoiceSettingsModal` - Select preset or cloned voice, tune voice parameters, preview
- **Agent Voice Assignment** - Each agent can use preset or custom cloned voice
- **Voice Preview on Agent Cards** - Play button to hear agent's voice before launching campaigns
  - Play/Pause toggle with visual state feedback (purple=idle, green=playing)
  - Uses ElevenLabs TTS for real-time audio generation
  - Custom preview text: "Hi, this is {agent_name}. I'm your AI sales agent..."
- **Synthflow-Style Subscription Billing System**:
  - `POST /api/subscriptions/create` - Create recurring Stripe subscription
  - `GET /api/subscriptions/portal` - Access Stripe Customer Portal for self-service management
  - `GET /api/subscriptions/current` - Get current subscription details
  - `GET /api/subscriptions/invoices` - Invoice history with downloadable PDFs
  - `POST /api/webhook/stripe-subscriptions` - Handle subscription lifecycle webhooks
  - `GET /api/usage/current-period` - Track usage and calculate overage charges
  - Auto-recurring billing on same day each month
  - Credit refresh on invoice.paid webhook
  - Late payment handling (past_due status after 5 days)
- **Backend Endpoints**:
  - `GET /api/voices/presets` - 10 ElevenLabs preset voices
  - `GET /api/voices/cloned` - User's cloned voices
  - `POST /api/voices/clone` - Clone voice with file upload
  - `POST /api/voices/preview` - Generate voice preview audio
  - `PUT /api/agents/{id}/voice` - Update agent voice settings
  - `DELETE /api/voices/cloned/{id}` - Delete cloned voice
- **Automated Follow-Up Call System** (Synthflow-style):
  - `GET /api/followups` - Get scheduled follow-up calls
  - `POST /api/followups` - Manually schedule a follow-up
  - `GET /api/followups/pending` - Get overdue follow-ups ready to execute
  - `POST /api/followups/{id}/execute` - Execute a scheduled follow-up call
  - `POST /api/followups/{id}/complete` - Mark complete with optional retry
  - `DELETE /api/followups/{id}` - Cancel a scheduled follow-up
  - `POST /api/followups/schedule-callback` - Schedule callback at lead's requested time
  - `GET /api/followups/stats` - Get follow-up statistics
  - `GET /api/followup-sequences` - Get multi-touch sequence templates
  - `POST /api/followup-sequences` - Create sequence template
  - `PUT /api/campaigns/{id}/followup-settings` - Configure campaign follow-up rules
  - `GET /api/campaigns/{id}/followup-settings` - Get campaign follow-up rules
  - Auto-scheduling after no-answer/voicemail via `auto_schedule_followup()` helper
- **Demo Narration System** (Landing Page):
  - `GET /api/demo/narration/{step_id}` - Generate audio narration for demo steps
  - Uses 3 distinct ElevenLabs voices to showcase AI variety:
    - Step 1 (Visual Sales Funnel): Rachel - professional female
    - Step 2 (AI Lead Discovery): Antoni - well-rounded calm male
    - Step 3 (Call Recordings): Bella - soft warm female
  - Audio is cached after first generation for performance
- **Call Yourself Demo** (New Trial Funnel):
  - `POST /api/demo/call-yourself` - Let users experience AI by calling their own phone
  - `GET /api/demo/twiml/{demo_call_id}` - TwiML for demo call
  - `GET /api/demo/calls-remaining` - Check remaining demo calls (2 free per user)
  - Low-cost way to prove AI quality without burning leads (~$0.50/call)
- **Silence Detection & Auto-Callback**:
  - 3 consecutive no-responses (12+ sec silence) triggers callback scheduling
  - AI says "Sounds like this might not be a good time. I'll give you a call back later!"
  - Auto-schedules follow-up call instead of burning the lead
  - 10-minute max call duration hard cap for cost protection

---

## Changelog

### December 2025 (Latest Session)

#### Completed This Session:
- **Voice Tuning Improvements**: Updated demo call to use ElevenLabs multilingual_v2 model with expressive settings (stability 0.5, similarity 0.75)
- **Voice Settings Modal Enhancement**: Added Quick Presets (Professional/Conversational/Energetic), contextual tips for each slider, Quick Setup Guide
- **Help System Implementation**:
  - Floating Help Button with interactive walkthroughs (driver.js)
  - 5 Product Tours (Dashboard, Agents, Voice Settings, Campaigns, Leads)
  - Full Help Center page (`/help`) with searchable FAQ
  - Video tutorial placeholders ready for Loom embeds
- **Video Tutorial Scripts**: Created 5 complete scripts in `/frontend/public/tutorials/VIDEO_SCRIPTS.md`
- **Step-by-Step Text Guides**: Added 6 comprehensive guides to Help Center (Quick Start, Agent Setup, Voice Tuning, Campaign Launch, Lead Discovery, Troubleshooting)
- **Caller ID Rotation Feature**: Added Number Pool management in Settings with:
  - Add/remove Twilio numbers to rotation pool
  - 3 rotation modes: Round-robin, Random, Geographic
  - Enable/disable toggle
  - Full setup instructions and benefit explanations
  - Pricing breakdown ($1-2/number + $39/month add-on or free on Pro+)

#### TO-DO LIST (Pending User Action):
1. **[ ] Record Loom Video Tutorials** - Scripts ready at `/frontend/public/tutorials/VIDEO_SCRIPTS.md`
   - VIDEO 1: 5-Minute Quickstart (5:00)
   - VIDEO 2: Setting Up AI Agents (4:15)
   - VIDEO 3: Voice Tuning Masterclass (3:45)
   - VIDEO 4: Launching Your First Campaign (5:00)
   - VIDEO 5: AI Lead Discovery (3:20)
   - After recording, add YouTube/Loom URLs to `ProductTour.jsx` → `VIDEO_TUTORIALS` object

2. **[ ] Generate AI Voiceover Audio** - Use ElevenLabs to generate MP3s from scripts (optional - user can narrate themselves)

3. **[ ] Update Twilio Inbound Webhook** - Point to current production URL for inbound sales agent testing

#### Technical Debt:
- [ ] Refactor `server.py` (11,400+ lines) into modular files
- [ ] Refactor `App.js` (4,200+ lines) into smaller components

### March 2026
- **New Trial Funnel**: Added $29/50 calls "Test Drive" plan, "Call Yourself" demo feature, and sandbox mode concept
- **Silence Detection + Auto-Callback**: Protects against runaway calls - 3 silences = schedule callback and hang up
- **10-Min Max Call Duration**: Hard cap to prevent cost overruns
- **Landing Page Updates**: Trust section with logos/badges, value prop callout, credit packs mention, feature order fix, GHL added to CRM integrations
- **Demo Voice Change**: Step 2 now uses Antoni (calm male) instead of Josh

### April 2026
- **Homepage Pricing Update**: Increased all prices for better profit margins
  - Test Drive: $29 → $49
  - BYOL Starter: $149 → $199, Pro: $349 → $449, Scale: $599 → $799
  - Discovery Starter: $299 → $399, Pro: $699 → $899, Elite: $1,299 → $1,599
  - Updated comparison table: $499-999 → $199-899
- **Apollo.io Badge Added**: Added Apollo.io to partner logos section on homepage
- **Credit Card Processing Script Template**: Added as preset use case in Agent Creation
  - Full objection handlers for "happy with current rates", "locked in contract", etc.
  - 20-40% savings hook, contract status qualifying questions
- **Comprehensive Instruction Tips**: Added 💡 tips across all major pages:
  - Lead Discovery: "Powered by Apollo.io's 275M+ B2B database..."
  - Campaigns: "Each campaign has its own script and settings..."
  - Agents: "Create an agent for each product/service..."
  - Call History: "Click any call to see the full transcript..."
  - Settings: "Connect Twilio for calls, ElevenLabs for voice..."
  - Funnel: "Drag leads between stages or click to call..."
  - Bookings: "Bookings sync with Calendly automatically..."
  - Compliance: "Required for TCPA compliance..."
  - Credit Packs: "Subscriptions reset monthly..."
  - Campaign Creation Modal: Script tips with {company}, {contact_name} variables
  - Agent Creation Modal: Use case-specific tips for each template
- **MongoDB Connection Fix**: Fixed TLS issue for localhost connections
- **Call Analytics Dashboard**: New page with key metrics (Total Calls, Answer Rate, Qualified Leads, Booking Rate), daily call charts, call outcomes breakdown, top performing campaigns, and best calling times
- **A/B Script Testing**: Added to Campaign creation - test two scripts with configurable traffic split (10%-90%), track results in Analytics
- **Low Balance Alerts**: Settings UI with enable/disable toggle, configurable lead/call credit thresholds, email notifications
- **Agency White-labeling**: Settings to hide DialGenix branding, custom brand name input, custom logo URL, brand color picker

### December 2025
- **3 Voice Demo Narrations**: Landing page demo buttons now use 3 distinct ElevenLabs voices (Rachel, Antoni, Bella) to showcase AI voice variety to visitors
