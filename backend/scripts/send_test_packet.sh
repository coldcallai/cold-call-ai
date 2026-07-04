#!/usr/bin/env bash
#
# Fire one real RankTrust handoff packet against the local IntentBrain webhook.
# Uses the SAME venv autodetection as deploy_preflight.sh / run_selftest.sh.
#
# Usage (from /var/www/dialgenix/backend):
#   bash scripts/send_test_packet.sh                             # default: +18885131913, delay=60s
#   bash scripts/send_test_packet.sh --phone +1XXXXXXXXXX
#   bash scripts/send_test_packet.sh --delay 300
#   bash scripts/send_test_packet.sh --url http://localhost:8001/api/webhooks/ranktrust/handoff
#
# Auth precedence (matches the webhook):
#   * If RANKTRUST_HANDOFF_SECRET is set in .env → HMAC-sign the body.
#   * Else if RANKTRUST_HANDOFF_TOKEN is set → append ?token=...
#   * Else → the webhook will 401 and this script surfaces that clearly.
#
# Hard rules:
#   * Never `cat`, `echo`, `printenv`, `grep` the .env file. Uses python-dotenv
#     inside the python helper below to read secrets safely.
#   * Never prints the secret / token / HMAC hex to stdout.
#   * Does not place a call directly — the packet goes through the webhook +
#     scheduler + outbound gate. OUTBOUND_DISABLED + DNC still hard-govern.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=./_lib_python_finder.sh
source "$SCRIPT_DIR/_lib_python_finder.sh" || true
PY="${OUTBOUND_PY:-}"
if [ -z "$PY" ]; then
    echo "[send_test_packet] FATAL: no python interpreter with fastapi+twilio installed could be found." >&2
    echo "[send_test_packet] Pass OUTBOUND_PYTHON=/path/to/venv/bin/python or activate the venv." >&2
    exit 1
fi

# Defaults
PHONE="+18885131913"
DELAY=60
URL="http://localhost:8001/api/webhooks/ranktrust/handoff"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --phone) PHONE="$2"; shift 2 ;;
        --delay) DELAY="$2"; shift 2 ;;
        --url)   URL="$2"; shift 2 ;;
        *) echo "[send_test_packet] unknown arg: $1" >&2; exit 2 ;;
    esac
done

echo "[send_test_packet] Using python: $PY"
echo "[send_test_packet] Target URL:   $URL"
echo "[send_test_packet] Test phone:   $PHONE"
echo "[send_test_packet] Delay (s):    $DELAY"

# The python helper builds the packet, reads the secret via python-dotenv,
# signs (if HMAC available) or appends ?token=, POSTs, and prints ONLY the
# HTTP status + response JSON. No secrets in output.
"$PY" - <<'PYEOF' -- "$BACKEND_DIR" "$URL" "$PHONE" "$DELAY"
import hashlib, hmac, json, sys, os, time, uuid, urllib.request, urllib.parse

_, _dash, backend_dir, url, phone, delay = sys.argv
delay = int(delay)

# Load .env via python-dotenv (no cat/echo/grep)
try:
    from dotenv import dotenv_values
except ImportError:
    print("[send_test_packet] FATAL: python-dotenv not installed.", file=sys.stderr)
    sys.exit(3)

env = dotenv_values(os.path.join(backend_dir, ".env"))
secret = env.get("RANKTRUST_HANDOFF_SECRET") or ""
token  = env.get("RANKTRUST_HANDOFF_TOKEN")  or ""

if not secret and not token:
    print("[send_test_packet] FATAL: neither RANKTRUST_HANDOFF_SECRET nor RANKTRUST_HANDOFF_TOKEN is set in .env.", file=sys.stderr)
    print("[send_test_packet] Add one of them (32+ random chars) and try again.", file=sys.stderr)
    sys.exit(4)

packet = {
    "packet_id": f"test-e2e-{int(time.time())}-{uuid.uuid4().hex[:8]}",
    "business": {
        "name": "IntentBrain Demo AI",
        "industry": "internal_test",
        "phone": phone,
        "website": "https://intentbrain.ai/demo",
    },
    "revenue_opportunity": 12000.0,
    "close_probability": 0.5,
    "best_offer": "E2E test — do not book a meeting; demo AI is on the other side.",
    "sales_script": {
        "opener": "Hi, this is Sarah calling from IntentBrain. This is an end-to-end integration test — please acknowledge.",
        "key_points": ["e2e handoff test", "safe to hang up"],
        "call_to_action": "Thanks for confirming.",
    },
    "objections": [],
    "conversation_strategy": "Do not engage in real conversation. This dial is a live E2E integration probe against a demo AI.",
    "delay_seconds": delay,
}

body = json.dumps(packet, separators=(",", ":")).encode("utf-8")

# Prefer HMAC when secret is present
final_url = url
headers = {"Content-Type": "application/json"}
auth_mode = ""
if secret:
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    headers["X-RankTrust-Signature"] = f"sha256={sig}"
    auth_mode = "hmac"
else:
    # Token fallback
    sep = "&" if "?" in url else "?"
    final_url = f"{url}{sep}token={urllib.parse.quote(token)}"
    auth_mode = "token"

print(f"[send_test_packet] Auth mode:    {auth_mode}")
print(f"[send_test_packet] packet_id:    {packet['packet_id']}")

req = urllib.request.Request(final_url, data=body, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body_out = resp.read().decode("utf-8", errors="replace")
        print(f"[send_test_packet] HTTP {resp.status}")
        # Print only the response JSON — the webhook _public_view already redacts callback_token
        print(body_out)
except urllib.error.HTTPError as e:
    print(f"[send_test_packet] HTTP {e.code}", file=sys.stderr)
    try:
        print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
    except Exception:
        pass
    sys.exit(1)
except Exception as e:
    print(f"[send_test_packet] ERROR: {e!r}", file=sys.stderr)
    sys.exit(1)

print("")
print("[send_test_packet] Packet accepted. The scheduler will fire in ~%ds." % delay)
print("[send_test_packet] Watch outcome via:")
print(f"[send_test_packet]   curl -s http://localhost:8001/api/webhooks/ranktrust/handoff/{packet['packet_id']} | python3 -m json.tool")
PYEOF
