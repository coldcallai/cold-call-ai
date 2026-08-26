"""Engine #4 — QualificationEngine. Flow control over BANT/pain matrix.
Asks fields the Playbook declared (no industry strings in conditionals here)."""
from __future__ import annotations
from typing import Optional
from ..contracts.playbook import Playbook, QualField
from ..state.conversation_state import ConversationState


class QualificationEngine:
    def __init__(self, playbook: Playbook) -> None:
        self.playbook = playbook
        self._fields: list[QualField] = playbook.get_qualification_fields()
        self._answers: dict[str, str] = {}

    def next_field(self) -> Optional[QualField]:
        for f in self._fields:
            if f.required and f.name not in self._answers:
                return f
        return None

    def capture(self, field_name: str, value: str) -> None:
        self._answers[field_name] = value

    def is_complete(self) -> bool:
        return self.next_field() is None

    @property
    def answers(self) -> dict[str, str]:
        return dict(self._answers)
