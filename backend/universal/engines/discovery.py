"""Engine #2 — DiscoveryEngine. Opens the call, identifies business, finds decision maker."""
from __future__ import annotations
from typing import Optional
from ..contracts.playbook import Playbook
from ..state.conversation_state import ConversationState, STAGE_DISCOVERY, STAGE_QUALIFICATION


class DiscoveryEngine:
    def __init__(self, playbook: Playbook) -> None:
        self.playbook = playbook

    def next_question(self, state: ConversationState) -> Optional[str]:
        if not state.decision_maker_known:
            return "Who would I be speaking with about this — are you the owner?"
        if not state.pain_known:
            kb = self.playbook.get_industry_kb()
            # Playbook supplies the *what*; engine wraps the *how*.
            return "What's the biggest headache with how you're currently handling that?"
        return None

    def advance(self, state: ConversationState) -> None:
        if state.decision_maker_known and state.pain_known and state.can_transition(STAGE_QUALIFICATION):
            state.transition(STAGE_QUALIFICATION)
        elif state.can_transition(STAGE_DISCOVERY):
            state.transition(STAGE_DISCOVERY)
