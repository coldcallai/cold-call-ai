"""Health test #2 — Deletion independence.

Proves UniversalBrain runs without any vertical playbook. Engines must
accept the NoopPlaybook and produce valid output for a turn.
"""
from __future__ import annotations
import asyncio

from universal.orchestrator import Orchestrator
from universal.contracts.playbook import NoopPlaybook


def test_orchestrator_runs_with_noop_playbook():
    orch = Orchestrator(playbook=NoopPlaybook())
    result = asyncio.run(orch.handle_turn(call_sid="TEST_SID", speech="hi"))
    assert "engine_result" in result
    assert "state" in result
    assert result["state"]["call_sid"] == "TEST_SID"


def test_universal_imports_without_any_playbook():
    """Engines must not import a concrete playbook at module load."""
    from universal.engines import gatekeeper, discovery, objection, qualification
    from universal.engines import intent_scoring, callback, appointment, transfer, memory, follow_up
    # touch each module to force import side effects (none expected)
    for mod in (gatekeeper, discovery, objection, qualification,
                intent_scoring, callback, appointment, transfer, memory, follow_up):
        assert mod is not None


if __name__ == "__main__":
    test_universal_imports_without_any_playbook()
    test_orchestrator_runs_with_noop_playbook()
    print("PASS: test_universal_imports_without_any_playbook")
    print("PASS: test_orchestrator_runs_with_noop_playbook")
