#!/usr/bin/env python3
"""
IntentBrain Dental Demo Audio Generator - Two Voice Version
Generates sample dental receptionist call recordings with separate voices for AI and Patient
"""

import os
import asyncio
import aiohttp
from datetime import datetime
import subprocess

# ElevenLabs config
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Voice IDs - using two distinct voices
AI_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - female, professional (AI Receptionist)
PATIENT_VOICE_ID = "TxGEqnHWrfWFTfGW9XjX"  # Josh - male, natural (Patient)

OUTPUT_DIR = "/app/frontend/public/audio/dental-demos"
TEMP_DIR = "/tmp/dental-audio-temp"

# Dental demo conversations - each line tagged with speaker
DENTAL_DEMOS = {
    "dental_new_patient": {
        "name": "New Patient Booking",
        "filename": "dental-new-patient-booking.mp3",
        "description": "AI handles a new patient scheduling a first appointment",
        "conversation": [
            {"speaker": "AI", "text": "Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?"},
            {"speaker": "PATIENT", "text": "I'm looking to schedule an appointment. I've never been to your office before."},
            {"speaker": "AI", "text": "Welcome! We'd love to have you as a new patient. For your first visit, we typically schedule a comprehensive exam and cleaning which takes about 90 minutes. This lets Dr. Johnson get to know your dental history and create a personalized care plan. Do you have a preference for morning or afternoon?"},
            {"speaker": "PATIENT", "text": "Morning would be better for me."},
            {"speaker": "AI", "text": "Perfect. I have availability this Thursday at 9 AM or next Monday at 10 AM. Which works better for you?"},
            {"speaker": "PATIENT", "text": "Thursday at 9 works great."},
            {"speaker": "AI", "text": "Wonderful! I've got you down for Thursday at 9 AM with Dr. Johnson. Can I get your name and a phone number where we can reach you?"},
            {"speaker": "PATIENT", "text": "It's Michael Thompson. 555-0123."},
            {"speaker": "AI", "text": "Thank you, Michael. You'll receive a confirmation text shortly with all the details and some new patient forms you can fill out ahead of time. Is there anything else I can help you with today?"},
            {"speaker": "PATIENT", "text": "No, that's everything. Thank you!"},
            {"speaker": "AI", "text": "You're welcome! We look forward to seeing you Thursday. Have a great day!"},
        ]
    },
    
    "dental_emergency": {
        "name": "Emergency Toothache",
        "filename": "dental-emergency-call.mp3",
        "description": "AI handles an urgent dental emergency with empathy",
        "conversation": [
            {"speaker": "AI", "text": "Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?"},
            {"speaker": "PATIENT", "text": "Hi, I have a really bad toothache. It's been killing me since last night."},
            {"speaker": "AI", "text": "I'm so sorry to hear you're in pain. We take dental emergencies seriously and want to get you feeling better as soon as possible. Can you tell me a bit more about the pain? Is it constant, or does it come and go?"},
            {"speaker": "PATIENT", "text": "It's pretty constant, and it gets worse when I drink anything cold."},
            {"speaker": "AI", "text": "That sounds really uncomfortable. Sensitivity to cold along with constant pain could indicate a few things, and Dr. Johnson will want to take a look right away. Let me check our schedule for the earliest available time today."},
            {"speaker": "PATIENT", "text": "Yes, please. I really need to get this looked at."},
            {"speaker": "AI", "text": "Great news - we had a cancellation and I can get you in at 2:30 this afternoon. That's in about 3 hours. Can you make that work?"},
            {"speaker": "PATIENT", "text": "Yes, absolutely. I'll be there."},
            {"speaker": "AI", "text": "Perfect. I've got you down for 2:30 PM as an emergency appointment. In the meantime, you can take over-the-counter pain medication like ibuprofen if you haven't already. Can I get your name and phone number?"},
            {"speaker": "PATIENT", "text": "It's David Martinez, 555-0456."},
            {"speaker": "AI", "text": "Thank you, David. We'll see you at 2:30. If the pain becomes unbearable before then, please call us back immediately. Hang in there!"},
        ]
    },
    
    "dental_insurance": {
        "name": "Insurance Question",
        "filename": "dental-insurance-question.mp3",
        "description": "AI handles insurance verification question",
        "conversation": [
            {"speaker": "AI", "text": "Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?"},
            {"speaker": "PATIENT", "text": "Hi, I was wondering if you accept Delta Dental insurance?"},
            {"speaker": "AI", "text": "Great question! Yes, we do work with Delta Dental. We actually accept most major insurance providers including Delta Dental, Cigna, MetLife, Aetna, and many others. To give you the most accurate information about your specific coverage, I'd be happy to verify your benefits before your appointment. Would you like me to do that?"},
            {"speaker": "PATIENT", "text": "Yes, that would be helpful."},
            {"speaker": "AI", "text": "Perfect. I'll just need a few details. Can I get your name as it appears on the insurance card?"},
            {"speaker": "PATIENT", "text": "It's Robert Chen."},
            {"speaker": "AI", "text": "And your Delta Dental member ID number?"},
            {"speaker": "PATIENT", "text": "It's 1 2 3 4 5 6 7 8 9."},
            {"speaker": "AI", "text": "Got it. And what's the best phone number to reach you?"},
            {"speaker": "PATIENT", "text": "555-0789."},
            {"speaker": "AI", "text": "Thank you, Robert. I'll verify your benefits and give you a call back within the next business day to let you know exactly what's covered. While I have you, would you like to go ahead and schedule an appointment?"},
            {"speaker": "PATIENT", "text": "Sure, that makes sense."},
            {"speaker": "AI", "text": "Wonderful! What works better for you, mornings or afternoons?"},
        ]
    },
    
    "dental_anxious": {
        "name": "Anxious Patient",
        "filename": "dental-anxious-patient.mp3", 
        "description": "AI handles a nervous patient with extra care",
        "conversation": [
            {"speaker": "AI", "text": "Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?"},
            {"speaker": "PATIENT", "text": "Hi, um, I need to make an appointment, but I have to be honest, I'm really nervous about going to the dentist. It's been a few years."},
            {"speaker": "AI", "text": "I completely understand, and I want you to know you're definitely not alone. Dental anxiety is really common, and our team is wonderful with patients who feel nervous. First of all, thank you for taking this step - I know it's not easy."},
            {"speaker": "PATIENT", "text": "Thanks. I just get really anxious about it."},
            {"speaker": "AI", "text": "That makes total sense. Dr. Johnson and our hygienists are trained to go at your pace. We also have several comfort options available. We offer nitrous oxide, sometimes called laughing gas, which helps you feel relaxed. We also have noise-canceling headphones if the sounds bother you, and we can take breaks anytime you need them."},
            {"speaker": "PATIENT", "text": "That actually makes me feel a bit better."},
            {"speaker": "AI", "text": "I'm glad! We also like to have a quick chat before we start anything, so you know exactly what to expect. No surprises. Would you like me to make a note on your file so the whole team knows to take extra care with you?"},
            {"speaker": "PATIENT", "text": "Yes, please. That would be really helpful."},
            {"speaker": "AI", "text": "Absolutely. I'll make sure everyone knows. Now, let's find a time that works for you. Would you prefer a morning appointment when things are quieter, or afternoon?"},
            {"speaker": "PATIENT", "text": "Morning, I think."},
            {"speaker": "AI", "text": "Perfect. How about next Tuesday at 8 AM? You'd be one of our first patients so it's nice and calm."},
            {"speaker": "PATIENT", "text": "That sounds good. Thank you for being so understanding."},
            {"speaker": "AI", "text": "Of course! That's what we're here for. We'll see you Tuesday, and remember, we're going to take great care of you."},
        ]
    },

    "dental_whitening": {
        "name": "Cosmetic Inquiry",
        "filename": "dental-whitening-inquiry.mp3",
        "description": "AI handles teeth whitening question",
        "conversation": [
            {"speaker": "AI", "text": "Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?"},
            {"speaker": "PATIENT", "text": "Hi, I'm interested in teeth whitening. Do you offer that?"},
            {"speaker": "AI", "text": "Yes, we do! We actually offer a couple of different options depending on what works best for you. Our in-office whitening can brighten your smile up to 8 shades in about an hour - that's perfect if you have an event coming up. We also have professional take-home kits that work more gradually over a couple of weeks but are very effective."},
            {"speaker": "PATIENT", "text": "What's the difference in cost?"},
            {"speaker": "AI", "text": "Great question. The in-office treatment runs about $400, and the take-home kits start at $250. Many patients actually love combining whitening with their regular cleaning appointment - you come in, get your teeth cleaned, and leave with a noticeably brighter smile."},
            {"speaker": "PATIENT", "text": "Oh, that's a good idea."},
            {"speaker": "AI", "text": "Would you like to schedule a consultation? Dr. Johnson can take a look at your teeth and recommend the best option for you. There's no obligation - it's just a chance to discuss what results you're looking for."},
            {"speaker": "PATIENT", "text": "Sure, let's do that."},
            {"speaker": "AI", "text": "Wonderful! I have availability this Friday at 11 AM or next Wednesday at 3 PM. Which works better?"},
            {"speaker": "PATIENT", "text": "Friday at 11 works for me."},
            {"speaker": "AI", "text": "Perfect! I've got you down for Friday at 11 AM for a whitening consultation. Can I get your name?"},
            {"speaker": "PATIENT", "text": "It's Amanda Wilson."},
            {"speaker": "AI", "text": "Thank you, Amanda. You'll receive a confirmation shortly. We look forward to helping you get that brighter smile!"},
        ]
    }
}

