"""MerchantBrain — Gatekeeper Library V1.

15 triggers authored by founder. Schema: Trigger -> Objective -> Variations.

CONVENTION (Gatekeeper-specific):
  next_state values may use sub-objective markers more granular than
  the top-level ConversationState stages. The orchestrator maps these:
      DECISION_MAKER_DISCOVERY      -> stage=DISCOVERY (with objective tag)
      CALLBACK_DISCOVERY            -> stage=DISCOVERY (then CALLBACK_SCHEDULED)
      CONTACT_DISCOVERY             -> stage=DISCOVERY
      ALTERNATIVE_CONTACT_DISCOVERY -> stage=DISCOVERY
      AUTHORITY_DISCOVERY           -> stage=DISCOVERY
      PREVIOUS_OBJECTIVE            -> retain current stage (no transition)

Agent identity ("Sarah" / "ABC Merchant Solutions") is hard-coded in V1 per
founder's authoring. Phase 3 (Account Customization) will swap these for
{agent_name} / {company_name} placeholders so the same playbook serves
multiple ISO/agent accounts.

Score philosophy (PRD §Gatekeeper Success Score):
    - Decision-maker name obtained on next turn: +15
    - Direct extension: +25
    - Email: +15
    - Best callback time: +10
    - Transferred to DM: +50
    - Hard block: -20
The intent_delta on each Objective below represents the value of *pursuing*
that objective in this turn; the next caller turn determines if intel was
actually captured (and additional score is applied then).
"""
from __future__ import annotations
from universal.contracts.trigger import Trigger, Objective


TAGS = ("gatekeeper", "v1", "merchant_services")


