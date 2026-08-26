"""MerchantBrain — Qualification Library V1.

Proactive qualification script. Determines authority, opportunity, timeline,
current processor, volume, pain, interest — without sounding like an application.

Scoring bands (engine-side, per Transfer V1):
    Strong Transfer Candidate (intent_score 85+)   -> live transfer
    Meeting Candidate         (intent_score 60-84) -> book appointment
    Nurture Candidate         (intent_score <60)   -> follow-up sequence
"""
from __future__ import annotations
from universal.contracts.discovery import DiscoveryQuestion


TAGS = ("qualification", "v1", "merchant_services")


QUALIFICATION_QUESTIONS: list[DiscoveryQuestion] = [
    DiscoveryQuestion(
        id="QUAL_Q1",
        objective="Decision Authority",
        primary="Typically when changes are made in this area, are you the person involved in those decisions?",
        variations=(
            "Who normally participates in evaluating those types of changes?",
            "Is that something you oversee personally?",
        ),
        capture_slots=("decision_authority",),
        captures_enum=("Decision Maker", "Influencer", "Not Authority"),
        intent_delta=15,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q2",
        objective="Current Processor",
        primary="Out of curiosity, who are you working with today for payment processing?",
        variations=("Who currently handles your card processing?",),
        capture_slots=("current_processor",),
        captures_enum=("Square", "Clover", "Toast", "Fiserv", "Stripe", "Chase", "Other"),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q3",
        objective="Relationship Length",
        primary="How long have you been with them?",
        variations=("Has that been a long-term relationship?",),
        capture_slots=("relationship_length",),
        captures_enum=("< 1 Year", "1-3 Years", "3-5 Years", "5+ Years"),
        intent_delta=5,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q4",
        objective="Monthly Volume",
        primary="Roughly how much payment volume does the business process in a typical month?",
        softer_version="Are we talking tens of thousands per month or hundreds of thousands?",
        capture_slots=("monthly_volume",),
        captures_enum=("<10k", "10-50k", "50-100k", "100-250k", "250k+"),
        intent_delta=15,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q5",
        objective="Payment Mix",
        primary="Are most payments in person, online, or a mix of both?",
        capture_slots=("payment_mix",),
        captures_enum=("Card Present", "Card Not Present", "Mixed"),
        intent_delta=5,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q6",
        objective="Review Frequency",
        primary="When was the last time you reviewed this part of the business?",
        variations=("Has anyone looked at your payment setup recently?",),
        capture_slots=("review_recency",),
        captures_enum=("Never", "1 Year+", "6 Months", "Recent"),
        intent_delta=15,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q7",
        objective="Timeline",
        primary="If you found a meaningful improvement, would that be something you'd look at now or sometime down the road?",
        variations=("Is this something you'd be open to reviewing in the near future?",),
        capture_slots=("timeline",),
        captures_enum=("Now", "30 Days", "90 Days", "Future", "Never"),
        intent_delta=20,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="QUAL_Q8",
        objective="Interest Level",
        primary="Based on what we've discussed, would it make sense to spend a few minutes reviewing potential opportunities?",
        variations=("Would you be open to a quick review if there was something worth looking at?",),
        capture_slots=("interest_level",),
        captures_enum=("High", "Medium", "Low"),
        intent_delta=25,
        playbook_tags=TAGS,
    ),
]
