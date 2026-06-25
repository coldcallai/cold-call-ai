#!/usr/bin/env python3
"""Outbound gate pre-flight self-test.

PURPOSE
-------
Regression-safe pre-flight before any prospect batch. Verifies the 9 hard rules
of the Outbound Human-Greeting Gate against the LIVE backend.

USAGE
-----
    cd /var/www/dialgenix/backend         # or /app/backend in dev
    PYTHONPATH=$PWD python3 scripts/outbound_selftest.py [--dial] [--phone +18885131913]

By default the script runs in STRUCTURAL mode: exercises every endpoint via the
mounted FastAPI app, validates TwiML, validates classifier, validates DNC write/
skip — without burning a Twilio minute.

Pass `--dial` to ALSO place a single live call to your test number (default
888-513-1913). The script will hardcode the opener text to the exact founder
phrasing per spec.

REPORTS
-------
Console: PASS/FAIL summary, per-check detail.
File:    /tmp/outbound_selftest_report.json — includes call SID (if --dial),
         each endpoint hit, each disposition observed, whether ElevenLabs audio
         URL was generated, and whether any <Say> was detected.

HARD RULE
---------
No live prospect dials unless this script exits 0.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# ----- Path / env bootstrap -----
HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

# ----- Imports (after path setup) -----
import httpx  # noqa: E402
from httpx import ASGITransport  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from routes import twilio_outbound  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("outbound_selftest")

# ----- Constants -----
DEFAULT_PHONE = "+18885131913"
EXACT_OPENER = (
    "Hi, this is Sarah. Quick question — who handles patient payment workflows for the practice?"
)
DNC_SENTINEL = "+15550000000"  # used in structural DNC check, cleaned up after
REPORT_PATH = "/tmp/outbound_selftest_report.json"


# ============================================================
# Report scaffolding
# ============================================================
class CheckResult(dict):
    def __init__(self, name: str, passed: bool, detail: str, **extra: Any):
        super().__init__(
            name=name,
            passed=bool(passed),
            detail=detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **extra,
        )


def _twiml_has_tag(xml: str, tag: str) -> bool:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return False
    return root.find(f".//{tag}") is not None


def _twiml_find(xml: str, tag: str) -> Optional[ET.Element]:
    try:
        return ET.fromstring(xml).find(f".//{tag}")
    except ET.ParseError:
        return None


# ============================================================
# Dependency wiring against the LIVE production app
# ============================================================
def _build_app_for_selftest():
    """Build a TestClient bound to the SAME router code as production.

    For --dial runs we also wire the REAL Twilio + ElevenLabs clients.
    For structural runs we wire fakes so no Twilio minute / ElevenLabs credit
    is spent. Both paths use the REAL Mongo so DNC writes are visible
    end-to-end and we exercise indices.
    """
    from fastapi import FastAPI

    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "intentbrain")
    if not mongo_url:
        raise SystemExit("Missing MONGO_URL in environment.")

    db = AsyncIOMotorClient(mongo_url)[db_name]

    voice_id = os.environ.get("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"
    backend_url = (
        os.environ.get("BACKEND_URL")
        or os.environ.get("REACT_APP_BACKEND_URL")
        or "http://localhost:8001"
    ).rstrip("/")
    from_number = os.environ.get("TWILIO_OUTBOUND_FROM") or os.environ.get("TWILIO_PHONE_NUMBER") or ""

    app = FastAPI()
    app.include_router(twilio_outbound.router, prefix="/api")
    app.include_router(twilio_outbound.tts_router, prefix="/api")

    return app, db, voice_id, backend_url, from_number


# ============================================================
# Structural checks (no Twilio minute spent)
# ============================================================
async def run_structural_checks(report: Dict[str, Any]) -> bool:
    log.info("== Structural checks (no live dial) ==")
    app, db, voice_id, backend_url, from_number = _build_app_for_selftest()

    # Wire FAKE Twilio + a stub ElevenLabs synthesizer so no credit is spent.
    class _FakeCalls:
        def __init__(self): self.created = []
        def create(self, **kw):
            self.created.append(kw)
            class C: sid = "CA" + uuid.uuid4().hex[:30]
            return C()

    class _FakeTwilio:
        def __init__(self): self.calls = _FakeCalls()

    fake_twilio = _FakeTwilio()
    fake_eleven_invocations: List[Dict[str, Any]] = []
    def _stub_synth(text: str, vid: str) -> bytes:
        fake_eleven_invocations.append({"text": text, "voice_id": vid})
        return b"ID3\x04\x00\x00\x00\x00\x00\x00FAKE_MP3:" + text.encode()[:64]

    twilio_outbound.setup_dependencies(
        db=db, twilio_client=fake_twilio, eleven_client=object(),
        synthesize_fn=_stub_synth, voice_id=voice_id,
        backend_url=backend_url, from_number=from_number or "+15005550006",
    )

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://selftest") as client:
        results = await _structural_checks_inner(client, db, fake_twilio, fake_eleven_invocations)

    report["checks"]["structural"] = results
    report["structural_passed"] = all(r["passed"] for r in results)
    # Cleanup structural test session docs to keep the collection tidy
    await db.outbound_sessions.delete_many({"experiment": "selftest_structural"})
    return report["structural_passed"]


async def _structural_checks_inner(client, db, fake_twilio, fake_eleven_invocations) -> List["CheckResult"]:
    results: List[CheckResult] = []

    # --- Setup: place a structural call (fake Twilio so no spend) ---
    result = await twilio_outbound.place_outbound_call(
        to_number="+15551112222",  # never dialed for real — fake client
        lead_id="selftest-structural",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        lead_attrs={"gbp_rank": 8, "niche": "selftest"},
        opener_text_override=EXACT_OPENER,
        experiment_tag="selftest_structural",
    )
    sid = result.get("call_sid")
    session_id = result.get("session_id")

    # ---- Check 1: phone rings silently (no opener in initial create) ----
    create_kw = fake_twilio.calls.created[-1] if fake_twilio.calls.created else {}
    payload = " ".join(str(v) for v in create_kw.values()).lower()
    cond = (
        "twiml" not in create_kw
        and "url" in create_kw
        and EXACT_OPENER.lower() not in payload
        and "<say" not in payload
        and "<play" not in payload
    )
    results.append(CheckResult(
        "1_phone_rings_silently",
        cond,
        detail="calls.create() uses url= callback, no inline TwiML, no opener in payload.",
        endpoint="twilio.calls.create",
        elevenlabs_audio_url=None,
        say_detected=False,
    ))

    # ---- Check 2: AI does not speak before answer (/answer is silent) ----
    resp = await client.post(
        f"/api/twilio/outbound/answer?session_id={session_id}",
        data={"CallSid": sid, "AnsweredBy": "human"},
    )
    xml = resp.text
    cond = (
        resp.status_code == 200
        and not _twiml_has_tag(xml, "Say")
        and not _twiml_has_tag(xml, "Play")
        and _twiml_has_tag(xml, "Redirect")
    )
    results.append(CheckResult(
        "2_ai_does_not_speak_before_answer",
        cond,
        detail="/answer emits silent <Redirect>; no <Say>, no <Play>.",
        endpoint="POST /api/twilio/outbound/answer",
        elevenlabs_audio_url=None,
        say_detected=_twiml_has_tag(xml, "Say"),
    ))

    # ---- Check 3: human greeting required before opener (/greeting silent Gather) ----
    resp = await client.post(
        f"/api/twilio/outbound/greeting?session_id={session_id}",
        data={"CallSid": sid},
    )
    xml = resp.text
    gather = _twiml_find(xml, "Gather")
    silent_gather = (
        gather is not None
        and gather.get("input", "").startswith("speech")
        and gather.get("speechTimeout") == "auto"
        and gather.find("./Say") is None
        and gather.find("./Play") is None
    )
    cond = (
        resp.status_code == 200
        and not _twiml_has_tag(xml, "Say")
        and not _twiml_has_tag(xml, "Play")
        and silent_gather
    )
    results.append(CheckResult(
        "3_human_greeting_required_before_opener",
        cond,
        detail="/greeting emits silent <Gather speechTimeout='auto'> awaiting speech; no Say/Play children.",
        endpoint="POST /api/twilio/outbound/greeting",
        elevenlabs_audio_url=None,
        say_detected=_twiml_has_tag(xml, "Say"),
    ))

    # ---- Check 4: opener uses ElevenLabs <Play>, not Twilio <Say> ----
    # Trigger /respond with a human greeting ("hello") and inspect the TwiML.
    resp = await client.post(
        f"/api/twilio/outbound/respond?session_id={session_id}",
        data={"CallSid": sid, "SpeechResult": "Hello, this is Sarah speaking."},
    )
    xml = resp.text
    play = _twiml_find(xml, "Play")
    play_url = (play.text or "").strip() if play is not None else ""
    cond = (
        resp.status_code == 200
        and not _twiml_has_tag(xml, "Say")
        and play is not None
        and "/api/tts/audio/" in play_url
    )
    results.append(CheckResult(
        "4_opener_uses_elevenlabs_play_not_say",
        cond,
        detail="/respond emits ElevenLabs <Play> referencing /api/tts/audio/{id}; no <Say>.",
        endpoint="POST /api/twilio/outbound/respond",
        elevenlabs_audio_url=play_url or None,
        say_detected=_twiml_has_tag(xml, "Say"),
    ))

    # ---- Check 5: opener EXACTLY matches founder phrasing (verified via session doc) ----
    sess = await db.outbound_sessions.find_one({"session_id": session_id})
    opener_in_db = (sess or {}).get("opener_text", "")
    cond = (opener_in_db == EXACT_OPENER)
    results.append(CheckResult(
        "5_opener_exact_phrasing",
        cond,
        detail=f"db.outbound_sessions.opener_text == EXACT_OPENER. observed={opener_in_db!r}",
        endpoint="db.outbound_sessions",
        elevenlabs_audio_url=None,
        say_detected=False,
    ))
    # Confirm the audio actually exists and is fetchable as audio/mpeg
    audio_id = (sess or {}).get("opener_audio_id")
    audio_ok = False
    if audio_id:
        ar = await client.get(f"/api/tts/audio/{audio_id}")
        audio_ok = (
            ar.status_code == 200
            and ar.headers.get("content-type", "").startswith("audio/mpeg")
            and len(ar.content) > 0
        )
    results.append(CheckResult(
        "5b_opener_audio_streamable",
        audio_ok,
        detail=f"GET /api/tts/audio/{audio_id} -> audio/mpeg, non-empty.",
        endpoint="GET /api/tts/audio/{id}",
        elevenlabs_audio_url=f"/api/tts/audio/{audio_id}" if audio_id else None,
        say_detected=False,
    ))

    # ---- Check 6: AI response handler uses ElevenLabs only (no Say anywhere across our endpoints) ----
    say_found_anywhere = False
    endpoints_swept = []
    # Re-sweep every endpoint we control with realistic inputs.
    sweep_cases = [
        ("/api/twilio/outbound/answer", {"CallSid": sid, "AnsweredBy": "human", "session_id": session_id}),
        ("/api/twilio/outbound/answer", {"CallSid": sid, "AnsweredBy": "machine_end_beep", "session_id": session_id}),
        ("/api/twilio/outbound/greeting", {"CallSid": sid, "session_id": session_id}),
        ("/api/twilio/outbound/respond", {"CallSid": sid, "SpeechResult": "Hello there", "session_id": session_id}),
        ("/api/twilio/outbound/respond", {"CallSid": sid, "SpeechResult": "Please leave a message after the tone", "session_id": session_id}),
        ("/api/twilio/outbound/respond", {"CallSid": sid, "SpeechResult": "For sales press 1", "session_id": session_id}),
        ("/api/twilio/outbound/respond", {"CallSid": sid, "SpeechResult": "Remove me from your list", "session_id": session_id}),
        ("/api/twilio/outbound/status", {"CallSid": sid, "CallStatus": "completed", "session_id": session_id}),
    ]
    for path, data in sweep_cases:
        qs = f"?session_id={data.pop('session_id')}" if "session_id" in data else ""
        r = await client.post(f"{path}{qs}", data=data)
        endpoints_swept.append({"path": path, "status": r.status_code, "say_detected": _twiml_has_tag(r.text, "Say")})
        if _twiml_has_tag(r.text, "Say"):
            say_found_anywhere = True
    results.append(CheckResult(
        "6_response_handler_uses_elevenlabs_only",
        not say_found_anywhere,
        detail="Swept all outbound endpoints with realistic inputs; no <Say> ever emitted.",
        endpoint="ALL /api/twilio/outbound/*",
        elevenlabs_audio_url=None,
        say_detected=say_found_anywhere,
        sweep=endpoints_swept,
    ))

    # ---- Check 7: voicemail / IVR classification does not start full conversation ----
    # Run 3 fresh sessions: voicemail phrase, IVR phrase, AMD machine.
    sub_results = []
    for label, kind, action in [
        ("voicemail_phrase", "respond", "Please leave a message after the tone"),
        ("ivr_phrase", "respond", "For sales press 1 for billing press 2"),
        ("amd_machine", "answer", "machine_end_beep"),
    ]:
        r = await twilio_outbound.place_outbound_call(
            to_number=f"+15551112{int(time.time())%1000:03d}",
            lead_id=f"selftest-{label}",
            campaign_id="ranktrust_local_growth",
            variant_index=3,
            opener_text_override=EXACT_OPENER,
            experiment_tag="selftest_structural",
        )
        sub_sid = r["session_id"]
        if kind == "respond":
            resp = await client.post(
                f"/api/twilio/outbound/respond?session_id={sub_sid}",
                data={"CallSid": r["call_sid"], "SpeechResult": action},
            )
        else:
            resp = await client.post(
                f"/api/twilio/outbound/answer?session_id={sub_sid}",
                data={"CallSid": r["call_sid"], "AnsweredBy": action},
            )
        xml = resp.text
        dosession = await db.outbound_sessions.find_one({"session_id": sub_sid})
        disposition = (dosession or {}).get("disposition", "")
        no_opener = not _twiml_has_tag(xml, "Play") and disposition in ("VOICEMAIL", "IVR")
        sub_results.append({
            "case": label,
            "disposition": disposition,
            "opener_played": (dosession or {}).get("opener_played", False),
            "twiml_has_play": _twiml_has_tag(xml, "Play"),
            "twiml_has_say": _twiml_has_tag(xml, "Say"),
            "passed": no_opener,
        })
    cond7 = all(s["passed"] for s in sub_results)
    results.append(CheckResult(
        "7_voicemail_ivr_does_not_start_conversation",
        cond7,
        detail="Voicemail / IVR / AMD machine all short-circuited with NO <Play> and disposition VOICEMAIL/IVR.",
        endpoint="POST /api/twilio/outbound/{answer,respond}",
        elevenlabs_audio_url=None,
        say_detected=any(s["twiml_has_say"] for s in sub_results),
        cases=sub_results,
    ))

    # ---- Check 8: DNC handling writes to db.dnc_list and skips future calls ----
    # 8a — caller asks to be removed → row written
    r = await twilio_outbound.place_outbound_call(
        to_number=DNC_SENTINEL,
        lead_id="selftest-dnc-write",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        opener_text_override=EXACT_OPENER,
        experiment_tag="selftest_structural",
    )
    dnc_session = r.get("session_id")
    resp = await client.post(
        f"/api/twilio/outbound/respond?session_id={dnc_session}",
        data={"CallSid": r["call_sid"], "SpeechResult": "Please take me off your list, do not call again."},
    )
    dnc_xml = resp.text
    dnc_row = await db.dnc_list.find_one({"phone_number": DNC_SENTINEL})
    dnc_sess = await db.outbound_sessions.find_one({"session_id": dnc_session})
    dnc_say_detected = _twiml_has_tag(dnc_xml, "Say")

    # 8b — same number now skipped on next dial
    r2 = await twilio_outbound.place_outbound_call(
        to_number=DNC_SENTINEL,
        lead_id="selftest-dnc-skip",
        campaign_id="ranktrust_local_growth",
        variant_index=3,
        opener_text_override=EXACT_OPENER,
        experiment_tag="selftest_structural",
    )
    cond8 = (
        dnc_row is not None
        and (dnc_sess or {}).get("disposition") == "DNC"
        and r2.get("ok") is False
        and r2.get("skipped") == "dnc"
        and not dnc_say_detected
    )
    results.append(CheckResult(
        "8_dnc_writes_and_skips",
        cond8,
        detail="DNC verbal request wrote db.dnc_list; subsequent dial returned skipped=dnc.",
        endpoint="POST /api/twilio/outbound/respond + place_outbound_call",
        elevenlabs_audio_url=None,
        say_detected=dnc_say_detected,
        dnc_row=dnc_row and {"phone_number": dnc_row["phone_number"], "reason": dnc_row.get("reason")},
        disposition=(dnc_sess or {}).get("disposition"),
    ))
    # Cleanup the sentinel DNC row so re-runs are idempotent
    await db.dnc_list.delete_one({"phone_number": DNC_SENTINEL})

    # ---- Check 9: Twilio <Say> is never used for AI voice ----
    results.append(CheckResult(
        "9_say_never_used_for_ai_voice",
        not say_found_anywhere,
        detail="Aggregate sweep from check 6: zero <Say> elements emitted anywhere across the outbound surface.",
        endpoint="ALL /api/twilio/outbound/*",
        elevenlabs_audio_url=None,
        say_detected=say_found_anywhere,
    ))

    return results


# ============================================================
# Live dial — ONLY runs with --dial, dials only one number
# ============================================================
async def run_live_dial(report: Dict[str, Any], phone: str) -> bool:
    log.info(f"== Live dial to {phone} ==")
    _app, db, voice_id, backend_url, from_number = _build_app_for_selftest()

    if not from_number:
        report["checks"]["live_dial"] = [CheckResult(
            "live_setup", False,
            "TWILIO_OUTBOUND_FROM / TWILIO_PHONE_NUMBER not set — cannot dial.",
            endpoint="env", elevenlabs_audio_url=None, say_detected=False,
        )]
        return False

    from elevenlabs import ElevenLabs
    from twilio.rest import Client as TwilioClient
    eleven_key = os.environ.get("ELEVENLABS_API_KEY")
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not (eleven_key and twilio_sid and twilio_token):
        report["checks"]["live_dial"] = [CheckResult(
            "live_setup", False,
            "Missing Twilio or ElevenLabs credentials.",
            endpoint="env", elevenlabs_audio_url=None, say_detected=False,
        )]
        return False

    twilio_outbound.setup_dependencies(
        db=db,
        twilio_client=TwilioClient(twilio_sid, twilio_token),
        eleven_client=ElevenLabs(api_key=eleven_key),
        synthesize_fn=None,  # real ElevenLabs synthesis
        voice_id=voice_id,
        backend_url=backend_url,
        from_number=from_number,
    )

    # Place the call with the exact opener phrasing locked in
    result = await twilio_outbound.place_outbound_call(
        to_number=phone,
        lead_id=f"selftest-live-{uuid.uuid4().hex[:8]}",
        campaign_id="selftest",
        variant_index=0,
        opener_text_override=EXACT_OPENER,
        business_name="SELFTEST",
        experiment_tag="selftest_live",
    )

    results: List[CheckResult] = []
    if not result.get("ok"):
        results.append(CheckResult(
            "live_dial_placed",
            False,
            f"place_outbound_call returned {result}",
            endpoint="twilio.calls.create",
            elevenlabs_audio_url=None,
            say_detected=False,
            call_sid=None,
        ))
        report["checks"]["live_dial"] = results
        return False

    call_sid = result["call_sid"]
    session_id = result["session_id"]
    log.info(f"Live call placed: sid={call_sid} session={session_id}")
    log.info("Answer the phone and say 'Hello'. Polling outbound_sessions for opener playback...")

    # Verify opener exact text + audio_id usable
    sess = await db.outbound_sessions.find_one({"session_id": session_id})
    opener_in_db = (sess or {}).get("opener_text", "")
    audio_id = (sess or {}).get("opener_audio_id")
    results.append(CheckResult(
        "live_opener_exact_phrasing",
        opener_in_db == EXACT_OPENER,
        detail=f"db.outbound_sessions.opener_text == EXACT_OPENER. observed={opener_in_db!r}",
        endpoint="db.outbound_sessions",
        elevenlabs_audio_url=f"{backend_url}/api/tts/audio/{audio_id}" if audio_id else None,
        say_detected=False,
        call_sid=call_sid,
    ))

    # Poll for up to 90s — wait for either opener_played or terminal disposition
    deadline = time.time() + 90
    last_state: Dict[str, Any] = {}
    while time.time() < deadline:
        s = await db.outbound_sessions.find_one({"session_id": session_id}) or {}
        last_state = s
        if s.get("opener_played") or s.get("disposition") in ("VOICEMAIL", "IVR", "DNC"):
            break
        await asyncio.sleep(2)

    disposition = last_state.get("disposition", "UNKNOWN")
    opener_played = bool(last_state.get("opener_played"))
    results.append(CheckResult(
        "live_call_disposition",
        disposition in ("CONVERSATION", "VOICEMAIL", "IVR", "DNC"),
        detail=f"Final disposition={disposition} opener_played={opener_played} answered_by={last_state.get('answered_by')}",
        endpoint="db.outbound_sessions",
        elevenlabs_audio_url=f"{backend_url}/api/tts/audio/{audio_id}" if audio_id else None,
        say_detected=False,
        call_sid=call_sid,
        disposition=disposition,
        opener_played=opener_played,
    ))

    report["checks"]["live_dial"] = results
    report["live_passed"] = all(r["passed"] for r in results)
    return report["live_passed"]


# ============================================================
# Entry point
# ============================================================
async def amain(args: argparse.Namespace) -> int:
    report: Dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phone": args.phone,
        "exact_opener": EXACT_OPENER,
        "mode": "dial" if args.dial else "structural_only",
        "checks": {},
    }

    structural_ok = await run_structural_checks(report)
    overall_ok = structural_ok

    if args.dial:
        # Hard rule: don't dial if structural failed
        if not structural_ok:
            log.error("Structural checks FAILED — refusing to place live dial.")
        else:
            live_ok = await run_live_dial(report, args.phone)
            overall_ok = overall_ok and live_ok

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = overall_ok

    # Write JSON
    Path(REPORT_PATH).write_text(json.dumps(report, indent=2, default=str))
    log.info(f"Report written: {REPORT_PATH}")

    # Console summary
    print("\n" + "=" * 70)
    print(f"OUTBOUND SELF-TEST — {'PASS' if overall_ok else 'FAIL'}")
    print("=" * 70)
    for section, items in report["checks"].items():
        print(f"\n[{section}]")
        for r in items:
            status = "✓" if r["passed"] else "✗"
            print(f"  {status}  {r['name']:50}  {r['detail']}")
    print("\nReport:", REPORT_PATH)
    print("=" * 70)

    return 0 if overall_ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dial", action="store_true",
                    help="Also place ONE live call to --phone (default 888-513-1913).")
    ap.add_argument("--phone", default=DEFAULT_PHONE, help="Test number to dial when --dial is set.")
    args = ap.parse_args()
    sys.exit(asyncio.run(amain(args)))


if __name__ == "__main__":
    main()
