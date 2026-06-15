"""
UniversalBrain Contract — Transfer decision model.

Captures the user's Transfer Logic V1:
    0-59   -> NURTURE
    60-79  -> APPOINTMENT
    80+    -> LIVE_TRANSFER

Plus signal boosts (phrase -> intent_delta) and consultative phrasings.

Rule (PRD §Transfer): a transfer must NEVER feel like "Great, let me transfer
you." It should always feel like "Based on what you've told me about X, Y, Z,
it sounds like there may be opportunities worth reviewing." The engine renders
that phrasing with state-derived context; the playbook supplies the templates.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


TRANSFER_LIVE = "LIVE_TRANSFER"
TRANSFER_APPOINTMENT = "APPOINTMENT"
TRANSFER_FOLLOW_UP = "FOLLOW_UP"
TRANSFER_NURTURE = "NURTURE"

ALL_TRANSFER_KINDS = frozenset({TRANSFER_LIVE, TRANSFER_APPOINTMENT, TRANSFER_FOLLOW_UP, TRANSFER_NURTURE})


@dataclass(frozen=True)
class TransferDecision:
    kind: str                                # one of ALL_TRANSFER_KINDS
    score_min: int
    score_max: Optional[int]                 # None = unbounded
    requires: tuple[str, ...] = ()           # human-readable preconditions
    phrasings: tuple[str, ...] = ()          # consultative ask templates
    playbook_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in ALL_TRANSFER_KINDS:
            raise ValueError(f"TransferDecision.kind {self.kind!r} not in {ALL_TRANSFER_KINDS}")
        if self.score_max is not None and self.score_max < self.score_min:
            raise ValueError(f"TransferDecision {self.kind!r} has score_max<score_min")

    def matches_score(self, score: int) -> bool:
        if score < self.score_min:
            return False
        if self.score_max is not None and score > self.score_max:
            return False
        return True


@dataclass(frozen=True)
class TransferSignal:
    """A phrase -> intent boost. e.g. ('We spend too much time on collections', +20)."""
    phrase: str          # substring match, case-insensitive
    intent_delta: int
    label: str = ""      # human-readable signal name


def select_decision(decisions: list[TransferDecision], intent_score: int) -> Optional[TransferDecision]:
    """Return the (single) decision matching the score band."""
    for d in decisions:
        if d.matches_score(intent_score):
            return d
    return None
