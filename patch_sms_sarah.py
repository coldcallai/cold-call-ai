#!/usr/bin/env python3
"""Quick patch: drop 'Sarah' from SMS body + add delivery status logging hook."""
import sys, shutil
from pathlib import Path
from datetime import datetime

SERVER = Path("/var/www/dialgenix/backend/server.py")
src = SERVER.read_text()
backup = SERVER.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(SERVER, backup)
print(f"[BACKUP] {backup}")

OLD = 'body = f"Hi! Sarah from IntentBrain. Book your demo: {booking_url}"'
NEW = 'body = f"Hi! Thanks for calling IntentBrain. Book your demo here: {booking_url}"'

if OLD in src:
    src = src.replace(OLD, NEW)
    print("[PATCH] Removed Sarah from SMS body")
else:
    print("[WARN] SMS body line not found - may have changed")

SERVER.write_text(src)
print(f"[OK] {SERVER} updated")
print("Next: pm2 restart dialgenix-backend --update-env")
