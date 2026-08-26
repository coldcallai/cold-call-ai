"""Campaign Layer V1 tests.

Hard architectural rules enforced here:
  1. RankTrust campaign has exactly 4 variants matching V1 spec.
  2. Variant selection is deterministic by lead_id.
  3. Eligibility rules with _min/_max bounds work correctly.
  4. NO Playbook (including MerchantBrain) imports anything from playbooks.campaigns
     (the campaign-invisibility-to-playbook rule).
  5. CallReport carries campaign attribution end-to-end.
"""
from __future__ import annotations
import os
import re

from universal.contracts.campaign import Campaign, EligibilityCriteria
from universal.engines.campaign_router import CampaignRouter, default_router
from playbooks.campaigns.ranktrust_local_growth import RANKTRUST_LOCAL_GROWTH
from playbooks.campaigns.merchant_services_default import MERCHANT_SERVICES_DEFAULT


def test_ranktrust_v1_has_four_variants():
    assert RANKTRUST_LOCAL_GROWTH.variant_count() == 4
    # Spot-check the founder's exact phrasings
    assert "happy with the number of calls and leads" in RANKTRUST_LOCAL_GROWTH.opening_variants[0]
    assert "priority this year" in RANKTRUST_LOCAL_GROWTH.opening_variants[1]
    assert "Google Maps compared to competitors" in RANKTRUST_LOCAL_GROWTH.opening_variants[2]
    assert "showing up in Google Maps but not consistently near the top" in RANKTRUST_LOCAL_GROWTH.opening_variants[3]


def test_ranktrust_eligibility_gbp_4_to_20():
    r = default_router()
    assert r.is_eligible("ranktrust_local_growth", {"gbp_rank": 8})
    assert r.is_eligible("ranktrust_local_growth", {"gbp_rank": 4})
    assert r.is_eligible("ranktrust_local_growth", {"gbp_rank": 20})
    assert not r.is_eligible("ranktrust_local_growth", {"gbp_rank": 3})   # too high (rank 1-3)
    assert not r.is_eligible("ranktrust_local_growth", {"gbp_rank": 21})  # too low (off page 1)
    assert not r.is_eligible("ranktrust_local_growth", {})  # missing attr


def test_variant_selection_is_deterministic():
    r = default_router()
    a1 = r.pick_variant("ranktrust_local_growth", "lead-XYZ-123")
    a2 = r.pick_variant("ranktrust_local_growth", "lead-XYZ-123")
    assert a1 == a2  # same lead -> same variant on every call


def test_variant_selection_distributes_across_variants():
    r = default_router()
    counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for i in range(1000):
        _, idx = r.pick_variant("ranktrust_local_growth", f"lead-{i:06d}")
        counts[idx] += 1
    # rough uniform: each bucket between 15% and 35% of 1000
    for c in counts.values():
        assert 150 < c < 350, f"variant distribution skew: {counts}"


def test_baseline_campaign_present():
    r = default_router()
    assert r.get("merchant_services_default") is not None
    assert MERCHANT_SERVICES_DEFAULT.variant_count() >= 1


def test_no_playbook_imports_a_campaign():
    """The binding architectural rule: MerchantBrain must not know which
    campaign produced the lead. We enforce this with a static grep."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "playbooks"))
    violations = []
    for dirpath, _, files in os.walk(root):
        # skip the campaigns dir itself
        if "campaigns" in dirpath.replace(root, "").split(os.sep):
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(dirpath, f)
            with open(path) as fh:
                for i, line in enumerate(fh, 1):
                    if re.match(r"^\s*(from|import)\s+.*playbooks\.campaigns", line):
                        violations.append(f"{path}:{i}: {line.strip()}")
    assert not violations, "Playbook imported a Campaign:\n  " + "\n  ".join(violations)


def test_call_report_carries_campaign_attribution():
    from universal.reporting.reporter import build_report
    from universal.state.conversation_state import ConversationState

    state = ConversationState(call_sid="CA_camp", stage="CONFIRMED", intent_score=80,
                              decision_maker_known=True)
    turns = [
        {"engine": "campaign_opener", "trigger_id": None, "agent_said": "Are you happy with...", "caller_said": ""},
        {"engine": "gatekeeper", "trigger_id": "GK_WHATS_THIS_REGARDING", "caller_said": "what's this about", "intent_delta": 15},
    ]
    r = build_report(
        state, turns,
        campaign_id="ranktrust_local_growth",
        campaign_variant_index=2,
        campaign_variant_text="Have you looked at where you're appearing in Google Maps compared to competitors?",
        lead_source="RankTrust Auto Discovery",
    )
    assert r.campaign_id == "ranktrust_local_growth"
    assert r.campaign_variant_index == 2
    assert r.lead_source == "RankTrust Auto Discovery"
    assert r.engaged_past_opener is True  # turn 2 has caller_said


def test_campaign_analytics_ab_compare():
    from universal.reporting.analytics import by_campaign, variant_performance, campaign_kpis
    reports = [
        # RankTrust variant 0 — 2 calls, both engage, 1 transfer
        {"campaign_id": "ranktrust_local_growth", "campaign_variant_index": 0, "engaged_past_opener": True, "decision_maker_reached": True, "outcome": "LIVE_TRANSFER", "duration_seconds": 240},
        {"campaign_id": "ranktrust_local_growth", "campaign_variant_index": 0, "engaged_past_opener": True, "decision_maker_reached": True, "outcome": "APPOINTMENT", "duration_seconds": 180},
        # RankTrust variant 2 — 1 call, doesn't engage
        {"campaign_id": "ranktrust_local_growth", "campaign_variant_index": 2, "engaged_past_opener": False, "decision_maker_reached": False, "outcome": "NURTURE", "duration_seconds": 30},
        # Control — 1 call
        {"campaign_id": "merchant_services_default", "campaign_variant_index": 0, "engaged_past_opener": True, "decision_maker_reached": False, "outcome": "FOLLOW_UP", "duration_seconds": 90},
    ]
    by_c = by_campaign(reports)
    assert set(by_c.keys()) == {"ranktrust_local_growth", "merchant_services_default"}
    assert by_c["ranktrust_local_growth"]["calls"] == 3
    assert by_c["merchant_services_default"]["calls"] == 1
    # 2 of 3 RankTrust calls engaged
    assert abs(by_c["ranktrust_local_growth"]["conversation_rate"] - 2/3) < 1e-6
    # Variant 0 is clearly winning vs variant 2
    perf = variant_performance(reports, "ranktrust_local_growth")
    assert perf[0]["conversation_rate"] == 1.0
    assert perf[2]["conversation_rate"] == 0.0
    assert perf[0]["transfer_rate"] == 0.5


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
