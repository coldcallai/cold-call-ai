"""TurnLog — per-turn structured event."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TurnLog:
    call_sid: str
    turn_index: int
    engine: str                       # "gatekeeper" | "decision_maker" | "discovery" | ...
    trigger_id: Optional[str] = None
    objective: Optional[str] = None
    variation_index: int = -1
    caller_said: str = ""
    agent_said: str = ""
    intent_delta: int = 0
    intent_score_after: int = 0
    stage_before: str = ""
    stage_after: str = ""
    captured: dict = field(default_factory=dict)
    jargon_flagged: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class TurnLogger:
    """Engines hand this a turn event; logger appends to ConversationState.turns
    and (optionally) persists asynchronously to MongoDB."""

    def __init__(self, persist_fn=None) -> None:
        self._persist = persist_fn  # async callable(turn_dict) or None

    def log(self, state, *, engine: str, caller_said: str, agent_said: str,
            engine_result: Optional[dict] = None, captured: Optional[dict] = None,
            jargon_flagged: Optional[list] = None) -> TurnLog:
        engine_result = engine_result or {}
        turn = TurnLog(
            call_sid=state.call_sid,
            turn_index=state.turns + 1 if isinstance(state.turns, int) else len(state.turns) + 1,
            engine=engine,
            trigger_id=engine_result.get("trigger_id"),
            objective=engine_result.get("objective"),
            variation_index=state.last_variation_index,
            caller_said=caller_said,
            agent_said=agent_said,
            intent_delta=engine_result.get("intent_delta", 0),
            intent_score_after=state.intent_score,
            stage_before=engine_result.get("stage_before", state.stage),
            stage_after=state.stage,
            captured=captured or {},
            jargon_flagged=jargon_flagged or [],
        )
        # Backward-compat: ConversationState.turns is currently `int` counter.
        # We piggyback a separate list on state via attribute injection.
        if not hasattr(state, "turn_log") or state.turn_log is None:
            state.turn_log = []
        state.turn_log.append(turn.to_dict())
        return turn
