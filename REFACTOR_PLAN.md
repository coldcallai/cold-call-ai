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

### Phase 3: Leads (Medium risk)
- [ ] Create `routes/leads.py`
- [ ] Create `services/lead_service.py`
- [ ] Add feature flag `USE_NEW_LEADS_ROUTES`
- Endpoints to migrate: /api/leads, /api/leads/discover, /api/leads/gpt-intent-search, /api/leads/upload-csv, /api/leads/export-csv, /api/leads/{id}, /api/leads/{id}/verify-phone, /api/leads/batch-icp-score

### Phase 4: Agents (Medium risk)
- [ ] Create `routes/agents.py`
- [ ] Create `services/agent_service.py`

### Phase 5: Calls/Twilio (Higher risk - core feature)
- [ ] Create `routes/calls.py`
- [ ] Create `services/twilio_service.py`
- [ ] Create `services/elevenlabs_service.py`

### Phase 6: Remaining (Final cleanup)
- [ ] routes/campaigns.py
- [ ] routes/bookings.py
- [ ] routes/settings.py
- [ ] routes/compliance.py
- [ ] routes/billing.py

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
