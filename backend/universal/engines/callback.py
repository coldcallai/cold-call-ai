"""Engine #6 — CallbackEngine. Parses callback time, schedules next action."""
from __future__ import annotations
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..state.conversation_state import ConversationState, STAGE_CALLBACK_SCHEDULED


# Behavior only. No vertical-specific logic.
DAY_WORDS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "tomorrow": -1, "today": -2,
}


class CallbackEngine:
    def parse_time(self, text: str) -> Optional[str]:
        """Lightweight parser. Returns ISO-like string or None.
        Production version will swap in `dateparser`."""
        t = (text or "").lower().strip()
        if not t:
            return None
        # explicit ISO/clock pattern
        m = re.search(r"(\d{1,2})\s*(am|pm|:\d{2}\s*(am|pm)?)", t)
        clock = m.group(0) if m else None
        day = next((d for d in DAY_WORDS if d in t), None)
        if day or clock:
            return " ".join(filter(None, [day, clock]))
        return None

    def schedule(self, state: ConversationState, when_text: str, wait_days: int = 0) -> dict:
        parsed = self.parse_time(when_text) or when_text
        state.best_callback_time = parsed
        state.best_time_obtained = True
        state.next_action = "CALL_BACK"
        when = datetime.now(timezone.utc) + timedelta(days=max(0, wait_days))
        state.next_action_at = when.isoformat()
        if state.can_transition(STAGE_CALLBACK_SCHEDULED):
            state.transition(STAGE_CALLBACK_SCHEDULED)
        return {"next_action": "CALL_BACK", "next_action_at": state.next_action_at, "when": parsed}
