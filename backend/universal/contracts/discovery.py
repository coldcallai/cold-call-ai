"""
UniversalBrain Contract — DiscoveryQuestion.

Proactive script item. Used by Workflow / Funding / Qualification libraries.
The engine plays these in order (gated by state), not pattern-matched to caller speech.

Schema (LOCKED June 15, 2026):
    id              - stable identifier (e.g. "WF_Q1", "FN_Q5", "QUAL_Q4")
    objective       - human-readable goal (e.g. "Understand payment flow")
    primary         - canonical phrasing
    variations      - 0..4 alternate phrasings (round-robin to avoid scripted feel)
    softer_version  - optional gentler phrasing for sensitive questions
    capture_slots   - state fields this question fills (e.g. ("monthly_volume",))
    captures_enum   - allowed values for the slot (e.g. ("<10k","10-50k","50-100k","100-250k","250k+"))
    intent_delta    - score change when answered
    next_state      - target conversation_state stage (optional)
    playbook_tags   - e.g. ("workflow_discovery", "v1", "merchant_services")
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiscoveryQuestion:
    id: str
    objective: str
    primary: str
    variations: tuple[str, ...] = ()
    softer_version: Optional[str] = None
    capture_slots: tuple[str, ...] = ()
    captures_enum: tuple[str, ...] = ()
    intent_delta: int = 0
    next_state: str = ""
    playbook_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("DiscoveryQuestion.id required")
        if not self.primary:
            raise ValueError(f"DiscoveryQuestion {self.id!r} requires primary phrasing")
        if len(self.variations) > 4:
            raise ValueError(
                f"DiscoveryQuestion {self.id!r} has {len(self.variations)} variations. Max 4."
            )
        for phrasing in (self.primary, *self.variations, *([self.softer_version] if self.softer_version else [])):
            if phrasing and len(phrasing.split()) > 35:
                raise ValueError(
                    f"DiscoveryQuestion {self.id!r} phrasing exceeds 35 words: {phrasing!r}"
                )

    def all_phrasings(self) -> tuple[str, ...]:
        return tuple(filter(None, (self.primary, *self.variations, self.softer_version)))


def question_from_dict(d: dict) -> DiscoveryQuestion:
    return DiscoveryQuestion(
        id=str(d["id"]),
        objective=str(d.get("objective", "")),
        primary=str(d.get("primary", "")),
        variations=tuple(d.get("variations") or ()),
        softer_version=d.get("softer_version"),
        capture_slots=tuple(d.get("capture_slots") or ()),
        captures_enum=tuple(d.get("captures_enum") or ()),
        intent_delta=int(d.get("intent_delta", 0)),
        next_state=str(d.get("next_state", "")),
        playbook_tags=tuple(d.get("playbook_tags") or ()),
    )
