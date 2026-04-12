#!/usr/bin/env python3
"""
DialGenix Dental Demo Audio Generator
Generates sample dental receptionist call recordings using ElevenLabs
"""

import os
import asyncio
import aiohttp
from datetime import datetime

# ElevenLabs config
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice

OUTPUT_DIR = "/app/frontend/public/audio/dental-demos"

# Dental demo call scripts
DENTAL_DEMOS = {
    "dental_new_patient": {
        "name": "New Patient Booking",
        "filename": "dental-new-patient-booking.mp3",
        "description": "AI handles a new patient scheduling a first appointment",
        "script": """Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?

I'm looking to schedule an appointment. I've never been to your office before.

Welcome! We'd love to have you as a new patient. For your first visit, we typically schedule a comprehensive exam and cleaning which takes about 90 minutes. This lets Dr. Johnson get to know your dental history and create a personalized care plan. Do you have a preference for morning or afternoon?

Morning would be better for me.

Perfect. I have availability this Thursday at 9 AM or next Monday at 10 AM. Which works better for you?

Thursday at 9 works great.

Wonderful! I've got you down for Thursday at 9 AM with Dr. Johnson. Can I get your name and a phone number where we can reach you?

It's Michael Thompson. 555-0123.

Thank you, Michael. You'll receive a confirmation text shortly with all the details and some new patient forms you can fill out ahead of time. Is there anything else I can help you with today?

No, that's everything. Thank you!

You're welcome! We look forward to seeing you Thursday. Have a great day!"""
    },
    
    "dental_emergency": {
        "name": "Emergency Toothache",
        "filename": "dental-emergency-call.mp3",
        "description": "AI handles an urgent dental emergency with empathy",
        "script": """Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?

Hi, I have a really bad toothache. It's been killing me since last night.

I'm so sorry to hear you're in pain. We take dental emergencies seriously and want to get you feeling better as soon as possible. Can you tell me a bit more about the pain? Is it constant, or does it come and go?

It's pretty constant, and it gets worse when I drink anything cold.

That sounds really uncomfortable. Sensitivity to cold along with constant pain could indicate a few things, and Dr. Johnson will want to take a look right away. Let me check our schedule for the earliest available time today. Can you hold for just a moment?

Yes, please.

Great news - we had a cancellation and I can get you in at 2:30 this afternoon. That's in about 3 hours. Can you make that work?

Yes, absolutely. I'll be there.

Perfect. I've got you down for 2:30 PM as an emergency appointment. In the meantime, you can take over-the-counter pain medication like ibuprofen if you haven't already, and try to avoid very hot or cold foods and drinks. Can I get your name and phone number?

Jennifer Walsh, 555-0456.

Thank you, Jennifer. We'll see you at 2:30. If the pain becomes unbearable before then, please call us back immediately. Hang in there!"""
    },
    
    "dental_insurance": {
        "name": "Insurance Question",
        "filename": "dental-insurance-question.mp3",
        "description": "AI handles insurance verification question",
        "script": """Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?

Hi, I was wondering if you accept Delta Dental insurance?

Great question! Yes, we do work with Delta Dental. We actually accept most major insurance providers including Delta Dental, Cigna, MetLife, Aetna, and many others. To give you the most accurate information about your specific coverage, I'd be happy to verify your benefits before your appointment. Would you like me to do that?

Yes, that would be helpful.

Perfect. I'll just need a few details. Can I get your name as it appears on the insurance card?

It's Robert Chen.

And your Delta Dental member ID number?

It's 123456789.

Got it. And what's the best phone number to reach you?

555-0789.

Thank you, Robert. I'll verify your benefits and give you a call back within the next business day to let you know exactly what's covered. While I have you, would you like to go ahead and schedule an appointment? That way we can have everything ready when you come in.

Sure, that makes sense.

Wonderful! What works better for you, mornings or afternoons?"""
    },
    
    "dental_anxious": {
        "name": "Anxious Patient",
        "filename": "dental-anxious-patient.mp3", 
        "description": "AI handles a nervous patient with extra care",
        "script": """Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?

Hi... um, I need to make an appointment, but I have to be honest, I'm really nervous about going to the dentist. It's been a few years.

I completely understand, and I want you to know you're definitely not alone. Dental anxiety is really common, and our team is wonderful with patients who feel nervous. First of all, thank you for taking this step - I know it's not easy.

Thanks... I just get really anxious.

That makes total sense. Dr. Johnson and our hygienists are trained to go at your pace. We also have several comfort options available. We offer nitrous oxide, sometimes called laughing gas, which helps you feel relaxed. We also have noise-canceling headphones if the sounds bother you, and we can take breaks anytime you need them.

That actually makes me feel a bit better.

I'm glad! We also like to have a quick chat before we start anything, so you know exactly what to expect. No surprises. Would you like me to make a note on your file so the whole team knows to take extra care with you?

Yes, please. That would be really helpful.

Absolutely. I'll make sure everyone knows. Now, let's find a time that works for you. Would you prefer a morning appointment when things are quieter, or afternoon?

Morning, I think.

Perfect. How about next Tuesday at 8 AM? You'd be one of our first patients so it's nice and calm.

That sounds good. Thank you for being so understanding.

Of course! That's what we're here for. We'll see you Tuesday, and remember, we're going to take great care of you."""
    },

    "dental_whitening": {
        "name": "Cosmetic Inquiry",
        "filename": "dental-whitening-inquiry.mp3",
        "description": "AI handles teeth whitening question",
        "script": """Hi, thank you for calling Smile Dental. This is Sarah, how can I help you today?

Hi, I'm interested in teeth whitening. Do you offer that?

Yes, we do! We actually offer a couple of different options depending on what works best for you. Our in-office whitening can brighten your smile up to 8 shades in about an hour - that's perfect if you have an event coming up. We also have professional take-home kits that work more gradually over a couple of weeks but are very effective.

What's the difference in cost?

Great question. The in-office treatment runs about $400, and the take-home kits start at $250. Many patients actually love combining whitening with their regular cleaning appointment - you come in, get your teeth cleaned, and leave with a noticeably brighter smile.

Oh, that's a good idea.

Would you like to schedule a consultation? Dr. Johnson can take a look at your teeth and recommend the best option for you. There's no obligation - it's just a chance to discuss what results you're looking for.

Sure, let's do that.

Wonderful! I have availability this Friday at 11 AM or next Wednesday at 3 PM. Which works better?"""
    }
}

async def generate_audio(text: str, output_path: str, voice_id: str = VOICE_ID):
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
                audio_data = await response.read()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                print(f"✅ Generated: {output_path}")
                return True
            else:
                error = await response.text()
                print(f"❌ Error generating audio: {error}")
                return False

async def main():
    print("=" * 60)
    print("DialGenix Dental Demo Audio Generator")
    print("=" * 60)
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return
    
    print(f"\nOutput directory: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for demo_id, demo in DENTAL_DEMOS.items():
        print(f"\n🎙️ Generating: {demo['name']}")
        print(f"   Description: {demo['description']}")
        
        output_path = os.path.join(OUTPUT_DIR, demo['filename'])
        
        success = await generate_audio(demo['script'], output_path)
        
        if success:
            # Get file size
            size = os.path.getsize(output_path)
            print(f"   Size: {size / 1024:.1f} KB")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("✅ All dental demo audio files generated!")
    print(f"📁 Files saved to: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
