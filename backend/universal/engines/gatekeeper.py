"""
Engine #1 — GatekeeperEngine.

RESPONSIBILITY:
    Detect deflection type, classify intent, pivot to intelligence capture.

BEHAVIOR ONLY. No industry strings appear in conditionals here.
The Playbook supplies trigger phrases and response copy; this engine
selects WHICH objective to pursue based on ConversationState.

Binding rules (PRD §Agent Brain Rules):
    1. Never pitch product/pricing to a gatekeeper.
    2. Goal is intelligence capture (DM name/email/extension/best time/transfer).
    3. Score every gatekeeper turn.
"""
from __future__ import annotations
from typing import Optional

from ..contracts.playbook import Playbook
from ..contracts.trigger import Trigger, Objective
from ..state.conversation_state import (
    ConversationState,
    missing_priority_fields,
)


# Priority order: which missing slot to fill first.
# Maps state-missing-field -> objective-name we look for in the trigger.
PRIORITY_TO_OBJECTIVE = [
    ("transfer", "TRANSFER"),
    ("decision_maker", "DECISION_MAKER_DISCOVERY"),
    ("callback_time", "CALLBACK"),
    ("email", "EMAIL_CAPTURE"),
    ("pain", "PAIN_DISCOVERY"),
]


class GatekeeperEngine:
    def __init__(self, playbook: Playbook) -> None:
        self.playbook = playbook
        self._trigger_index = playbook.trigger_index()

    def match_trigger(self, speech: str) -> Optional[Trigger]:
        s = (speech or "").lower().strip()
        if not s:
            return None
        for t in self._trigger_index.values():
            for phrase in t.matches:
                if phrase.lower() in s:
                    return t
        return None

    def select_objective(self, trigger: Trigger, state: ConversationState) -> Optional[Objective]:
        """Pick the objective that fills the highest-priority missing slot."""
        missing = missing_priority_fields(state)
        for slot in missing:
            mapped = next((obj for (s, obj) in PRIORITY_TO_OBJECTIVE if s == slot), None)
            if mapped and mapped in trigger.objectives:
                return trigger.objectives[mapped]
        # No priority match — fall back to first declared objective
        first_key = next(iter(trigger.objectives))
        return trigger.objectives[first_key]

    def pick_variation(self, objective: Objective, state: ConversationState) -> str:
        """Round-robin to avoid sounding scripted. NEVER random.choice."""
        idx = (state.last_variation_index + 1) % len(objective.variations)
        state.last_variation_index = idx
        return objective.variations[idx]

    def handle(self, speech: str, state: ConversationState) -> Optional[dict]:
        trigger = self.match_trigger(speech)
        if not trigger:
            return None
        objective = self.select_objective(trigger, state)
        if not objective:
            return None
        response = self.pick_variation(objective, state)
        state.last_trigger_id = trigger.id
        state.apply_objective(objective.name, objective.intent_delta, objective.next_state)
        state.turns += 1
        return {
            "engine": "gatekeeper",
            "trigger_id": trigger.id,
            "objective": objective.name,
            "response": response,
            "next_state_hint": objective.next_state,
            "intent_delta": objective.intent_delta,
        }
