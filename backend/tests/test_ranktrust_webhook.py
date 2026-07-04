"""Regression tests for the RankTrust handoff webhook.

Covers:
  1. HMAC auth accepted with valid signature; rejected with tampered body.
  2. Token fallback accepted via ?token= query and via X-RankTrust-Token header.
  3. Unauthorized requests never touch the DB.
  4. Missing phone → status='needs_phone', callback fires with the reason,
     no scheduled_call row created.
  5. Valid packet with phone → status='scheduled' + ranktrust_scheduled_calls row.
  6. Idempotency on packet_id — second POST returns replayed=true, no dupes.
  7. Delay-range validation: <60 and >86400 → 422.
  8. Scheduler tick with OUTBOUND_DISABLED sentinel → status='blocked_outbound_disabled',
     callback fires with the reason, place_outbound_call refuses (respects the gate).
  9. Scheduler tick with phone on DNC → status='blocked_dnc', callback fires.
 10. Scheduler tick happy path → dial placed, callback fires 'dial_placed'.
 11. Callback body never contains callback_token or HMAC secret.
 12. Public response never leaks callback_token.
"""
from __future__ import annotations

import hashlib
import hmac
import json as _json
import os
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from routes import ranktrust_webhook, twilio_outbound  # noqa: E402


HMAC_SECRET = "supersecret_test_hmac_key_do_not_leak"
TOKEN = "shared_token_test_value"


def _sign(body: bytes, secret: str = HMAC_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _valid_packet(**overrides) -> Dict[str, Any]:
    packet = {
        "packet_id": "pkt-001",
        "business": {
            "name": "Acme Dental",
            "industry": "dental",
            "phone": "+14045551234",
            "website": "https://acme.example.com",
        },
        "revenue_opportunity": 45000.0,
        "close_probability": 0.62,
        "best_offer": "Free 30-day pilot",
        "sales_script": {
            "opener": "Hi, this is Sarah. I noticed Acme Dental could be reaching more patients — got 30 seconds?",
            "key_points": ["local SEO", "review generation"],
            "call_to_action": "Book a 15-minute strategy call",
        },
        "objections": [
            {"objection": "We already have an SEO company",
             "response": "Totally fair — most agencies focus on rankings, we focus on booked patients."}
        ],
        "conversation_strategy": "Warm, consultative. Never pitch — ask questions.",
        "delay_seconds": 300,
        "callback_url": "https://ranktrust.example.com/webhooks/intentbrain",
        "callback_token": "top_secret_callback_bearer_XYZ",
    }
    packet.update(overrides)
    return packet


@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    return client["intentbrain_test_ranktrust"]


@pytest.fixture
def app(db, monkeypatch):
    # Isolate the outbound router's kill switch to a temp path so tests don't
    # collide with any real OUTBOUND_DISABLED file.
    kill_switch = "/tmp/_ranktrust_test_kill_switch"
    if os.path.exists(kill_switch):
        os.unlink(kill_switch)

    class _FakeTwilioCalls:
        def __init__(self): self.created = []
        def create(self, **kw):
            self.created.append(kw)
            class _C: sid = "CATEST" + str(len(self.created)).zfill(30)
            return _C()

    class _FakeTwilio:
        def __init__(self): self.calls = _FakeTwilioCalls()

    fake_twilio = _FakeTwilio()

    def _stub_synth(text: str, vid: str) -> bytes:
        return b"ID3\x04\x00\x00\x00" + text.encode()[:80]

    twilio_outbound.setup_dependencies(
        db=db, twilio_client=fake_twilio, eleven_client=object(),
        synthesize_fn=_stub_synth,
        voice_id="V", backend_url="https://test.example.com",
        from_number="+15005550006",
        kill_switch_path=kill_switch,
        selftest_report_path="/tmp/_ranktrust_test_report_does_not_exist.json",
    )

    ranktrust_webhook.setup_dependencies(
        db=db,
        handoff_secret=HMAC_SECRET,
        handoff_token=TOKEN,
        callback_url_default="",
        callback_token_default="",
        poll_seconds=1,
    )
    # Capture all callback POSTs from tests
    posted: List[Dict[str, Any]] = []

    async def _capture_callback(url, json=None, headers=None, **kw):
        posted.append({"url": url, "json": json, "headers": dict(headers or {})})
        class _R:
            status_code = 200
            text = "ok"
        return _R()

    async def _fake_client_post_ctx(*args, **kwargs):
        # Wrapped via monkeypatching httpx.AsyncClient
        raise AssertionError("should not be reached — httpx patched at the class level")

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, url, json=None, headers=None, **kw):
            return await _capture_callback(url, json=json, headers=headers, **kw)

    monkeypatch.setattr(ranktrust_webhook.httpx, "AsyncClient", _FakeAsyncClient)

    app_obj = FastAPI()
    app_obj.include_router(ranktrust_webhook.router, prefix="/api")

    # Expose test hooks
    app_obj.state.posted_callbacks = posted
    app_obj.state.fake_twilio = fake_twilio
    app_obj.state.kill_switch_path = kill_switch
    return app_obj


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://selftest") as c:
        yield c


