"""MerchantBrain — Gatekeeper Library V1.

STATUS: AWAITING CONTENT FROM FOUNDER.

The previous session captured the 15 Gatekeeper triggers but they did not
survive the handoff. This module is a stub so MerchantBrain can be imported
and the rest of V1 can be validated. Populate this module's GATEKEEPER_TRIGGERS
list when the V1 content is resent.

Expected schema (already supported by Trigger contract):
    Trigger(
        id="GK_OWNER_BUSY",
        matches=("...", "..."),
        possible_meanings=("OWNER_BUSY",),
        playbook_tags=("gatekeeper", "v1", "merchant_services"),
        objectives={
            "DECISION_MAKER_DISCOVERY": Objective(
                name="DECISION_MAKER_DISCOVERY",
                intent_delta=15,
                next_state="DISCOVERY",
                variations=("...", "...", "..."),
            ),
            ...
        },
    )
"""
from __future__ import annotations
from universal.contracts.trigger import Trigger  # noqa: F401


# Empty list intentionally — replace with the 15 Gatekeeper V1 triggers.
GATEKEEPER_TRIGGERS: list[Trigger] = []

# Placeholder flag for the deletion-independence test — MerchantBrain remains
# a valid Playbook even with an empty Gatekeeper library.
GATEKEEPER_STATUS = "AWAITING_V1_CONTENT"
