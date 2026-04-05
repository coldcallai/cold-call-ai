# DialGenix.ai Test Credentials

## Admin User (Unlimited Tier)
- **Email**: test@example.com
- **Password**: Test123!
- **Tier**: unlimited
- **Phone Verified**: Yes

## Free Trial User
- **Email**: freetrial@test.com
- **Password**: Test123!
- **Tier**: free
- **Phone Verified**: No

## User B (Testing Multi-tenant)
- **Email**: test_user_b@example.com
- **Password**: Test456!
- **Tier**: starter

## Trial State Test Users
| State | Email | Password |
|-------|-------|----------|
| Fresh trial | trial_fresh_befc8abc@test.com | Test123! |
| Low trial (5 min) | trial_low_355019df@test.com | Test123! |
| Critical trial (2 min) | trial_critical_a44e1a05@test.com | Test123! |
| Expired trial | trial_test_1774537902@test.com | Test123! |

## Starter Tier User
- **Email**: test_starter_1ea49b76@example.com
- **Password**: Test123!
- **Tier**: starter

---
Last Updated: April 2026

## Notes
- Auth module has been refactored (Phase 2 Strangler Fig) - USE_NEW_AUTH_ROUTES=true
- Leads module has been refactored (Phase 3 Strangler Fig) - USE_NEW_LEADS_ROUTES=true
- Agents module has been refactored (Phase 4 Strangler Fig) - USE_NEW_AGENTS_ROUTES=true
- Campaigns module has been refactored (Phase 5 Strangler Fig) - USE_NEW_CAMPAIGNS_ROUTES=true
- Calls module has been refactored (Phase 6 Strangler Fig) - USE_NEW_CALLS_ROUTES=true
- Bookings/Settings/Billing modules have been refactored (Phase 7 Strangler Fig)
  - USE_NEW_BOOKINGS_ROUTES=true
  - USE_NEW_SETTINGS_ROUTES=true
  - USE_NEW_BILLING_ROUTES=true
- All auth endpoints work with both Bearer tokens and session cookies
- Backend refactoring COMPLETE - 8 modules extracted, 148 total tests passing

## Additional Test User
- **User B**: test_user_b@example.com / Test456! (used for multi-tenant isolation tests)
