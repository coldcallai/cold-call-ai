#!/usr/bin/env python3
"""
Patch for BUG #004 - Latency & Silent Dead-End after brain response.

Adds:
  1. _BRAIN_FAST_PATH_CACHE: deterministic responses for AI-identity questions
     (bypasses OpenAI -> ~50ms instead of ~3000ms).
  2. Auto-appends a follow-up question when action=="continue" and the brain's
     response_text doesn't already end with '?'. Kills the silent dead-end.

Safe to re-run: idempotent (checks for FAST_PATH marker before patching).
"""

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

SERVER = Path("/var/www/dialgenix/backend/server.py")

if not SERVER.exists():
    print(f"[FATAL] {SERVER} not found")
    sys.exit(1)

src = SERVER.read_text()

# --------------------------------------------------------------------------
# Idempotency guard
# --------------------------------------------------------------------------
if "_BRAIN_FAST_PATH_CACHE" in src:
    print("[SKIP] Fast-path cache already present. No changes made.")
    sys.exit(0)

# --------------------------------------------------------------------------
# Backup
# --------------------------------------------------------------------------
backup = SERVER.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(SERVER, backup)
print(f"[BACKUP] {backup}")

# --------------------------------------------------------------------------
# Insert FAST_PATH cache + helper near top of file (after imports, before app)
# --------------------------------------------------------------------------
helper_block = '''
# ---------------------------------------------------------------------------
# BUG #004 fix - Fast-path cache for AI identity questions.
# Bypasses OpenAI (~3s) for predictable phrases. Returns deterministic answer
# already terminated with a follow-up question so the Gather never dead-ends.
# ---------------------------------------------------------------------------
_BRAIN_FAST_PATH_CACHE = {
    # AI / human / identity probes
    "are you human": "I'm an AI assistant for IntentBrain, but I can help you just like a real rep would. Would you like to hear how IntentBrain works, or book a quick demo?",
    "are you a human": "I'm an AI assistant for IntentBrain, but I can help you just like a real rep would. Would you like to hear how IntentBrain works, or book a quick demo?",
    "are you ai": "Yes, I'm an AI built by IntentBrain to demo what our cold-calling agents sound like. Want me to walk you through what we do, or book a demo?",
    "are you a i": "Yes, I'm an AI built by IntentBrain to demo what our cold-calling agents sound like. Want me to walk you through what we do, or book a demo?",
    "are you an ai": "Yes, I'm an AI built by IntentBrain to demo what our cold-calling agents sound like. Want me to walk you through what we do, or book a demo?",
    "are you a robot": "I'm an AI assistant, yes. This is actually a live demo of our cold-calling product. Want to hear how it works, or book a demo?",
    "are you a bot": "I'm an AI assistant, yes. This is actually a live demo of our cold-calling product. Want to hear how it works, or book a demo?",
    "is this a bot": "Yes, you're talking to IntentBrain's AI agent right now. Pretty realistic, right? Want me to explain what we do, or book a demo?",
    "is this a robot": "Yes, you're talking to IntentBrain's AI agent right now. Pretty realistic, right? Want me to explain what we do, or book a demo?",
    "is this ai": "Yes, you're talking to IntentBrain's AI agent right now. Pretty realistic, right? Want me to explain what we do, or book a demo?",
    "are you real": "I'm a real AI agent, not a real person. I'm built by IntentBrain to show off our cold-calling tech. Want to hear more or book a demo?",
    "are you a live person": "I'm an AI agent, not a live person, but I can answer most questions. Want me to walk you through IntentBrain, or book a demo?",
    "are you a real person": "I'm an AI agent, not a real person. I'm IntentBrain's demo agent. Want me to walk you through what we do, or book a demo?",
    "are you automated": "Yes, I'm an automated AI agent built by IntentBrain. Want me to explain what we do, or book a quick demo?",
    "is this a recording": "Nope, this isn't a recording. I'm IntentBrain's AI agent answering in real time. Want me to explain what we do, or book a demo?",
    # Name / origin probes
    "what are you": "I'm IntentBrain's AI cold-calling agent, here to show you what our product can do. Want to hear how it works, or book a demo?",
    "who are you": "I'm IntentBrain's AI sales agent. We build AI cold-callers for B2B sales teams. Want to hear how it works, or book a demo?",
    "what's your name": "You can call me the IntentBrain agent. I'm an AI built to demo our cold-calling platform. Want to hear how it works, or book a demo?",
    "whats your name": "You can call me the IntentBrain agent. I'm an AI built to demo our cold-calling platform. Want to hear how it works, or book a demo?",
    "what is your name": "You can call me the IntentBrain agent. I'm an AI built to demo our cold-calling platform. Want to hear how it works, or book a demo?",
    "who built you": "I was built by the team at IntentBrain. We make AI cold-callers for B2B sales teams. Want to hear how it works, or book a demo?",
    "who created you": "The IntentBrain team built me. We make AI cold-callers for B2B sales teams. Want to hear how it works, or book a demo?",
    "who made you": "The IntentBrain team built me. We make AI cold-callers for B2B sales teams. Want to hear how it works, or book a demo?",
    "where are you calling from": "I'm calling from IntentBrain - we're an AI cold-calling platform. Want to hear how it works, or book a demo?",
    "what voice are you using": "I'm using ElevenLabs voice synthesis paired with our own AI brain. Sounds pretty good, right? Want to hear what IntentBrain does, or book a demo?",
    "are you using elevenlabs": "Yes, ElevenLabs is the voice engine. The brain and orchestration is all IntentBrain. Want me to walk you through it, or book a demo?",
    "can people tell you're ai": "Most callers don't catch on right away - that's kind of the point. Want me to explain how IntentBrain works, or book a demo?",
    "can people tell youre ai": "Most callers don't catch on right away - that's kind of the point. Want me to explain how IntentBrain works, or book a demo?",
    "how human do you sound": "Pretty human, apparently - most people don't notice until I tell them. Want me to walk you through what IntentBrain does, or book a demo?",
}


def _fast_path_lookup(text: str):
    """Return canned answer for AI-identity questions, or None."""
    if not text:
        return None
    norm = re.sub(r"[^a-z0-9\\s']", "", text.lower()).strip()
    norm = re.sub(r"\\s+", " ", norm)
    if norm in _BRAIN_FAST_PATH_CACHE:
        return _BRAIN_FAST_PATH_CACHE[norm]
    # Try fuzzy contains on shorter keys (e.g. "hey are you human really?")
    for key, val in _BRAIN_FAST_PATH_CACHE.items():
        if len(key) >= 10 and key in norm:
            return val
    return None


def _ensure_followup(response_text: str) -> str:
    """If the brain answer doesn't end with a question, append a follow-up
    so the caller knows the AI is waiting for them to speak."""
    if not response_text:
        return "Would you like to hear how IntentBrain works, or book a quick demo?"
    stripped = response_text.rstrip()
    if stripped.endswith("?"):
        return response_text
    # Append follow-up
    if not stripped.endswith((".", "!", ":")):
        stripped += "."
    return stripped + " Did that answer your question, or would you like to book a quick demo?"


'''