async def generate_audio_segment(text: str, voice_id: str, output_path: str):
    """Generate a single audio segment using ElevenLabs API"""
    
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
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                audio_data = await response.read()
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                return True
            else:
                error = await response.text()
                print(f"   ❌ Error: {error}")
                return False

def concatenate_audio_files(input_files: list, output_path: str):
    """Concatenate multiple MP3 files into one using ffmpeg"""
    
    # Create a file list for ffmpeg
    list_file = os.path.join(TEMP_DIR, "filelist.txt")
    with open(list_file, 'w') as f:
        for audio_file in input_files:
            f.write(f"file '{audio_file}'\n")
    
    # Use ffmpeg to concatenate
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

async def generate_conversation(demo_id: str, demo: dict):
    """Generate a full conversation with two voices"""
    
    print(f"\n🎙️ Generating: {demo['name']}")
    print(f"   Description: {demo['description']}")
    print(f"   Lines: {len(demo['conversation'])}")
    
    # Create temp directory for segments
    demo_temp_dir = os.path.join(TEMP_DIR, demo_id)
    os.makedirs(demo_temp_dir, exist_ok=True)
    
    segment_files = []
    
    for i, line in enumerate(demo['conversation']):
        speaker = line['speaker']
        text = line['text']
        
        # Choose voice based on speaker
        voice_id = AI_VOICE_ID if speaker == "AI" else PATIENT_VOICE_ID
        voice_name = "Sarah (AI)" if speaker == "AI" else "Patient"
        
        segment_path = os.path.join(demo_temp_dir, f"segment_{i:03d}.mp3")
        
        print(f"   [{i+1}/{len(demo['conversation'])}] {voice_name}: {text[:40]}...")
        
        success = await generate_audio_segment(text, voice_id, segment_path)
        
        if success:
            segment_files.append(segment_path)
        else:
            print(f"   ❌ Failed to generate segment {i}")
            return False
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Concatenate all segments
    print(f"   🔗 Combining {len(segment_files)} segments...")
    
    output_path = os.path.join(OUTPUT_DIR, demo['filename'])
    
    if concatenate_audio_files(segment_files, output_path):
        size = os.path.getsize(output_path)
        print(f"   ✅ Generated: {output_path}")
        print(f"   📦 Size: {size / 1024:.1f} KB")
        return True
    else:
        print(f"   ❌ Failed to concatenate audio")
        return False

async def main():
    print("=" * 60)
    print("IntentBrain Dental Demo Audio Generator")
    print("Two-Voice Version (AI + Patient)")
    print("=" * 60)
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return
    
    print(f"\n🎤 AI Voice: Rachel (female, professional)")
    print(f"🎤 Patient Voice: Josh (male, natural)")
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    success_count = 0
    
    for demo_id, demo in DENTAL_DEMOS.items():
        if await generate_conversation(demo_id, demo):
            success_count += 1
        
        # Delay between conversations
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {success_count}/{len(DENTAL_DEMOS)} dental demo audio files!")
    print(f"📁 Files saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    # List generated files
    print("\n📋 Generated files:")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.mp3'):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"   • {f} ({size/1024:.1f} KB)")

if __name__ == "__main__":
    asyncio.run(main())