GATEKEEPER_TRIGGERS: list[Trigger] = [
    Trigger(
        id="GK_WHATS_THIS_REGARDING",
        matches=(
            "what's this regarding",
            "whats this regarding",
            "what's this about",
            "whats this about",
            "what is this regarding",
            "what is this about",
            "what's it regarding",
        ),
        possible_meanings=("SCREENING", "INFORMATION_REQUEST"),
        playbook_tags=TAGS,
        objectives={
            "DECISION_MAKER_DISCOVERY": Objective(
                name="DECISION_MAKER_DISCOVERY",
                intent_delta=15,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "It's regarding payment processing and a couple of workflow questions. I wasn't sure if that would be the owner or office manager.",
                    "Just a quick question about how customer payments are handled there.",
                    "I'm trying to determine who oversees payment processing for the business.",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_ALREADY_HAVE_PROCESSOR",
        matches=(
            "already have a processor",
            "we have a processor",
            "use a processor",
            "got a processor",
        ),
        possible_meanings=("GENUINE_INCUMBENT", "BRUSH_OFF", "SCREENING"),
        playbook_tags=TAGS,
        objectives={
            "DECISION_MAKER_DISCOVERY": Objective(
                name="DECISION_MAKER_DISCOVERY",
                intent_delta=15,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "That makes sense. Who typically oversees that relationship?",
                    "Got it. Is that something the owner handles personally?",
                    "Who usually evaluates those options when they come up?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_HANDLE_INTERNALLY",
        matches=("handle that internally", "do it internally", "in-house", "in house"),
        possible_meanings=("INTERNAL_MANAGEMENT",),
        playbook_tags=TAGS,
        objectives={
            "DECISION_MAKER_DISCOVERY": Objective(
                name="DECISION_MAKER_DISCOVERY",
                intent_delta=15,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "That makes sense. Out of curiosity, who oversees that internally?",
                    "Is that something the owner handles personally?",
                    "Who typically evaluates that side of the business?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_OWNER_NOT_AVAILABLE",
        matches=(
            "owner isn't available",
            "owner is not available",
            "owner not available",
            "owner isn't here",
            "owner is not here",
            "owner's not in",
            "owner's not here",
            "they're not available",
            "they are not available",
        ),
        possible_meanings=("OWNER_UNAVAILABLE",),
        playbook_tags=TAGS,
        objectives={
            "CALLBACK_DISCOVERY": Objective(
                name="CALLBACK_DISCOVERY",
                intent_delta=10,
                next_state="CALLBACK_DISCOVERY",
                variations=(
                    "No problem. When is usually the best time to catch them?",
                    "Understood. What time gives me the best chance of reaching them?",
                    "I'd be happy to call back. What's normally the easiest time to reach them?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_CAN_I_TAKE_A_MESSAGE",
        matches=("take a message", "leave a message", "want to leave a message"),
        possible_meanings=("SCREENING", "DEFLECTION"),
        playbook_tags=TAGS,
        objectives={
            "DECISION_MAKER_DISCOVERY": Objective(
                name="DECISION_MAKER_DISCOVERY",
                intent_delta=15,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "Possibly. Before I leave one, who normally handles payment processing?",
                    "Sure. Who should I direct the message to?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_JUST_SEND_AN_EMAIL",
        matches=(
            "just send an email",
            "send us an email",
            "send me an email",
            "send an email",
            "email us",
            "email me",
        ),
        possible_meanings=("SEND_EMAIL_DEFLECTION",),
        playbook_tags=TAGS,
        objectives={
            "CONTACT_DISCOVERY": Objective(
                name="CONTACT_DISCOVERY",
                intent_delta=15,
                next_state="CONTACT_DISCOVERY",
                variations=(
                    "Happy to. Who would be the best person to send it to?",
                    "Absolutely. Who oversees that area for the business?",
                    "I'd rather make sure it reaches the right person. Who should I address it to?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_IS_THIS_A_SALES_CALL",
        matches=("is this a sales call", "are you selling", "this a sales call", "sales call"),
        possible_meanings=("RESISTANCE", "SCREENING"),
        playbook_tags=TAGS,
        objectives={
            "REDUCE_RESISTANCE": Objective(
                name="REDUCE_RESISTANCE",
                intent_delta=5,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "Potentially, if there's a reason to continue the conversation. Right now I'm just trying to determine who handles payment processing.",
                    "At this point I'm simply trying to identify the right person to speak with.",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_NO_SALES_CALLS",
        matches=(
            "don't take sales calls",
            "do not take sales calls",
            "no sales calls",
            "no cold calls",
            "no soliciting",
        ),
        possible_meanings=("NO_COLD_CALLS_POLICY",),
        playbook_tags=TAGS,
        objectives={
            "ALTERNATIVE_CONTACT_DISCOVERY": Objective(
                name="ALTERNATIVE_CONTACT_DISCOVERY",
                intent_delta=10,
                next_state="ALTERNATIVE_CONTACT_DISCOVERY",
                variations=(
                    "I understand. That's actually why I wanted to make sure I had the right person.",
                    "Makes sense. Who normally evaluates that area when questions come up?",
                    "Understood. Is there a better way to get a question in front of them?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_CALL_BACK_LATER",
        matches=(
            "call back later",
            "try back later",
            "try again later",
            "call us back",
            "call them back",
        ),
        possible_meanings=("CALL_BACK_LATER",),
        playbook_tags=TAGS,
        objectives={
            "CALLBACK_DISCOVERY": Objective(
                name="CALLBACK_DISCOVERY",
                intent_delta=10,
                next_state="CALLBACK_DISCOVERY",
                variations=(
                    "Absolutely. What time works best?",
                    "Happy to. What usually gives me the best chance of reaching them?",
                    "Sure. Is there a particular day that's easier?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_HAPPY_WITH_PROCESSOR",
        matches=(
            "happy with our processor",
            "we're happy with our processor",
            "we are happy with our processor",
            "happy with the processor",
        ),
        possible_meanings=("SATISFIED_INCUMBENT", "BRUSH_OFF"),
        playbook_tags=TAGS,
        objectives={
            "DECISION_MAKER_DISCOVERY": Objective(
                name="DECISION_MAKER_DISCOVERY",
                intent_delta=15,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "That's great. Who typically oversees that relationship?",
                    "Most businesses I speak with are happy with their processor. Who handles those decisions there?",
                    "That's good to hear. Has that arrangement been working the way you'd hoped?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_WHO_ARE_YOU",
        matches=("who are you", "who's calling", "who is this", "who's this"),
        possible_meanings=("IDENTITY_CHECK",),
        playbook_tags=TAGS,
        objectives={
            # Phase 3 (Account layer) will replace literal "Sarah" / "ABC Merchant Solutions"
            # with {agent_name} / {company_name} template placeholders.
            "IDENTIFY_AND_CONTINUE": Objective(
                name="IDENTIFY_AND_CONTINUE",
                intent_delta=0,
                next_state="PREVIOUS_OBJECTIVE",
                variations=(
                    "This is Sarah with ABC Merchant Solutions.",
                    "Sarah calling on behalf of ABC Merchant Solutions.",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_WHO_REFERRED_YOU",
        matches=("who referred you", "who gave you our", "where'd you get our", "where did you get our"),
        possible_meanings=("REFERRAL_CHECK",),
        playbook_tags=TAGS,
        objectives={
            "STAY_NEUTRAL": Objective(
                name="STAY_NEUTRAL",
                intent_delta=0,
                next_state="PREVIOUS_OBJECTIVE",
                variations=(
                    "Nobody specifically. We work with businesses in the area and your company came up during our research.",
                    "No direct referral. We were reviewing local businesses and your company came up.",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_TOO_BUSY",
        matches=("too busy", "we're too busy", "we are too busy", "really busy"),
        possible_meanings=("TIME_PROTECTION",),
        playbook_tags=TAGS,
        objectives={
            "CALLBACK_DISCOVERY": Objective(
                name="CALLBACK_DISCOVERY",
                intent_delta=10,
                next_state="CALLBACK_DISCOVERY",
                variations=(
                    "I completely understand. When does it usually slow down a bit?",
                    "That's exactly why I don't want to waste anyone's time. Who would be best to speak with later?",
                    "Makes sense. Is there a better day to reach out?",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_WHAT_DO_YOU_WANT",
        matches=("what do you want", "what do you need", "what are you after"),
        possible_meanings=("CLARIFICATION_REQUEST",),
        playbook_tags=TAGS,
        objectives={
            "CLARIFY_PURPOSE": Objective(
                name="CLARIFY_PURPOSE",
                intent_delta=5,
                next_state="DECISION_MAKER_DISCOVERY",
                variations=(
                    "Fair question. I'm trying to determine who oversees payment processing.",
                    "I'm looking for the person responsible for payment processing decisions.",
                    "Just trying to identify the right person for a quick question.",
                ),
            ),
        },
    ),
    Trigger(
        id="GK_NOT_INTERESTED",
        matches=("not interested", "no interest", "we're set", "we're good"),
        possible_meanings=("BRUSH_OFF", "GENUINE_NO_INTEREST"),
        playbook_tags=TAGS,
        objectives={
            "AUTHORITY_DISCOVERY": Objective(
                name="AUTHORITY_DISCOVERY",
                intent_delta=15,
                next_state="AUTHORITY_DISCOVERY",
                variations=(
                    "Understood. Before I update my notes, are you the person who handles payment processing decisions?",
                    "No problem. Has anyone reviewed that area of the business recently?",
                ),
            ),
        },
    ),
]


# Flag stays here for backwards-compatibility with the deletion test that
# checked GATEKEEPER_STATUS. Now reports SHIPPED.
GATEKEEPER_STATUS = "V1_SHIPPED"
