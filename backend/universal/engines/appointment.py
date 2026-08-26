"""Engine #7 — AppointmentEngine. Booking link dispatch + confirmation flow."""
from __future__ import annotations
from typing import Optional
from ..state.conversation_state import ConversationState, STAGE_BOOKING, STAGE_CONFIRMED


class AppointmentEngine:
    def __init__(self, booking_url_provider, sms_sender=None) -> None:
        # Both injected — engine is agnostic to Calendly/Twilio.
        self._booking_url_provider = booking_url_provider
        self._sms_sender = sms_sender

    async def initiate(self, state: ConversationState, phone_e164: str) -> dict:
        url = self._booking_url_provider()
        if state.can_transition(STAGE_BOOKING):
            state.transition(STAGE_BOOKING)
        result: dict = {"booking_url": url, "phone": phone_e164}
        if self._sms_sender:
            sms_result = await self._sms_sender(phone_e164, url)
            result["sms"] = sms_result
        return result

    def confirm(self, state: ConversationState) -> None:
        if state.can_transition(STAGE_CONFIRMED):
            state.transition(STAGE_CONFIRMED)
