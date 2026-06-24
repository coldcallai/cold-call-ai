"""Pipeline — orchestrates normalize -> dedup -> score for any provider."""
from __future__ import annotations
from .models import RawListing, Prospect
from .deduper import dedupe
from .scorer import score_all


def run_pipeline(raws: list[RawListing]) -> list[Prospect]:
    """Provider-agnostic. Pass any RawListing list, get scored Prospects."""
    prospects = dedupe(raws)
    # Compute competitor_max_reviews per (keyword, city) cohort
    cohorts: dict[tuple, int] = {}
    for p in prospects:
        key = ((p.keyword or "").lower(), (p.city or "").lower())
        cohorts[key] = max(cohorts.get(key, 0), p.review_count or 0)
    # competitor_max_reviews floor of 100 — when cohort has only 1 prospect we
    # don't want review_gap component to be 0 (real-world competitors exist).
    for p in prospects:
        key = ((p.keyword or "").lower(), (p.city or "").lower())
        cmax = max(cohorts.get(key, 100), 100)
        score_all(p, competitor_max_reviews=cmax)
    # sort by opportunity desc, easy_win first
    prospects.sort(key=lambda p: (not p.easy_win, -p.opportunity_score, p.rank or 999))
    return prospects


# ---------- Provider adapters ----------
# Each adapter takes the provider's raw shape and returns RawListing.
# Easy to add more providers later.

def from_outscraper(record: dict) -> RawListing:
    return RawListing(
        provider="outscraper",
        business_name=record.get("name") or record.get("title") or "",
        website=record.get("site") or record.get("website"),
        phone=record.get("phone"),
        address=record.get("full_address") or record.get("address"),
        city=record.get("city"),
        state=record.get("state"),
        zip_code=record.get("postal_code") or record.get("zip"),
        categories=record.get("categories") or ([record["category"]] if record.get("category") else []),
        rating=record.get("rating"),
        review_count=record.get("reviews") or record.get("review_count"),
        rank=record.get("position") or record.get("rank"),
        keyword=record.get("query") or record.get("keyword"),
        raw=record,
    )


def from_serpapi(record: dict) -> RawListing:
    return RawListing(
        provider="serpapi",
        business_name=record.get("title") or "",
        website=record.get("website") or record.get("link"),
        phone=record.get("phone"),
        address=record.get("address"),
        categories=[record["type"]] if record.get("type") else (record.get("types") or []),
        rating=record.get("rating"),
        review_count=record.get("reviews"),
        rank=record.get("position"),
        keyword=record.get("search_query"),
        raw=record,
    )


def from_google_maps(record: dict) -> RawListing:
    return RawListing(
        provider="google_maps",
        business_name=record.get("name", ""),
        website=record.get("website"),
        phone=record.get("formatted_phone_number") or record.get("international_phone_number"),
        address=record.get("formatted_address") or record.get("vicinity"),
        categories=record.get("types") or [],
        rating=record.get("rating"),
        review_count=record.get("user_ratings_total"),
        rank=record.get("rank"),
        raw=record,
    )


def from_dataforseo(record: dict) -> RawListing:
    return RawListing(
        provider="dataforseo",
        business_name=record.get("title", ""),
        website=record.get("url"),
        phone=record.get("phone"),
        address=record.get("address"),
        city=record.get("city"),
        categories=record.get("category") and [record["category"]] or [],
        rating=(record.get("rating") or {}).get("value") if isinstance(record.get("rating"), dict) else record.get("rating"),
        review_count=(record.get("rating") or {}).get("votes_count") if isinstance(record.get("rating"), dict) else record.get("votes"),
        rank=record.get("rank_absolute") or record.get("rank_group"),
        keyword=record.get("keyword"),
        raw=record,
    )


PROVIDER_ADAPTERS = {
    "outscraper": from_outscraper,
    "serpapi": from_serpapi,
    "google_maps": from_google_maps,
    "dataforseo": from_dataforseo,
}


def adapt(records: list[dict], provider: str) -> list[RawListing]:
    if provider not in PROVIDER_ADAPTERS:
        raise ValueError(f"Unknown provider {provider!r}. Available: {sorted(PROVIDER_ADAPTERS)}")
    return [PROVIDER_ADAPTERS[provider](r) for r in records]
