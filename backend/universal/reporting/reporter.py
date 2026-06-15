"""CallReport — final structured post-call summary.

This is the exact YAML shape Brian sketched:
    Gatekeeper Trigger: ...
    Response Used: Variant N
    Decision Maker Reached: yes/no
    Workflow Opportunity: yes/no
    Funding Opportunity: yes/no
    Intent Score: N
    Outcome: ...
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CallReport:
    call_sid: str
    generated_at: str
    duration_seconds: Optional[int] = None
    turns: list = field(default_factory=list)
    # campaign attribution (Layer 4)
    campaign_id: Optional[str] = None
    campaign_variant_index: int = -1
    campaign_variant_text: Optional[str] = None
    lead_source: Optional[str] = None
    # gatekeeper
    gatekeeper_trigger: Optional[str] = None
    gatekeeper_objective: Optional[str] = None
    gatekeeper_variant_index: int = -1
    # captured intel
    decision_maker_reached: bool = False
    decision_maker_name: Optional[str] = None
    current_processor: Optional[str] = None
    workflow_opportunity: bool = False
    funding_opportunity: bool = False
    intent_score: int = 0
    deflection_type: Optional[str] = None
    outcome: str = "UNKNOWN"          # APPOINTMENT | LIVE_TRANSFER | FOLLOW_UP | NURTURE | UNKNOWN
    next_action: Optional[str] = None
    next_action_at: Optional[str] = None
    # "Conversation rate" signal — did the caller engage past the opener?
    engaged_past_opener: bool = False
    jargon_hits: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# Heuristics used to roll-up a state + turn_log into a CallReport.
WORKFLOW_TAGS = ("workflow_discovery",)
FUNDING_TAGS = ("funding_discovery",)


def build_report(state, turn_log: list, playbook=None, *,
                 campaign_id: Optional[str] = None,
                 campaign_variant_index: int = -1,
                 campaign_variant_text: Optional[str] = None,
                 lead_source: Optional[str] = None) -> CallReport:
    """Roll up a ConversationState + raw turn_log into a CallReport."""
    report = CallReport(
        call_sid=state.call_sid,
        generated_at=datetime.now(timezone.utc).isoformat(),
        turns=list(turn_log or []),
        intent_score=state.intent_score,
        deflection_type=state.deflection_type,
        decision_maker_reached=state.decision_maker_known,
        decision_maker_name=state.decision_maker_name,
        current_processor=state.current_processor,
        next_action=state.next_action,
        next_action_at=state.next_action_at,
        campaign_id=campaign_id,
        campaign_variant_index=campaign_variant_index,
        campaign_variant_text=campaign_variant_text,
        lead_source=lead_source,
    )

    # "Engaged past opener" = caller produced at least 1 non-empty post-opener turn
    if turn_log and len(turn_log) >= 2:
        report.engaged_past_opener = any(
            (t.get("caller_said") or "").strip() for t in turn_log[1:]
        )

    # Find first gatekeeper turn
    for t in (turn_log or []):
        if t.get("engine") == "gatekeeper":
            report.gatekeeper_trigger = t.get("trigger_id")
            report.gatekeeper_objective = t.get("objective")
            report.gatekeeper_variant_index = t.get("variation_index", -1)
            break

    # Workflow / Funding opportunity = any intent-positive answer captured
    # under those libraries
    if playbook is not None:
        wf_ids = {q.id for q in playbook.get_questions("workflow")}
        fn_ids = {q.id for q in playbook.get_questions("funding")}
    else:
        wf_ids, fn_ids = set(), set()

    for t in (turn_log or []):
        tid = t.get("trigger_id") or ""
        if tid in wf_ids and t.get("intent_delta", 0) > 0:
            report.workflow_opportunity = True
        if tid in fn_ids and t.get("intent_delta", 0) > 0:
            report.funding_opportunity = True

    # Jargon hits — any turn that flagged jargon
    for t in (turn_log or []):
        for j in (t.get("jargon_flagged") or []):
            report.jargon_hits.append({"turn_index": t.get("turn_index"), "jargon": j})

    # Outcome
    if state.stage == "CONFIRMED":
        report.outcome = "APPOINTMENT"
    elif state.stage == "TRANSFERRING":
        report.outcome = "LIVE_TRANSFER"
    elif state.stage == "CALLBACK_SCHEDULED":
        report.outcome = "FOLLOW_UP"
    elif state.intent_score < 60:
        report.outcome = "NURTURE"

    return report


class Reporter:
    """Persistence facade. Pass in a Motor collection to enable Mongo storage."""

    def __init__(self, collection=None) -> None:
        self.col = collection

    async def save(self, report: CallReport) -> None:
        if self.col is None:
            return
        await self.col.update_one(
            {"call_sid": report.call_sid},
            {"$set": report.to_dict()},
            upsert=True,
        )

    async def load(self, call_sid: str) -> Optional[dict]:
        if self.col is None:
            return None
        return await self.col.find_one({"call_sid": call_sid}, {"_id": 0})
