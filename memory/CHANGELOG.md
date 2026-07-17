# CHANGELOG

## 2026-06 — Cloned-Voice Voicemail Drop: surgical deploy package delivered
- Verified voicemail source is intact in repo (backend/services/vm_cloned_audio.py + 5 test_vm_*.py + voicemail hunks in server.py & routes/campaigns.py).
- Re-ran full VM test suite: 33 passed, 1 skipped; the 4 negative-path tests are env-gated (assert 400 only when TWILIO_PHONE_NUMBER='' AND user has no phone) and were confirmed passing under that config. `resolve_callback_number` 3-tier fallback (campaign → user.phone_number → TWILIO_PHONE_NUMBER) working as designed.
- Downloaded user-uploaded PROD baselines (assets #424/#425); SHAs match recorded 64636d32… / 7c46aa66…
- Built a validated SURGICAL patch (voicemail-only) that applies cleanly onto the drifted prod baseline WITHOUT wholesale-replacing files:
  - `deploy/voicemail_drop/patches/vm_server.patch` (8 hunks)
  - `deploy/voicemail_drop/patches/vm_campaigns.patch` (6 hunks)
  - Deliberately EXCLUDED non-voicemail drift: twilio_sms_number/10DLC, RankTrust webhook, brain/tts_speak/inbound-handler rewrites, demo-audio refactor.
  - Validation: git apply --check clean vs baseline, py_compile OK, result reproduces validated target byte-for-byte, no duplicate defs, deps (eleven_client) present.
- Added `deploy/voicemail_drop/deploy_voicemail.sh` (baseline SHA guard → backup → dry-run → apply → copy new files → hash verify → run VM tests → restart backend PM2 only → E2E prompt → rollback) and `README.md`.
- testing_agent iter33: 100% backend pass (19/19, 1 documented skip). Feature deploy-ready.
- Delivery method: GitHub (user to click "Save to Github"). VPS NOT touched.

### Post-patch verification hashes
- backend/server.py after patch: 61f45a15ab60626a76441cfccee6e34e724d67e7f8837d790526aabb8bd0e8a4
- backend/routes/campaigns.py after patch: 2bb9b0812f3cca0a34d33a2f55ac0ef03bba0f806a056bdce3e7e06b566d3303

### Backlog surfaced by testing (optional, NOT done — out of scope)
- Remove legacy shadowed voicemail guard in server.py (~6891-7020) duplicating routes/campaigns.py.
- Whitelist accepted fields in PUT /api/campaigns/{id} (currently unrestricted Dict).
- Twilio SMS 30034 (A2P 10DLC registration) — user action outside code.
