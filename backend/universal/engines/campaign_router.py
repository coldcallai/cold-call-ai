"""CampaignRouter — campaign + variant selection.

Responsibilities:
    1. Resolve campaign_id -> Campaign.
    2. Pick a variant deterministically by lead_id (so re-calls hit the same
       variant — keeps A/B clean across retries).
    3. Check eligibility (a lead's attributes must satisfy campaign rules).

NOT a responsibility:
    - Anything about the post-opener conversation. That's UniversalBrain +
      the campaign's declared playbook.
"""
from __future__ import annotations
import hashlib
from typing import Optional

from universal.contracts.campaign import Campaign


class CampaignRouter:
    def __init__(self, campaigns: list[Campaign]) -> None:
        self._campaigns: dict[str, Campaign] = {c.id: c for c in campaigns}

    def register(self, campaign: Campaign) -> None:
        self._campaigns[campaign.id] = campaign

    def get(self, campaign_id: str) -> Optional[Campaign]:
        return self._campaigns.get(campaign_id)

    def list_ids(self) -> list[str]:
        return list(self._campaigns.keys())

    def is_eligible(self, campaign_id: str, lead_attrs: dict) -> bool:
        c = self.get(campaign_id)
        if not c:
            return False
        rules = c.eligibility.as_dict()
        for key, val in rules.items():
            # Numeric bound rules: <key>_min, <key>_max -> compare lead[<key>]
            if key.endswith("_min"):
                base = key[:-4]
                if base not in lead_attrs:
                    return False
                if lead_attrs[base] < val:
                    return False
            elif key.endswith("_max"):
                base = key[:-4]
                if base not in lead_attrs:
                    return False
                if lead_attrs[base] > val:
                    return False
            else:
                # Exact-match rule
                if lead_attrs.get(key) != val:
                    return False
        return True

    def pick_variant(self, campaign_id: str, lead_id: str) -> tuple[str, int]:
        """Returns (opener_text, variant_index). Deterministic by lead_id."""
        c = self.get(campaign_id)
        if not c:
            raise KeyError(f"Unknown campaign {campaign_id!r}")
        n = c.variant_count()
        if not lead_id:
            return c.opening_variants[0], 0
        h = hashlib.sha256(lead_id.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % n
        return c.opening_variants[idx], idx

    def variant_at(self, campaign_id: str, index: int) -> Optional[str]:
        c = self.get(campaign_id)
        if not c or index < 0 or index >= c.variant_count():
            return None
        return c.opening_variants[index]


def default_router() -> CampaignRouter:
    """Built-in registry with the two V1 campaigns wired up."""
    from playbooks.campaigns.ranktrust_local_growth import RANKTRUST_LOCAL_GROWTH
    from playbooks.campaigns.merchant_services_default import MERCHANT_SERVICES_DEFAULT
    return CampaignRouter([RANKTRUST_LOCAL_GROWTH, MERCHANT_SERVICES_DEFAULT])
