# DialGenix.ai - AI Cold Calling SaaS Platform

## Original Problem Statement
Build an AI cold calling machine that calls businesses, qualifies them, and routes qualified leads to different sales agents for payment processing.

## Product Vision
A vertical-agnostic B2B SaaS platform that:
1. Discovers high-intent leads via GPT-5.2
2. Executes AI cold calls with natural voice (ElevenLabs Flash v2)
3. Qualifies leads with DISC personality detection
4. Books meetings via Calendly or live transfers to human agents
5. Full TCPA compliance built-in

## Current Status: PRE-LAUNCH
- Platform fully functional
- Domain: dialgenix.ai (rebranding to intentcue.ai pending)
- ElevenLabs: 8 credits remaining, resets May 5 or upgrade to Scale
- All voice now uses eleven_flash_v2 (2x more efficient than multilingual_v2)

## Architecture
- **Frontend:** React 18, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, Motor (async MongoDB)
- **Voice Pipeline:** Twilio → FastAPI WebSocket → GPT-5.2 → ElevenLabs Flash v2
- **Pricing:** BYOK model (users bring own Twilio + ElevenLabs keys)

## Key Features by Section

### Getting Started
- Setup checklist with progress %
- Step-by-step instructions for Twilio, ElevenLabs, compliance

### BYOK Setup Wizard
- 4-step guided onboarding (Welcome, Twilio, ElevenLabs, Complete)
- Cost comparison vs competitors
- Encrypted credential storage (Fernet)
- Real-time balance verification

### Credit Alert Banner
- Global warning when Twilio <$10 or ElevenLabs <20%
- Polls every 5 minutes, dismissible

### Sales Funnel
- Kanban board: New → Contacted → Qualified → Booked

### Lead Discovery
- GPT-powered intent search
- CSV upload
- Phone verification (mobile/landline/VoIP)
- ICP scoring

### Campaigns
- Full AI script editor with use case templates
- DISC personality detection questions
- A/B script testing
- Dial Settings: calls/day, calls/hour, start/end time, calling days
- Voicemail drop (AMD detection)
- Follow-up settings
- ICP configuration

### Agents
- Use case templates (Sales, Credit Card, Appointment, Receptionist, Customer Service)
- Voice cloning (ElevenLabs IVC)
- Voice tuning (stability, similarity, expressiveness)
- Voice preview
- Live transfer to human
- Auto AI disclosure (mobile vs landline)
- 50+ language support

### Bookings
- Calendly-synced meetings
- Filter by status/agent

### Call History
- Recording playback
- Full transcripts
- AMD status
- Call outcomes

### Analytics
- Answer rate, qualified leads, booking rate
- Daily charts, top campaigns, best calling times

### CRM Integrations
- GoHighLevel, Salesforce, HubSpot
- Auto-push qualified leads

### Compliance
- B2B/B2C mode selection
- TCPA acknowledgment
- Calling hours enforcement (8am-9pm local + state-specific)
- DNC management (National, State, Internal, Litigator)

### Settings
- BYOK Twilio/ElevenLabs config
- Low balance alerts
- Caller ID rotation
- White-labeling
- Team management

## Prioritized Backlog

### P0 - Critical
- [x] All core features complete

### P1 - High Priority
- [ ] Industry script template library (roofing, dental, legal, etc.)
- [ ] IntentCue.ai rebrand

### P2 - Medium Priority
- [ ] Predictive dialer (parallel calling)
- [ ] Open Dental RPA integration
- [ ] Payment Overlay Platform

### P3 - Future
- [ ] Calendly Webhook Sync
- [ ] Deepgram STT (cost optimization)
- [ ] More SEO pages

## Testing
- Backend: pytest suites (200+ tests across all modules)
- Test reports: /app/test_reports/iteration_1.json through iteration_18.json
- Admin test user: test@example.com / Test123!

## 3rd Party Integrations
| Service | Status | Model |
|---------|--------|-------|
| OpenAI GPT-5.2 | Active | Via Emergent LLM Key |
| ElevenLabs | Active | eleven_flash_v2 (switched from multilingual_v2) |
| Twilio | Active | Token rotated April 2026 |
| Stripe | Active | Live keys |
| Emergent Auth | Active | Google OAuth |

## Recent Changes (April 13, 2026)
- Switched all ElevenLabs TTS from eleven_multilingual_v2 to eleven_flash_v2 (2x efficiency)
- Added disk caching for inbound audio (no ElevenLabs credit burn on restart)
- Added Campaign Dial Settings (calls/day, calls/hour, start/end time, calling days)
- Created agency/sales team campaign script with 7-state flow
- Created audio generation script for cached demo audio
- Fixed GitHub secret exposure, rotated Twilio token, repo set to private
- BYOK Setup Wizard with encrypted credential storage
- Credit Alert Banner for low Twilio/ElevenLabs balances
- FAQ entry for free trial question
