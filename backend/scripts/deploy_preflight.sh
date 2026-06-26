#!/usr/bin/env bash
#
# Outbound-dialing deploy pre-flight.
#
# Runs scripts/outbound_selftest.py in STRUCTURAL mode. Manages the runtime
# kill switch file (OUTBOUND_DISABLED) that routes/twilio_outbound.py reads
# on every dial attempt. Effect:
#
#   exit 0 → kill switch removed → outbound dialer ALLOWED to dial.
#   exit 1 → kill switch written  → outbound dialer REFUSES every dial,
#            prints the mandated banner, and surfaces exit code 1 to the
#            caller (pm2 / systemd / GitHub Action / git hook).
#
# Hard rules enforced here:
#   * Never runs --dial. Structural only. (--dial is a manual operator action.)
#   * Never prints .env, never echoes secrets.
#   * Never touches legacy /api/twilio/inbound* routes.
#   * Default behaviour: if anything goes wrong, FAIL CLOSED (kill switch on).
#
# Usage:
#   bash scripts/deploy_preflight.sh                  # default — exits with selftest code
#   bash scripts/deploy_preflight.sh && pm2 restart dialgenix-backend
#
# Operator override (do NOT use without reading the report first):
#   FORCE_ENABLE=1 bash scripts/deploy_preflight.sh   # bypass kill switch (NOT recommended)
#
# Venv auto-detection: this script searches for a python interpreter that has
# `fastapi` importable (the venv pm2 uses on the VPS). Override with:
#   OUTBOUND_PYTHON=/path/to/venv/bin/python bash scripts/deploy_preflight.sh

set -u  # NO `-x` ever — that would echo secrets if any leaked into args.

# --- Locate paths (no secrets touched) ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"
SELFTEST="$BACKEND_DIR/scripts/outbound_selftest.py"
KILL_SWITCH="${OUTBOUND_KILL_SWITCH:-$BACKEND_DIR/OUTBOUND_DISABLED}"
REPORT="${OUTBOUND_SELFTEST_REPORT:-/tmp/outbound_selftest_report.json}"

if [ ! -f "$SELFTEST" ]; then
    echo "[deploy_preflight] FATAL: selftest script not found at $SELFTEST" >&2
    echo "selftest_missing" > "$KILL_SWITCH"
    echo ""
    echo "================================================================"
    echo "OUTBOUND SELF-TEST FAILED — LIVE DIALING DISABLED"
    echo "================================================================"
    exit 1
fi

# --- Auto-detect a python interpreter that has fastapi available ---
# pm2 on the VPS runs the backend from a virtualenv; the system `python3` may
# not have fastapi/twilio/elevenlabs installed. The shared finder probes
# candidates and exports OUTBOUND_PY. See scripts/_lib_python_finder.sh.
# shellcheck source=./_lib_python_finder.sh
source "$SCRIPT_DIR/_lib_python_finder.sh" || true
PY="${OUTBOUND_PY:-}"

if [ -z "$PY" ]; then
    echo "[deploy_preflight] FATAL: no python interpreter with fastapi+twilio installed could be found." >&2
    echo "[deploy_preflight] Tried: \$OUTBOUND_PYTHON, $BACKEND_DIR/{venv,.venv}, $REPO_ROOT/{venv,.venv}, system python3/python." >&2
    echo "[deploy_preflight] Pass OUTBOUND_PYTHON=/path/to/venv/bin/python or activate the venv first." >&2
    echo "[deploy_preflight] Hint: pm2 describe dialgenix-backend | grep 'exec interpreter'" >&2
    {
        echo "selftest_python_missing"
        echo "exit_code=2"
        echo "at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$KILL_SWITCH"
    echo ""
    echo "================================================================"
    echo "OUTBOUND SELF-TEST FAILED — LIVE DIALING DISABLED"
    echo "================================================================"
    exit 1
fi

echo "[deploy_preflight] Using python: $PY"

# --- Run the structural self-test ---
echo "[deploy_preflight] Running structural self-test (no live dial, no secrets printed)..."
cd "$BACKEND_DIR"

# Run with PYTHONPATH but NEVER echo env. Stdout/stderr stream to console;
# the script itself avoids printing secrets.
set +e
PYTHONPATH="$BACKEND_DIR" "$PY" "$SELFTEST"
SELFTEST_EXIT=$?
set -e 2>/dev/null || true

# --- Manage the kill switch based on exit code ---
if [ "$SELFTEST_EXIT" -eq 0 ]; then
    if [ -f "$KILL_SWITCH" ]; then
        rm -f "$KILL_SWITCH"
        echo "[deploy_preflight] Kill switch REMOVED — outbound dialer enabled."
    else
        echo "[deploy_preflight] Kill switch was not present — outbound dialer remains enabled."
    fi
    echo ""
    echo "================================================================"
    echo "OUTBOUND SELF-TEST PASSED — live dialing allowed"
    echo "Report: $REPORT"
    echo "================================================================"
    exit 0
fi

# --- Failure path: write the kill switch and print the mandated banner ---
{
    echo "selftest_failed"
    echo "exit_code=$SELFTEST_EXIT"
    echo "at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "report=$REPORT"
} > "$KILL_SWITCH"

echo ""
echo "================================================================"
echo "OUTBOUND SELF-TEST FAILED — LIVE DIALING DISABLED"
echo "================================================================"
echo "Exit code: $SELFTEST_EXIT"
echo "Kill switch written: $KILL_SWITCH"
echo "Report:              $REPORT"
echo ""
echo "What this means:"
echo "  * routes/twilio_outbound.py::place_outbound_call() will refuse every dial"
echo "    until the kill switch is removed."
echo "  * Inspect the report. Fix the regression. Re-run this script."
echo "  * DO NOT manually remove $KILL_SWITCH unless you've verified the fix."
echo "================================================================"

# Allow the operator to force-enable in an emergency. This is loud on purpose.
if [ "${FORCE_ENABLE:-0}" = "1" ]; then
    echo ""
    echo "[deploy_preflight] !!! FORCE_ENABLE=1 set by operator — REMOVING kill switch"
    echo "[deploy_preflight] !!! This bypasses the safety gate. You own the consequences."
    rm -f "$KILL_SWITCH"
    exit 1   # still surface non-zero so CI/deploy treats this as failure
fi

exit 1
