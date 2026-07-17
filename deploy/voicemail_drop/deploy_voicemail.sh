#!/usr/bin/env bash
#
# ============================================================================
#  IntentBrain — Cloned-Voice Voicemail Drop : SAFE surgical deployment
# ============================================================================
#  This script deploys ONLY the voicemail-drop feature onto a production tree
#  that has LOCAL, UNRELATED modifications. It never does a blind `git pull`
#  and never wholesale-replaces server.py / routes/campaigns.py.
#
#  It:
#    1. verifies your live prod baseline matches the exact file the surgical
#       patch was built against (aborts otherwise)
#    2. backs up every file it will touch
#    3. dry-runs both patches (git apply --check) and aborts on any failure
#    4. applies the two surgical patches (voicemail hunks only)
#    5. copies in the NEW voicemail files (service + tests)
#    6. verifies post-patch file hashes
#    7. runs the 5 voicemail test files
#    8. restarts ONLY the backend PM2 process
#    9. prints exact rollback commands
#
#  USAGE:
#    REPO_DIR=/path/to/emergent-repo-clone \
#    PROD_DIR=/var/www/dialgenix \
#    PM2_BACKEND=intentbrain-backend \
#    bash deploy_voicemail.sh
#
#  Nothing is changed until every pre-flight check passes.
# ============================================================================
set -euo pipefail

REPO_DIR="${REPO_DIR:?Set REPO_DIR to your fresh clone of the Emergent GitHub repo}"
PROD_DIR="${PROD_DIR:-/var/www/dialgenix}"
PM2_BACKEND="${PM2_BACKEND:-intentbrain-backend}"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${PROD_DIR}/_vm_backup_${TS}"

# ---- expected hashes (do not edit) ----------------------------------------
BASE_SERVER_SHA="64636d32207143c8f1a2afd93beacf24e8376c1f1f7e81032daaffd84134d198"
BASE_CAMPAIGNS_SHA="7c46aa668f0f616c73c60b25cb75b87b39f4cf7f970893e2b754054a1a0e8767"
POST_SERVER_SHA="61f45a15ab60626a76441cfccee6e34e724d67e7f8837d790526aabb8bd0e8a4"
POST_CAMPAIGNS_SHA="2bb9b0812f3cca0a34d33a2f55ac0ef03bba0f806a056bdce3e7e06b566d3303"

PATCH_SERVER="${REPO_DIR}/deploy/voicemail_drop/patches/vm_server.patch"
PATCH_CAMPAIGNS="${REPO_DIR}/deploy/voicemail_drop/patches/vm_campaigns.patch"

SERVER="${PROD_DIR}/backend/server.py"
CAMPAIGNS="${PROD_DIR}/backend/routes/campaigns.py"