# ============================================================
# 1 — HMAC accepted; tampered body rejected.
# ============================================================
@pytest.mark.asyncio
async def test_1_hmac_valid_and_tampered(client, db):
    packet = _valid_packet()
    body = _json.dumps(packet).encode()
    # Valid signature
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "scheduled"

    # Tampered body (change one byte) — signature no longer matches
    tampered = body.replace(b"Acme Dental", b"Nope Dental")
    r2 = await client.post("/api/webhooks/ranktrust/handoff", content=tampered,
                           headers={"X-RankTrust-Signature": _sign(body),  # signed original
                                    "Content-Type": "application/json"})
    assert r2.status_code == 401
    # Confirm no dupe row
    count = await db.ranktrust_handoffs.count_documents({"packet_id": "pkt-001"})
    assert count == 1


# ============================================================
# 2 — Token fallback accepted (query + header).
# ============================================================
@pytest.mark.asyncio
async def test_2_token_fallback_query_and_header(client, db):
    packet = _valid_packet(packet_id="pkt-token-query")
    body = _json.dumps(packet).encode()
    r = await client.post(f"/api/webhooks/ranktrust/handoff?token={TOKEN}",
                          content=body, headers={"Content-Type": "application/json"})
    assert r.status_code == 200

    packet2 = _valid_packet(packet_id="pkt-token-hdr")
    body2 = _json.dumps(packet2).encode()
    r2 = await client.post("/api/webhooks/ranktrust/handoff",
                           content=body2,
                           headers={"X-RankTrust-Token": TOKEN,
                                    "Content-Type": "application/json"})
    assert r2.status_code == 200


# ============================================================
# 3 — Unauthorized requests never touch the DB.
# ============================================================
@pytest.mark.asyncio
async def test_3_unauthorized_no_db_write(client, db):
    packet = _valid_packet(packet_id="pkt-noauth")
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"Content-Type": "application/json"})
    assert r.status_code == 401
    r2 = await client.post(f"/api/webhooks/ranktrust/handoff?token=WRONG_TOKEN",
                           content=body, headers={"Content-Type": "application/json"})
    assert r2.status_code == 401
    r3 = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                           headers={"X-RankTrust-Signature": _sign(body, "WRONG_SECRET"),
                                    "Content-Type": "application/json"})
    assert r3.status_code == 401

    count = await db.ranktrust_handoffs.count_documents({"packet_id": "pkt-noauth"})
    assert count == 0


# ============================================================
# 4 — Missing phone → status='needs_phone', callback fires, NO scheduled dial.
# ============================================================
@pytest.mark.asyncio
async def test_4_missing_phone_needs_phone(app, client, db):
    packet = _valid_packet(packet_id="pkt-nophone")
    packet["business"]["phone"] = None
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200
    assert r.json()["status"] == "needs_phone"
    # No scheduled call
    scheduled = await db.ranktrust_scheduled_calls.count_documents({"packet_id": "pkt-nophone"})
    assert scheduled == 0
    # Give the create_task a beat to run
    import asyncio; await asyncio.sleep(0.05)
    calls = [c for c in app.state.posted_callbacks if c["json"]["packet_id"] == "pkt-nophone"]
    assert len(calls) == 1
    assert calls[0]["json"]["outcome"] == "needs_phone"


# ============================================================
# 5 — Valid packet with phone → scheduled row created with target_at ~ now+delay.
# ============================================================
@pytest.mark.asyncio
async def test_5_scheduled_row_created(client, db):
    packet = _valid_packet(packet_id="pkt-sched", delay_seconds=120)
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200
    row = await db.ranktrust_scheduled_calls.find_one({"packet_id": "pkt-sched"})
    assert row is not None
    assert row["status"] == "pending"
    assert row["phone"] == "+14045551234"
    # target_at is ISO — verify it's in the future
    from datetime import datetime, timezone
    target = datetime.fromisoformat(row["target_at"])
    assert (target - datetime.now(timezone.utc)).total_seconds() > 60


