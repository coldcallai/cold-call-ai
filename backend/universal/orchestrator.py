"""
UniversalBrain Orchestrator.

Thin coordinator that owns NO domain knowledge. Loads a Playbook (Layer 2),
applies Account overrides (Layer 3) and Campaign overrides (Layer 4),
then routes one conversational turn through the 10 engines.

Feature-flagged: enabled only when env UNIVERSAL_BRAIN_ENABLED=true.
This lets the legacy inline brain in server.py keep running in production
while Phase 1 stabilizes.
"""
from __future__ import annotations
import os
from typing import Optional

from .contracts.playbook import Playbook, NoopPlaybook
from .engines.gatekeeper import GatekeeperEngine
from .engines.discovery import DiscoveryEngine
from .engines.objection import ObjectionEngine
from .engines.qualification import QualificationEngine
from .engines.intent_scoring import IntentScoringEngine
from .engines.callback import CallbackEngine
from .engines.appointment import AppointmentEngine
from .engines.transfer import TransferEngine
from .engines.memory import MemoryEngine
from .engines.follow_up import FollowUpEngine
from .state.conversation_state import ConversationState


def is_enabled() -> bool:
    return os.environ.get("UNIVERSAL_BRAIN_ENABLED", "false").lower() == "true"


class Orchestrator:
    def __init__(
        self,
        playbook: Optional[Playbook] = None,
        memory_collection=None,
        booking_url_provider=None,
        sms_sender=None,
    ) -> None:
        self.playbook = playbook or NoopPlaybook()
        self.gatekeeper = GatekeeperEngine(self.playbook)
        self.discovery = DiscoveryEngine(self.playbook)
        self.objection = ObjectionEngine(self.playbook)
        self.qualification = QualificationEngine(self.playbook)
        self.intent = IntentScoringEngine(self.playbook)
        self.callback = CallbackEngine()
        self.appointment = AppointmentEngine(booking_url_provider or (lambda: ""), sms_sender)
        self.transfer = TransferEngine(self.playbook)
        self.memory = MemoryEngine(memory_collection) if memory_collection is not None else None
        self.follow_up = FollowUpEngine()

    async def handle_turn(self, call_sid: str, speech: str) -> dict:
        """Single-turn pipeline. Returns {response, state_snapshot}."""
        if self.memory:
            state = await self.memory.load(call_sid) or ConversationState(call_sid=call_sid)
        else:
            state = ConversationState(call_sid=call_sid)

        # 1. Gatekeeper trigger match (if any)
        gk = self.gatekeeper.handle(speech, state)
        if gk:
            self.intent.recompute_from_state(state)
            if self.memory:
                await self.memory.save(state)
            return {"engine_result": gk, "state": state.to_dict()}

        # 2. Generic objection fallback
        trig = self.objection.match(speech)
        if trig:
            ob = self.objection.respond(trig, state)
            self.intent.recompute_from_state(state)
            if self.memory:
                await self.memory.save(state)
            return {"engine_result": ob, "state": state.to_dict()}

        # 3. Discovery question (default)
        q = self.discovery.next_question(state)
        if q:
            self.discovery.advance(state)
            if self.memory:
                await self.memory.save(state)
            return {
                "engine_result": {
                    "engine": "discovery",
                    "response": q,
                },
                "state": state.to_dict(),
            }

        # 4. Qualification flow
        field = self.qualification.next_field()
        if field:
            if self.memory:
                await self.memory.save(state)
            return {
                "engine_result": {"engine": "qualification", "response": field.prompt, "field": field.name},
                "state": state.to_dict(),
            }

        # 5. Transfer eligibility
        rule = self.transfer.should_transfer(state)
        if rule:
            res = self.transfer.initiate(state, rule)
            if self.memory:
                await self.memory.save(state)
            return {"engine_result": {"engine": "transfer", **res}, "state": state.to_dict()}

        # 6. Fallback: end politely
        if self.memory:
            await self.memory.save(state)
        return {
            "engine_result": {
                "engine": "fallback",
                "response": "Got it. Anything else I can help with?",
            },
            "state": state.to_dict(),
        }
