"""Phase 2 Lite tests — opener wiring + objection intercept + report capture."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone

from universal.engines.campaign_session import CampaignSession


def test_session_picks_ranktrust_when_eligible():
    session = CampaignSession.start("lead-abc-001", {"gbp_rank": 8})
    assert session.campaign.id == "ranktrust_local_growth"
    assert 0 <= session.variant_index <= 3
    assert session.opener_text in session.campaign.opening_variants


def test_session_falls_back_to_merchant_default_when_gbp_missing():
    session = CampaignSession.start("lead-no-gbp-001", {})
    assert session.campaign.id == "merchant_services_default"


def test_session_falls_back_when_gbp_out_of_range():
    # rank 2 → too high (RankTrust wants 4-20, leaves top spots alone)
    session = CampaignSession.start("lead-top-rank", {"gbp_rank": 2})
    assert session.campaign.id == "merchant_services_default"
    # rank 50 → too low
    session = CampaignSession.start("lead-low-rank", {"gbp_rank": 50})
    assert session.campaign.id == "merchant_services_default"


def test_objection_intercept_canned_response_for_ranking_question():
    session = CampaignSession.start("lead-eligible", {"gbp_rank": 8})
    resp = session.check_objection("how did you find my ranking?")
    assert resp is not None
    assert "public Google Maps data" in resp
    assert "no list, no purchase" not in resp  # that's the OTHER response


def test_objection_intercept_misses_unknown_phrase():
    session = CampaignSession.start("lead-eligible", {"gbp_rank": 8})
    assert session.check_objection("yeah that sounds good") is None


def test_session_context_roundtrip():
    s1 = CampaignSession.start("lead-001", {"gbp_rank": 12})
    ctx = s1.session_context()
    assert ctx["campaign_id"] == "ranktrust_local_growth"
    assert "variant" in str(ctx).lower()
    s2 = CampaignSession.rehydrate(ctx)
    assert s2.campaign.id == s1.campaign.id
    assert s2.variant_index == s1.variant_index
    assert s2.opener_text == s1.opener_text


def test_finalize_builds_report_with_campaign_attribution():
    s = CampaignSession.start("lead-finalize", {"gbp_rank": 6})
    legacy_doc = {
        "decision_maker_name": "Tom Smith",
        "current_processor": "Square",
        "intent_score": 78,
        "appointment_booked": True,
        "turns": [
            {"role": "user", "text": "yeah we use square actually"},
            {"role": "assistant", "text": "how long have you been with them?"},
            {"role": "user", "text": "going on 3 years"},
        ],
    }
    report = asyncio.run(s.finalize(call_sid="CA_finalize_test", legacy_call_doc=legacy_doc))
    assert report.campaign_id == "ranktrust_local_growth"
    assert report.campaign_variant_index == s.variant_index
    assert report.lead_source == "RankTrust Auto Discovery"
    assert report.engaged_past_opener is True
    assert report.decision_maker_reached is True
    assert report.decision_maker_name == "Tom Smith"
    assert report.outcome == "APPOINTMENT"
    assert report.duration_seconds is not None and report.duration_seconds >= 0


def test_finalize_no_engagement_reports_nurture_path():
    s = CampaignSession.start("lead-noengage", {"gbp_rank": 10})
    legacy_doc = {
        "conversation_stage": "exit",
        "intent_score": 0,
        "turns": [],
    }
    report = asyncio.run(s.finalize(call_sid="CA_no_engage", legacy_call_doc=legacy_doc))
    assert report.campaign_id == "ranktrust_local_growth"
    assert report.engaged_past_opener is False
    assert report.decision_maker_reached is False


if __name__ == "__main__":
    import inspect, sys
    me = sys.modules[__name__]
    failed = 0
    for n, f in inspect.getmembers(me, inspect.isfunction):
        if not n.startswith("test_"):
            continue
        try:
            f()
            print(f"PASS: {n}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {n}: {e}")
    sys.exit(1 if failed else 0)
