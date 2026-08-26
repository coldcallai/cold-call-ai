#!/usr/bin/env python3
"""Idempotent installer for the Outbound Human-Greeting Gate mount block in
backend/server.py. Safe to run multiple times — only inserts if not already
present. Never touches existing inbound code, never deletes anything.

Usage (from /var/www/dialgenix/backend):
    python3 scripts/install_mount_block.py
"""
import os
import sys
from pathlib import Path

SERVER_PY = Path(__file__).resolve().parent.parent / "server.py"
MARKER = "Mounted Outbound Human-Greeting Gate"
ANCHOR = "# Include main api_router (legacy routes)\napp.include_router(api_router)"
MOUNT_BLOCK = '''
# ============================================================
# Outbound Human-Greeting Gate (additive — does NOT touch inbound)
# ============================================================
try:
    from routes import twilio_outbound as _twilio_outbound

    _outbound_voice_id = os.environ.get("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"  # Rachel default
    _outbound_backend_url = (os.environ.get("BACKEND_URL") or os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    _outbound_from = os.environ.get("TWILIO_OUTBOUND_FROM") or twilio_phone_number or ""

    _twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=twilio_client,
        eleven_client=eleven_client,
        synthesize_fn=None,
        voice_id=_outbound_voice_id,
        backend_url=_outbound_backend_url,
        from_number=_outbound_from,
    )
    app.include_router(_twilio_outbound.router, prefix="/api")
    app.include_router(_twilio_outbound.tts_router, prefix="/api")
    app.include_router(_twilio_outbound.admin_router, prefix="/api")
    logger.info(
        "Mounted Outbound Human-Greeting Gate at /api/twilio/outbound/* "
        f"(backend_url={'set' if _outbound_backend_url else 'MISSING'}, "
        f"voice_id={_outbound_voice_id}, from={'set' if _outbound_from else 'MISSING'})"
    )
except Exception as _outbound_err:
    logger.error(f"Failed to mount outbound router: {_outbound_err}")

'''


def main():
    if not SERVER_PY.exists():
        print(f"FATAL: {SERVER_PY} not found", file=sys.stderr)
        sys.exit(1)

    src = SERVER_PY.read_text()
    if MARKER in src:
        print(f"[install_mount_block] Already installed in {SERVER_PY} — no changes.")
        sys.exit(0)

    if ANCHOR not in src:
        print(
            f"FATAL: could not find anchor line in {SERVER_PY}.\n"
            f"Looking for:\n{ANCHOR}\n\n"
            "Either server.py is too modified or already mounted differently. "
            "Inspect manually before retrying.",
            file=sys.stderr,
        )
        sys.exit(2)

    new_src = src.replace(ANCHOR, ANCHOR + "\n" + MOUNT_BLOCK, 1)
    # Backup
    backup = SERVER_PY.with_suffix(".py.bak.outbound_mount")
    backup.write_text(src)
    SERVER_PY.write_text(new_src)
    print(f"[install_mount_block] Patched {SERVER_PY}. Backup at {backup}.")


if __name__ == "__main__":
    main()
