#!/usr/bin/env python3
"""
Patch v5:
  1. Remove "who built you" from prompt_injection guard (fast-path handles it)
  2. Remove "are you a bot" from OFF list (fast-path handles it)
  3. Add language/Spanish fast-path entries
"""
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

SERVER = Path("/var/www/dialgenix/backend/server.py")
if not SERVER.exists():
    print(f"[FATAL] {SERVER} not found")
    sys.exit(1)

src = SERVER.read_text()
backup = SERVER.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(SERVER, backup)
print(f"[BACKUP] {backup}")

# -------------------------------------------------------------
# 1) Remove "who built you" from prompt_injection list
# -------------------------------------------------------------
OLD_INJ = '"what company runs this", "who built you",'
NEW_INJ = '"what company runs this",'
if OLD_INJ in src:
    src = src.replace(OLD_INJ, NEW_INJ)
    print('[PATCH] Removed "who built you" from prompt_injection list')
else:
    print('[WARN] Did not find "who built you" in prompt_injection list')

# -------------------------------------------------------------
# 2) Remove "are you a bot" from OFF list
# -------------------------------------------------------------
OLD_OFF = '"world cup", "movie", " song", " joke", "tell me a joke",\n            "are you a bot",\n'
NEW_OFF = '"world cup", "movie", " song", " joke", "tell me a joke",\n'
if OLD_OFF in src:
    src = src.replace(OLD_OFF, NEW_OFF)
    print('[PATCH] Removed "are you a bot" from OFF list')
else:
    # Try with single-line version
    if '"are you a bot",' in src and OLD_OFF not in src:
        # try a more lenient match - just remove the line
        lines = src.split("\n")
        new_lines = []
        removed = False
        for line in lines:
            if not removed and line.strip() == '"are you a bot",':
                removed = True
                continue
            new_lines.append(line)
        if removed:
            src = "\n".join(new_lines)
            print('[PATCH] Removed "are you a bot" from OFF list (single-line)')
        else:
            print('[WARN] Could not remove "are you a bot" from OFF list')

# -------------------------------------------------------------
# 3) Add Spanish/language fast-path entries
# -------------------------------------------------------------
# Insert into _BRAIN_FAST_PATH_CACHE, right before closing brace
INSERT_BEFORE = '    "how human do you sound": "Pretty human apparently. Want a quick walkthrough?",\n}'
NEW_ENTRIES = '''    "how human do you sound": "Pretty human apparently. Want a quick walkthrough?",
    # Language support probes
    "do you speak spanish": "Yes, IntentBrain supports Spanish-speaking businesses. Want a quick demo?",
    "do you speak espanol": "Yes, IntentBrain supports Spanish-speaking businesses. Want a quick demo?",
    "can you speak spanish": "Yes, IntentBrain supports Spanish-speaking businesses. Want a quick demo?",
    "habla espanol": "Yes, our AI agents can speak Spanish too. Want a quick demo?",
    "hablas espanol": "Yes, our AI agents can speak Spanish too. Want a quick demo?",
    "what languages do you speak": "IntentBrain supports English and Spanish today. More coming soon. Want a demo?",
    "what languages do you support": "IntentBrain supports English and Spanish today. More coming soon. Want a demo?",
    "do you do spanish": "Yes, IntentBrain supports Spanish. Want a quick demo?",
}'''
if INSERT_BEFORE in src:
    src = src.replace(INSERT_BEFORE, NEW_ENTRIES)
    print("[PATCH] Added 8 Spanish/language fast-path entries")
else:
    print("[WARN] Could not locate fast-path cache closing brace")

SERVER.write_text(src)
print(f"[OK] {SERVER} updated.")
print("")
print("Next: pm2 restart dialgenix-backend --update-env")
print("(Prewarm will auto-generate audio for new Spanish entries on startup)")
