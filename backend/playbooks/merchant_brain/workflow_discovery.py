"""MerchantBrain — Workflow Discovery Library V1.

Proactive script. Triggered once rapport is established.
Goal: identify time drains, manual work, customer friction, payment friction,
automation opportunities. NOT rates.

Scoring (engine-side, derived from answers):
    No Workflow Issues          -> workflow_score: 90
    Minor Workflow Issues       -> workflow_score: 70
    Major Workflow Issues       -> workflow_score: 40
"""
from __future__ import annotations
from universal.contracts.discovery import DiscoveryQuestion


TAGS = ("workflow_discovery", "v1", "merchant_services")


WORKFLOW_QUESTIONS: list[DiscoveryQuestion] = [
    DiscoveryQuestion(
        id="WF_Q1",
        objective="Understand payment flow",
        primary="Out of curiosity, how are customer payments typically handled today?",
        variations=(
            "How do customers usually pay you?",
            "Walk me through what happens when a customer is ready to make a payment.",
        ),
        capture_slots=("payment_channels",),
        captures_enum=("In Person", "Online", "Invoice", "Phone", "Recurring"),
        intent_delta=5,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q2",
        objective="Understand channels",
        primary="Are most payments happening in person, online, or through invoices?",
        variations=("What percentage would you say is card present versus remote payments?",),
        capture_slots=("payment_channel_mix",),
        captures_enum=("Card Present", "Card Not Present", "Invoice", "Mixed"),
        intent_delta=5,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q3",
        objective="Find manual processes",
        primary="Are there any parts of the payment process that take more staff time than you'd like?",
        variations=(
            "What part of collecting payments tends to be the biggest headache?",
            "If you could eliminate one payment-related task tomorrow, what would it be?",
        ),
        capture_slots=("manual_pain",),
        intent_delta=15,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q4",
        objective="Find invoicing opportunities",
        primary="Do you send invoices manually or is that process automated?",
        variations=("How are invoices typically generated today?",),
        capture_slots=("invoicing_mode",),
        captures_enum=("Manual", "Automated", "Mixed"),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q5",
        objective="Find collection issues",
        primary="How much time does your team spend following up on unpaid invoices?",
        variations=("Do customers generally pay right away or does follow-up become necessary?",),
        capture_slots=("collections_time",),
        intent_delta=20,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q6",
        objective="Discover payment friction",
        primary="Do customers ever call in payments over the phone?",
        variations=("How often are employees taking card numbers manually?",),
        capture_slots=("phone_payments",),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q7",
        objective="Discover recurring opportunities",
        primary="Do you have customers that pay you repeatedly?",
        variations=("Is recurring billing part of the business?",),
        capture_slots=("recurring_present",),
        intent_delta=10,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q8",
        objective="Identify software stack",
        primary="What systems are you currently using to manage payments and invoicing?",
        variations=("What software does your team spend the most time in each day?",),
        capture_slots=("software_stack",),
        captures_enum=("QuickBooks", "Shopify", "Toast", "Clover", "Square", "ServiceTitan", "Housecall Pro", "Other"),
        intent_delta=5,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q9",
        objective="Identify integration gaps",
        primary="Do those systems communicate with each other automatically, or is there still some manual work involved?",
        variations=("Are people still moving information from one system into another?",),
        capture_slots=("integration_gaps",),
        intent_delta=15,
        playbook_tags=TAGS,
    ),
    DiscoveryQuestion(
        id="WF_Q10",
        objective="Future-state question (the magic question)",
        primary="If you could improve one thing about the payment process tomorrow, what would it be?",
        variations=("What's one thing you'd love to stop dealing with?",),
        capture_slots=("future_state_wish",),
        intent_delta=20,
        playbook_tags=TAGS,
    ),
]
