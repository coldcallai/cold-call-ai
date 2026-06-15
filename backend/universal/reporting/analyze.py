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

from .analytics import summary, load_all_reports


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
    print()


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
    _print_report(summary(reports))


def main() -> None:
    ap = argparse.ArgumentParser(description="MerchantBrain Call Review report")
    ap.add_argument("--jsonl", help="Path to JSONL of CallReports", default=None)
    ap.add_argument("--limit", type=int, default=500, help="Max reports to load from DB")
    args = ap.parse_args()
    asyncio.run(_run_async(args))


if __name__ == "__main__":
    main()
