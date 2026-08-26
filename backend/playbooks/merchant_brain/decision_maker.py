"""MerchantBrain — Decision Maker Library V1.

Reactive triggers. The Decision Maker is on the line; intent of caller phrase
maps to one objective whose variations are rotated.
"""
from __future__ import annotations
from universal.contracts.trigger import Trigger, Objective


TAGS = ("decision_maker", "v1", "merchant_services")


DECISION_MAKER_TRIGGERS: list[Trigger] = [
    Trigger(
        id="DM_ALREADY_HAVE_PROCESSOR",
        matches=("already have a processor", "we have a processor", "use a processor"),
        possible_meanings=("GENUINE_INCUMBENT", "BRUSH_OFF"),
        playbook_tags=TAGS,
        objectives={
            "DISCOVER_RELATIONSHIP": Objective(
                name="DISCOVER_RELATIONSHIP",
                intent_delta=5,
                next_state="DISCOVERY",
                variations=(
                    "That makes sense. Most businesses do. Out of curiosity, what led you to choose them originally?",
                    "Got it. How long have you been with them?",
                    "What do you think they do particularly well?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_HAPPY_WITH_THEM",
        matches=("happy with them", "we're happy", "no complaints", "satisfied with"),
        possible_meanings=("SATISFIED", "HIDDEN_PAIN_POSSIBLE"),
        playbook_tags=TAGS,
        objectives={
            "IDENTIFY_HIDDEN_PAIN": Objective(
                name="IDENTIFY_HIDDEN_PAIN",
                intent_delta=5,
                next_state="DISCOVERY",
                variations=(
                    "That's great. What do you think has worked best about the relationship?",
                    "Glad to hear it. If you could improve one thing, what would it be?",
                    "What keeps you with them?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_NOT_INTERESTED",
        matches=("not interested", "no interest", "we're good", "we're set"),
        possible_meanings=("BRUSH_OFF", "GENUINE_NO_INTEREST"),
        playbook_tags=TAGS,
        objectives={
            "UNDERSTAND_REASON": Objective(
                name="UNDERSTAND_REASON",
                intent_delta=0,
                next_state="DISCOVERY",
                variations=(
                    "Understood. Is that because you're happy with what you're doing today, or just not something you're looking at right now?",
                    "Makes sense. What usually drives businesses like yours to review that area?",
                    "Has someone recently reviewed it with you?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_USE_CLOVER",
        matches=("use clover", "we have clover", "clover system"),
        possible_meanings=("INCUMBENT_CLOVER",),
        playbook_tags=TAGS,
        objectives={
            "DISCOVER_WORKFLOW": Objective(
                name="DISCOVER_WORKFLOW",
                intent_delta=10,
                next_state="DISCOVERY",
                variations=(
                    "How has Clover been working for you?",
                    "What do you like most about it?",
                    "Are you mainly using it for payments, or are you using the full system?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_USE_SQUARE",
        matches=("use square", "we have square", "square reader", "with square"),
        possible_meanings=("INCUMBENT_SQUARE",),
        playbook_tags=TAGS,
        objectives={
            "DISCOVER_WHY": Objective(
                name="DISCOVER_WHY",
                intent_delta=10,
                next_state="DISCOVERY",
                variations=(
                    "What made you choose Square originally?",
                    "How long have you been with them?",
                    "Has it continued to work the way you'd hoped?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_GET_GREAT_RATES",
        matches=("great rates", "good rates", "low rates", "best rate", "competitive rate"),
        possible_meanings=("RATE_DEFENSE",),
        playbook_tags=TAGS,
        objectives={
            "MOVE_BEYOND_RATES": Objective(
                name="MOVE_BEYOND_RATES",
                intent_delta=5,
                next_state="DISCOVERY",
                variations=(
                    "That's good to hear. Besides rates, what matters most to you in that relationship?",
                    "Makes sense. How often do you review that side of the business?",
                    "What else do you evaluate besides cost?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_SEND_INFO",
        matches=("send me information", "send me info", "email me", "send something over"),
        possible_meanings=("SCREENING", "GENUINE_INTEREST"),
        playbook_tags=TAGS,
        objectives={
            "CREATE_ENGAGEMENT": Objective(
                name="CREATE_ENGAGEMENT",
                intent_delta=5,
                next_state="DISCOVERY",
                variations=(
                    "Happy to. What specifically would be most relevant?",
                    "Absolutely. Before I send something, what are you most interested in?",
                    "I can do that. Just so I don't waste your time, what part of your current setup would you want to improve if anything?",
                ),
            ),
        },
    ),
    Trigger(
        id="DM_TOO_BUSY",
        matches=("too busy", "no time", "i'm busy", "can't talk", "in a meeting"),
        possible_meanings=("TIME_PROTECTION",),
        playbook_tags=TAGS,
        objectives={
            "SCHEDULE_LATER": Objective(
                name="SCHEDULE_LATER",
                intent_delta=10,
                next_state="CALLBACK_SCHEDULED",
                variations=(
                    "I completely understand. When does it usually slow down a bit?",
                    "Makes sense. Is there a better time to reconnect?",
                    "No problem. What would be the best day to reach you?",
                ),
            ),
        },
    ),
]
