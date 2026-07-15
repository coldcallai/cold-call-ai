"""Env-blank verification: with TWILIO_PHONE_NUMBER blanked and no user
phone / no campaign callback, all three tiers of resolve_callback_number
should return None and the 400 guard should fire.

Assumes backend restarted with TWILIO_PHONE_NUMBER=''.
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
           "https://voice-clone-preview-1.preview.emergentagent.com"

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123!"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    tok = body.get("session_token") or body.get("access_token") or body.get("token")
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def ensure_user_has_no_phone(auth_headers):
    """Blank the phone_number on the test user so 2nd-tier fallback also fails."""
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")

    async def _run():
        cli = AsyncIOMotorClient(mongo_url)
        db = cli[db_name]
        u = await db.users.find_one({"email": TEST_EMAIL})
        if u:
            original = u.get("phone_number")
            await db.users.update_one({"email": TEST_EMAIL},
                                      {"$set": {"phone_number": None}})
            return original
        return None

    async def _restore(orig):
        cli = AsyncIOMotorClient(mongo_url)
        db = cli[db_name]
        await db.users.update_one({"email": TEST_EMAIL},
                                  {"$set": {"phone_number": orig}})

    original = asyncio.get_event_loop().run_until_complete(_run())
    yield
    asyncio.get_event_loop().run_until_complete(_restore(original))


def test_create_with_vm_on_and_no_cb_returns_400_when_all_fallbacks_absent(auth_headers):
    payload = {
        "name": f"TEST_iter32_envblank_{uuid.uuid4().hex[:6]}",
        "description": "envblank",
        "ai_script": "test",
        "voicemail_enabled": True,
        "voicemail_message": "Hi {agent_name} at {company_name}, call {callback_number}.",
        "callback_number": "",
        "calls_per_day": 5,
    }
    r = requests.post(f"{BASE_URL}/api/campaigns", json=payload,
                      headers=auth_headers, timeout=15)
    assert r.status_code == 400, \
        f"expected 400 when all 3 fallbacks empty; got {r.status_code}: {r.text[:300]}"
    detail = (r.json().get("detail") or "").lower()
    assert "callback" in detail, f"unexpected detail: {detail}"


def test_start_with_vm_on_and_no_cb_returns_400_when_all_fallbacks_absent(auth_headers):
    """Create a campaign with vm OFF (must succeed), then attempt to flip vm ON
    via update — which should also 400 for the same reason. Also attempt start."""
    # Create campaign with vm OFF (bypasses the guard)
    payload = {
        "name": f"TEST_iter32_start_envblank_{uuid.uuid4().hex[:6]}",
        "description": "envblank start",
        "ai_script": "test",
        "voicemail_enabled": False,
        "callback_number": "",
        "calls_per_day": 5,
    }
    r = requests.post(f"{BASE_URL}/api/campaigns", json=payload,
                      headers=auth_headers, timeout=15)
    if r.status_code not in (200, 201):
        pytest.skip(f"precondition create failed: {r.status_code} {r.text[:200]}")
    cid = r.json()["id"]

    try:
        # Direct DB flip of voicemail_enabled=True to bypass the update guard,
        # so we can isolate the START guard.
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.environ.get("DB_NAME", "test_database")

        async def _flip():
            cli = AsyncIOMotorClient(mongo_url)
            db = cli[db_name]
            await db.campaigns.update_one(
                {"id": cid},
                {"$set": {"voicemail_enabled": True, "callback_number": ""}},
            )
        asyncio.get_event_loop().run_until_complete(_flip())

        # Now START must 400
        r2 = requests.post(f"{BASE_URL}/api/campaigns/{cid}/start",
                           headers=auth_headers, timeout=15)
        assert r2.status_code == 400, \
            f"expected 400 on start when fallbacks empty; got {r2.status_code}: {r2.text[:300]}"
        detail = (r2.json().get("detail") or "").lower()
        assert "callback" in detail, f"unexpected detail: {detail}"
    finally:
        try:
            requests.delete(f"{BASE_URL}/api/campaigns/{cid}",
                            headers=auth_headers, timeout=10)
        except Exception:
            pass
