# DialGenix.ai Refactoring Plan

## Strategy: Strangler Fig Pattern (Incremental Refactor)

### Why This Approach
- **Zero downtime** - Production stays stable
- **Instant rollback** - Feature flags enable/disable new code
- **Low risk** - One domain at a time
- **Testable** - Each phase can be verified independently

---

## Migration Order

### Phase 1: Models ✅ DONE
- Created `/app/backend/models/` directory
- Files: enums.py, user.py, lead.py, agent.py, campaign.py, call.py, booking.py, followup.py, compliance.py, billing.py, crm.py

### Phase 2: Auth ✅ DONE
- [x] Create `routes/auth.py`
- [x] Create `services/auth_service.py`
- [x] Add feature flag `USE_NEW_AUTH_ROUTES`
- [x] Test and deploy
- Files: /app/backend/routes/auth.py, /app/backend/services/auth_service.py
- Feature flag: USE_NEW_AUTH_ROUTES=true (set in .env)

### Phase 3: Leads ✅ DONE
- [x] Create `routes/leads.py`
- [x] Create `services/lead_service.py`
- [x] Add feature flag `USE_NEW_LEADS_ROUTES`
- [x] Test and deploy
- Files: /app/backend/routes/leads.py, /app/backend/services/lead_service.py
- Feature flag: USE_NEW_LEADS_ROUTES=true (set in .env)
- Endpoints migrated: /api/leads, /api/leads/discover, /api/leads/gpt-intent-search, /api/leads/upload-csv, /api/leads/export-csv, /api/leads/{id}, /api/leads/{id}/verify-phone, /api/leads/batch-icp-score, /api/leads/preview-examples, /api/leads/phone-stats

### Phase 4: Agents ✅ DONE
- [x] Create `routes/agents.py`
- [x] Create `services/agent_service.py`
- [x] Add feature flag `USE_NEW_AGENTS_ROUTES`
- [x] Test and deploy
- Files: /app/backend/routes/agents.py, /app/backend/services/agent_service.py
- Feature flag: USE_NEW_AGENTS_ROUTES=true (set in .env)
- Endpoints migrated: /api/agents (CRUD), /api/voices/presets, /api/voices/cloned, /api/voices/clone, /api/voices/preview, /api/agents/{id}/voice

### Phase 5: Campaigns ✅ DONE
- [x] Create `routes/campaigns.py`
- [x] Create `services/campaign_service.py`
- [x] Add feature flag `USE_NEW_CAMPAIGNS_ROUTES`
- [x] Test and deploy
- Files: /app/backend/routes/campaigns.py, /app/backend/services/campaign_service.py
- Feature flag: USE_NEW_CAMPAIGNS_ROUTES=true (set in .env)
- Endpoints migrated: /api/campaigns (CRUD), /api/campaigns/{id}/start, /api/campaigns/{id}/pause, /api/campaigns/{id}/score-all-leads, /api/campaigns/{id}/followup-settings

### Phase 6: Calls ✅ DONE
- [x] Create `routes/calls.py`
- [x] Create `services/call_service.py`
- [x] Add feature flag `USE_NEW_CALLS_ROUTES`
- [x] Test and deploy
- Files: /app/backend/routes/calls.py, /app/backend/services/call_service.py
- Feature flag: USE_NEW_CALLS_ROUTES=true (set in .env)
- Endpoints migrated: /api/calls (list), /api/calls/{id}, /api/calls/twilio-status, /api/calls/{id}/amd-status, /api/calls/{id}/recording, /api/calls/{id}/transcript, /api/calls/{id}/transcribe, /api/analytics
- NOTE: Twilio webhooks, /api/calls/initiate, and realtime WebSocket remain in server.py for stability

### Phase 7: Remaining ✅ DONE
- [x] Create `routes/bookings.py` and `services/booking_service.py`
- [x] Create `routes/settings.py`
- [x] Create `routes/billing.py`
- [x] Add feature flags: USE_NEW_BOOKINGS_ROUTES, USE_NEW_SETTINGS_ROUTES, USE_NEW_BILLING_ROUTES
- Files created:
  - /app/backend/routes/bookings.py, /app/backend/services/booking_service.py
  - /app/backend/routes/settings.py
  - /app/backend/routes/billing.py
- Endpoints migrated:
  - Bookings: /api/bookings (CRUD), /api/bookings/{id}/status
  - Settings: /api/settings, /api/packs, /api/account/usage, /api/team/members, /api/team/invite
  - Billing: /api/subscription/features, /api/subscriptions/create, /api/subscriptions/portal, /api/subscriptions/current, /api/subscriptions/invoices
- NOTE: Stripe webhooks, Twilio webhooks, and demo endpoints remain in server.py

---

## Feature Flag Implementation

```python
# server.py
import os

# Feature flags for gradual migration
USE_NEW_AUTH_ROUTES = os.getenv("USE_NEW_AUTH_ROUTES", "false").lower() == "true"
USE_NEW_LEADS_ROUTES = os.getenv("USE_NEW_LEADS_ROUTES", "false").lower() == "true"
USE_NEW_AGENTS_ROUTES = os.getenv("USE_NEW_AGENTS_ROUTES", "false").lower() == "true"
USE_NEW_CALLS_ROUTES = os.getenv("USE_NEW_CALLS_ROUTES", "false").lower() == "true"

# Conditional router inclusion
if USE_NEW_AUTH_ROUTES:
    from routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/api")

if USE_NEW_LEADS_ROUTES:
    from routes.leads import router as leads_router
    app.include_router(leads_router, prefix="/api")
```

### .env Configuration
```
USE_NEW_AUTH_ROUTES=false
USE_NEW_LEADS_ROUTES=false
USE_NEW_AGENTS_ROUTES=false
USE_NEW_CALLS_ROUTES=false
```

---

## Deployment Process (Per Phase)

1. **Develop** - Create new route/service files
2. **Test Preview** - Verify on Emergent preview environment
3. **Sync to VPS** - With feature flag OFF (disabled)
4. **Enable Flag** - Turn on in .env, restart PM2
5. **Monitor** - Watch logs for errors
6. **Rollback if needed** - Disable flag, restart PM2
7. **Cleanup** - Remove old code once stable

---

## Current File Sizes (Reference)

| File | Lines | Status |
|------|-------|--------|
| server.py | 11,600+ | Needs refactoring |
| App.js | 5,500+ | Needs refactoring |

---

## Notes

- **DO NOT** rewrite server.py all at once
- **DO** migrate one domain at a time
- **DO** keep old code as fallback until new code is proven stable
- **DO** use feature flags for instant rollback capability

Last Updated: April 2026
