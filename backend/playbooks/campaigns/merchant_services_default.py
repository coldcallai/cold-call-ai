"""Campaign V1 — Merchant Services Default (baseline / control).

The current cold-call opener path. Serves as the A/B control for any
new campaign experiment (e.g. ranktrust_local_growth).
"""
from __future__ import annotations
from universal.contracts.campaign import Campaign, EligibilityCriteria


MERCHANT_SERVICES_DEFAULT = Campaign(
    id="merchant_services_default",
    display_name="Merchant Services (Default Control)",
    source="General B2B Outreach",
    eligibility=EligibilityCriteria(rules=()),  # no eligibility filter
    playbook_id="merchant_brain",
    opening_variants=(
        # Single variant pinned to Brian's exact Control wording for the
        # Day-1 validation experiment. Add more variants later once the
        # baseline conversation rate is known.
        "Who handles patient payment workflows for the practice?",
    ),
    metadata={
        "version": "v1",
        "role": "control",
        "experiment": "ranktrust_validation_day_1",
    },
)
