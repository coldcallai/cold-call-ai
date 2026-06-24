"""Phases 5, 6, 7, 8 — Data quality, opportunity, easy_win, estimated lead gain.

Pure functions. No I/O. Each takes a Prospect, returns it (mutated) or
returns the computed value. Composable.
"""
from __future__ import annotations
from .models import Prospect


# ---------- Phase 5 — Data Quality (0-100) ----------

def compute_data_quality(p: Prospect) -> int:
    score = 0
    if p.normalized_website: score += 25
    if p.normalized_phone: score += 25
    if p.normalized_address: score += 20
    if p.categories: score += 15
    if p.review_count and p.review_count > 0: score += 15
    p.data_quality_score = min(100, score)
    return p.data_quality_score


# ---------- Phase 6 — Opportunity (0-100) ----------
# Weights:
#   Current Rank          40%
#   Review Gap            20%
#   Rating Gap            10%
#   Website Missing       10%
#   Category Optimization 10%
#   Business Completeness 10%

def _rank_component(rank: int | None) -> float:
    """Sweet spot is 4-10 (HIGH opportunity). 1-3 = low (already winning).
    11-20 = medium. >20 or None = low signal."""
    if rank is None:
        return 30.0
    if 4 <= rank <= 7:
        return 100.0
    if 8 <= rank <= 10:
        return 85.0
    if 11 <= rank <= 15:
        return 65.0
    if 16 <= rank <= 20:
        return 45.0
    if rank <= 3:
        return 15.0  # already winning
    return 25.0  # >20: probably not on page 1


def _review_gap_component(p: Prospect, competitor_max_reviews: int) -> float:
    """Larger gap to leader = more opportunity. Capped at 200 reviews gap."""
    gap = max(0, competitor_max_reviews - (p.review_count or 0))
    return min(100.0, (gap / 200.0) * 100.0)


def _rating_gap_component(rating: float | None) -> float:
    """Lower rating = more room to grow. 5.0 = 0 opportunity, 3.0 = 100."""
    if rating is None:
        return 50.0
    if rating >= 4.8:
        return 10.0
    if rating >= 4.5:
        return 30.0
    if rating >= 4.0:
        return 55.0
    if rating >= 3.5:
        return 80.0
    return 100.0


def _website_missing_component(p: Prospect) -> float:
    return 100.0 if not p.normalized_website else 0.0


def _category_component(p: Prospect) -> float:
    n = len(p.categories or [])
    if n == 0: return 100.0
    if n == 1: return 60.0
    if n == 2: return 30.0
    return 10.0  # already well-categorized


def _completeness_component(p: Prospect) -> float:
    # Inverse of data quality: less complete = more opportunity to help
    return 100.0 - (p.data_quality_score or 0)


def compute_opportunity(p: Prospect, *, competitor_max_reviews: int = 100) -> int:
    score = (
        0.40 * _rank_component(p.rank) +
        0.20 * _review_gap_component(p, competitor_max_reviews) +
        0.10 * _rating_gap_component(p.rating) +
        0.10 * _website_missing_component(p) +
        0.10 * _category_component(p) +
        0.10 * _completeness_component(p)
    )
    p.opportunity_score = int(round(score))
    if p.opportunity_score >= 80:
        p.opportunity_level = "VERY_HIGH"
    elif p.opportunity_score >= 60:
        p.opportunity_level = "HIGH"
    elif p.opportunity_score >= 40:
        p.opportunity_level = "MEDIUM"
    else:
        p.opportunity_level = "LOW"
    return p.opportunity_score


# ---------- Phase 7 — Easy Win ----------

def compute_easy_win(p: Prospect, *, competitor_max_reviews: int = 100) -> bool:
    if p.rank is None or not (4 <= p.rank <= 10):
        p.easy_win = False
        return False
    review_gap = max(0, competitor_max_reviews - (p.review_count or 0))
    if review_gap >= 100:
        p.easy_win = False
        return False
    if (p.rating or 0) < 4.0:
        p.easy_win = False
        return False
    if not p.normalized_website:
        p.easy_win = False
        return False
    if (p.data_quality_score or 0) < 70:
        p.easy_win = False
        return False
    p.easy_win = True
    return True


# ---------- Phase 8 — Estimated Lead Gain ----------
# Heuristic: ranks 4-10 capture significant traffic, 11-20 much less.
# We'll improve this with real CTR data later.

_RANK_LEAD_GAIN = {
    4: 50, 5: 45, 6: 40, 7: 35, 8: 30, 9: 26, 10: 22,
    11: 20, 12: 18, 13: 15, 14: 12, 15: 10,
    16: 9, 17: 8, 18: 7, 19: 6, 20: 5,
}


def compute_estimated_lead_gain(p: Prospect) -> int:
    """Heuristic per spec: closer-to-page-1 ranks have higher realistic gain.
    Rank 4-10 = sweet spot. 11-20 declining. Outside = 0."""
    if p.rank is None:
        p.estimated_lead_gain = 0
        return 0
    gain = _RANK_LEAD_GAIN.get(p.rank, 0)
    p.estimated_lead_gain = gain
    return gain


# ---------- Composer ----------

def score_all(p: Prospect, *, competitor_max_reviews: int = 100) -> Prospect:
    compute_data_quality(p)
    compute_opportunity(p, competitor_max_reviews=competitor_max_reviews)
    compute_easy_win(p, competitor_max_reviews=competitor_max_reviews)
    compute_estimated_lead_gain(p)
    return p
