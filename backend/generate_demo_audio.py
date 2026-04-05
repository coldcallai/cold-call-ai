"""
Generate static demo narration audio files using ElevenLabs.
These files will be served directly without needing API calls.
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

DEMO_NARRATIONS = {
    "step1": {
        "title": "Visual Sales Funnel",
        "text": "Welcome to DialGenix. Your visual sales funnel shows every lead's journey - from discovery to booked meeting. Track real-time stats on qualification rates, calls made, and bookings. Just click 'Call' to let AI do the heavy lifting.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "voice_name": "Rachel"
    },
    "step2": {
        "title": "AI Lead Discovery",
        "text": "Finding leads is easy. Enter your target keywords - like 'Toast alternative' or 'payment processing' - and our AI finds businesses actively searching for solutions like yours. You can also upload your own CSV with existing leads.",
        "voice_id": "ErXwobaYiN019PkySvjV",  # Antoni
        "voice_name": "Antoni"
    },
    "step3": {
        "title": "Call Recordings & Results", 
        "text": "After each call, review the full recording and AI-generated transcript. See qualification scores to know which leads are hot. Your AI agent handles objections, qualifies prospects, and books meetings - all automatically.",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella
        "voice_name": "Bella"
    }
}

OUTPUT_DIR = "/app/frontend/public/audio"

async def generate_audio_files():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found")
        return False
    
    print(f"Using ElevenLabs API key: {api_key[:15]}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for step_id, narration in DEMO_NARRATIONS.items():
            print(f"\n🎙️ Generating {step_id}: {narration['title']}")
            print(f"   Voice: {narration['voice_name']} ({narration['voice_id']})")
            
            try:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{narration['voice_id']}",
                    headers={
                        "xi-api-key": api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": narration["text"],
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75
                        }
                    }
                )
                
                if response.status_code == 200:
                    output_path = os.path.join(OUTPUT_DIR, f"demo_{step_id}.mp3")
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    
                    file_size = os.path.getsize(output_path)
                    print(f"   ✅ Saved: {output_path} ({file_size:,} bytes)")
                else:
                    print(f"   ❌ Error {response.status_code}: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(generate_audio_files())
    if success:
        print("\n✅ All audio files generated successfully!")
        print(f"📁 Location: {OUTPUT_DIR}")
    else:
        print("\n❌ Failed to generate audio files")