# Find anchor: place helper block right before `app = FastAPI(`
anchor_match = re.search(r"^app\s*=\s*FastAPI\(", src, re.MULTILINE)
if not anchor_match:
    print("[FATAL] Could not find `app = FastAPI(` anchor in server.py")
    sys.exit(1)

anchor_pos = anchor_match.start()
src = src[:anchor_pos] + helper_block + src[anchor_pos:]
print(f"[INSERT] Helper block inserted at line {src[:anchor_pos].count(chr(10)) + 1}")

# --------------------------------------------------------------------------
# Patch the brain handling block - inject fast-path + follow-up wrapper
# --------------------------------------------------------------------------

OLD = '''            try:
                brain = await brain_respond(speech_result, stage=last_stage or "INTRO")
                response_text = brain.get("response_text", "")
                action = brain.get("action", "continue")
                intent = brain.get("detected_intent", "UNKNOWN")
                logger.info(f"Brain handled '{speech_result[:60]}' -> intent={intent} action={action}")'''

NEW = '''            try:
                # BUG #004 fix - Fast-path cache (bypass OpenAI for AI-identity probes)
                _fast = _fast_path_lookup(speech_result)
                if _fast is not None:
                    logger.info(f"FAST_PATH hit for '{speech_result[:60]}' (no LLM call)")
                    brain = {"response_text": _fast, "action": "continue", "detected_intent": "AI_IDENTITY"}
                else:
                    brain = await brain_respond(speech_result, stage=last_stage or "INTRO")
                response_text = brain.get("response_text", "")
                action = brain.get("action", "continue")
                intent = brain.get("detected_intent", "UNKNOWN")
                # BUG #004 fix - guarantee a follow-up question on continue paths
                if action == "continue":
                    response_text = _ensure_followup(response_text)
                logger.info(f"Brain handled '{speech_result[:60]}' -> intent={intent} action={action}")'''

if OLD not in src:
    print("[FATAL] Could not locate brain handler block to patch.")
    print("        The file may have already been modified. Aborting.")
    sys.exit(1)

src = src.replace(OLD, NEW, 1)
print("[PATCH] Brain handler block patched (fast-path + follow-up wrapper)")

# --------------------------------------------------------------------------
# Write
# --------------------------------------------------------------------------
SERVER.write_text(src)
print(f"[OK] {SERVER} updated.")
print("")
print("Next steps:")
print("  pm2 restart dialgenix-backend --update-env")
print("  pm2 logs dialgenix-backend --lines 50")
