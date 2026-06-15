"""Engine #3 — ObjectionEngine. Generic objection handling: select objective from state."""
from __future__ import annotations
from typing import Optional
from ..contracts.playbook import Playbook
from ..contracts.trigger import Trigger, Objective
from ..state.conversation_state import ConversationState


class ObjectionEngine:
    """Shares trigger-selection mechanics with GatekeeperEngine but is invoked
    from non-gatekeeper stages (decision-maker pushback, pricing pushback, etc).
    Engine owns the SELECTION; Playbook owns the CONTENT."""

    def __init__(self, playbook: Playbook) -> None:
        self.playbook = playbook
        self._idx = playbook.trigger_index()

    def match(self, speech: str) -> Optional[Trigger]:
        s = (speech or "").lower().strip()
        if not s:
            return None
        for t in self._idx.values():
            for phrase in t.matches:
                if phrase.lower() in s:
                    return t
        return None

    def respond(self, trigger: Trigger, state: ConversationState) -> Optional[dict]:
        # Default: first declared objective (callers may pass specific objective name).
        first_key = next(iter(trigger.objectives))
        objective = trigger.objectives[first_key]
        idx = (state.last_variation_index + 1) % len(objective.variations)
        state.last_variation_index = idx
        response = objective.variations[idx]
        state.last_trigger_id = trigger.id
        state.apply_objective(objective.name, objective.intent_delta, objective.next_state)
        state.turns += 1
        return {
            "engine": "objection",
            "trigger_id": trigger.id,
            "objective": objective.name,
            "response": response,
            "intent_delta": objective.intent_delta,
        }
