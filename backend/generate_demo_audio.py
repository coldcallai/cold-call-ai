"""
Generate static demo narration audio files using OpenAI TTS.
These files will be served directly without needing ElevenLabs API calls.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load env from specific path
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.openai import OpenAITextToSpeech

DEMO_NARRATIONS = {
    "step1": {
        "title": "Visual Sales Funnel",
        "text": "Welcome to DialGenix. Your visual sales funnel shows every lead's journey - from discovery to booked meeting. Track real-time stats on qualification rates, calls made, and bookings. Just click 'Call' to let AI do the heavy lifting.",
        "voice": "nova"  # Energetic, upbeat - good for welcome
    },
    "step2": {
        "title": "AI Lead Discovery",
        "text": "Finding leads is easy. Enter your target keywords - like 'Toast alternative' or 'payment processing' - and our AI finds businesses actively searching for solutions like yours. You can also upload your own CSV with existing leads.",
        "voice": "alloy"  # Neutral, balanced - good for explanation
    },
    "step3": {
        "title": "Call Recordings & Results",
        "text": "After each call, review the full recording and AI-generated transcript. See qualification scores to know which leads are hot. Your AI agent handles objections, qualifies prospects, and books meetings - all automatically.",
        "voice": "shimmer"  # Bright, cheerful - good for showcasing results
    }
}

OUTPUT_DIR = "/app/frontend/public/audio"

async def generate_audio_files():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY not found in environment")
        return
    
    print(f"Using API key: {api_key[:20]}...")
    
    tts = OpenAITextToSpeech(api_key=api_key)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for step_id, narration in DEMO_NARRATIONS.items():
        print(f"\nGenerating {step_id}: {narration['title']}...")
        print(f"  Voice: {narration['voice']}")
        print(f"  Text length: {len(narration['text'])} chars")
        
        try:
            audio_bytes = await tts.generate_speech(
                text=narration['text'],
                model="tts-1-hd",  # High quality for homepage demo
                voice=narration['voice'],
                response_format="mp3"
            )
            
            output_path = os.path.join(OUTPUT_DIR, f"demo_{step_id}.mp3")
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            
            file_size = os.path.getsize(output_path)
            print(f"  ✓ Saved: {output_path} ({file_size:,} bytes)")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(generate_audio_files())
    print("\n✓ Done! Audio files generated in", OUTPUT_DIR)
