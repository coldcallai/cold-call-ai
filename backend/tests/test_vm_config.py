"""Voicemail configuration — server-side helpers + validation.

Verifies:
  1. normalize_phone_for_speech renders E.164 / 10-digit / arbitrary phones for TTS.
  2. resolve_callback_number honours the campaign → user → env fallback order.
  3. resolve_agent_name picks the linked agent's name, falls back to user, then default.
  4. hydrate_campaign_for_vm attaches _resolved_ fields.
  5. generate_voicemail_twiml Polly path interpolates all 4 variables.
  6. generate_voicemail_twiml never speaks an unresolved literal placeholder.

Never touches RankTrust webhook, SMS, funnel, retry cadence, or the ElevenLabs
Human-Greeting Gate.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


@pytest_asyncio.fixture
async def db():
    client = AsyncMongoMockClient()
    return client["intentbrain_test_vm_config"]


# --------- 1) Phone normalization for speech ---------
def test_1_normalize_phone_for_speech():
    from server import normalize_phone_for_speech
    # +1 country code stripped, grouped for cadence
    assert normalize_phone_for_speech("+14045557777") == "4 0 4, 5 5 5, 7 7 7 7"
    # 10-digit US without +1 → same
    assert normalize_phone_for_speech("4045557777") == "4 0 4, 5 5 5, 7 7 7 7"
    # Formatting characters ignored
    assert normalize_phone_for_speech("(404) 555-7777") == "4 0 4, 5 5 5, 7 7 7 7"
    # Empty / None safe
    assert normalize_phone_for_speech(None) == ""
    assert normalize_phone_for_speech("") == ""


# --------- 2) resolve_callback_number priority chain ---------
@pytest.mark.asyncio
async def test_2a_callback_uses_campaign_field_first(db, monkeypatch):
    import server
    monkeypatch.setattr(server, "twilio_phone_number", "+18885551234")
    await db.users.insert_one({"user_id": "u1", "phone_number": "+15551119999"})
    campaign = {"callback_number": "+14045550000"}
    assert await server.resolve_callback_number(db, campaign, "u1") == "+14045550000"


@pytest.mark.asyncio
async def test_2b_callback_falls_back_to_user_profile(db, monkeypatch):
    import server
    monkeypatch.setattr(server, "twilio_phone_number", "+18885551234")
    await db.users.insert_one({"user_id": "u2", "phone_number": "+15551119999"})
    assert await server.resolve_callback_number(db, {}, "u2") == "+15551119999"


@pytest.mark.asyncio
async def test_2c_callback_falls_back_to_env(db, monkeypatch):
    import server
    monkeypatch.setattr(server, "twilio_phone_number", "+18885551234")
    # No campaign field, no user
    assert await server.resolve_callback_number(db, {}, "unknown-user") == "+18885551234"


@pytest.mark.asyncio
async def test_2d_callback_returns_none_when_nothing_available(db, monkeypatch):
    import server
    monkeypatch.setattr(server, "twilio_phone_number", None)
    assert await server.resolve_callback_number(db, {}, "unknown-user") is None


# --------- 3) resolve_agent_name preference ---------
@pytest.mark.asyncio
async def test_3a_agent_name_uses_linked_agent(db):
    import server
    await db.agents.insert_one({"id": "agent-1", "user_id": "u3", "name": "David"})
    await db.users.insert_one({"user_id": "u3", "name": "Ryan"})
    campaign = {"agent_id": "agent-1"}
    assert await server.resolve_agent_name(db, campaign, "u3") == "David"


@pytest.mark.asyncio
async def test_3b_agent_name_falls_back_to_user_profile(db):
    import server
    await db.users.insert_one({"user_id": "u4", "name": "Ryan"})
    # No agent_id on campaign
    assert await server.resolve_agent_name(db, {}, "u4") == "Ryan"


@pytest.mark.asyncio
async def test_3c_agent_name_default_when_missing_everywhere(db):
    import server
    assert await server.resolve_agent_name(db, {}, "unknown") == "your account rep"


# --------- 4) hydrate_campaign_for_vm attaches _resolved_ fields ---------
@pytest.mark.asyncio
async def test_4_hydrate_attaches_resolved_fields(db):
    import server
    await db.users.insert_one({"user_id": "u5", "name": "Ryan", "phone_number": "+14045557777"})
    await db.agents.insert_one({"id": "agent-5", "user_id": "u5", "name": "David"})
    campaign = {"id": "c5", "user_id": "u5", "agent_id": "agent-5"}
    hydrated = await server.hydrate_campaign_for_vm(db, campaign)
    assert hydrated["_resolved_agent_name"] == "David"
    assert hydrated["_resolved_callback_number_raw"] == "+14045557777"
    assert hydrated["_resolved_callback_number_spoken"] == "4 0 4, 5 5 5, 7 7 7 7"


# --------- 5) TwiML interpolates all 4 variables + guards placeholders ---------
def test_5_twiml_interpolates_four_variables():
    import server
    twiml = server.twilio_service.generate_voicemail_twiml(
        lead={"business_name": "Acme Roofing", "contact_name": "Sam"},
        campaign={
            "id": "c-x",
            "company_name": "RankTrust",
            "voicemail_message": (
                "Hi {contact_name}, this is {agent_name} with {company_name} "
                "for {business_name}. Reach me at {callback_number}."
            ),
            "_resolved_agent_name": "David",
            "_resolved_callback_number_spoken": "4 0 4, 5 5 5, 7 7 7 7",
        },
    )
    # No unresolved placeholders may appear in the final TwiML
    assert "{" not in twiml and "}" not in twiml
    assert "David" in twiml
    assert "RankTrust" in twiml
    assert "Acme Roofing" in twiml
    assert "Sam" in twiml
    assert "4 0 4, 5 5 5, 7 7 7 7" in twiml


def test_6_twiml_never_speaks_unresolved_literal_placeholder():
    import server
    # Simulate a broken/unmigrated template using [bracket] placeholders
    twiml = server.twilio_service.generate_voicemail_twiml(
        lead={"business_name": "Acme"},
        campaign={
            "id": "c-y",
            "voicemail_message": "Hi, this is [Your Name]. Call [Your Number].",
            "_resolved_agent_name": "David",
            "_resolved_callback_number_spoken": "4 0 4",
        },
    )
    # Neither [bracket] literal may appear — the guard strips them
    assert "[Your Name]" not in twiml
    assert "[Your Number]" not in twiml


# --------- 7) VM_DEFAULT_SCRIPT is well-formed and uses all 4 variables ---------
def test_7_default_script_is_well_formed():
    from server import VM_DEFAULT_SCRIPT
    assert "{agent_name}" in VM_DEFAULT_SCRIPT
    assert "{company_name}" in VM_DEFAULT_SCRIPT
    assert "{callback_number}" in VM_DEFAULT_SCRIPT
    # Says the callback number TWICE — better for real recall on a voicemail
    assert VM_DEFAULT_SCRIPT.count("{callback_number}") == 2