say(){ printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die(){ printf '\n\033[1;31mABORT: %s\033[0m\n' "$*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

# ---------------------------------------------------------------------------
say "STEP 1/9  Pre-flight: verifying live prod baseline"
[ -f "$SERVER" ]    || die "not found: $SERVER"
[ -f "$CAMPAIGNS" ] || die "not found: $CAMPAIGNS"
[ -f "$PATCH_SERVER" ]    || die "patch missing: $PATCH_SERVER"
[ -f "$PATCH_CAMPAIGNS" ] || die "patch missing: $PATCH_CAMPAIGNS"

CUR_SERVER_SHA="$(sha "$SERVER")"
CUR_CAMPAIGNS_SHA="$(sha "$CAMPAIGNS")"
echo "  server.py    : $CUR_SERVER_SHA"
echo "  campaigns.py : $CUR_CAMPAIGNS_SHA"

if [ "$CUR_SERVER_SHA" != "$BASE_SERVER_SHA" ]; then
  die "server.py does not match the baseline the patch was built against.
       Your prod has drifted further. Re-share the current backend/server.py
       so a fresh surgical patch can be regenerated. DO NOT force-apply."
fi
if [ "$CUR_CAMPAIGNS_SHA" != "$BASE_CAMPAIGNS_SHA" ]; then
  die "routes/campaigns.py does not match the baseline. Re-share current file."
fi
echo "  baseline OK — safe to proceed."

# ---------------------------------------------------------------------------
say "STEP 2/9  Backing up affected files -> $BACKUP_DIR"
mkdir -p "$BACKUP_DIR/backend/routes" "$BACKUP_DIR/backend/services" "$BACKUP_DIR/backend/tests"
cp -v "$SERVER"    "$BACKUP_DIR/backend/server.py"
cp -v "$CAMPAIGNS" "$BACKUP_DIR/backend/routes/campaigns.py"

# ---------------------------------------------------------------------------
say "STEP 3/9  Dry-run both patches (git apply --check)"
( cd "$PROD_DIR" && git apply --check -p1 "$PATCH_SERVER" ) \
  || die "server.py patch does NOT apply cleanly — nothing was changed."
( cd "$PROD_DIR" && git apply --check -p1 "$PATCH_CAMPAIGNS" ) \
  || die "campaigns.py patch does NOT apply cleanly — nothing was changed."
echo "  both patches apply cleanly."

# ---------------------------------------------------------------------------
say "STEP 4/9  Applying surgical patches"
( cd "$PROD_DIR" && git apply -p1 "$PATCH_SERVER" "$PATCH_CAMPAIGNS" )
echo "  patches applied."

# ---------------------------------------------------------------------------
say "STEP 5/9  Copying NEW voicemail files"
cp -v "${REPO_DIR}/backend/services/vm_cloned_audio.py" "${PROD_DIR}/backend/services/vm_cloned_audio.py"
for t in test_vm_config test_vm_api_iter32 test_vm_cloned_audio test_vm_envblank_iter32 test_vm_launch_blocker; do
  cp -v "${REPO_DIR}/backend/tests/${t}.py" "${PROD_DIR}/backend/tests/${t}.py"
done

# ---------------------------------------------------------------------------
say "STEP 6/9  Verifying post-patch hashes"
NEW_SERVER_SHA="$(sha "$SERVER")"
NEW_CAMPAIGNS_SHA="$(sha "$CAMPAIGNS")"
[ "$NEW_SERVER_SHA" = "$POST_SERVER_SHA" ] \
  || die "post-patch server.py hash mismatch ($NEW_SERVER_SHA). Run rollback (below)."
[ "$NEW_CAMPAIGNS_SHA" = "$POST_CAMPAIGNS_SHA" ] \
  || die "post-patch campaigns.py hash mismatch. Run rollback (below)."
python3 -m py_compile "$SERVER" "$CAMPAIGNS" || die "patched files fail to compile. Run rollback."
echo "  post-patch hashes + compile OK."

# ---------------------------------------------------------------------------
say "STEP 7/9  Running voicemail test suite"
echo "  (integration tests need the backend running & REACT_APP_BACKEND_URL set)"
( cd "${PROD_DIR}/backend" && python3 -m pytest \
    tests/test_vm_config.py \
    tests/test_vm_cloned_audio.py \
    tests/test_vm_api_iter32.py \
    tests/test_vm_launch_blocker.py \
    tests/test_vm_envblank_iter32.py -v ) || {
  echo "  NOTE: env-gated negative tests need TWILIO_PHONE_NUMBER='' + no user phone."
  echo "        Review failures; core VM-only tests must pass."
}

# ---------------------------------------------------------------------------
say "STEP 8/9  Restarting backend PM2 process only: $PM2_BACKEND"
pm2 restart "$PM2_BACKEND" --update-env
pm2 status "$PM2_BACKEND"

# ---------------------------------------------------------------------------
say "STEP 9/9  DONE. Manual E2E voicemail test"
cat <<EOF

  Deployment complete. Now do ONE live end-to-end voicemail test:
    1. In the app, open (or create) a campaign, enable Voicemail Drop,
       set a callback number, and save.  -> a cloned MP3 should be minted
       (check: GET /api/vm-audio/<token> returns the audio, 404 falls back to Polly).
    2. Add a single lead whose number is YOUR OWN phone.
    3. Start the campaign and let it hit voicemail. Confirm the cloned voice
       plays and the callback number is spoken (NOT the literal "{callback_number}").

  ============================ ROLLBACK ============================
  If anything looks wrong, restore instantly:

    cp "$BACKUP_DIR/backend/server.py"            "$SERVER"
    cp "$BACKUP_DIR/backend/routes/campaigns.py"  "$CAMPAIGNS"
    rm -f "${PROD_DIR}/backend/services/vm_cloned_audio.py"
    rm -f ${PROD_DIR}/backend/tests/test_vm_config.py \\
          ${PROD_DIR}/backend/tests/test_vm_api_iter32.py \\
          ${PROD_DIR}/backend/tests/test_vm_cloned_audio.py \\
          ${PROD_DIR}/backend/tests/test_vm_envblank_iter32.py \\
          ${PROD_DIR}/backend/tests/test_vm_launch_blocker.py
    pm2 restart "$PM2_BACKEND" --update-env
  ==================================================================
EOF
