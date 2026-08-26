"""Campaign V1 — RankTrust Local Growth.

A growth-oriented opener experiment. Lead source: RankTrust auto-discovery
of businesses ranking GBP positions 4-20 (visible but not dominant).

Hypothesis: a growth-oriented opener engages merchants who would deflect
on a payment-processing opener. Once engaged, MerchantBrain handles the
conversation identically — Decision Maker, Workflow, Funding, Qualification,
Transfer Logic all unchanged.

Success criteria (vs merchant_services_default control):
    - Conversation Rate (got past opener)
    - Decision Maker Rate
    - Transfer Rate
    - Appointment Rate
    - Call Duration
"""
from __future__ import annotations
from universal.contracts.campaign import Campaign, EligibilityCriteria


RANKTRUST_LOCAL_GROWTH = Campaign(
    id="ranktrust_local_growth",
    display_name="RankTrust Local Growth",
    source="RankTrust Auto Discovery",
    eligibility=EligibilityCriteria(rules=(
        ("gbp_rank_min", 4),
        ("gbp_rank_max", 20),
    )),
    playbook_id="merchant_brain",
    opening_variants=(
        # Variant A — direct value question
        "Are you happy with the number of calls and leads you're getting from Google today?",
        # Variant B — priority framing
        "Is generating more local customers a priority this year?",
        # Variant C — competitive framing
        "Have you looked at where you're appearing in Google Maps compared to competitors?",
        # Variant D — observation-based
        "We noticed your business is showing up in Google Maps but not consistently near the top. Is increasing visibility something you're focused on this year?",
    ),
    metadata={
        "version": "v1",
        "lead_source_module": "ranktrust.io",
        "hypothesis": "growth-oriented opener > payment-processing opener for GBP 4-20",
    },
    # Campaign-level objection responses — fired BEFORE handing off to MerchantBrain.
    # Substring match on caller speech (case-insensitive).
    objection_responses=(
        (
            "how did you find my ranking",
            "We use public Google Maps data to identify businesses that may have "
            "opportunities to improve visibility. Your business came up during that review.",
        ),
        (
            "already have an seo",
            "That makes sense. Many businesses we speak with already have someone helping them. "
            "I'm curious — are you happy with the number of calls and leads you're getting from Google today?",
        ),
        (
            "already have someone doing seo",
            "That makes sense. Many businesses we speak with already have someone helping them. "
            "I'm curious — are you happy with the number of calls and leads you're getting from Google today?",
        ),
        (
            "already working with an seo",
            "That makes sense. Many businesses we speak with already have someone helping them. "
            "I'm curious — are you happy with the number of calls and leads you're getting from Google today?",
        ),
        (
            "where did you get my number",
            "Your number is published on your Google business listing. We reached out "
            "directly to ask one quick question about visibility — no list, no purchase.",
        ),
        (
            "is this a robocall",
            "No — I'm an AI assistant calling with one quick question about Google visibility. "
            "I'll keep it short. Do you have a minute?",
        ),
    ),
)
