"""Phase 2 + 3 + 4 — Dedup, category merging, practice identification.

Match hierarchy (highest priority first):
  1. normalized_website
  2. normalized_phone
  3. normalized_address
  4. fuzzy normalized_name (>= 85% similarity)
"""
from __future__ import annotations
import uuid
from difflib import SequenceMatcher
from typing import Optional

from .models import RawListing, Prospect
from .normalizer import (
    normalize_website, normalize_phone, normalize_address, normalize_name,
)


FUZZY_THRESHOLD = 0.85


def _fuzzy(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _make_prospect(raw: RawListing) -> Prospect:
    nw = normalize_website(raw.website)
    np_ = normalize_phone(raw.phone)
    na = normalize_address(raw.address)
    nm = normalize_name(raw.business_name)
    return Prospect(
        prospect_id=str(uuid.uuid4()),
        original_name=raw.business_name,
        normalized_name=nm or "",
        website=raw.website,
        normalized_website=nw,
        phone=raw.phone,
        normalized_phone=np_,
        address=raw.address,
        normalized_address=na,
        city=raw.city,
        state=raw.state,
        categories=list(raw.categories or []),
        primary_category=(raw.categories[0] if raw.categories else None),
        rating=raw.rating,
        review_count=int(raw.review_count or 0),
        rank=raw.rank,
        keyword=raw.keyword,
        source_providers=[raw.provider] if raw.provider else [],
        raw_sources=[raw.raw] if raw.raw else [],
    )


def _matches(a: Prospect, b: Prospect) -> bool:
    if a.normalized_website and b.normalized_website and a.normalized_website == b.normalized_website:
        return True
    if a.normalized_phone and b.normalized_phone and a.normalized_phone == b.normalized_phone:
        return True
    if a.normalized_address and b.normalized_address and a.normalized_address == b.normalized_address:
        return True
    if _fuzzy(a.normalized_name, b.normalized_name) >= FUZZY_THRESHOLD:
        # require same city to avoid cross-metro collisions on common names
        if (a.city or "").lower() == (b.city or "").lower():
            return True
    return False


def _merge_into(target: Prospect, other: Prospect) -> None:
    """Fold `other` into `target` in place. Phase 3 + 4 happen here."""
    # categories — set union, preserve order from target first
    for c in other.categories:
        if c not in target.categories:
            target.categories.append(c)
    if not target.primary_category and other.primary_category:
        target.primary_category = other.primary_category
    # prefer best rating + max review count
    if (other.review_count or 0) > (target.review_count or 0):
        target.review_count = other.review_count
        if other.rating is not None:
            target.rating = other.rating
    elif target.rating is None and other.rating is not None:
        target.rating = other.rating
    # best (lowest) rank
    if other.rank is not None and (target.rank is None or other.rank < target.rank):
        target.rank = other.rank
        target.keyword = other.keyword or target.keyword
    # fill missing fields from other
    for fld in ("website", "normalized_website", "phone", "normalized_phone",
                "address", "normalized_address", "city", "state"):
        if not getattr(target, fld) and getattr(other, fld):
            setattr(target, fld, getattr(other, fld))
    # practice grouping (Phase 4)
    target.practitioner_count += 1
    target.source_providers.extend(p for p in other.source_providers if p not in target.source_providers)
    target.raw_sources.extend(other.raw_sources)
    # practice_name: prefer the shortest non-empty original_name (often the parent)
    if not target.practice_name:
        target.practice_name = target.original_name
    if other.original_name and len(other.original_name) < len(target.practice_name or ""):
        target.practice_name = other.original_name


def dedupe(raws: list[RawListing]) -> list[Prospect]:
    """Reduce a list of raw listings to one Prospect per practice."""
    prospects: list[Prospect] = []
    for raw in raws:
        candidate = _make_prospect(raw)
        merged = False
        for existing in prospects:
            if _matches(existing, candidate):
                _merge_into(existing, candidate)
                merged = True
                break
        if not merged:
            candidate.practice_name = candidate.original_name
            prospects.append(candidate)
    # location_count: count how many raw sources share normalized_website
    if prospects:
        web_counts: dict[str, int] = {}
        for p in prospects:
            if p.normalized_website:
                web_counts[p.normalized_website] = web_counts.get(p.normalized_website, 0) + 1
        for p in prospects:
            if p.normalized_website and web_counts.get(p.normalized_website, 0) > 1:
                p.location_count = web_counts[p.normalized_website]
    return prospects
