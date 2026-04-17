#!/usr/bin/env python3
"""
IntentBrain Sales Demo Audio Generator - Two Voice Version
Generates sample sales call recordings showing IntentBrain AI in action
"""

import os
import asyncio
import aiohttp
import subprocess

# ElevenLabs config
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Voice IDs - using two distinct voices
AI_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - female, professional (Sarah - AI Sales Agent)
PROSPECT_VOICE_ID = "TxGEqnHWrfWFTfGW9XjX"  # Josh - male, natural (Business Owner)

OUTPUT_DIR = "/app/frontend/public/audio/sales-demos"
TEMP_DIR = "/tmp/sales-audio-temp"

# IntentBrain Sales Demo Conversations
SALES_DEMOS = {
    "sales_cold_call_interested": {
        "name": "Cold Call - Interested Prospect",
        "filename": "dialgenix-cold-call-interested.mp3",
        "description": "AI cold calls a business owner who's interested and books a demo",
        "conversation": [
            {"speaker": "AI", "text": "Hi, this is Sarah, AI agent with IntentBrain.ai. We help sales companies bring in more clients with booked meetings, live transfers, personality detection, and intent leads. Would you be open to a quick 15 minute demo to see how it works?"},
            {"speaker": "PROSPECT", "text": "AI agent? So you're not a real person?"},
            {"speaker": "AI", "text": "That's right! I'm an AI, and what you're hearing right now is exactly what your prospects would experience. I can have natural conversations, answer questions, handle objections, and book qualified meetings directly into your calendar. Pretty cool, right?"},
            {"speaker": "PROSPECT", "text": "Okay, that's actually impressive. How does this work exactly?"},
            {"speaker": "AI", "text": "Great question. We find businesses that are actively looking to buy using intent data, then I call them and have conversations just like this one. When someone's interested, I can either book them for a demo or transfer them live to your sales team. No more cold calling for your reps - they only talk to warm leads."},
            {"speaker": "PROSPECT", "text": "What do you mean by intent data?"},
            {"speaker": "AI", "text": "Intent leads are businesses showing buying signals - like searching for solutions you offer, visiting competitor websites, or engaging with relevant content. Instead of calling random lists, we call people who are already in the market. Way higher conversion rates."},
            {"speaker": "PROSPECT", "text": "That makes sense. What does something like this cost?"},
            {"speaker": "AI", "text": "Our plans start at $99 per month, and most clients see ROI within the first week. One booked meeting typically covers the entire monthly cost. Would you like to see a full demo? I can get you scheduled with one of our specialists who can walk you through everything and answer your specific questions."},
            {"speaker": "PROSPECT", "text": "Sure, let's do it."},
            {"speaker": "AI", "text": "Perfect! I have availability tomorrow at 2 PM or Thursday at 10 AM. Which works better for you?"},
            {"speaker": "PROSPECT", "text": "Thursday at 10 works."},
            {"speaker": "AI", "text": "Wonderful! I've got you down for Thursday at 10 AM. You'll receive a calendar invite shortly. Can I get your email to send that over?"},
            {"speaker": "PROSPECT", "text": "It's john at acme sales dot com."},
            {"speaker": "AI", "text": "Got it, john at acme sales dot com. You'll have that invite in the next few minutes. Looking forward to showing you what IntentBrain can do for your sales team. Have a great day!"},
        ]
    },
    
    "sales_objection_handling": {
        "name": "Objection Handling - Already Have Solution",
        "filename": "dialgenix-objection-handling.mp3",
        "description": "AI handles objections about existing solutions and competitors",
        "conversation": [
            {"speaker": "AI", "text": "Hi, this is Sarah, AI agent with IntentBrain.ai. We help sales companies bring in more clients with booked meetings and live transfers. Do you have a quick moment?"},
            {"speaker": "PROSPECT", "text": "We already use a dialer. Not really looking for anything new."},
            {"speaker": "AI", "text": "Totally understand. Out of curiosity, what are you using now? I ask because most dialers just help your team make more calls faster. We actually do the calling for you - your reps never touch the phone until someone's already qualified and interested."},
            {"speaker": "PROSPECT", "text": "Wait, so the AI does the actual cold calling?"},
            {"speaker": "AI", "text": "Exactly. I'm doing it right now! I have conversations just like this one, handle objections, answer questions, and when someone's interested, I either book a meeting or transfer them live to your team. Your sales reps only talk to warm, qualified leads."},
            {"speaker": "PROSPECT", "text": "How is that different from those robocalls that everyone hangs up on?"},
            {"speaker": "AI", "text": "Great question. Robocalls play pre-recorded messages. I'm having a real conversation with you - I can understand what you're saying, respond naturally, and adapt to the flow of the conversation. Plus, I detect personality types and adjust my communication style. If you're direct, I get to the point. If you want more details, I slow down and explain."},
            {"speaker": "PROSPECT", "text": "Hmm, that's interesting. But our team is pretty good at what they do."},
            {"speaker": "AI", "text": "I'm sure they are! This isn't about replacing them - it's about multiplying them. Think about it: your best closer probably spends 80% of their time dialing and leaving voicemails. What if they only talked to people who already said yes to a conversation? That's what we do."},
            {"speaker": "PROSPECT", "text": "What kind of results are people seeing?"},
            {"speaker": "AI", "text": "Our clients typically see 3 to 5 times more qualified conversations per rep. One client went from 2 booked meetings per day to 8 - same team, just using us to handle the top of funnel. Would you like to see a demo and I can show you exactly how it would work for your specific use case?"},
            {"speaker": "PROSPECT", "text": "You know what, yeah. Let's take a look."},
            {"speaker": "AI", "text": "Awesome! Let me get you scheduled. Would tomorrow afternoon or later this week work better?"},
        ]
    },
    
    "sales_live_transfer": {
        "name": "Live Transfer Demo",
        "filename": "dialgenix-live-transfer.mp3",
        "description": "AI qualifies a hot lead and offers to transfer them live",
        "conversation": [
            {"speaker": "AI", "text": "Hi, this is Sarah, AI agent with IntentBrain.ai. We help sales teams book more qualified meetings using AI that actually makes the calls for you. Is this something you're actively looking to improve?"},
            {"speaker": "PROSPECT", "text": "Actually, yeah. We've been struggling with our outbound. Our team hates cold calling and our numbers are way down."},
            {"speaker": "AI", "text": "I hear that a lot. Cold calling burnout is real - most reps quit within 90 days because of it. What if your team never had to make another cold call? They'd only get on the phone with people who already said they're interested."},
            {"speaker": "PROSPECT", "text": "That sounds great but how does that actually work?"},
            {"speaker": "AI", "text": "I do what I'm doing right now - I call your prospects, have real conversations, qualify them, and when someone's ready to talk, I can transfer them directly to your team in real-time. No scheduling, no follow-up needed. Hot lead, live on the phone, ready to buy."},
            {"speaker": "PROSPECT", "text": "So you can just transfer them right now if they're interested?"},
            {"speaker": "AI", "text": "Exactly. In fact, since you seem like a great fit and you're actively looking for a solution, I could transfer you to one of our specialists right now if you have a few minutes. They can answer all your questions and show you a quick demo. Would that work?"},
            {"speaker": "PROSPECT", "text": "Yeah, I've got about 15 minutes. Let's do it."},
            {"speaker": "AI", "text": "Perfect! I'm connecting you now to Mike, one of our solution specialists. He'll take great care of you. One moment please while I transfer the call."},
            {"speaker": "PROSPECT", "text": "Sounds good, thanks Sarah."},
            {"speaker": "AI", "text": "You're welcome! Transferring now."},
        ]
    },
    
    "sales_not_interested": {
        "name": "Not Interested - Graceful Exit",
        "filename": "dialgenix-not-interested.mp3",
        "description": "AI handles rejection gracefully and leaves door open",
        "conversation": [
            {"speaker": "AI", "text": "Hi, this is Sarah, AI agent with IntentBrain.ai. We help sales companies bring in more clients with AI-powered cold calling. Do you have a quick moment?"},
            {"speaker": "PROSPECT", "text": "Not really interested, thanks."},
            {"speaker": "AI", "text": "No problem at all. Before I let you go - is it that you're not doing outbound sales, or just not the right time?"},
            {"speaker": "PROSPECT", "text": "We do outbound but we're pretty set with our current process."},
            {"speaker": "AI", "text": "Got it, I respect that. If things ever change or you want to see what AI cold calling looks like, we're always here. Would it be okay if I sent you a quick email with some info, just so you have it? No follow-up calls, I promise."},
            {"speaker": "PROSPECT", "text": "Sure, that's fine."},
            {"speaker": "AI", "text": "Great. What's the best email for you?"},
            {"speaker": "PROSPECT", "text": "Mike at northwest sales dot com."},
            {"speaker": "AI", "text": "Perfect, mike at northwest sales dot com. I'll send that over. Thanks for your time today, and good luck with your sales goals. Have a great one!"},
            {"speaker": "PROSPECT", "text": "Thanks, you too."},
        ]
    },

    "sales_disc_adaptation": {
        "name": "DISC Personality Adaptation",
        "filename": "dialgenix-disc-adaptation.mp3",
        "description": "AI demonstrates adapting to a fast-paced D-type personality",
        "conversation": [
            {"speaker": "AI", "text": "Hi, this is Sarah with IntentBrain. We help sales teams book more meetings using AI. Got a minute?"},
            {"speaker": "PROSPECT", "text": "I've got 60 seconds. What do you got?"},
            {"speaker": "AI", "text": "Straight to it. AI makes your cold calls. Books meetings. Transfers hot leads live. Your team only talks to people who said yes. ROI in week one. Interested?"},
            {"speaker": "PROSPECT", "text": "How much?"},
            {"speaker": "AI", "text": "Starts at 99 a month. One meeting pays for it."},
            {"speaker": "PROSPECT", "text": "What's the catch?"},
            {"speaker": "AI", "text": "No catch. No contracts. Cancel anytime. We win when you win."},
            {"speaker": "PROSPECT", "text": "Send me info."},
            {"speaker": "AI", "text": "Done. Email?"},
            {"speaker": "PROSPECT", "text": "Tom at rapid growth dot io."},
            {"speaker": "AI", "text": "Sent in 2 minutes. Includes ROI calculator and demo link. Check your inbox. Anything else?"},
            {"speaker": "PROSPECT", "text": "Nope. Thanks."},
            {"speaker": "AI", "text": "You got it. Talk soon."},
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
    
    list_file = os.path.join(TEMP_DIR, "filelist.txt")
    with open(list_file, 'w') as f:
        for audio_file in input_files:
            f.write(f"file '{audio_file}'\n")
    
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
    
    demo_temp_dir = os.path.join(TEMP_DIR, demo_id)
    os.makedirs(demo_temp_dir, exist_ok=True)
    
    segment_files = []
    
    for i, line in enumerate(demo['conversation']):
        speaker = line['speaker']
        text = line['text']
        
        voice_id = AI_VOICE_ID if speaker == "AI" else PROSPECT_VOICE_ID
        voice_name = "Sarah (AI)" if speaker == "AI" else "Prospect"
        
        segment_path = os.path.join(demo_temp_dir, f"segment_{i:03d}.mp3")
        
        print(f"   [{i+1}/{len(demo['conversation'])}] {voice_name}: {text[:40]}...")
        
        success = await generate_audio_segment(text, voice_id, segment_path)
        
        if success:
            segment_files.append(segment_path)
        else:
            print(f"   ❌ Failed to generate segment {i}")
            return False
        
        await asyncio.sleep(0.5)
    
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
    print("IntentBrain Sales Demo Audio Generator")
    print("Two-Voice Version (AI + Prospect)")
    print("=" * 60)
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return
    
    print(f"\n🎤 AI Voice: Rachel (female, professional) - Sarah")
    print(f"🎤 Prospect Voice: Josh (male, natural) - Business Owner")
    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    success_count = 0
    
    for demo_id, demo in SALES_DEMOS.items():
        if await generate_conversation(demo_id, demo):
            success_count += 1
        
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {success_count}/{len(SALES_DEMOS)} sales demo audio files!")
    print(f"📁 Files saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    print("\n📋 Generated files:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.mp3'):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"   • {f} ({size/1024:.1f} KB)")

if __name__ == "__main__":
    asyncio.run(main())
