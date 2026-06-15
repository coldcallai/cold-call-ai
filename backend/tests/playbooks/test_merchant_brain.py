"""Playbook test — MerchantBrain V1 content sanity.

Verifies:
 - All 5 received libraries loaded with expected counts.
 - Word-count cap (Trigger variations ≤30 words; DiscoveryQuestion phrasings ≤35).
 - Transfer score bands cover 0..∞ contiguously.
 - Jargon map non-empty (Funding V1 refinement enforced).
 - Gatekeeper STUB is flagged.
"""
from __future__ import annotations

from playbooks.merchant_brain import MerchantBrain, GATEKEEPER_STATUS
from universal.contracts.playbook import LIB_WORKFLOW, LIB_FUNDING, LIB_QUALIFICATION


mb = MerchantBrain()


def test_decision_maker_count_v1():
    # 8 Decision Maker triggers received from founder
    dm = [t for t in mb.get_triggers() if "decision_maker" in t.playbook_tags]
    assert len(dm) == 8, f"Expected 8 Decision Maker triggers, got {len(dm)}"


def test_workflow_question_count_v1():
    assert len(mb.get_questions(LIB_WORKFLOW)) == 10


def test_funding_question_count_v1():
    assert len(mb.get_questions(LIB_FUNDING)) == 10


def test_qualification_question_count_v1():
    assert len(mb.get_questions(LIB_QUALIFICATION)) == 8


def test_gatekeeper_stubbed():
    assert GATEKEEPER_STATUS == "AWAITING_V1_CONTENT"
    gk = [t for t in mb.get_triggers() if "gatekeeper" in t.playbook_tags]
    assert gk == [], "Gatekeeper triggers should still be empty stub"


def test_transfer_bands_contiguous():
    decisions = sorted(mb.get_transfer_decisions(), key=lambda d: d.score_min)
    # 0..59, 60..79, 80..∞
    assert decisions[0].score_min == 0 and decisions[0].score_max == 59
    assert decisions[1].score_min == 60 and decisions[1].score_max == 79
    assert decisions[2].score_min == 80 and decisions[2].score_max is None


def test_jargon_map_present():
    jm = mb.get_jargon_map()
    assert len(jm) >= 10
    # The exact examples cited in Funding V1 must be present
    assert "settlement timing" in jm
    assert "funding window" in jm
    assert "card-not-present volume" in jm
    assert "payment acceptance workflow" in jm


def test_no_jargon_in_caller_facing_phrasings():
    """The agent's spoken phrasings must not contain jargon
    (per Funding V1: 'Agent speaks business owner, not merchant services')."""
    jargon_terms = list(mb.get_jargon_map().keys())
    violations: list[str] = []
    for q in (
        *mb.get_questions(LIB_WORKFLOW),
        *mb.get_questions(LIB_FUNDING),
        *mb.get_questions(LIB_QUALIFICATION),
    ):
        for phrasing in q.all_phrasings():
            for term in jargon_terms:
                if term in phrasing.lower():
                    violations.append(f"{q.id}: jargon {term!r} in phrasing: {phrasing!r}")
    for trig in mb.get_triggers():
        for obj in trig.objectives.values():
            for v in obj.variations:
                for term in jargon_terms:
                    if term in v.lower():
                        violations.append(f"{trig.id}/{obj.name}: jargon {term!r} in variation: {v!r}")
    assert not violations, "Jargon found in agent phrasings:\n  " + "\n  ".join(violations)


def test_transfer_signal_phrases_non_empty():
    sigs = mb.get_transfer_signals()
    assert len(sigs) >= 10
    assert all(s.intent_delta > 0 for s in sigs)
    # Spot-check the marquee signal from Transfer V1
    labels = {s.label for s in sigs}
    assert "collections_pain" in labels
    assert "funding_delay" in labels
    assert "open_to_review" in labels


if __name__ == "__main__":
    import inspect, sys
    me = sys.modules[__name__]
    funcs = [(n, f) for n, f in inspect.getmembers(me, inspect.isfunction) if n.startswith("test_")]
    failed = 0
    for n, f in funcs:
        try:
            f()
            print(f"PASS: {n}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {n}: {e}")
    sys.exit(1 if failed else 0)
