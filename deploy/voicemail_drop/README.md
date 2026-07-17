# Cloned-Voice Voicemail Drop — Surgical Deployment Package

This folder contains everything needed to deploy the **Cloned-Voice Voicemail
Drop** feature onto the production VPS (`/var/www/dialgenix`) **without**
disturbing the unrelated local modifications that live there.

It never does a blind `git pull` and never wholesale-replaces `server.py` or
`routes/campaigns.py`. Only the voicemail hunks are applied.

---

## What's in the box

```
deploy/voicemail_drop/
├── README.md                 <- this file
├── deploy_voicemail.sh       <- safe, idempotent-safe deploy script
└── patches/
    ├── vm_server.patch       <- 8 voicemail-only hunks for backend/server.py
    └── vm_campaigns.patch    <- 6 voicemail-only hunks for backend/routes/campaigns.py
```

The two **new** files the feature needs live at their normal repo locations
(the deploy script copies them from your clone):

- `backend/services/vm_cloned_audio.py`   (NEW — ElevenLabs VM MP3 cache/synth)
- `backend/tests/test_vm_config.py`        (NEW)
- `backend/tests/test_vm_api_iter32.py`    (NEW)
- `backend/tests/test_vm_cloned_audio.py`  (NEW)
- `backend/tests/test_vm_envblank_iter32.py` (NEW)
- `backend/tests/test_vm_launch_blocker.py`  (NEW)

---

## Exactly what the patches change (voicemail only)

**backend/server.py** (8 hunks)
- `Campaign` model: `+voicemail_audio_url`, `+voicemail_audio_key`, `+callback_number`
- New helpers: `normalize_phone_for_speech`, `resolve_callback_number`,
  `resolve_agent_name`, `hydrate_campaign_for_vm`, `VM_DEFAULT_SCRIPT`,
  `_PLACEHOLDER_LITERAL_RE`
- `generate_voicemail_twiml`: cloned-voice `<Play>` path + Polly fallback +
  `{agent_name}`/`{callback_number}` interpolation + **placeholder guard**
- create / update / start campaign endpoints: **callback-required safety guard**
  + `refresh_campaign_vm_audio` regen hooks
- AMD machine-detected branch: `hydrate_campaign_for_vm(...)` before TwiML
- New route `GET /api/vm-audio/{token}` (serves the MP3; 404 → Polly fallback)
- New startup hook `_vm_cloned_audio_startup_sweep`

**backend/routes/campaigns.py** (6 hunks)
- VM model fields (`voicemail_audio_url/key`, `callback_number`, `agent_id`)
- create / update / start guards + `refresh_campaign_vm_audio` hooks
- `+import os`

### Deliberately EXCLUDED (not part of voicemail; left untouched on prod)
- `twilio_sms_number` / 10DLC SMS sender changes
- RankTrust handoff webhook mount
- the "brain" / `tts_speak` / `_detect_speech_intent` / inbound-handler rewrites
- demo-audio refactor

---

## Verification hashes

| file | baseline (before) | after patch |
|---|---|---|
| `backend/server.py` | `64636d32207143c8f1a2afd93beacf24e8376c1f1f7e81032daaffd84134d198` | `61f45a15ab60626a76441cfccee6e34e724d67e7f8837d790526aabb8bd0e8a4` |
| `backend/routes/campaigns.py` | `7c46aa668f0f616c73c60b25cb75b87b39f4cf7f970893e2b754054a1a0e8767` | `2bb9b0812f3cca0a34d33a2f55ac0ef03bba0f806a056bdce3e7e06b566d3303` |

New-file hashes:
```
be2c46680751284336989b2c36e62bc6a6d53ceb8495d49d2e382e3510a95926  backend/services/vm_cloned_audio.py
9a2118e5b4a2da48c97fef5619e9f44a443b522487f1c468dbde6e09e29bb6da  backend/tests/test_vm_config.py
0a1dcd922180731740d27295315bac111b953174811c1b14e5b2df8812471260  backend/tests/test_vm_api_iter32.py
887fa0a2b39b4bcf8680b56bff4331b13d5c5679c86db03d94c94d473e544bbb  backend/tests/test_vm_cloned_audio.py
a62e333e00cfae7651cb436ac19ce7d4cde7e64c5864d2bbf104ddb1fb813fc6  backend/tests/test_vm_envblank_iter32.py
66690397a3f86a3cb3371d4dd29a9357455ac99e90c4d69a5ae3c31ff40690d9  backend/tests/test_vm_launch_blocker.py
```

Patches were validated in a sandbox: `git apply --check` clean against the
baseline, `py_compile` OK after apply, and the result reproduces the exact
validated target byte-for-byte.

---

## How to deploy (reviewed, no blind pull)

```bash
# 1. Get a FRESH clone of the Emergent repo somewhere OUTSIDE your prod tree
git clone <your-github-repo-url> /tmp/ib_repo
#    (or: cd /tmp/ib_repo && git fetch && git checkout <commit-sha>)

# 2. Run the safe deploy (dry-runs everything, backs up, applies, tests, restarts)
REPO_DIR=/tmp/ib_repo \
PROD_DIR=/var/www/dialgenix \
PM2_BACKEND=<your-backend-pm2-name> \
bash /tmp/ib_repo/deploy/voicemail_drop/deploy_voicemail.sh
```

The script aborts before touching anything if your live baseline hashes don't
match the table above (meaning prod drifted further — in that case re-share the
current `server.py` / `campaigns.py` and a fresh patch will be regenerated).

Rollback commands are printed at the end of a run and also live in the backup
dir it creates: `/var/www/dialgenix/_vm_backup_<timestamp>/`.

### Environment notes
- The cloned-MP3 synth needs `ELEVENLABS_API_KEY` and a resolvable
  `BACKEND_PUBLIC_URL` (or `REACT_APP_BACKEND_URL`) in the backend env.
- The negative-path tests (`test_vm_envblank_iter32`, and sections 2/7 of
  `test_vm_launch_blocker`) assert a 400 only when **all** callback fallbacks
  are empty. They pass when run with `TWILIO_PHONE_NUMBER=''` **and** the test
  user has no `phone_number`. With a real fallback present they intentionally
  return 200 (the guard found a callback) — this is correct behaviour, not a bug.