# ============================================================
# 6 — Idempotent on packet_id.
# ============================================================
@pytest.mark.asyncio
async def test_6_idempotent_on_packet_id(client, db):
    packet = _valid_packet(packet_id="pkt-idem")
    body = _json.dumps(packet).encode()
    r1 = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                           headers={"X-RankTrust-Signature": _sign(body),
                                    "Content-Type": "application/json"})
    assert r1.status_code == 200
    assert r1.json()["replayed"] is False

    # Second identical POST
    r2 = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                           headers={"X-RankTrust-Signature": _sign(body),
                                    "Content-Type": "application/json"})
    assert r2.status_code == 200
    assert r2.json()["replayed"] is True

    assert await db.ranktrust_handoffs.count_documents({"packet_id": "pkt-idem"}) == 1
    assert await db.ranktrust_scheduled_calls.count_documents({"packet_id": "pkt-idem"}) == 1


# ============================================================
# 7 — Delay-range validation.
# ============================================================
@pytest.mark.asyncio
async def test_7_delay_range_validation(client):
    for bad in (30, 59, 86401, 999999):
        packet = _valid_packet(packet_id=f"pkt-bad-{bad}", delay_seconds=bad)
        body = _json.dumps(packet).encode()
        r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                              headers={"X-RankTrust-Signature": _sign(body),
                                       "Content-Type": "application/json"})
        assert r.status_code == 422, f"delay={bad} should be rejected"


# ============================================================
# 8 — Scheduler + kill switch: place_outbound_call refuses → blocked_outbound_disabled.
# ============================================================
@pytest.mark.asyncio
async def test_8_scheduler_respects_kill_switch(app, client, db):
    packet = _valid_packet(packet_id="pkt-killed", delay_seconds=60)
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200

    # Fast-forward the scheduled target_at + write the kill switch
    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-killed"}, {"$set": {"target_at": past}}
    )
    with open(app.state.kill_switch_path, "w") as f:
        f.write("selftest_failed\n")

    stats = await ranktrust_webhook.scheduler_tick_once()
    assert stats["blocked"] == 1

    sched = await db.ranktrust_scheduled_calls.find_one({"packet_id": "pkt-killed"})
    assert sched["status"] == "blocked_outbound_disabled"
    # Twilio must not have been called
    assert len(app.state.fake_twilio.calls.created) == 0
    # Callback fired with the right outcome
    callbacks = [c for c in app.state.posted_callbacks if c["json"]["packet_id"] == "pkt-killed"]
    assert any(c["json"]["outcome"] == "blocked_outbound_disabled" for c in callbacks)

    os.unlink(app.state.kill_switch_path)


# ============================================================
# 9 — Scheduler + DNC: phone on DNC → blocked_dnc.
# ============================================================
@pytest.mark.asyncio
async def test_9_scheduler_respects_dnc(app, client, db):
    packet = _valid_packet(packet_id="pkt-dnc", delay_seconds=60)
    packet["business"]["phone"] = "+14045552222"
    await db.dnc_list.insert_one({"phone_number": "+14045552222",
                                   "added_at": "2026-01-01T00:00:00Z", "reason": "prior"})
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200

    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-dnc"}, {"$set": {"target_at": past}}
    )
    stats = await ranktrust_webhook.scheduler_tick_once()
    assert stats["blocked"] == 1

    sched = await db.ranktrust_scheduled_calls.find_one({"packet_id": "pkt-dnc"})
    assert sched["status"] == "blocked_dnc"
    assert len(app.state.fake_twilio.calls.created) == 0
    callbacks = [c for c in app.state.posted_callbacks if c["json"]["packet_id"] == "pkt-dnc"]
    assert any(c["json"]["outcome"] == "blocked_dnc" for c in callbacks)


# ============================================================
# 10 — Scheduler happy path: dial placed, callback 'dial_placed'.
# ============================================================
@pytest.mark.asyncio
async def test_10_scheduler_happy_path(app, client, db):
    packet = _valid_packet(packet_id="pkt-happy")
    packet["business"]["phone"] = "+14045553333"
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200

    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-happy"}, {"$set": {"target_at": past}}
    )
    stats = await ranktrust_webhook.scheduler_tick_once()
    assert stats["dialed"] == 1

    sched = await db.ranktrust_scheduled_calls.find_one({"packet_id": "pkt-happy"})
    assert sched["status"] == "dialed"
    assert sched["call_sid"].startswith("CATEST")
    assert len(app.state.fake_twilio.calls.created) == 1

    # Give create_task a beat
    import asyncio; await asyncio.sleep(0.05)
    callbacks = [c for c in app.state.posted_callbacks if c["json"]["packet_id"] == "pkt-happy"]
    assert any(c["json"]["outcome"] == "dial_placed" for c in callbacks)


