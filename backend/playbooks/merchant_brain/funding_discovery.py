"""MerchantBrain — Funding Discovery Library V1.

Proactive script. Follows Workflow Discovery in natural conversation flow.
Goal: discover funding delays, cash flow friction, collection delays,
deposit timing issues, faster-revenue-access opportunities.

Note: all phrasings already passed the "would a restaurant owner understand
this immediately?" test. No "settlement timing", no "funding window",
no "card-not-present volume". (Per PRD jargon-translation rule.)

Scoring (engine-side):
    Healthy Funding             -> funding_score: 90
    Moderate Opportunity        -> funding_score: 70
    Major Opportunity           -> funding_score: 40
"""
from __future__ import annotations
from universal.contracts.discovery import DiscoveryQuestion


TAGS = ("funding_discovery", "v1", "merchant_services")


FUNDING_QUESTIONS: list[DiscoveryQuestion] = [
    DiscoveryQuestion(
        id="FN_Q1",
        objective="Establish current funding speed",
        primary="How quickly do deposits typically hit your account today?",
        variations=(
            "How long does it usually take before funds become available?",
            "Are you seeing deposits same day, next day, or longer?",
        ),
        capture_slots=("funding_speed",),
        captures_enum=("Same Day", "Next Day", "2-3 Days", "Unknown"),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q2",
        objective="Identify funding satisfaction",
        primary="Has that timing worked well for the business?",
        variations=(
            "Do you ever wish funds were available faster?",
            "Has there ever been a time when you wished money from customer payments reached your account faster?",
        ),
        capture_slots=("funding_satisfaction",),
        captures_enum=("Satisfied", "Neutral", "Dissatisfied"),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q3",
        objective="Discover weekend funding gaps",
        primary="Do you receive weekend funding today?",
        variations=("How are Friday and weekend transactions handled?",),
        capture_slots=("weekend_funding",),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q4",
        objective="Discover invoice collection delays",
        primary="When customers receive invoices, how quickly do they typically pay?",
        variations=("What's the average time between sending an invoice and getting paid?",),
        capture_slots=("invoice_payment_speed",),
        captures_enum=("Immediate", "1-7 Days", "8-30 Days", "30+ Days"),
        intent_delta=15,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q5",
        objective="Identify AR pain",
        primary="Does your team spend much time following up on outstanding balances?",
        variations=("How much effort goes into collecting unpaid invoices?",),
        capture_slots=("ar_pain",),
        intent_delta=20,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q6",
        objective="Find collection bottlenecks",
        primary="What's usually the biggest reason payments get delayed?",
        variations=("Where does the collection process tend to slow down?",),
        capture_slots=("collection_bottleneck",),
        captures_enum=("Customer Delay", "Manual Process", "Approval Delay", "Billing Error", "Unknown"),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q7",
        objective="Identify seasonal cash flow pressure",
        primary="Are there times during the year when cash flow becomes more challenging?",
        variations=("Does funding timing matter more during certain months?",),
        capture_slots=("seasonal_pressure",),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q8",
        objective="Future-state discovery (funding magic question)",
        primary="If you could improve one thing about how revenue gets into the business, what would it be?",
        variations=("What's one thing you'd change about the payment and collection process?",),
        capture_slots=("funding_future_wish",),
        intent_delta=20,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q9",
        objective="Discover emergency cash flow issues",
        primary="Have delayed payments ever created operational challenges for the business?",
        variations=("Have slow collections ever impacted staffing, inventory, or growth plans?",),
        capture_slots=("cash_flow_emergencies",),
        intent_delta=25,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="FN_Q10",
        objective="Tie funding to business goals",
        primary="If revenue reached your account faster, where would that make the biggest impact?",
        variations=("What would faster access to funds allow you to do differently?",),
        capture_slots=("funding_business_outcomes",),
        intent_delta=20,
        playbook_tags=TAGS,
    ),
]
