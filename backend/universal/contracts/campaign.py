"""UniversalBrain Contract — Campaign (Layer 4).

A Campaign owns:
    - The opener (1..N variants — selected per lead, recorded per call)
    - Eligibility criteria (who qualifies for this campaign)
    - Lead source (where leads come from: RankTrust, scraped, referral, ...)
    - The downstream playbook_id (which Playbook handles post-opener conversation)
    - Free-form metadata (anything campaign-specific)

A Campaign owns NOTHING about the post-opener conversation. Once the lead
engages, MerchantBrain/UniversalBrain take over — MerchantBrain is unaware
of which Campaign produced the lead. That's the binding rule.

Hard rule (test: test_campaign_invisibility_to_playbook):
    No Playbook may import from playbooks.campaigns.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class EligibilityCriteria:
    """Free-form structured eligibility. Engines/routers interpret per-key."""
    rules: tuple[tuple[str, object], ...] = ()  # (("gbp_rank_min", 4), ("gbp_rank_max", 20))

    def as_dict(self) -> dict:
        return dict(self.rules)


@dataclass(frozen=True)
class Campaign:
    id: str
    display_name: str
    source: str                              # "RankTrust Auto Discovery"
    eligibility: EligibilityCriteria
    playbook_id: str                         # "merchant_brain" — the downstream brain
    opening_variants: tuple[str, ...]        # exactly the spoken-line variants
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.opening_variants:
            raise ValueError(f"Campaign {self.id!r} requires at least one opening variant")
        if len(self.opening_variants) > 8:
            raise ValueError(
                f"Campaign {self.id!r} has {len(self.opening_variants)} variants. "
                f"Keep it ≤ 8 for clean A/B statistical analysis."
            )
        for v in self.opening_variants:
            if len(v.split()) > 60:
                raise ValueError(
                    f"Campaign {self.id!r} opener exceeds 60 words: {v!r}"
                )

    def variant_count(self) -> int:
        return len(self.opening_variants)
