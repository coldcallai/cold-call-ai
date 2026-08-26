"""
UniversalBrain Contract — Playbook abstract base class.

Every vertical Playbook (MerchantBrain, RoofingBrain, ...) implements this
contract. Engines depend ONLY on this contract — never on concrete playbooks.

Architectural rule: deleting any playbook must leave UniversalBrain runnable
(NoopPlaybook fills in). The health test test_deletion_independence enforces.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .trigger import Trigger
from .discovery import DiscoveryQuestion
from .transfer import TransferDecision, TransferSignal


@dataclass(frozen=True)
class QualField:
    name: str
    prompt: str
    required: bool = True


@dataclass(frozen=True)
class IndustryKB:
    summary: str
    facts: tuple[str, ...] = ()


# Library names — what proactive question sets a playbook can expose.
LIB_WORKFLOW = "workflow"
LIB_FUNDING = "funding"
LIB_QUALIFICATION = "qualification"


class Playbook(ABC):
    """Vertical content provider. Contains domain knowledge only."""

    playbook_id: str = "base"
    display_name: str = "Base"

    # --- reactive content ---
    @abstractmethod
    def get_triggers(self) -> list[Trigger]:
        """All reactive triggers (gatekeeper + objection + decision-maker)."""

    # --- proactive content ---
    @abstractmethod
    def get_questions(self, library: str) -> list[DiscoveryQuestion]:
        """Return the proactive question script for the named library."""

    @abstractmethod
    def get_qualification_fields(self) -> list[QualField]:
        """Structured BANT/pain slots (independent of spoken scripts)."""

    # --- scoring & transfer ---
    @abstractmethod
    def get_intent_weights(self) -> dict[str, int]:
        """Per-signal score weights (the math is universal; the weights are per vertical)."""

    @abstractmethod
    def get_transfer_decisions(self) -> list[TransferDecision]:
        """Score-banded transfer decisions (LIVE / APPOINTMENT / FOLLOW_UP / NURTURE)."""

    @abstractmethod
    def get_transfer_signals(self) -> list[TransferSignal]:
        """Phrases that boost intent_score on the fly."""

    # --- vertical knowledge ---
    @abstractmethod
    def get_industry_kb(self) -> IndustryKB:
        ...

    @abstractmethod
    def get_jargon_map(self) -> dict[str, str]:
        """Vertical jargon -> business-owner translation. Empty dict if none."""

    # convenience
    def trigger_index(self) -> dict[str, Trigger]:
        return {t.id: t for t in self.get_triggers()}

    def question_index(self, library: str) -> dict[str, DiscoveryQuestion]:
        return {q.id: q for q in self.get_questions(library)}


class NoopPlaybook(Playbook):
    """Fallback playbook proving UniversalBrain runs without any vertical.

    Used by `test_deletion_independence` and as a safety net when an account
    has no playbook assigned. Returns empty/generic content.
    """

    playbook_id = "noop"
    display_name = "Generic (no vertical)"

    def get_triggers(self) -> list[Trigger]:
        return []

    def get_questions(self, library: str) -> list[DiscoveryQuestion]:
        return []

    def get_qualification_fields(self) -> list[QualField]:
        return [
            QualField(name="business_name", prompt="What's the name of your business?"),
            QualField(name="decision_maker", prompt="Who would I be speaking with about this?"),
        ]

    def get_intent_weights(self) -> dict[str, int]:
        return {
            "decision_maker_name": 15,
            "decision_maker_email": 15,
            "decision_maker_direct_phone": 25,
            "best_callback_time": 10,
            "transferred_to_dm": 50,
            "hard_block": -20,
        }

    def get_transfer_decisions(self) -> list[TransferDecision]:
        return [
            TransferDecision(kind="NURTURE", score_min=0, score_max=59),
            TransferDecision(kind="APPOINTMENT", score_min=60, score_max=79),
            TransferDecision(kind="LIVE_TRANSFER", score_min=80, score_max=None),
        ]

    def get_transfer_signals(self) -> list[TransferSignal]:
        return []

    def get_industry_kb(self) -> IndustryKB:
        return IndustryKB(summary="Generic B2B outreach. No vertical specialization.")

    def get_jargon_map(self) -> dict[str, str]:
        return {}
