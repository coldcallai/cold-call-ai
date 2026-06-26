#!/usr/bin/env bash
#
# Shared python-interpreter finder for the outbound gate scripts.
# Sourced by:
#   - scripts/deploy_preflight.sh   (CI / VPS pre-flight)
#   - scripts/run_selftest.sh       (operator-run structural / --dial)
#
# Contract:
#   * Sources MUST set BACKEND_DIR (absolute) before sourcing this file.
#   * On success: exports OUTBOUND_PY = absolute path to a python that has
#     fastapi + twilio importable.
#   * On failure: leaves OUTBOUND_PY="" and returns non-zero. Caller decides
#     fail-closed semantics (kill switch, banner, etc.).
#
# Hard rules:
#   * No `set -x`. No echoing of env vars / .env / secrets.
#   * Probe redirects BOTH stdout and stderr to /dev/null.
#   * Never invokes any tool that prints API keys.

# Don't `set -e` here — we want graceful fall-through.

if [ -z "${BACKEND_DIR:-}" ]; then
    echo "[python_finder] FATAL: BACKEND_DIR not set before sourcing _lib_python_finder.sh" >&2
    OUTBOUND_PY=""
    return 1 2>/dev/null || exit 1
fi

_REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd 2>/dev/null || echo "")"

OUTBOUND_PY=""
_candidates=(
    "${OUTBOUND_PYTHON:-}"
    "$BACKEND_DIR/venv/bin/python3"
    "$BACKEND_DIR/venv/bin/python"
    "$BACKEND_DIR/.venv/bin/python3"
    "$BACKEND_DIR/.venv/bin/python"
    "$_REPO_ROOT/venv/bin/python3"
    "$_REPO_ROOT/venv/bin/python"
    "$_REPO_ROOT/.venv/bin/python3"
    "$_REPO_ROOT/.venv/bin/python"
    "$(command -v python3 2>/dev/null || true)"
    "$(command -v python 2>/dev/null || true)"
)

for _c in "${_candidates[@]}"; do
    [ -n "$_c" ] && [ -x "$_c" ] || continue
    # Silent probe — both streams suppressed to keep any path info out of logs.
    if "$_c" -c "import fastapi, twilio" >/dev/null 2>&1; then
        OUTBOUND_PY="$_c"
        break
    fi
done

unset _candidates _c _REPO_ROOT

if [ -z "$OUTBOUND_PY" ]; then
    return 1 2>/dev/null || exit 1
fi
return 0 2>/dev/null || exit 0
