"""
UniversalBrain Contract — Trigger schema.

LOCKED SCHEMA (June 15, 2026). Every Playbook entry (gatekeeper, objection,
funding, workflow, statement) conforms to this shape.

Schema:
    id:                str         - stable identifier (e.g. "WE_ALREADY_HAVE_PROCESSOR")
    matches:           list[str]   - phrase patterns the classifier maps to this trigger
    possible_meanings: list[str]   - human-readable intents this phrase can carry
                                     (e.g. SCREENING, GENUINE_INCUMBENT, BRUSH_OFF)
    playbook_tags:     list[str]   - e.g. ["gatekeeper", "v1", "merchant_services"]
                                     Used for filtering/versioning content sets.
    objectives:        dict[str, Objective] - 1..N objective-paths the brain may
                                     pursue. Selected by ConversationState, NOT
                                     by random.choice.

Each Objective declares:
    intent_delta:      int         - score change when this objective fires
    next_state:        str         - target conversation_state stage
    variations:        list[str]   - 2-3 natural phrasings (never 20)

PRINCIPLE:
    The N responses per trigger are NOT alternatives — they are objective-paths.
    UniversalBrain picks the OBJECTIVE from state; within the objective, it
    rotates variations to avoid sounding scripted.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Objective:
    name: str
    intent_delta: int
    next_state: str
    variations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.variations:
            raise ValueError(f"Objective {self.name!r} must have at least one variation")
        if len(self.variations) > 5:
            raise ValueError(
                f"Objective {self.name!r} has {len(self.variations)} variations. "
                f"Max is 5. Elite reps don't memorize 20 lines per objective."
            )
        for v in self.variations:
            wc = len(v.split())
            if wc > 30:
                raise ValueError(
                    f"Objective {self.name!r} variation exceeds 30 words ({wc}): {v!r}"
                )


@dataclass(frozen=True)
class Trigger:
    id: str
    matches: tuple[str, ...]
    possible_meanings: tuple[str, ...]
    playbook_tags: tuple[str, ...]
    objectives: dict[str, Objective]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Trigger.id required")
        if not self.objectives:
            raise ValueError(f"Trigger {self.id!r} must define at least one objective")

    def objective_names(self) -> list[str]:
        return list(self.objectives.keys())


def trigger_from_dict(d: dict) -> Trigger:
    """Build a Trigger from a YAML/JSON dict. Validates shape."""
    objectives = {}
    for name, obj_d in (d.get("objectives") or {}).items():
        objectives[name] = Objective(
            name=name,
            intent_delta=int(obj_d.get("intent_delta", 0)),
            next_state=str(obj_d.get("next_state", "")),
            variations=tuple(obj_d.get("variations") or ()),
        )
    return Trigger(
        id=str(d["id"]),
        matches=tuple(d.get("matches") or ()),
        possible_meanings=tuple(d.get("possible_meanings") or ()),
        playbook_tags=tuple(d.get("playbook_tags") or ()),
        objectives=objectives,
    )
