"""Health test #3 — Schema lock.

The Trigger / Objective / DiscoveryQuestion schemas are LOCKED on June 15, 2026.
Any change to required fields must be deliberate; this test fails when fields
drift.
"""
from __future__ import annotations
from dataclasses import fields

from universal.contracts.trigger import Trigger, Objective
from universal.contracts.discovery import DiscoveryQuestion
from universal.contracts.transfer import TransferDecision, TransferSignal


LOCKED_TRIGGER_FIELDS = {"id", "matches", "possible_meanings", "playbook_tags", "objectives"}
LOCKED_OBJECTIVE_FIELDS = {"name", "intent_delta", "next_state", "variations"}
LOCKED_QUESTION_FIELDS = {
    "id", "objective", "primary", "variations", "softer_version",
    "capture_slots", "captures_enum", "intent_delta", "next_state", "playbook_tags",
}
LOCKED_TRANSFER_DECISION_FIELDS = {"kind", "score_min", "score_max", "requires", "phrasings", "playbook_tags"}
LOCKED_TRANSFER_SIGNAL_FIELDS = {"phrase", "intent_delta", "label"}


def _names(cls) -> set[str]:
    return {f.name for f in fields(cls)}


def test_trigger_schema_locked():
    assert _names(Trigger) == LOCKED_TRIGGER_FIELDS, f"Trigger drift: {_names(Trigger) ^ LOCKED_TRIGGER_FIELDS}"


def test_objective_schema_locked():
    assert _names(Objective) == LOCKED_OBJECTIVE_FIELDS, f"Objective drift: {_names(Objective) ^ LOCKED_OBJECTIVE_FIELDS}"


def test_question_schema_locked():
    assert _names(DiscoveryQuestion) == LOCKED_QUESTION_FIELDS, f"DiscoveryQuestion drift: {_names(DiscoveryQuestion) ^ LOCKED_QUESTION_FIELDS}"


def test_transfer_decision_schema_locked():
    assert _names(TransferDecision) == LOCKED_TRANSFER_DECISION_FIELDS


def test_transfer_signal_schema_locked():
    assert _names(TransferSignal) == LOCKED_TRANSFER_SIGNAL_FIELDS


if __name__ == "__main__":
    test_trigger_schema_locked()
    test_objective_schema_locked()
    test_question_schema_locked()
    test_transfer_decision_schema_locked()
    test_transfer_signal_schema_locked()
    print("PASS: all schemas locked")
