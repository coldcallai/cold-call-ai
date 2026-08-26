"""
UniversalBrain — ConversationState.

The single source of truth that engines read+update per turn. Persisted to
MongoDB collection `call_intelligence` (one doc per call_sid).

Stage lifecycle:
    INTRO -> DISCOVERY -> QUALIFICATION -> BOOKING -> CONFIRMED -> EXIT
    Branches: any -> CALLBACK_SCHEDULED -> EXIT
              any -> TRANSFERRING -> EXIT

Rule: CONFIRMED and EXIT are TERMINAL. Engines must never write a
greeting/intro stage when previous stage in {BOOKING, CONFIRMED, EXIT}.
(This is the fix for BUG #002 conversation state leakage.)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


STAGE_INTRO = "INTRO"
STAGE_DISCOVERY = "DISCOVERY"
STAGE_QUALIFICATION = "QUALIFICATION"
STAGE_BOOKING = "BOOKING"
STAGE_CONFIRMED = "CONFIRMED"
STAGE_CALLBACK_SCHEDULED = "CALLBACK_SCHEDULED"
STAGE_TRANSFERRING = "TRANSFERRING"
STAGE_EXIT = "EXIT"

TERMINAL_STAGES = frozenset({STAGE_CONFIRMED, STAGE_EXIT})

LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    STAGE_INTRO: frozenset({STAGE_DISCOVERY, STAGE_QUALIFICATION, STAGE_CALLBACK_SCHEDULED, STAGE_TRANSFERRING, STAGE_EXIT}),
    STAGE_DISCOVERY: frozenset({STAGE_DISCOVERY, STAGE_QUALIFICATION, STAGE_BOOKING, STAGE_CALLBACK_SCHEDULED, STAGE_TRANSFERRING, STAGE_EXIT}),
    STAGE_QUALIFICATION: frozenset({STAGE_QUALIFICATION, STAGE_BOOKING, STAGE_CALLBACK_SCHEDULED, STAGE_TRANSFERRING, STAGE_EXIT}),
    STAGE_BOOKING: frozenset({STAGE_BOOKING, STAGE_CONFIRMED, STAGE_CALLBACK_SCHEDULED, STAGE_EXIT}),
    STAGE_CALLBACK_SCHEDULED: frozenset({STAGE_EXIT}),
    STAGE_TRANSFERRING: frozenset({STAGE_EXIT}),
    STAGE_CONFIRMED: frozenset({STAGE_EXIT}),
    STAGE_EXIT: frozenset({STAGE_EXIT}),
}


@dataclass
class ConversationState:
    call_sid: str
    stage: str = STAGE_INTRO

    # Gatekeeper Success Score booleans
    decision_maker_known: bool = False
    decision_maker_name: Optional[str] = None
    decision_maker_title: Optional[str] = None
    decision_maker_email: Optional[str] = None
    decision_maker_direct_phone: Optional[str] = None
    gatekeeper_first_name: Optional[str] = None
    best_callback_time: Optional[str] = None
    email_obtained: bool = False
    best_time_obtained: bool = False
    processor_mentioned: bool = False
    gatekeeper_name_obtained: bool = False

    # Discovery / qualification
    pain_known: bool = False
    current_processor: Optional[str] = None
    contract_end_date: Optional[str] = None

    # Outcomes
    transfer_eligible: bool = False
    intent_score: int = 0
    next_action: Optional[str] = None
    next_action_at: Optional[str] = None

    # Bookkeeping
    deflection_type: Optional[str] = None
    last_trigger_id: Optional[str] = None
    last_objective: Optional[str] = None
    last_variation_index: int = -1
    turns: int = 0
    updated_at: Optional[str] = None

    def can_transition(self, next_stage: str) -> bool:
        """Enforces the state-machine guard (fix for BUG #002)."""
        allowed = LEGAL_TRANSITIONS.get(self.stage, frozenset())
        return next_stage in allowed

    def transition(self, next_stage: str) -> None:
        if not self.can_transition(next_stage):
            raise IllegalStateTransition(
                f"Illegal transition {self.stage} -> {next_stage}. "
                f"Allowed: {sorted(LEGAL_TRANSITIONS.get(self.stage, set()))}"
            )
        self.stage = next_stage
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def apply_objective(self, objective_name: str, intent_delta: int, next_state: str) -> None:
        self.last_objective = objective_name
        self.intent_score += intent_delta
        # next_state on objective is informational; we only transition if it's a real stage
        if next_state in LEGAL_TRANSITIONS and self.can_transition(next_state):
            self.transition(next_state)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ConversationState":
        # ignore unknown keys for forward compatibility
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in valid})


class IllegalStateTransition(Exception):
    pass


def missing_priority_fields(state: ConversationState) -> list[str]:
    """The intelligence-capture priority order. Engines pick the objective
    that fills the highest-priority missing field."""
    order = []
    if not state.decision_maker_known:
        order.append("decision_maker")
    if not state.gatekeeper_name_obtained:
        order.append("gatekeeper_name")
    if not state.best_time_obtained:
        order.append("callback_time")
    if not state.email_obtained:
        order.append("email")
    if not state.pain_known:
        order.append("pain")
    if not state.transfer_eligible:
        order.append("transfer")
    return order
