"""
Launch-blocker regression tests for cloned-voice voicemail drops.

Covers:
  - Section 6: GET /api/vm-audio/{token} returns 404 on missing token
  - Section 7: POST /api/campaigns/{id}/start returns 400 when voicemail_enabled
    is true and no callback_number can be resolved
  - Section 1/2 API layer: create/update campaign with voicemail must supply
    callback_number when voicemail_enabled=true
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
           "https://voice-clone-preview-1.preview.emergentagent.com"

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "Test123!"


# --- auth fixture -----------------------------------------------------------
@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token") or r.json().get("token") or r.json().get("session_token")
    assert tok, f"no token in login response: {r.text[:200]}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# --- Section 6 --------------------------------------------------------------
def test_section6_vm_audio_missing_token_returns_404():
    """A bogus token must yield 404 so TwiML Play can fall through to Polly."""
    r = requests.get(
        f"{BASE_URL}/api/vm-audio/deadbeef00000000000000000000dead",
        timeout=15,
        allow_redirects=False,
    )
    assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:200]}"


# --- Section 1 API: create-campaign callback validation ---------------------
def test_section1_create_campaign_blocks_missing_callback(auth_headers):
    """
    POST /api/campaigns with voicemail_enabled=true and no callback_number
    must be rejected with 400 and the guarded error message.
    """
    payload = {
        "name": f"TEST_launch_blocker_no_cb_{uuid.uuid4().hex[:6]}",
        "description": "test",
        "voicemail_enabled": True,
        "voicemail_message": "Hi, this is {agent_name} with {company_name}. "
                             "Reach me at {callback_number}.",
        "callback_number": "",
        "calls_per_day": 10,
        "calling_hours_start": "09:00",
        "calling_hours_end": "17:00",
        "calling_days": ["mon"],
    }
    r = requests.post(
        f"{BASE_URL}/api/campaigns",
        json=payload,
        headers=auth_headers,
        timeout=15,
    )
    # Accept either 400 (guarded) or 422 (pydantic) — must NOT be 201/200
    assert r.status_code in (400, 422), \
        f"expected 400/422, got {r.status_code}: {r.text[:300]}"
    if r.status_code == 400:
        detail = (r.json().get("detail") or "").lower()
        assert "callback" in detail, f"unexpected detail: {detail}"


# --- Section 2 API: update-campaign preserves callback rule -----------------
def test_section2_update_campaign_persists_callback_and_message(auth_headers):
    """
    Create a valid campaign, then PUT with an updated voicemail_message + callback.
    Verify the row round-trips.
    """
    # Create
    create_payload = {
        "name": f"TEST_launch_blocker_edit_{uuid.uuid4().hex[:6]}",
        "description": "edit test", "ai_script": "test script",
        "voicemail_enabled": True,
        "voicemail_message": "Hi, this is {agent_name} with {company_name}. "
                             "Callback {callback_number}.",
        "callback_number": "+14045557777",
        "calls_per_day": 5,
        "calling_hours_start": "09:00",
        "calling_hours_end": "17:00",
        "calling_days": ["mon"],
    }
    r = requests.post(
        f"{BASE_URL}/api/campaigns",
        json=create_payload,
        headers=auth_headers,
        timeout=20,
    )
    assert r.status_code in (200, 201), f"create failed: {r.status_code} {r.text[:300]}"
    camp = r.json()
    cid = camp.get("id") or camp.get("_id") or camp.get("campaign_id")
    assert cid, f"no id in create response: {camp}"

    try:
        # Update
        new_msg = "UPDATED: Hi, this is {agent_name} with {company_name}. " \
                  "Callback {callback_number}."
        upd = {
            "voicemail_enabled": True,
            "voicemail_message": new_msg,
            "callback_number": "+14045558888",
        }
        r2 = requests.put(
            f"{BASE_URL}/api/campaigns/{cid}",
            json=upd,
            headers=auth_headers,
            timeout=20,
        )
        assert r2.status_code == 200, f"update failed: {r2.status_code} {r2.text[:300]}"

        # Verify persisted
        r3 = requests.get(
            f"{BASE_URL}/api/campaigns/{cid}",
            headers=auth_headers,
            timeout=15,
        )
        assert r3.status_code == 200, f"get failed: {r3.status_code} {r3.text[:300]}"
        row = r3.json()
        assert row.get("voicemail_message") == new_msg, \
            f"voicemail_message not persisted: {row.get('voicemail_message')!r}"
        assert row.get("callback_number") == "+14045558888", \
            f"callback_number not persisted: {row.get('callback_number')!r}"
    finally:
        # Cleanup
        try:
            requests.delete(
                f"{BASE_URL}/api/campaigns/{cid}",
                headers=auth_headers,
                timeout=10,
            )
        except Exception:
            pass


# --- Section 2 API: update rejects clearing callback while vm on ------------
def test_section2_update_rejects_clearing_callback_with_vm_on(auth_headers):
    """
    If a campaign has voicemail_enabled=true, attempting to PUT
    callback_number='' must be rejected (matches the FE disabled-save rule).
    """
    create_payload = {
        "name": f"TEST_launch_blocker_clearcb_{uuid.uuid4().hex[:6]}",
        "description": "clear cb test", "ai_script": "test script",
        "voicemail_enabled": True,
        "voicemail_message": "Hi {agent_name} {company_name} {callback_number}",
        "callback_number": "+14045557777",
        "calls_per_day": 5,
        "calling_hours_start": "09:00",
        "calling_hours_end": "17:00",
        "calling_days": ["mon"],
    }
    r = requests.post(
        f"{BASE_URL}/api/campaigns", json=create_payload,
        headers=auth_headers, timeout=20,
    )
    if r.status_code not in (200, 201):
        pytest.skip(f"create precondition failed: {r.status_code}")
    cid = r.json().get("id") or r.json().get("_id")
    try:
        r2 = requests.put(
            f"{BASE_URL}/api/campaigns/{cid}",
            json={"voicemail_enabled": True, "callback_number": ""},
            headers=auth_headers, timeout=15,
        )
        # We expect the backend to reject this (400) — if it accepts (200),
        # that's a launch-blocker gap in the update route validation.
        assert r2.status_code in (400, 422), \
            f"backend allowed empty callback with vm on: {r2.status_code} {r2.text[:300]}"
    finally:
        try:
            requests.delete(f"{BASE_URL}/api/campaigns/{cid}",
                            headers=auth_headers, timeout=10)
        except Exception:
            pass


# --- Section 7: start campaign blocks when no callback ----------------------
def test_section7_start_campaign_blocks_when_no_callback(auth_headers):
    """
    Directly probe start-safety by attempting to PUT a campaign so that
    voicemail_enabled=true and callback_number='', then start.

    Note: creation with vm on + empty cb is expected to be rejected (Section 1).
    So we instead create with vm off, flip vm on via PUT while cb is empty,
    and confirm start returns 400 with the expected detail.
    """
    # Create with voicemail OFF (allowed)
    create_payload = {
        "name": f"TEST_launch_blocker_start_{uuid.uuid4().hex[:6]}",
        "description": "start-safety test", "ai_script": "test script",
        "voicemail_enabled": False,
        "voicemail_message": "Hi {agent_name} {company_name} {callback_number}",
        "callback_number": "",
        "calls_per_day": 5,
        "calling_hours_start": "09:00",
        "calling_hours_end": "17:00",
        "calling_days": ["mon"],
    }
    r = requests.post(
        f"{BASE_URL}/api/campaigns", json=create_payload,
        headers=auth_headers, timeout=20,
    )
    if r.status_code not in (200, 201):
        pytest.skip(f"create precondition failed: {r.status_code} {r.text[:200]}")
    cid = r.json().get("id") or r.json().get("_id")

    try:
        # Try to flip vm ON with empty cb
        r2 = requests.put(
            f"{BASE_URL}/api/campaigns/{cid}",
            json={"voicemail_enabled": True, "callback_number": ""},
            headers=auth_headers, timeout=15,
        )
        # If PUT correctly rejects (400/422), the guard works at update layer
        if r2.status_code in (400, 422):
            # Great — cannot even reach the vm-on/no-cb state. Test the start
            # path with the OFF campaign to make sure start doesn't 400.
            r3 = requests.post(
                f"{BASE_URL}/api/campaigns/{cid}/start",
                headers=auth_headers, timeout=20,
            )
            # Start may 200 or fail for other reasons (leads etc) but must
            # NOT return the callback-required error.
            if r3.status_code == 400:
                assert "callback" not in (r3.json().get("detail") or "").lower(), \
                    f"vm-off campaign still hit callback guard: {r3.text[:200]}"
            return
        # If PUT allowed it, now start MUST reject
        r3 = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/start",
            headers=auth_headers, timeout=20,
        )
        assert r3.status_code == 400, \
            f"expected 400, got {r3.status_code}: {r3.text[:300]}"
        detail = (r3.json().get("detail") or "").lower()
        assert "callback" in detail, f"unexpected detail: {detail}"
    finally:
        try:
            requests.delete(f"{BASE_URL}/api/campaigns/{cid}",
                            headers=auth_headers, timeout=10)
        except Exception:
            pass


# --- Section 3: verify normalize_phone_for_speech via server import ---------
def test_section3_normalize_phone_for_speech():
    """Direct in-process check of the phone-normalization helper."""
    import sys
    sys.path.insert(0, "/app/backend")
    from server import normalize_phone_for_speech
    assert normalize_phone_for_speech("+14045557777") == "4 0 4, 5 5 5, 7 7 7 7"
