"""CLI: analyze.py — runs the Top-5 Failure Points report from terminal.

Usage:
    PYTHONPATH=$PWD python3 -m universal.reporting.analyze --limit 100

If MONGO_URL is set in env, reads call_reports collection.
Otherwise reads JSONL from --jsonl path (one CallReport dict per line).
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Optional

from .analytics import summary, load_all_reports, by_campaign, variant_performance, filter_by_campaign, top_caller_phrases, top_objection_phrases


def _fmt_row(rows, fmt="{0:>4}  {1}"):
    if not rows:
        return "  (none)"
    out = []
    for k, v in rows:
        if isinstance(v, float):
            out.append(f"  {v:>6.1f}  {k}")
        else:
            out.append(fmt.format(v, k))
    return "\n".join(out)


def _print_report(s: dict) -> None:
    print("=" * 60)
    print(f"  MerchantBrain Call Review — {s['calls_total']} calls")
    print("=" * 60)
    print(f"\nDecision Maker Reached Rate: {s['decision_maker_reached_rate']*100:.1f}%")
    print(f"Outcome Breakdown: {s['outcome_breakdown']}")
    print("\nTop Gatekeeper Triggers:")
    print(_fmt_row(s["top_gatekeeper_triggers"]))
    print("\nTop Decision Maker Objections:")
    print(_fmt_row(s["top_decision_maker_objections"]))
    print("\nHighest Workflow Engagement (avg intent_delta):")
    print(_fmt_row(s["highest_workflow_engagement"]))
    print("\nMost Confusing Funding Questions:")
    print(_fmt_row(s["most_confusing_funding_questions"]))
    print("\nHighest Transfer Drivers:")
    print(_fmt_row(s["highest_transfer_drivers"]))
    print("\nTop Merchant Phrases (post-opener):")
    print(_fmt_row(s.get("top_caller_phrases", [])))
    print("\nTop Objection Phrases:")
    print(_fmt_row(s.get("top_objection_phrases", [])))
    print()


def _print_kpis(label: str, k: dict) -> None:
    print(f"\n  {label}")
    print(f"    Calls               : {k['calls']}")
    print(f"    Conversation Rate   : {k['conversation_rate']*100:>5.1f}%")
    print(f"    Decision Maker Rate : {k['decision_maker_rate']*100:>5.1f}%")
    print(f"    Transfer Rate       : {k['transfer_rate']*100:>5.1f}%")
    print(f"    Appointment Rate    : {k['appointment_rate']*100:>5.1f}%")
    print(f"    Avg Duration (sec)  : {k['avg_duration_sec']:>5.1f}")


def _print_campaign_section(reports: list[dict], focus_campaign: Optional[str] = None) -> None:
    print("\n" + "=" * 60)
    print("  Campaign A/B Comparison (Layer 4)")
    print("=" * 60)
    groups = by_campaign(reports)
    if not groups:
        print("  (no campaign-tagged calls yet)")
        return
    for cid, k in sorted(groups.items(), key=lambda kv: -kv[1]["calls"]):
        _print_kpis(cid, k)
    if focus_campaign:
        print("\n" + "=" * 60)
        print(f"  Variant Performance — {focus_campaign}")
        print("=" * 60)
        variants = variant_performance(reports, focus_campaign)
        if not variants:
            print(f"  (no calls for campaign {focus_campaign!r})")
            return
        for idx, k in sorted(variants.items()):
            label = f"Variant {chr(65 + idx) if idx >= 0 else '?'}"
            _print_kpis(label, k)


async def _run_async(args):
    reports: list[dict] = []
    if args.jsonl and Path(args.jsonl).exists():
        with open(args.jsonl) as f:
            reports = [json.loads(line) for line in f if line.strip()]
    elif os.environ.get("MONGO_URL"):
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ.get("DB_NAME", "intentbrain")]
        reports = await load_all_reports(db.call_reports, limit=args.limit)
    else:
        print("No data source. Pass --jsonl <path> or set MONGO_URL.")
        return
    if args.campaign:
        reports = filter_by_campaign(reports, args.campaign)
    _print_report(summary(reports))
    _print_campaign_section(reports, focus_campaign=args.campaign)


def main() -> None:
    ap = argparse.ArgumentParser(description="MerchantBrain Call Review report")
    ap.add_argument("--jsonl", help="Path to JSONL of CallReports", default=None)
    ap.add_argument("--limit", type=int, default=500, help="Max reports to load from DB")
    ap.add_argument("--campaign", help="Filter + variant-breakdown for one campaign_id", default=None)
    args = ap.parse_args()
    asyncio.run(_run_async(args))


if __name__ == "__main__":
    main()
