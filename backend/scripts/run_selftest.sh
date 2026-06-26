#!/usr/bin/env bash
#
# Operator wrapper for the outbound gate self-test.
#
# Why this exists:
#   The self-test must run under the same venv-managed python that pm2 uses
#   for the backend (because fastapi / twilio / elevenlabs / motor are all
#   installed there, not in the system python). This wrapper handles
#   interpreter detection + PYTHONPATH so you can run:
#
#       bash scripts/run_selftest.sh                # structural pre-flight
#       bash scripts/run_selftest.sh --dial         # live dial to your phone
#       bash scripts/run_selftest.sh --dial --phone +1XXXXXXXXXX
#
# Hard rules (matches deploy_preflight.sh):
#   * Uses the SAME python finder as deploy_preflight.sh
#     (scripts/_lib_python_finder.sh). One source of truth.
#   * NEVER injects --dial. Only passes --dial when YOU type it.
#   * No `set -x`. No secrets / .env printed.
#   * Prints which python was selected so you know what just ran.
#   * Exits with the SAME exit code as scripts/outbound_selftest.py.
#   * Fails closed (exit 1, banner) if no usable python is found.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SELFTEST="$BACKEND_DIR/scripts/outbound_selftest.py"

if [ ! -f "$SELFTEST" ]; then
    echo "[run_selftest] FATAL: selftest not found at $SELFTEST" >&2
    exit 1
fi

# --- Reuse the shared finder. Exports OUTBOUND_PY on success. ---
# shellcheck source=./_lib_python_finder.sh
source "$SCRIPT_DIR/_lib_python_finder.sh" || true
PY="${OUTBOUND_PY:-}"

if [ -z "$PY" ]; then
    echo "[run_selftest] FATAL: no python interpreter with fastapi+twilio installed could be found." >&2
    echo "[run_selftest] Pass OUTBOUND_PYTHON=/path/to/venv/bin/python or activate the venv first." >&2
    echo "[run_selftest] Hint: pm2 describe dialgenix-backend | grep 'exec interpreter'" >&2
    exit 1
fi

echo "[run_selftest] Using python: $PY"
if [[ " $* " == *" --dial "* ]]; then
    echo "[run_selftest] LIVE DIAL MODE — a real Twilio call will be placed."
else
    echo "[run_selftest] Structural mode — no live dial."
fi

# All operator args ("$@") are passed through verbatim. We never inject --dial.
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" "$PY" "$SELFTEST" "$@"
exit $?
