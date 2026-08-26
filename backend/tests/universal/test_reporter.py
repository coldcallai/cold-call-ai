"""Reporter + Analytics tests — synthetic call data drives the Top-5 report."""
from __future__ import annotations
from universal.reporting.reporter import CallReport, build_report
from universal.reporting.analytics import summary, top_gatekeeper_triggers, funding_confusion
from universal.state.conversation_state import ConversationState, STAGE_CONFIRMED


def _mk_turn(engine, trigger_id, intent_delta=10, variation_index=0, caller_said="", agent_said="", jargon=None):
    return {
        "engine": engine,
        "trigger_id": trigger_id,
        "objective": "TEST",
        "variation_index": variation_index,
        "caller_said": caller_said,
        "agent_said": agent_said,
        "intent_delta": intent_delta,
        "jargon_flagged": jargon or [],
    }


def test_build_report_minimum_path():
    state = ConversationState(call_sid="CA_test", stage=STAGE_CONFIRMED, intent_score=85,
                              decision_maker_known=True, decision_maker_name="Tom")
    turns = [
        _mk_turn("gatekeeper", "GK_ALREADY_HAVE_PROCESSOR", intent_delta=15, variation_index=1,
                 caller_said="we already have a processor",
                 agent_said="That makes sense. Who typically oversees that relationship?"),
        _mk_turn("objection", "DM_USE_CLOVER", intent_delta=10, caller_said="we use clover"),
    ]
    r = build_report(state, turns)
    assert r.call_sid == "CA_test"
    assert r.gatekeeper_trigger == "GK_ALREADY_HAVE_PROCESSOR"
    assert r.gatekeeper_variant_index == 1
    assert r.decision_maker_reached is True
    assert r.decision_maker_name == "Tom"
    assert r.intent_score == 85
    assert r.outcome == "APPOINTMENT"


def test_top_gatekeeper_triggers():
    reports = [
        {"gatekeeper_trigger": "GK_WHATS_THIS_REGARDING", "turns": []},
        {"gatekeeper_trigger": "GK_WHATS_THIS_REGARDING", "turns": []},
        {"gatekeeper_trigger": "GK_ALREADY_HAVE_PROCESSOR", "turns": []},
    ]
    top = top_gatekeeper_triggers(reports, n=2)
    assert top[0] == ("GK_WHATS_THIS_REGARDING", 2)
    assert top[1] == ("GK_ALREADY_HAVE_PROCESSOR", 1)


def test_funding_confusion_detects_what_do_you_mean():
    reports = [{
        "turns": [
            _mk_turn("discovery", "FN_Q3", caller_said="", agent_said="Do you receive weekend funding today?"),
            _mk_turn("discovery", None, caller_said="what do you mean?"),
        ]
    }]
    confusion = funding_confusion(reports)
    assert confusion[0][0] == "FN_Q3"
    assert confusion[0][1] == 1


def test_summary_full():
    reports = [
        {
            "outcome": "APPOINTMENT",
            "decision_maker_reached": True,
            "gatekeeper_trigger": "GK_TOO_BUSY",
            "turns": [
                _mk_turn("gatekeeper", "GK_TOO_BUSY", intent_delta=10),
                _mk_turn("discovery", "WF_Q5", intent_delta=20),
            ],
        },
        {
            "outcome": "NURTURE",
            "decision_maker_reached": False,
            "gatekeeper_trigger": "GK_NOT_INTERESTED",
            "turns": [_mk_turn("gatekeeper", "GK_NOT_INTERESTED", intent_delta=0)],
        },
    ]
    s = summary(reports)
    assert s["calls_total"] == 2
    assert abs(s["decision_maker_reached_rate"] - 0.5) < 1e-6
    assert s["outcome_breakdown"]["APPOINTMENT"] == 1
    assert s["outcome_breakdown"]["NURTURE"] == 1
    assert ("WF_Q5", 20.0) in s["highest_workflow_engagement"]


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
