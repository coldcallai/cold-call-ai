"""CampaignSession — Phase 2 Lite production hook.

THREE functions. That's it. server.py calls them at three integration points
and gets:
    1. Campaign opener at call start
    2. Optional canned objection responses (RankTrust-specific) during the call
    3. A CallReport persisted to MongoDB at call end

Legacy brain is UNTOUCHED. Phase 2 Lite layers ABOVE it:

    ┌──────────────────┐
    │ CampaignSession  │  ← Layer 4 (opener + objection_responses + report)
    │                  │
    │ ┌──────────────┐ │
    │ │ Legacy Brain │ │  ← unchanged, still handles the full conversation
    │ └──────────────┘ │
    └──────────────────┘
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from universal.contracts.campaign import Campaign
from universal.engines.campaign_router import CampaignRouter, default_router
from universal.state.conversation_state import ConversationState
from universal.reporting.reporter import build_report, CallReport, Reporter


class CampaignSession:
    """One CampaignSession per call. Stateless apart from selected variant."""

    def __init__(self, *, campaign: Campaign, variant_index: int, opener_text: str,
                 lead_id: str, lead_attrs: dict, started_at: datetime):
        self.campaign = campaign
        self.variant_index = variant_index
        self.opener_text = opener_text
        self.lead_id = lead_id
        self.lead_attrs = lead_attrs
        self.started_at = started_at

    # -------- Integration point #1: at outbound call dial --------
    @classmethod
    def start(cls, lead_id: str, lead_attrs: dict, router: Optional[CampaignRouter] = None,
              fallback_campaign_id: str = "merchant_services_default") -> "CampaignSession":
        """Pick a campaign + variant for this lead. Returns the session."""
        router = router or default_router()
        chosen_id = None
        # priority: most-specific eligibility match
        best_specificity = -1
        for cid in router.list_ids():
            c = router.get(cid)
            if c is None:
                continue
            if router.is_eligible(cid, lead_attrs):
                specificity = len(c.eligibility.as_dict())
                if specificity > best_specificity:
                    best_specificity = specificity
                    chosen_id = cid
        if chosen_id is None:
            chosen_id = fallback_campaign_id
        opener, idx = router.pick_variant(chosen_id, lead_id)
        return cls(
            campaign=router.get(chosen_id),
            variant_index=idx,
            opener_text=opener,
            lead_id=lead_id,
            lead_attrs=lead_attrs,
            started_at=datetime.now(timezone.utc),
        )

    # -------- Integration point #2: per-turn optional intercept --------
    def check_objection(self, caller_said: str) -> Optional[str]:
        """If the caller said something the campaign has a canned response for,
        return that response. Otherwise return None and let the legacy brain
        handle the turn."""
        if not caller_said:
            return None
        text = caller_said.lower()
        for phrase, response in self.campaign.objection_responses:
            if phrase.lower() in text:
                return response
        return None

    # -------- Integration point #3: at call end (Twilio status webhook) --------
    async def finalize(self, *, call_sid: str, legacy_call_doc: dict,
                       reports_collection=None) -> CallReport:
        """Build the CallReport from whatever legacy brain captured + persist.

        legacy_call_doc is your existing inbound_calls / outbound_calls doc.
        Expected fields we'll read (all optional):
            - decision_maker_name, current_processor, conversation_stage / status
            - outcome, transferred, appointment_booked, intent_score
            - turns / transcript (list of {role, text}) — if present, we map it
        """
        state = _state_from_legacy(call_sid, legacy_call_doc)
        turn_log = _turn_log_from_legacy(legacy_call_doc, opener_text=self.opener_text)

        ended_at = datetime.now(timezone.utc)
        duration = int((ended_at - self.started_at).total_seconds())

        report = build_report(
            state, turn_log,
            campaign_id=self.campaign.id,
            campaign_variant_index=self.variant_index,
            campaign_variant_text=self.opener_text,
            lead_source=self.campaign.source,
        )
        report.duration_seconds = duration

        # Tag with anything the legacy doc told us
        if legacy_call_doc.get("outcome"):
            report.outcome = str(legacy_call_doc["outcome"]).upper()
        elif legacy_call_doc.get("transferred"):
            report.outcome = "LIVE_TRANSFER"
        elif legacy_call_doc.get("appointment_booked"):
            report.outcome = "APPOINTMENT"

        if reports_collection is not None:
            reporter = Reporter(reports_collection)
            await reporter.save(report)
        return report

    def session_context(self) -> dict:
        """Compact dict to persist on the inbound_calls / outbound_calls doc
        at call-start time. Lets the call-end webhook find this session."""
        return {
            "campaign_id": self.campaign.id,
            "campaign_variant_index": self.variant_index,
            "campaign_variant_text": self.opener_text,
            "lead_source": self.campaign.source,
            "lead_id": self.lead_id,
            "started_at": self.started_at.isoformat(),
        }

    @classmethod
    def rehydrate(cls, context: dict, lead_attrs: Optional[dict] = None,
                  router: Optional[CampaignRouter] = None) -> "CampaignSession":
        """Reconstruct a session at call-end from the context dict stored at call-start."""
        router = router or default_router()
        c = router.get(context["campaign_id"])
        started_at = datetime.fromisoformat(context["started_at"])
        return cls(
            campaign=c,
            variant_index=int(context["campaign_variant_index"]),
            opener_text=str(context["campaign_variant_text"]),
            lead_id=str(context["lead_id"]),
            lead_attrs=lead_attrs or {},
            started_at=started_at,
        )


# ---------- legacy-doc -> state/turn_log adapters ----------

def _state_from_legacy(call_sid: str, doc: dict) -> ConversationState:
    """Map your existing call doc into a ConversationState for build_report."""
    stage_map = {
        "confirmed": "CONFIRMED", "booked": "CONFIRMED",
        "transferring": "TRANSFERRING", "transferred": "TRANSFERRING",
        "callback_scheduled": "CALLBACK_SCHEDULED",
        "exit": "EXIT", "hung_up": "EXIT", "ended": "EXIT",
    }
    raw_stage = (doc.get("conversation_stage") or doc.get("status") or "").lower()
    stage = stage_map.get(raw_stage, "EXIT")
    state = ConversationState(call_sid=call_sid, stage=stage)
    state.decision_maker_known = bool(doc.get("decision_maker_name") or doc.get("decision_maker_reached"))
    state.decision_maker_name = doc.get("decision_maker_name")
    state.current_processor = doc.get("current_processor")
    state.intent_score = int(doc.get("intent_score") or 0)
    state.next_action = doc.get("next_action")
    state.next_action_at = doc.get("next_action_at")
    state.transfer_eligible = bool(doc.get("transferred") or doc.get("transfer_eligible"))
    return state


def _turn_log_from_legacy(doc: dict, *, opener_text: str) -> list:
    """If the legacy doc has a transcript/turns array, map it. Otherwise we
    only know the opener turn — that's enough to compute engaged_past_opener
    and conversation_rate."""
    raw = doc.get("turns") or doc.get("transcript") or []
    turn_log = [{
        "turn_index": 1,
        "engine": "campaign_opener",
        "trigger_id": None,
        "agent_said": opener_text,
        "caller_said": "",
        "intent_delta": 0,
    }]
    for i, t in enumerate(raw, start=2):
        # accept either {role, text} or {speaker, said}
        role = (t.get("role") or t.get("speaker") or "").lower()
        text = t.get("text") or t.get("said") or ""
        if role in ("user", "caller", "human"):
            turn_log.append({
                "turn_index": i,
                "engine": "legacy",
                "caller_said": text,
                "agent_said": "",
                "intent_delta": 0,
            })
        else:
            turn_log.append({
                "turn_index": i,
                "engine": "legacy",
                "caller_said": "",
                "agent_said": text,
                "intent_delta": 0,
            })
    return turn_log
