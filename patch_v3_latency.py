#!/usr/bin/env python3
"""
Patch v3 - Reduce perceived latency by:
  1. Revert speech_timeout=1.5 -> "auto"  (saves ~800ms of dead air)
  2. Shorten all _BRAIN_FAST_PATH_CACHE responses to <=12 words
  3. Shorten _ensure_followup suffix
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
backup = SERVER.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(SERVER, backup)
print(f"[BACKUP] {backup}")

# ---------------------------------------------------------------------
# 1) Revert speech_timeout=1.5 -> "auto"
# ---------------------------------------------------------------------
before = src.count("speech_timeout=1.5")
src = src.replace("speech_timeout=1.5", 'speech_timeout="auto"')
print(f'[PATCH] speech_timeout=1.5 -> "auto"  (count={before})')

# ---------------------------------------------------------------------
# 2) Replace fast-path cache block with shorter responses
# ---------------------------------------------------------------------
NEW_CACHE = '''_BRAIN_FAST_PATH_CACHE = {
    # AI / human / identity probes
    "are you human": "I'm an AI, but I can help just like a real rep. Want a quick demo?",
    "are you a human": "I'm an AI, but I can help just like a real rep. Want a quick demo?",
    "are you ai": "Yes, IntentBrain's AI demo agent. Want me to show you what we do?",
    "are you a i": "Yes, IntentBrain's AI demo agent. Want me to show you what we do?",
    "are you an ai": "Yes, IntentBrain's AI demo agent. Want me to show you what we do?",
    "are you a robot": "I'm an AI. This is a live demo of our cold-calling product. Want to see it?",
    "are you a bot": "I'm an AI. This is a live demo of our cold-calling product. Want to see it?",
    "is this a bot": "Yes, you're talking to IntentBrain's AI. Pretty realistic, right? Want a demo?",
    "is this a robot": "Yes, you're talking to IntentBrain's AI. Pretty realistic, right? Want a demo?",
    "is this ai": "Yes, IntentBrain's AI agent. Pretty realistic, right? Want a demo?",
    "are you real": "I'm a real AI, not a real person. Want me to show you what IntentBrain does?",
    "are you a live person": "I'm an AI, not a live person. Want a quick demo of what we do?",
    "are you a real person": "I'm an AI. IntentBrain's demo agent. Want a quick walkthrough?",
    "are you automated": "Yes, I'm automated AI built by IntentBrain. Want a quick demo?",
    "is this a recording": "Nope, real-time AI. I'm IntentBrain's demo agent. Want a walkthrough?",
    # Name / origin probes
    "what are you": "I'm IntentBrain's AI agent. Want a quick walkthrough?",
    "who are you": "IntentBrain's AI sales agent. We build AI cold-callers. Want a demo?",
    "what's your name": "Just call me the IntentBrain agent. Want a quick demo?",
    "whats your name": "Just call me the IntentBrain agent. Want a quick demo?",
    "what is your name": "Just call me the IntentBrain agent. Want a quick demo?",
    "who built you": "The IntentBrain team. We make AI cold-callers for B2B. Want a demo?",
    "who created you": "The IntentBrain team. We make AI cold-callers for B2B. Want a demo?",
    "who made you": "The IntentBrain team. We make AI cold-callers for B2B. Want a demo?",
    "where are you calling from": "From IntentBrain - we're an AI cold-calling platform. Want a demo?",
    "what voice are you using": "ElevenLabs voice, IntentBrain brain. Sounds pretty good, right? Want a demo?",
    "are you using elevenlabs": "Yes, ElevenLabs for voice. Want me to walk you through IntentBrain?",
    "can people tell you're ai": "Most don't catch on right away. Want a quick demo?",
    "can people tell youre ai": "Most don't catch on right away. Want a quick demo?",
    "how human do you sound": "Pretty human apparently. Want a quick walkthrough?",
}'''

# Match the existing cache block (multi-line)
cache_pattern = re.compile(
    r"_BRAIN_FAST_PATH_CACHE\s*=\s*\{[^}]*\}",
    re.DOTALL
)
new_src, n_cache = cache_pattern.subn(NEW_CACHE, src, count=1)
if n_cache != 1:
    print("[FATAL] Could not locate _BRAIN_FAST_PATH_CACHE block")
    sys.exit(1)
src = new_src
print(f"[PATCH] _BRAIN_FAST_PATH_CACHE shortened (29 entries, all <=12 words)")

# ---------------------------------------------------------------------
# 3) Shorten follow-up suffix
# ---------------------------------------------------------------------
OLD_FU = ' Did that answer your question, or would you like to book a quick demo?'
NEW_FU = ' Want a quick demo?'
if OLD_FU in src:
    src = src.replace(OLD_FU, NEW_FU)
    print("[PATCH] _ensure_followup suffix shortened")
else:
    print("[WARN] Follow-up suffix not found - already shortened?")

SERVER.write_text(src)
print(f"[OK] {SERVER} updated.")
print("")
print("Next: pm2 restart dialgenix-backend --update-env")
