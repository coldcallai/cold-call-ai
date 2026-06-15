"""Analytics — the 5 priority questions answered as aggregations.

Each function takes either:
    - a list[dict] of CallReports (in-memory), OR
    - a Motor `call_reports` collection (async DB)
"""
from __future__ import annotations
from collections import Counter
from typing import Optional


def _iter_reports(reports):
    return reports or []


# ---- in-memory aggregations (great for tests / CLI) ----

def top_gatekeeper_triggers(reports: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """Q1 — which gatekeeper triggers occur most often?"""
    c = Counter()
    for r in _iter_reports(reports):
        if r.get("gatekeeper_trigger"):
            c[r["gatekeeper_trigger"]] += 1
    return c.most_common(n)


def top_decision_maker_objections(reports: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """Q2 — which DM objections occur most? (turns whose engine=='objection'
    or trigger_id starts with 'DM_')."""
    c = Counter()
    for r in _iter_reports(reports):
        for t in r.get("turns") or []:
            tid = t.get("trigger_id") or ""
            if tid.startswith("DM_"):
                c[tid] += 1
    return c.most_common(n)


def workflow_engagement(reports: list[dict], n: int = 5) -> list[tuple[str, float]]:
    """Q3 — which workflow questions create the most engagement?
    Engagement = mean intent_delta over all firings."""
    sums: dict[str, int] = {}
    counts: dict[str, int] = {}
    for r in _iter_reports(reports):
        for t in r.get("turns") or []:
            tid = t.get("trigger_id") or ""
            if tid.startswith("WF_"):
                sums[tid] = sums.get(tid, 0) + t.get("intent_delta", 0)
                counts[tid] = counts.get(tid, 0) + 1
    rates = [(k, sums[k] / counts[k]) for k in sums if counts[k] > 0]
    rates.sort(key=lambda kv: kv[1], reverse=True)
    return rates[:n]


def funding_confusion(reports: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """Q4 — which funding questions are followed by 'what do you mean?' /
    jargon-flag? Higher = more confusing."""
    c = Counter()
    for r in _iter_reports(reports):
        turns = r.get("turns") or []
        for i, t in enumerate(turns):
            tid = t.get("trigger_id") or ""
            if not tid.startswith("FN_"):
                continue
            # Look at the next caller turn for confusion signals
            if i + 1 < len(turns):
                nxt = turns[i + 1].get("caller_said", "").lower()
                if any(p in nxt for p in ("what do you mean", "what does that mean", "i'm not sure", "huh", "what?", "come again")):
                    c[tid] += 1
            if t.get("jargon_flagged"):
                c[tid] += 1
    return c.most_common(n)


def transfer_drivers(reports: list[dict], n: int = 5) -> list[tuple[str, int]]:
    """Q5 — which questions produce transfers?
    Counts the trigger fired immediately before the call hit LIVE_TRANSFER
    or APPOINTMENT outcome."""
    c = Counter()
    for r in _iter_reports(reports):
        if r.get("outcome") not in ("LIVE_TRANSFER", "APPOINTMENT"):
            continue
        turns = r.get("turns") or []
        # last trigger that produced positive intent before outcome
        for t in reversed(turns):
            tid = t.get("trigger_id") or ""
            if tid and t.get("intent_delta", 0) > 0:
                c[tid] += 1
                break
    return c.most_common(n)


def summary(reports: list[dict]) -> dict:
    """Top-5 Failure Points (and wins) report. The exact format Brian asked for."""
    n_calls = len(reports or [])
    n_dm = sum(1 for r in (reports or []) if r.get("decision_maker_reached"))
    outcomes = Counter((r.get("outcome") or "UNKNOWN") for r in (reports or []))
    return {
        "calls_total": n_calls,
        "decision_maker_reached_rate": (n_dm / n_calls) if n_calls else 0.0,
        "outcome_breakdown": dict(outcomes),
        "top_gatekeeper_triggers": top_gatekeeper_triggers(reports),
        "top_decision_maker_objections": top_decision_maker_objections(reports),
        "highest_workflow_engagement": workflow_engagement(reports),
        "most_confusing_funding_questions": funding_confusion(reports),
        "highest_transfer_drivers": transfer_drivers(reports),
    }


# ---- async DB variants ----

async def load_all_reports(collection, limit: int = 1000) -> list[dict]:
    if collection is None:
        return []
    cursor = collection.find({}, {"_id": 0}).sort("generated_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ---- Campaign analytics (Layer 4) ----

def filter_by_campaign(reports: list[dict], campaign_id: str) -> list[dict]:
    return [r for r in (reports or []) if r.get("campaign_id") == campaign_id]


def _rate(numerator: int, denominator: int) -> float:
    return (numerator / denominator) if denominator else 0.0


def _outcome_rate(reports: list[dict], outcome: str) -> float:
    n = len(reports)
    if not n:
        return 0.0
    return _rate(sum(1 for r in reports if r.get("outcome") == outcome), n)


def campaign_kpis(reports: list[dict]) -> dict:
    """The 5 success metrics:
        - Conversation Rate (engaged past opener)
        - Decision Maker Rate
        - Transfer Rate (LIVE_TRANSFER outcome)
        - Appointment Rate (APPOINTMENT outcome)
        - Avg Call Duration (seconds)
    """
    n = len(reports or [])
    if not n:
        return {
            "calls": 0, "conversation_rate": 0.0, "decision_maker_rate": 0.0,
            "transfer_rate": 0.0, "appointment_rate": 0.0, "avg_duration_sec": 0.0,
        }
    durations = [r.get("duration_seconds") for r in reports if r.get("duration_seconds") is not None]
    return {
        "calls": n,
        "conversation_rate": _rate(sum(1 for r in reports if r.get("engaged_past_opener")), n),
        "decision_maker_rate": _rate(sum(1 for r in reports if r.get("decision_maker_reached")), n),
        "transfer_rate": _outcome_rate(reports, "LIVE_TRANSFER"),
        "appointment_rate": _outcome_rate(reports, "APPOINTMENT"),
        "avg_duration_sec": (sum(durations) / len(durations)) if durations else 0.0,
    }


def by_campaign(reports: list[dict]) -> dict[str, dict]:
    """Group reports by campaign_id -> KPI dict. The A/B comparison view."""
    groups: dict[str, list[dict]] = {}
    for r in (reports or []):
        cid = r.get("campaign_id") or "_uncategorized"
        groups.setdefault(cid, []).append(r)
    return {cid: campaign_kpis(rs) for cid, rs in groups.items()}


def variant_performance(reports: list[dict], campaign_id: Optional[str] = None) -> dict[int, dict]:
    """Per-variant KPI breakdown within a campaign. Used to find the winning variant."""
    src = filter_by_campaign(reports, campaign_id) if campaign_id else (reports or [])
    by_variant: dict[int, list[dict]] = {}
    for r in src:
        idx = r.get("campaign_variant_index", -1)
        by_variant.setdefault(idx, []).append(r)
    return {idx: campaign_kpis(rs) for idx, rs in by_variant.items()}
