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
        # Single variant — matches the legacy production opener intent.
        # Add more variants once you have baseline conversation-rate data.
        "Hi, I'm calling about payment processing and a couple of quick workflow questions. Is the owner or office manager available?",
    ),
    metadata={
        "version": "v1",
        "role": "control",
    },
)
