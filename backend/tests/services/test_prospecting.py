"""Prospecting tests — normalization, dedup, scoring, full pipeline."""
from __future__ import annotations
from services.prospecting.normalizer import (
    normalize_website, normalize_phone, normalize_address, normalize_name,
)
from services.prospecting.models import RawListing
from services.prospecting.deduper import dedupe
from services.prospecting.scorer import (
    compute_data_quality, compute_opportunity, compute_easy_win, compute_estimated_lead_gain,
)
from services.prospecting.pipeline import run_pipeline, adapt


# ---- normalization ----
def test_normalize_website():
    assert normalize_website("https://www.example.com/path") == "example.com"
    assert normalize_website("http://example.com") == "example.com"
    assert normalize_website("example.com") == "example.com"
    assert normalize_website("") is None
    assert normalize_website(None) is None


def test_normalize_phone():
    assert normalize_phone("(404) 555-1212") == "4045551212"
    assert normalize_phone("+1-404-555-1212") == "4045551212"
    assert normalize_phone("404.555.1212") == "4045551212"
    assert normalize_phone("404 555 1212") == "4045551212"
    assert normalize_phone("123") is None


def test_normalize_address():
    a = normalize_address("620 Peachtree Road, Suite 200")
    b = normalize_address("620 Peachtree Rd Ste 200")
    assert a == b


def test_normalize_name_strips_suffixes():
    assert normalize_name("Atlanta Dental LLC") == "atlanta dental"
    assert normalize_name("Atlanta Dental Center") == "atlanta dental"
    assert normalize_name("Atlanta Dental Inc.") == "atlanta dental"


# ---- dedup ----
def test_dedupe_merges_by_website():
    raws = [
        RawListing(provider="outscraper", business_name="Atlanta Dental", website="https://www.atlantadental.com", phone="404-555-1111", categories=["Dentist"]),
        RawListing(provider="outscraper", business_name="Atlanta Dental Center", website="atlantadental.com", phone="(404) 555-1111", categories=["Cosmetic Dentist"]),
    ]
    out = dedupe(raws)
    assert len(out) == 1
    assert "Dentist" in out[0].categories and "Cosmetic Dentist" in out[0].categories


def test_dedupe_merges_by_phone():
    raws = [
        RawListing(provider="outscraper", business_name="Smile Center", phone="(404) 555-9999", city="Atlanta"),
        RawListing(provider="outscraper", business_name="Smile Center LLC", phone="4045559999", city="Atlanta"),
    ]
    out = dedupe(raws)
    assert len(out) == 1


def test_dedupe_fuzzy_name_same_city():
    raws = [
        RawListing(provider="outscraper", business_name="Atlanta Family Dental", city="Atlanta"),
        RawListing(provider="outscraper", business_name="Atlanta Family Dental Center", city="Atlanta"),
    ]
    out = dedupe(raws)
    assert len(out) == 1


def test_dedupe_fuzzy_name_different_city_does_not_merge():
    raws = [
        RawListing(provider="outscraper", business_name="Atlanta Dental", city="Atlanta"),
        RawListing(provider="outscraper", business_name="Atlanta Dental", city="Boston"),
    ]
    out = dedupe(raws)
    assert len(out) == 2  # same name, different cities — separate


# ---- scoring ----
def test_easy_win_at_rank_7_with_complete_data():
    """A rank-7 prospect with complete data is the textbook easy_win.
    Opportunity_level is MEDIUM (not HIGH) because high data quality lowers
    the "completeness" component — they need less help fixing data, but
    they're easy to close because they're already organized."""
    raws = [RawListing(
        provider="outscraper", business_name="Joe Dental", phone="404-555-7777",
        website="https://joedental.com", address="1 Main St", categories=["Dentist"],
        rating=4.6, review_count=80, rank=7, keyword="dentist atlanta", city="Atlanta",
    )]
    out = run_pipeline(raws)
    assert out[0].easy_win is True, "rank 7 + complete data + good rating must be easy_win"
    assert out[0].opportunity_level in ("MEDIUM", "HIGH"), f"got {out[0].opportunity_level}"


def test_low_opportunity_when_already_winning():
    raws = [RawListing(
        provider="outscraper", business_name="Top Dental", website="https://top.com",
        phone="404-555-0001", address="1 First St", categories=["Dentist"],
        rating=4.9, review_count=400, rank=2, keyword="dentist atlanta", city="Atlanta",
    )]
    out = run_pipeline(raws)
    assert out[0].opportunity_level in ("LOW", "MEDIUM")
    assert out[0].easy_win is False


def test_data_quality_score():
    raws = [RawListing(provider="outscraper", business_name="Minimal", rank=8)]
    out = run_pipeline(raws)
    assert out[0].data_quality_score < 50


# ---- pipeline ----
def test_pipeline_sorts_easy_wins_first():
    raws = [
        RawListing(provider="outscraper", business_name="A LowOp", rank=18, city="Atlanta", keyword="dentist"),
        RawListing(provider="outscraper", business_name="B EasyWin", phone="404-555-2222",
                   website="https://b.com", address="2 Main St", categories=["Dentist"],
                   rating=4.7, review_count=50, rank=6, city="Atlanta", keyword="dentist"),
    ]
    out = run_pipeline(raws)
    assert out[0].original_name == "B EasyWin"
    assert out[0].easy_win is True


def test_estimated_lead_gain_decreases_with_worse_rank():
    raws = [
        RawListing(provider="outscraper", business_name="Rank8", rank=8, city="A", keyword="k"),
        RawListing(provider="outscraper", business_name="Rank18", rank=18, city="B", keyword="k"),
    ]
    out = sorted(run_pipeline(raws), key=lambda p: p.rank)
    assert out[0].estimated_lead_gain > out[1].estimated_lead_gain


# ---- provider adapters ----
def test_outscraper_adapter():
    raw = adapt([{
        "name": "Test", "site": "https://test.com", "phone": "(404) 555-0000",
        "rating": 4.5, "reviews": 50, "position": 6, "query": "dentist atlanta",
    }], "outscraper")
    assert raw[0].business_name == "Test"
    assert raw[0].rating == 4.5
    assert raw[0].rank == 6


def test_serpapi_adapter():
    raw = adapt([{"title": "X", "website": "https://x.com", "rating": 4.0, "position": 9}], "serpapi")
    assert raw[0].business_name == "X"
    assert raw[0].rank == 9


def test_unknown_provider_raises():
    try:
        adapt([{}], "bogus")
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    import inspect, sys
    me = sys.modules[__name__]
    failed = 0
    for n, f in inspect.getmembers(me, inspect.isfunction):
        if not n.startswith("test_"):
            continue
        try:
            f()
            print(f"PASS: {n}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {n}: {e}")
    sys.exit(1 if failed else 0)
