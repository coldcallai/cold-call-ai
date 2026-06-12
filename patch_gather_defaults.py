#!/usr/bin/env python3
"""
Patch Gather defaults across server.py:
  speech_timeout="auto"   ->  speech_timeout=1.5
  timeout=8               ->  timeout=5   (inside Gather() blocks only)
  timeout=10 (sms-number) ->  LEFT ALONE
"""
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

SERVER = Path("/var/www/dialgenix/backend/server.py")
if not SERVER.exists():
    print(f"[FATAL] {SERVER} not found"); sys.exit(1)

src = SERVER.read_text()

# Backup
backup = SERVER.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(SERVER, backup)
print(f"[BACKUP] {backup}")

# --- 1) speech_timeout="auto"  ->  speech_timeout=1.5  (global) -----------
before_auto = src.count('speech_timeout="auto"')
src = src.replace('speech_timeout="auto"', 'speech_timeout=1.5')
src = src.replace("speech_timeout='auto'", "speech_timeout=1.5")
print(f"[PATCH] speech_timeout=\"auto\" -> 1.5  (count={before_auto})")

# --- 2) timeout=8 inside Gather() blocks only -----------------------------
# Walk through the file and find every Gather( ... ) span (single or multi-line).
def patch_gather_blocks(text: str):
    out = []
    i = 0
    L = len(text)
    changed = 0
    while i < L:
        idx = text.find("Gather(", i)
        if idx == -1:
            out.append(text[i:])
            break
        out.append(text[i:idx])
        # find matching close paren
        depth = 0
        j = idx
        while j < L:
            c = text[j]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        block = text[idx:j]
        new_block, n = re.subn(r"\btimeout\s*=\s*8\b", "timeout=5", block)
        changed += n
        out.append(new_block)
        i = j
    return "".join(out), changed

src, n_timeout = patch_gather_blocks(src)
print(f"[PATCH] timeout=8 -> timeout=5  inside Gather() blocks (count={n_timeout})")

SERVER.write_text(src)
print(f"[OK] {SERVER} updated.")
print("")
print("Next: pm2 restart dialgenix-backend --update-env")
