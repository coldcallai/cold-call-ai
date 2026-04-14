"""
Generate and cache the full Agency Outbound Demo Audio.
Run this ONCE when ElevenLabs credits are available.
Generates audio for each state of the agency pitch and caches to disk.

Usage: cd /app/backend && python scripts/generate_agency_demo_audio.py
"""

import os
import sys
import json
import time
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent / '.env')

ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
CACHE_DIR = Path(__file__).parent.parent / 'agency_audio_cache'
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel
MODEL_ID = "eleven_flash_v2"

# All audio segments for the agency pitch
SEGMENTS = {
    "opening": "Hey — this is Sarah from DialGenix. Quick one — am I speaking with someone who handles lead generation or outbound for your sales team?",
    
    "what_is_this": "I'll keep it simple — we built an AI system that reaches out to businesses actively looking for services like yours and turns them into booked meetings or live transfers. You're actually experiencing it right now — this call is being made by it.",
    
    "experience_loop_1": "The reason I'm calling is simple — instead of explaining how it works, we let you experience it directly.",
    
    "experience_loop_2": "You're hearing the same system sales teams use to book qualified meetings automatically.",
    
    "experience_loop_3": "Most people only have one question after this — does it actually work for my sales team?",
    
    "qualifying_1": "How are you currently handling outbound or lead generation right now?",
    
    "qualifying_2": "Got it — so the real bottleneck is usually either volume, cost, or consistency. Which one hits you hardest right now?",
    
    "value_drop_1": "That's exactly what this solves.",
    
    "value_drop_2": "It doesn't replace your sales team — it removes the manual outreach layer and only delivers qualified, high-intent conversations your team can actually close.",
    
    "value_drop_3": "So instead of your team spending time chasing leads, they only speak to people already showing intent, already in conversation, and already partially qualified.",
    
    "obj_too_good": "Totally fair — that's why we don't rely on explanation. You're already interacting with it. The system proves itself in real time, not in theory.",
    
    "obj_have_sdrs": "Perfect — this doesn't replace them, it feeds them better conversations at higher intent.",
    
    "obj_legal": "Yes — TCPA, DNC, call windows, and full audit logging are built in. It operates like a compliant outbound team, just automated.",
    
    "obj_robotic": "No — it uses natural voice models and adapts tone based on how the conversation is going. Most people don't realize it's AI until later.",
    
    "obj_cost": "Most sales teams start around $199 a month for the platform, plus you pay Twilio and ElevenLabs directly for usage — usually $100-150 total. Way less than one SDR.",
    
    "obj_send_info": "Absolutely. But honestly, you're getting more from this 2-minute call than any email could give you. What if I just get you set up on a test run this week so you can see real results?",
    
    "obj_not_right_time": "Totally understand. Quick question though — is it timing, or is there something specific holding you back? Because most sales teams that say later end up watching competitors adopt it first.",
    
    "close_transition_1": "So based on what you've seen — the question isn't really whether it works.",
    
    "close_transition_2": "It's whether you want to start using it to generate and qualify pipeline for your sales team right now, or later once others in your space adopt it first.",
    
    "close_1": "Does it make sense to get you set up on a starter plan so we can start delivering qualified conversations and booked meetings this week?",
    
    "close_2": "If it fits, we scale it. If not, you've at least seen exactly how it performs in real conditions.",
    
    "close_yes": "Great — I'll have someone reach out in the next hour to get you onboarded. What email works best for you?",
    
    "close_maybe": "No pressure. Most sales teams start with a small test — light volume, prove conversion, then scale. Want to start there?",
    
    "close_no": "No problem at all. When the time is right, you'll know where to find us. Have a great day!",
    
    "wrong_person": "No worries — who would be the right person to chat with about your outbound strategy?"
}


def generate_audio(text, cache_key):
    """Generate audio via ElevenLabs and save to disk."""
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.75,
                "style": 0.35
            }
        },
        timeout=30
    )
    
    if response.status_code == 200:
        # Save as MP3
        mp3_path = CACHE_DIR / f"{cache_key}.mp3"
        with open(mp3_path, "wb") as f:
            f.write(response.content)
        
        # Save as base64 data URI for Twilio
        b64_path = CACHE_DIR / f"{cache_key}.b64"
        audio_b64 = base64.b64encode(response.content).decode('utf-8')
        with open(b64_path, "w") as f:
            f.write(f"data:audio/mpeg;base64,{audio_b64}")
        
        return True
    else:
        print(f"  ERROR: Status {response.status_code} - {response.text[:200]}")
        return False


def main():
    if not ELEVENLABS_API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set in .env")
        sys.exit(1)
    
    CACHE_DIR.mkdir(exist_ok=True)
    
    total = len(SEGMENTS)
    success = 0
    failed = 0
    
    print(f"Generating {total} audio segments for Agency Campaign...")
    print(f"Voice: Rachel ({VOICE_ID})")
    print(f"Model: {MODEL_ID}")
    print(f"Cache: {CACHE_DIR}")
    print("-" * 50)
    
    for i, (key, text) in enumerate(SEGMENTS.items(), 1):
        # Skip if already cached
        if (CACHE_DIR / f"{key}.mp3").exists():
            print(f"  [{i}/{total}] {key} - CACHED (skipping)")
            success += 1
            continue
        
        print(f"  [{i}/{total}] {key} - generating...", end=" ")
        if generate_audio(text, key):
            print("OK")
            success += 1
        else:
            print("FAILED")
            failed += 1
        
        # Rate limit - 0.5s between calls
        time.sleep(0.5)
    
    print("-" * 50)
    print(f"Done: {success} success, {failed} failed")
    print(f"Files saved to: {CACHE_DIR}")
    
    # Estimate credits used
    total_chars = sum(len(t) for t in SEGMENTS.values())
    print(f"Total characters: {total_chars} (~{total_chars} credits on Flash)")


if __name__ == "__main__":
    main()
