#!/usr/bin/env python3
"""
Patch v4:
  1. Add background prewarm of fast-path audio at startup (semaphore=4)
  2. Fix "Sarah" identity leak in greeting
  3. Delete stale inbound_greeting.b64 so new greeting gets regenerated
"""
import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

SERVER = Path("/var/www/dialgenix/backend/server.py")
CACHE_DIR = Path("/var/www/dialgenix/backend/inbound_audio_cache")
if not SERVER.exists():
    print(f"[FATAL] {SERVER} not found"); sys.exit(1)

src = SERVER.read_text()

# Idempotency
if "prewarm_fast_path_audio" in src:
    print("[SKIP] Prewarm function already present.")
else:
    backup = SERVER.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(SERVER, backup)
    print(f"[BACKUP] {backup}")

    # -------------------------------------------------------------
    # 1) Fix "Sarah" identity leak in greeting text
    # -------------------------------------------------------------
    OLD_GREETING = '"greeting": "Hi, thanks for calling IntentBrain! This is Sarah, your AI sales assistant. I can answer questions about our platform, help you understand if we\'re a good fit, and even book a demo with our team. How can I help you today?"'
    NEW_GREETING = '"greeting": "Hi, thanks for calling IntentBrain! I\'m your AI assistant. I can answer questions about the platform, help you figure out if we\'re a good fit, and even book a demo. How can I help?"'
    if OLD_GREETING in src:
        src = src.replace(OLD_GREETING, NEW_GREETING)
        print("[PATCH] Greeting text updated (Sarah -> neutral identity)")
    else:
        print("[WARN] Old greeting text not found - may have been edited already")

    # -------------------------------------------------------------
    # 2) Insert prewarm hook AFTER cache_inbound_audio definition
    # -------------------------------------------------------------
    PREWARM_BLOCK = '''
# ---------------------------------------------------------------------------
# BUG #004 fix - Pre-warm fast-path audio in background so first call is fast
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def prewarm_fast_path_audio():
    """Kick off background generation of TTS audio for fast-path responses.
    Runs after startup so it doesn't block app readiness."""
    if not elevenlabs_api_key:
        logger.info("No ElevenLabs key - skipping fast-path prewarm")
        return
    asyncio.create_task(_do_prewarm_fast_path_audio())


async def _do_prewarm_fast_path_audio():
    try:
        sem = asyncio.Semaphore(4)
        unique_texts = sorted(set(_BRAIN_FAST_PATH_CACHE.values()))

        async def _gen_one(text: str):
            async with sem:
                h = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
                ck = f"inbound_dyn_{h}"
                if ck in _inbound_audio_cache:
                    return "memory"
                disk_path = os.path.join(_INBOUND_AUDIO_DIR, f"{ck}.b64")
                if os.path.exists(disk_path):
                    with open(disk_path, "r") as f:
                        _inbound_audio_cache[ck] = f.read()
                    return "disk"
                await generate_inbound_audio(text, cache_key=ck)
                return "fresh" if ck in _inbound_audio_cache else "failed"

        results = await asyncio.gather(*[_gen_one(t) for t in unique_texts],
                                       return_exceptions=True)
        counts = {"memory": 0, "disk": 0, "fresh": 0, "failed": 0, "error": 0}
        for r in results:
            if isinstance(r, Exception):
                counts["error"] += 1
            elif r in counts:
                counts[r] += 1
        logger.info(
            f"Fast-path audio prewarm complete: total={len(unique_texts)} "
            f"memory={counts['memory']} disk={counts['disk']} "
            f"fresh={counts['fresh']} failed={counts['failed']} error={counts['error']}"
        )
    except Exception as e:
        logger.error(f"Fast-path prewarm error: {e}")

'''

    # Insert AFTER the cache_inbound_audio function ends.
    # Anchor: the line `# Endpoint to serve cached inbound audio`
    anchor = "# Endpoint to serve cached inbound audio"
    if anchor not in src:
        print(f"[FATAL] Anchor not found: {anchor!r}")
        sys.exit(1)
    src = src.replace(anchor, PREWARM_BLOCK + "\n" + anchor, 1)
    print("[PATCH] Prewarm hook inserted")

    SERVER.write_text(src)
    print(f"[OK] {SERVER} updated.")

# -------------------------------------------------------------
# 3) Delete stale greeting cache so it regenerates with new text
# -------------------------------------------------------------
stale = CACHE_DIR / "inbound_greeting.b64"
if stale.exists():
    stale.unlink()
    print(f"[DELETE] {stale} (will regenerate on next startup)")
else:
    print(f"[INFO] {stale} not present - nothing to delete")

print("")
print("Next: pm2 restart dialgenix-backend --update-env")
print("Wait ~30s for fast-path prewarm to finish, then test the call.")
