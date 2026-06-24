"""Prospect data models — provider-agnostic.

Raw records from any source (Outscraper, SerpAPI, Google Maps, DataForSEO)
normalize into RawListing, then merge/score into Prospect.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class RawListing:
    """Single record as received from a provider. Provider-agnostic shape."""
    provider: str                                    # "outscraper" | "serpapi" | "google_maps" | "dataforseo"
    business_name: str = ""
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    categories: list = field(default_factory=list)
    rating: Optional[float] = None
    review_count: Optional[int] = None
    rank: Optional[int] = None                       # GBP rank for the search keyword
    keyword: Optional[str] = None                    # the search term that produced this listing
    raw: dict = field(default_factory=dict)          # original record for audit


@dataclass
class Prospect:
    """Deduped, normalized, scored prospect record."""
    prospect_id: str
    # Identity
    original_name: str = ""
    normalized_name: str = ""
    practice_name: Optional[str] = None
    # Contact
    website: Optional[str] = None
    normalized_website: Optional[str] = None
    phone: Optional[str] = None
    normalized_phone: Optional[str] = None
    address: Optional[str] = None
    normalized_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    # Categories
    categories: list = field(default_factory=list)
    primary_category: Optional[str] = None
    # Listing data
    rating: Optional[float] = None
    review_count: int = 0
    rank: Optional[int] = None
    keyword: Optional[str] = None
    # Practice grouping
    location_count: int = 1
    practitioner_count: int = 1
    # Quality + scoring
    data_quality_score: int = 0
    opportunity_score: int = 0
    opportunity_level: str = "LOW"                   # LOW | MEDIUM | HIGH | VERY_HIGH
    easy_win: bool = False
    estimated_lead_gain: int = 0
    # Audit
    source_providers: list = field(default_factory=list)
    raw_sources: list = field(default_factory=list)  # original raw dicts

    def to_dict(self) -> dict:
        return asdict(self)
