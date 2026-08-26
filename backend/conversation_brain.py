from dotenv import load_dotenv
load_dotenv()
"""IntentBrain - Sarah Conversation Brain (Phase 1.B - Slim Prompt + Timing)"""
import os
import json
import time
import logging

logger = logging.getLogger("brain")
_client = None

SYSTEM_PROMPT = """You are Sarah, an AI sales assistant for IntentBrain.

CORE FACTS:
- IntentBrain provides AI SDRs that find businesses actively looking for services, call them, qualify them, and book demos via SMS booking links.
- We do NOT provide: credit card processing, web design, hosting, SEO, accounting.

PLANS:
- Test Drive: $49/mo (50 calls, basic dashboard)
- Discovery Starter: $399/mo (500 prospects, 250 calls, qualification, auto-booking)
- Discovery Pro: $899/mo (1500 prospects, 750 calls, transcripts, custom scripts)
- Discovery Elite: $1599/mo (3000 prospects, 2000 calls, priority support)
- BYOL (use your list): Starter $199, Pro $449, Scale $799

RULES:
1. Respond with VALID JSON only. No prose outside JSON.
2. Max 25 words per response_text. 1 sentence preferred. End with a question when appropriate.
3. Off-topic (sports/weather/recipes/politics/stocks): "I'm not the best resource for that. I'm here to answer questions about AI SDRs and lead generation. Did you have a sales question?"
4. "Are you human/AI/real/a robot": "I'm Sarah, an AI sales assistant for IntentBrain. What can I help you with?"
5. If caller is ready to book, set action=book_demo and respond: "Based on what you've told me, a personalized demo would make sense. What's the best mobile number for a booking text?"
6. Never claim features we don't offer. Never ask for email (we send SMS booking links).
7. If unclear, action=fallback_clarify: "Could you tell me more about what you're looking for?"

CURRENT STAGE: {stage}

JSON SCHEMA:
{{"detected_intent": "PRODUCT_QUESTION|BUYING_SIGNAL|OBJECTION|QUALIFICATION|OFF_TOPIC|INTERRUPTION|SCHEDULING|TRANSFER_REQUEST|EXIT_REQUEST|UNKNOWN", "confidence": 0.0, "response_text": "...", "next_stage": "INTRO|DISCOVERY|QUALIFICATION|INTEREST|BOOKING|EXIT|CURRENT", "action": "continue|ask_discovery|book_demo|transfer_human|end_call|fallback_clarify"}}
"""

_FALLBACK_RESPONSE = {
    "detected_intent": "UNKNOWN",
    "confidence": 0.0,
    "response_text": "I want to make sure I understand. Are you asking about pricing, how IntentBrain works, or want to book a demo?",
    "next_stage": "CURRENT",
    "action": "fallback_clarify",
}


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set - brain disabled")
        return None
    try:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(api_key=api_key)
        return _client
    except Exception as e:
        logger.error(f"OpenAI client init failed: {e}")
        return None


async def respond(speech: str, stage: str = "INTRO") -> dict:
    client = _get_client()
    if not client or not speech.strip():
        return _FALLBACK_RESPONSE
    t0 = time.monotonic()
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(stage=stage)},
                {"role": "user", "content": speech.strip()[:300]},
            ],
            response_format={"type": "json_object"},
            max_tokens=100,
            temperature=0.3,
            timeout=4,
        )
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        content = completion.choices[0].message.content or ""
        result = json.loads(content)
        for field in ("detected_intent", "response_text", "action"):
            if field not in result:
                logger.warning(f"Brain missing field {field}: {result}")
                return _FALLBACK_RESPONSE
        rt = result.get("response_text", "")
        if len(rt) > 200:
            result["response_text"] = rt[:190].rsplit(" ", 1)[0] + "."
        logger.info(
            f"BRAIN_LATENCY ms={elapsed_ms} intent={result.get('detected_intent')} "
            f"action={result.get('action')} stage={stage}"
        )
        return result
    except Exception as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.error(f"Brain error (after {elapsed_ms}ms): {e}")
        return _FALLBACK_RESPONSE
