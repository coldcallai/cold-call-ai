#!/usr/bin/env python3
"""Sarah - Hybrid TTS (BUG #001). ElevenLabs everywhere, Polly only on failure."""
import re, shutil, sys
from datetime import datetime
from pathlib import Path

BACKEND = Path("/var/www/dialgenix/backend")
SERVER = BACKEND / "server.py"

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(SERVER, BACKEND / f"server.py.bak_{ts}")
print(f"BACKUP: server.py.bak_{ts}")

src = SERVER.read_text()
orig_len = len(src)
changes = []

pattern = re.compile(
    r"(\w+)\.say\(\s*([^()]+?)\s*,\s*voice=['\"]Polly\.Joanna-Neural['\"]\s*\)",
    re.DOTALL,
)

def replacer(match):
    line_end = src.find("\n", match.end())
    if line_end == -1:
        line_end = len(src)
    line_content = src[match.start():line_end]
    if "tts_fallback" in line_content:
        return match.group(0)
    var = match.group(1)
    args = match.group(2).strip()
    args_collapsed = " ".join(args.split())
    return f"await tts_speak({var}, {args_collapsed})"

src_new, n_repl = pattern.subn(replacer, src)
src = src_new
changes.append(f"Replaced {n_repl} Polly direct call(s) with await tts_speak(...)")

if "import hashlib" not in src:
    src = re.sub(r"(\nimport os\n)", r"\1import hashlib\n", src, count=1)
    if "import hashlib" not in src:
        src = "import hashlib\n" + src
    changes.append("Added 'import hashlib'")

TTS_HELPER = '''# === Central TTS helper (BUG #001 fix) ===
_TTS_LOG = logging.getLogger("tts")

async def tts_speak(target, text, *, audio_key=None, intent="UNKNOWN",
                    stage="UNKNOWN", call_sid="", route=""):
    backend_url = os.environ.get("BACKEND_URL", "")
    provider = "polly"
    voice_id = "Polly.Joanna-Neural"
    cache_hit = False
    fallback_reason = None
    safe_text = (text or "").strip()
    if not safe_text:
        return
    if audio_key:
        cache_key = f"inbound_{audio_key}"
        url_path = audio_key
    else:
        h = hashlib.md5(safe_text.encode("utf-8")).hexdigest()[:16]
        cache_key = f"inbound_dyn_{h}"
        url_path = f"dyn_{h}"
    try:
        if cache_key in _inbound_audio_cache:
            target.play(f"{backend_url}/api/inbound-audio/{url_path}")
            provider = "elevenlabs"
            voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "default")
            cache_hit = True
        else:
            try:
                await generate_inbound_audio(safe_text, cache_key=cache_key)
                if cache_key in _inbound_audio_cache:
                    target.play(f"{backend_url}/api/inbound-audio/{url_path}")
                    provider = "elevenlabs"
                    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "default")
                    cache_hit = False
                else:
                    raise RuntimeError("ElevenLabs returned no audio")
            except Exception as e:
                fallback_reason = f"elevenlabs_failed:{type(e).__name__}:{str(e)[:80]}"
                target.say(safe_text, voice='Polly.Joanna-Neural')  # noqa: tts_fallback
    except Exception as e:
        fallback_reason = f"tts_helper_error:{type(e).__name__}:{str(e)[:80]}"
        try:
            target.say(safe_text, voice='Polly.Joanna-Neural')  # noqa: tts_fallback
        except Exception:
            pass
    log_text = safe_text[:120].replace("\\n", " ").replace('"', "'")
    _TTS_LOG.info(
        f'TTS_USED call_sid={call_sid or "n/a"} intent={intent} stage={stage} '
        f'provider={provider} voice_id={voice_id} cache_hit={cache_hit} '
        f'fallback_reason={fallback_reason or "null"} route={route or "n/a"} '
        f'response="{log_text}"'
    )


'''

ANCHOR = '@api_router.get("/inbound-audio/{audio_key}")'
if "async def tts_speak" not in src:
    if ANCHOR not in src:
        print("ERROR: anchor not found"); sys.exit(2)
    src = src.replace(ANCHOR, TTS_HELPER + ANCHOR, 1)
    changes.append("Inserted async tts_speak() helper")
else:
    changes.append("SKIP: tts_speak already present")

SERVER.write_text(src)
print(f"WROTE: server.py ({orig_len} -> {len(src)} bytes)")
print()
print("==== SUMMARY ====")
for c in changes:
    print(f"  * {c}")
