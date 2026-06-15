"""Engine #8 — TransferEngine.

Owns transfer routing BEHAVIOR. Playbook supplies decision bands + phrasings.
Rule: a transfer must never feel like "Great, let me transfer you." Engine
renders consultative phrasing from a template + state-derived context.
"""
from __future__ import annotations
from typing import Optional

from ..contracts.playbook import Playbook
from ..contracts.transfer import TransferDecision, TransferSignal, select_decision
from ..state.conversation_state import ConversationState, STAGE_TRANSFERRING


class TransferEngine:
    def __init__(self, playbook: Playbook) -> None:
        self.decisions: list[TransferDecision] = playbook.get_transfer_decisions()
        self.signals: list[TransferSignal] = playbook.get_transfer_signals()

    def apply_signals(self, speech: str, state: ConversationState) -> int:
        """Scan caller speech for boost phrases; apply intent_delta. Returns total delta."""
        s = (speech or "").lower()
        total = 0
        for sig in self.signals:
            if sig.phrase.lower() in s:
                state.intent_score += sig.intent_delta
                total += sig.intent_delta
        return total

    def decide(self, state: ConversationState) -> Optional[TransferDecision]:
        return select_decision(self.decisions, state.intent_score)

    def initiate(self, state: ConversationState, decision: TransferDecision) -> dict:
        if decision.kind == "LIVE_TRANSFER":
            state.transfer_eligible = True
            if state.can_transition(STAGE_TRANSFERRING):
                state.transition(STAGE_TRANSFERRING)
        # APPOINTMENT / FOLLOW_UP / NURTURE — state transitions handled by their respective engines.
        phrasing = decision.phrasings[0] if decision.phrasings else ""
        return {"decision": decision.kind, "phrasing": phrasing}
