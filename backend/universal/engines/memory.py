"""Engine #9 — MemoryEngine. call_intelligence I/O + name-drop lookups."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from ..state.conversation_state import ConversationState


class MemoryEngine:
    """Persistence layer wrapper. Receives a Motor collection.

    The engine never knows about specific verticals; it just persists
    the structured ConversationState dict + retrieves it by call_sid.
    """

    def __init__(self, collection) -> None:
        self.col = collection

    async def load(self, call_sid: str) -> Optional[ConversationState]:
        doc = await self.col.find_one({"call_sid": call_sid}, {"_id": 0})
        if not doc:
            return None
        return ConversationState.from_dict(doc)

    async def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.now(timezone.utc).isoformat()
        await self.col.update_one(
            {"call_sid": state.call_sid},
            {"$set": state.to_dict()},
            upsert=True,
        )

    async def name_drop_lookup(self, lead_id: str) -> dict:
        """Return prior-call intel for the warm callback opener."""
        doc = await self.col.find_one(
            {"lead_id": lead_id, "decision_maker_name": {"$ne": None}},
            {"_id": 0, "decision_maker_name": 1, "gatekeeper_first_name": 1, "best_callback_time": 1},
            sort=[("updated_at", -1)],
        )
        return doc or {}
