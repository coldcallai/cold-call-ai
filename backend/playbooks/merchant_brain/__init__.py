"""MerchantBrain — Vertical Playbook for Merchant Services.

V1 contents:
    - Decision Maker triggers (8)              -> decision_maker.py
    - Gatekeeper triggers (STUB)               -> gatekeeper.py  [awaiting content]
    - Workflow Discovery questions (10)        -> workflow_discovery.py
    - Funding Discovery questions (10)         -> funding_discovery.py
    - Qualification questions (8)              -> qualification.py
    - Transfer decisions + signals             -> transfer.py
    - Jargon translation map                   -> jargon.py

Architectural rule: this module imports ONLY from universal.contracts and
from sibling playbooks/merchant_brain modules. It must never import an engine.
"""
from __future__ import annotations

from universal.contracts.playbook import (
    Playbook,
    QualField,
    IndustryKB,
    LIB_WORKFLOW,
    LIB_FUNDING,
    LIB_QUALIFICATION,
)
from universal.contracts.trigger import Trigger
from universal.contracts.discovery import DiscoveryQuestion
from universal.contracts.transfer import TransferDecision, TransferSignal

from playbooks.merchant_brain.decision_maker import DECISION_MAKER_TRIGGERS
from playbooks.merchant_brain.gatekeeper import GATEKEEPER_TRIGGERS, GATEKEEPER_STATUS
from playbooks.merchant_brain.workflow_discovery import WORKFLOW_QUESTIONS
from playbooks.merchant_brain.funding_discovery import FUNDING_QUESTIONS
from playbooks.merchant_brain.qualification import QUALIFICATION_QUESTIONS
from playbooks.merchant_brain.transfer import TRANSFER_DECISIONS, TRANSFER_SIGNALS
from playbooks.merchant_brain.jargon import JARGON_MAP


class MerchantBrain(Playbook):
    playbook_id = "merchant_brain"
    display_name = "IntentBrain Merchant Services Playbook"

    # --- reactive content ---
    def get_triggers(self) -> list[Trigger]:
        # Gatekeeper triggers run FIRST in the orchestrator's match order, so
        # we put them at the head of the list even though V1 is empty.
        return [*GATEKEEPER_TRIGGERS, *DECISION_MAKER_TRIGGERS]

    # --- proactive content ---
    def get_questions(self, library: str) -> list[DiscoveryQuestion]:
        if library == LIB_WORKFLOW:
            return list(WORKFLOW_QUESTIONS)
        if library == LIB_FUNDING:
            return list(FUNDING_QUESTIONS)
        if library == LIB_QUALIFICATION:
            return list(QUALIFICATION_QUESTIONS)
        return []

    def get_qualification_fields(self) -> list[QualField]:
        # Derived from QUAL questions' capture_slots — engine-friendly structure.
        return [
            QualField(name="decision_authority", prompt="Are you the decision maker here?"),
            QualField(name="current_processor", prompt="Who handles your processing today?"),
            QualField(name="monthly_volume", prompt="Roughly how much volume per month?"),
            QualField(name="payment_mix", prompt="In-person, online, or a mix?"),
            QualField(name="timeline", prompt="Now, 30 days, 90 days, or down the road?"),
            QualField(name="interest_level", prompt="Open to reviewing if there's an opportunity?"),
        ]

    # --- scoring & transfer ---
    def get_intent_weights(self) -> dict[str, int]:
        return {
            # gatekeeper success score (PRD §)
            "decision_maker_name": 15,
            "decision_maker_email": 15,
            "decision_maker_direct_phone": 25,
            "best_callback_time": 10,
            "transferred_to_dm": 50,
            "hard_block": -20,
            # merchant-specific signals
            "current_processor": 10,
            "contract_end_date": 20,
            "monthly_volume_50k_plus": 15,
            "manual_invoices_present": 15,
            "funding_delays_present": 20,
            "collections_pain_present": 20,
            "open_to_review": 25,
        }

    def get_transfer_decisions(self) -> list[TransferDecision]:
        return list(TRANSFER_DECISIONS)

    def get_transfer_signals(self) -> list[TransferSignal]:
        return list(TRANSFER_SIGNALS)

    # --- vertical knowledge ---
    def get_industry_kb(self) -> IndustryKB:
        return IndustryKB(
            summary=(
                "Merchant services: payment processing for businesses. Key "
                "players include Clover, Square, Toast, Fiserv, Stripe, Chase. "
                "Buying signals cluster around workflow pain (manual invoices, "
                "phone payments), funding delays (slow deposits, AR follow-up), "
                "and lack of recent review."
            ),
            facts=(
                "Common processors: Clover, Square, Toast, Fiserv, Stripe, Chase",
                "Workflow signals: manual invoicing, phone card entry, multiple disconnected systems",
                "Funding signals: 2-3 day deposit times, weekend funding gaps, slow collections",
                "Conversational flow: Decision Maker -> Current Processor -> Experience -> Workflow -> Funding -> Pain -> Qualification -> Transfer",
            ),
        )

    def get_jargon_map(self) -> dict[str, str]:
        return dict(JARGON_MAP)


__all__ = ["MerchantBrain", "GATEKEEPER_STATUS"]
