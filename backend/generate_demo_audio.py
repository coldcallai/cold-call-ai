#!/usr/bin/env python3
"""
IntentBrain Demo Call Audio Generator
Generates sample call recordings for sales demos using ElevenLabs
"""

import os
import asyncio
import aiohttp
from datetime import datetime

# ElevenLabs config
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice

# Demo call scripts
DEMO_CALLS = {
    "d_type_call": {
        "name": "D-Type (Dominant) - Fast Buyer",
        "duration": "~25 seconds",
        "script": [
            {"speaker": "AI", "text": "Hi, this is Sarah calling from Acme Solutions. Do you have a quick moment?"},
            {"speaker": "PROSPECT", "text": "Yeah, but make it fast. I've got a meeting in 5."},
            {"speaker": "AI", "text": "Got it. I'll be direct. We help sales teams close 40% more deals by adapting to each buyer's style in real-time. Are you hitting your numbers this quarter or leaving money on the table?"},
            {"speaker": "PROSPECT", "text": "We're at about 85% of target."},
            {"speaker": "AI", "text": "That gap is exactly what we fix. I can get you a 15-minute walkthrough with a closer on our team. What's better, tomorrow at 2 or Thursday morning?"},
            {"speaker": "PROSPECT", "text": "Thursday works."},
            {"speaker": "AI", "text": "Perfect. You'll get a calendar invite in the next 2 minutes. Talk Thursday."},
        ]
    },
    "s_type_call": {
        "name": "S-Type (Steady) - Relationship Buyer", 
        "duration": "~30 seconds",
        "script": [
            {"speaker": "AI", "text": "Hi, this is Sarah with Acme. Hope I'm not catching you at a bad time?"},
            {"speaker": "PROSPECT", "text": "No, it's okay. What's this about?"},
            {"speaker": "AI", "text": "I appreciate you taking a moment. I know you're busy. We work with sales teams to help them connect better with different types of buyers. I'm not here to pitch you, just wanted to see if it's something worth exploring together."},
            {"speaker": "PROSPECT", "text": "Okay, what do you mean by different types?"},
            {"speaker": "AI", "text": "Great question. Some buyers want the facts fast. Others, like yourself, prefer to build a bit of trust first. Most sales reps miss that. We help them adapt. Would you be open to a quick call with someone on our team who can walk you through it? No pressure at all."},
            {"speaker": "PROSPECT", "text": "Sure, that sounds reasonable."},
            {"speaker": "AI", "text": "Wonderful. I'll send over a few time options. Looking forward to connecting you with our team."},
        ]
    },
    "vm_drop": {
        "name": "Voicemail Drop - Conversational",
        "duration": "~20 seconds", 
        "script": [
            {"speaker": "AI", "text": "Hi, this is Sarah with IntentBrain. I just wanted to raise my hand and let you know I'm out here. I focus on helping sales teams get more qualified leads and booked appointments. If you need help with live transfers or just want to bounce an idea, I'm happy to chat, whether you're a client or not. My number is 8 8 8, 5 1 3, 1 9 1 3. Talk soon."},
        ]
    }
}

async def generate_audio_elevenlabs(text: str, voice_id: str = VOICE_ID) -> bytes:
    """Generate audio using ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                return await response.read()
            else:
                error = await response.text()
                raise Exception(f"ElevenLabs error: {error}")

async def generate_demo_call(call_key: str, output_dir: str = "/app/frontend/public/demo-audio"):
    """Generate a complete demo call audio file"""
    
    if call_key not in DEMO_CALLS:
        print(f"Unknown call type: {call_key}")
        return
    
    call = DEMO_CALLS[call_key]
    print(f"\n🎙️ Generating: {call['name']}")
    print(f"   Duration: {call['duration']}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # For AI lines only (we'll generate AI voice, prospect lines are just for script)
    ai_lines = [item for item in call["script"] if item["speaker"] == "AI"]
    
    # Combine all AI lines with pauses
    full_script = " ... ".join([item["text"] for item in ai_lines])
    
    print(f"   Generating audio...")
    try:
        audio_data = await generate_audio_elevenlabs(full_script)
        
        output_path = f"{output_dir}/{call_key}.mp3"
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        print(f"   ✅ Saved: {output_path}")
        return output_path
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

async def generate_all_demos():
    """Generate all demo call audio files"""
    print("=" * 50)
    print("IntentBrain Demo Audio Generator")
    print("=" * 50)
    
    if not ELEVENLABS_API_KEY:
        print("\n❌ ERROR: ELEVENLABS_API_KEY not set")
        print("Please set your ElevenLabs API key in backend/.env")
        return
    
    results = []
    for call_key in DEMO_CALLS.keys():
        result = await generate_demo_call(call_key)
        results.append((call_key, result))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for call_key, path in results:
        status = "✅" if path else "❌"
        print(f"{status} {call_key}: {path or 'FAILED'}")
    
    print("\n📁 Audio files saved to: /app/frontend/public/demo-audio/")
    print("🌐 Access at: https://intentbrain.ai/demo-audio/d_type_call.mp3")

if __name__ == "__main__":
    asyncio.run(generate_all_demos())
