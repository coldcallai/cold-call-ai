"""MerchantBrain — Transfer Logic V1.

Score bands:
    0-59   -> NURTURE      (exit gracefully)
    60-79  -> APPOINTMENT  (book a follow-up)
    80+    -> LIVE_TRANSFER (consultative handoff to specialist)

Signal boosts: phrases that immediately move intent_score on detection.

Phrasings are consultative — never "Let me transfer you." Always
"Based on what you've told me about X, Y, Z, it sounds like there may be
opportunities worth reviewing." Engine renders the X/Y/Z from state.
"""
from __future__ import annotations
from universal.contracts.transfer import (
    TransferDecision,
    TransferSignal,
    TRANSFER_LIVE,
    TRANSFER_APPOINTMENT,
    TRANSFER_FOLLOW_UP,
    TRANSFER_NURTURE,
)


TAGS = ("transfer", "v1", "merchant_services")


TRANSFER_DECISIONS: list[TransferDecision] = [
    TransferDecision(
        kind=TRANSFER_NURTURE,
        score_min=0,
        score_max=59,
        requires=("intent_score < 60",),
        phrasings=(
            "It sounds like things are working well right now. If anything changes down the road, we'd be happy to reconnect.",
        ),
        playbook_tags=TAGS,
    ),
    TransferDecision(
        kind=TRANSFER_APPOINTMENT,
        score_min=60,
        score_max=79,
        requires=("intent_score 60-79", "interest >= medium"),
        phrasings=(
            "No problem. What's usually the best day and time for a quick review?",
            "If now isn't ideal, when would be a better time to continue the conversation?",
        ),
        playbook_tags=TAGS,
    ),
    TransferDecision(
        kind=TRANSFER_LIVE,
        score_min=80,
        score_max=None,
        requires=(
            "intent_score >= 80",
            "decision_maker == true",
            "interest >= medium",
            "opportunity in {workflow, funding, processor_review, statement_review}",
        ),
        phrasings=(
            "Based on what you've shared, it sounds like there may be a few areas worth reviewing. Would you be opposed to a brief conversation with a specialist?",
            "It sounds like there may be an opportunity here. If they're available, would it make sense to bring a specialist into the conversation now?",
            "Based on what you've told me, I think it might be helpful to get another set of eyes on it. Are you open to that?",
        ),
        playbook_tags=TAGS,
    ),
]


# Phrase -> intent_delta. Substring match, case-insensitive.
TRANSFER_SIGNALS: list[TransferSignal] = [
    TransferSignal(phrase="too much time on collections", intent_delta=20, label="collections_pain"),
    TransferSignal(phrase="chasing invoices", intent_delta=20, label="collections_pain"),
    TransferSignal(phrase="chasing payments", intent_delta=20, label="collections_pain"),
    TransferSignal(phrase="funding takes longer", intent_delta=20, label="funding_delay"),
    TransferSignal(phrase="funding takes too long", intent_delta=20, label="funding_delay"),
    TransferSignal(phrase="nobody has reviewed", intent_delta=15, label="stale_review"),
    TransferSignal(phrase="no one has reviewed", intent_delta=15, label="stale_review"),
    TransferSignal(phrase="willing to look at options", intent_delta=25, label="open_to_review"),
    TransferSignal(phrase="open to a review", intent_delta=25, label="open_to_review"),
    TransferSignal(phrase="cash flow is tight", intent_delta=15, label="cash_flow_pain"),
    TransferSignal(phrase="30 days to pay", intent_delta=15, label="slow_collections"),
    TransferSignal(phrase="staff manually enters payments", intent_delta=15, label="manual_entry"),
    TransferSignal(phrase="systems don't communicate", intent_delta=15, label="integration_gap"),
]
