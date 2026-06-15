"""Engine #10 — FollowUpEngine. Nurture drip + SEND_EMAIL_AND_CALL scheduling.

Implements the Next Best Action table from PRD §"Next Best Action Engine".
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..state.conversation_state import ConversationState


# Behavior table — universal across verticals.
NEXT_ACTION_RULES: dict[str, dict] = {
    "OWNER_BUSY": {"action": "CALL_BACK", "wait_days": 1},
    "OWNER_UNAVAILABLE": {"action": "CALL_BACK", "wait_days": 0, "use_captured_time": True},
    "NO_COLD_CALLS": {"action": "SEND_EMAIL_AND_CALL", "wait_days": 3},
    "SEND_EMAIL": {"action": "SEND_EMAIL_AND_CALL", "wait_days": 2},
    "GATEKEEPER_BLOCK": {"action": "CALL_BACK", "wait_days": 5},
    "CALL_BACK_LATER": {"action": "CALL_BACK", "wait_days": 0, "use_captured_time": True},
    "SCREENING": {"action": "EMAIL_THEN_CALL", "wait_days": 1},
    "NOT_INTERESTED": {"action": "NURTURE_DRIP", "wait_days": 30},
    "ALREADY_HAVE_PROCESSOR": {"action": "NURTURE_DRIP", "wait_days": 30},  # default; can be tightened by playbook
    "UNKNOWN": {"action": "CALL_BACK", "wait_days": 3},
}


class FollowUpEngine:
    def plan(self, deflection_type: str, state: ConversationState) -> dict:
        rule = NEXT_ACTION_RULES.get(deflection_type, NEXT_ACTION_RULES["UNKNOWN"])
        when = datetime.now(timezone.utc) + timedelta(days=rule["wait_days"])
        state.next_action = rule["action"]
        state.next_action_at = when.isoformat()
        state.deflection_type = deflection_type
        return {
            "next_action": rule["action"],
            "next_action_at": state.next_action_at,
            "wait_days": rule["wait_days"],
        }