# ============================================================
# 11 — Callback body never contains callback_token or HMAC secret.
# ============================================================
@pytest.mark.asyncio
async def test_11_callback_bearer_uses_token_but_body_omits_secrets(app, client, db):
    packet = _valid_packet(packet_id="pkt-secretcheck")
    body = _json.dumps(packet).encode()
    await client.post("/api/webhooks/ranktrust/handoff", content=body,
                      headers={"X-RankTrust-Signature": _sign(body),
                               "Content-Type": "application/json"})
    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-secretcheck"}, {"$set": {"target_at": past}}
    )
    await ranktrust_webhook.scheduler_tick_once()
    import asyncio; await asyncio.sleep(0.05)

    hits = [c for c in app.state.posted_callbacks if c["json"]["packet_id"] == "pkt-secretcheck"]
    assert hits
    for c in hits:
        flat = _json.dumps(c["json"])
        assert "top_secret_callback_bearer_XYZ" not in flat, "callback_token leaked into body"
        assert HMAC_SECRET not in flat, "HMAC secret leaked into body"
        # The Authorization header IS allowed to carry the token — that's how callbacks auth.
        assert c["headers"].get("Authorization") == "Bearer top_secret_callback_bearer_XYZ"


# ============================================================
# 12 — Public GET response never leaks callback_token.
# ============================================================
@pytest.mark.asyncio
async def test_12_public_view_redacts_callback_token(client, db):
    packet = _valid_packet(packet_id="pkt-view")
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200
    flat = _json.dumps(r.json())
    assert "top_secret_callback_bearer_XYZ" not in flat

    # And the GET endpoint too
    r2 = await client.get("/api/webhooks/ranktrust/handoff/pkt-view")
    assert r2.status_code == 200
    assert "top_secret_callback_bearer_XYZ" not in _json.dumps(r2.json())


# ============================================================
# 13 — RankTrust handoff dials get the runaway-cost cap.
# Default 120s. OUTBOUND_MAX_CALL_SECONDS env var overrides. Non-positive
# / malformed env values fall back to the 120s default.
# ============================================================
@pytest.mark.asyncio
async def test_13a_ranktrust_dial_gets_default_120s_cap(app, client, db, monkeypatch):
    monkeypatch.delenv("OUTBOUND_MAX_CALL_SECONDS", raising=False)
    packet = _valid_packet(packet_id="pkt-cap-default")
    packet["business"]["phone"] = "+14045557777"
    body = _json.dumps(packet).encode()
    r = await client.post("/api/webhooks/ranktrust/handoff", content=body,
                          headers={"X-RankTrust-Signature": _sign(body),
                                   "Content-Type": "application/json"})
    assert r.status_code == 200

    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-cap-default"}, {"$set": {"target_at": past}}
    )
    await ranktrust_webhook.scheduler_tick_once()

    created = app.state.fake_twilio.calls.created
    assert len(created) == 1
    assert created[0].get("time_limit") == 120, (
        f"RankTrust handoff dial must get the default 120s cap. Got: {created[0].get('time_limit')!r}"
    )


@pytest.mark.asyncio
async def test_13b_ranktrust_dial_honors_env_override(app, client, db, monkeypatch):
    monkeypatch.setenv("OUTBOUND_MAX_CALL_SECONDS", "45")
    packet = _valid_packet(packet_id="pkt-cap-env")
    packet["business"]["phone"] = "+14045558888"
    body = _json.dumps(packet).encode()
    await client.post("/api/webhooks/ranktrust/handoff", content=body,
                      headers={"X-RankTrust-Signature": _sign(body),
                               "Content-Type": "application/json"})

    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-cap-env"}, {"$set": {"target_at": past}}
    )
    await ranktrust_webhook.scheduler_tick_once()

    created = app.state.fake_twilio.calls.created
    # The env-override run is the SECOND call fired in this test file's fixture.
    # Assert the latest call has time_limit=45.
    assert created[-1].get("time_limit") == 45


@pytest.mark.asyncio
async def test_13c_ranktrust_dial_falls_back_on_bad_env(app, client, db, monkeypatch):
    monkeypatch.setenv("OUTBOUND_MAX_CALL_SECONDS", "not_an_int")
    packet = _valid_packet(packet_id="pkt-cap-badenv")
    packet["business"]["phone"] = "+14045559999"
    body = _json.dumps(packet).encode()
    await client.post("/api/webhooks/ranktrust/handoff", content=body,
                      headers={"X-RankTrust-Signature": _sign(body),
                               "Content-Type": "application/json"})

    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.ranktrust_scheduled_calls.update_one(
        {"packet_id": "pkt-cap-badenv"}, {"$set": {"target_at": past}}
    )
    await ranktrust_webhook.scheduler_tick_once()

    created = app.state.fake_twilio.calls.created
    assert created[-1].get("time_limit") == 120, "malformed env must fall back to 120"
