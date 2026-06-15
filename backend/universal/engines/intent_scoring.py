"""Engine #5 — IntentScoringEngine. The math. Playbook supplies weights only."""
from __future__ import annotations
from ..contracts.playbook import Playbook
from ..state.conversation_state import ConversationState


class IntentScoringEngine:
    def __init__(self, playbook: Playbook) -> None:
        self.weights: dict[str, int] = dict(playbook.get_intent_weights())

    def apply_signal(self, signal: str, state: ConversationState) -> int:
        delta = self.weights.get(signal, 0)
        state.intent_score += delta
        return delta

    def total(self, state: ConversationState) -> int:
        return state.intent_score

    def recompute_from_state(self, state: ConversationState) -> int:
        score = 0
        if state.decision_maker_name:
            score += self.weights.get("decision_maker_name", 0)
        if state.decision_maker_email:
            score += self.weights.get("decision_maker_email", 0)
        if state.decision_maker_direct_phone:
            score += self.weights.get("decision_maker_direct_phone", 0)
        if state.best_callback_time:
            score += self.weights.get("best_callback_time", 0)
        if state.transfer_eligible:
            score += self.weights.get("transferred_to_dm", 0)
        if state.current_processor:
            score += self.weights.get("current_processor", 0)
        if state.contract_end_date:
            score += self.weights.get("contract_end_date", 0)
        state.intent_score = score
        return score
