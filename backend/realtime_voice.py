"""
Real-Time AI Voice Calling System
Synthflow-style architecture using Twilio Media Streams + GPT + ElevenLabs
"""
import asyncio
import base64
import json
import logging
import struct
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os

logger = logging.getLogger(__name__)

# System prompt for the AI sales agent
SALES_AGENT_PROMPT = """You are an AI sales agent making outbound calls for {company_name}. Your goal is to qualify leads and book meetings.

CRITICAL RULES:
1. Keep responses SHORT (1-2 sentences max) - this is a phone call
2. Sound natural and conversational, not robotic
3. Always start with the compliance disclosure on first message
4. If they say "stop", "remove me", "don't call" - immediately say goodbye politely
5. Your goal: Qualify the lead and book a meeting

COMPANY INFO:
- Company: {company_name}
- Value Proposition: {value_prop}

LEAD INFO:
- Business: {business_name}
- Contact: {contact_name}

QUALIFICATION QUESTIONS (ask naturally, not all at once):
1. Are you the person who handles [relevant area] decisions?
2. Is this something you're currently exploring?
3. What's your timeline?

IF QUALIFIED:
- Offer to book a 15-minute call with a specialist
- Get their preferred time (this week or next)
- Confirm their email for the calendar invite

IF NOT INTERESTED:
- Thank them politely
- Offer to send info via email
- Say goodbye

REMEMBER: Short responses only! This is a real-time phone conversation."""

class ConversationState:
    """Track the state of a phone conversation"""
    def __init__(self, call_sid: str, lead: Dict, campaign: Dict):
        self.call_sid = call_sid
        self.lead = lead
        self.campaign = campaign
        self.messages = []
        self.is_first_message = True
        self.is_qualified = False
        self.wants_dnc = False
        self.booking_info = {}
        self.transcript = []
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self.transcript.append({"role": role, "content": content})

class RealtimeVoiceAI:
    """
    Real-time AI voice agent using:
    - Twilio Media Streams for audio
    - GPT for conversation
    - ElevenLabs for TTS
    """
    
    def __init__(self):
        self.active_calls: Dict[str, ConversationState] = {}
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
    
    def create_conversation(self, call_sid: str, lead: Dict, campaign: Dict) -> ConversationState:
        """Initialize a new conversation state"""
        state = ConversationState(call_sid, lead, campaign)
        self.active_calls[call_sid] = state
        return state
    
    def get_conversation(self, call_sid: str) -> Optional[ConversationState]:
        """Get existing conversation state"""
        return self.active_calls.get(call_sid)
    
    def end_conversation(self, call_sid: str) -> Optional[ConversationState]:
        """End and return conversation state"""
        return self.active_calls.pop(call_sid, None)
    
    async def generate_response(self, state: ConversationState, user_input: str = None) -> str:
        """Generate AI response using GPT"""
        
        # Build system prompt with context
        system_prompt = SALES_AGENT_PROMPT.format(
            company_name=state.campaign.get('company_name', 'our company'),
            value_prop=state.campaign.get('ai_script', 'helping businesses increase profits'),
            business_name=state.lead.get('business_name', 'your company'),
            contact_name=state.lead.get('contact_name', 'there')
        )
        
        # First message includes compliance disclosure
        if state.is_first_message:
            state.is_first_message = False
            company = state.campaign.get('company_name', 'our company')
            business = state.lead.get('business_name', 'your company')
            
            opening = (
                f"Hi, this is an AI assistant calling on behalf of {company}. "
                "This is an automated business call. "
                f"Am I speaking with someone at {business}?"
            )
            state.add_message("assistant", opening)
            return opening
        
        # Add user input to conversation
        if user_input:
            state.add_message("user", user_input)
            
            # Check for DNC keywords
            dnc_keywords = ["stop", "remove", "don't call", "do not call", "unsubscribe", "not interested", "take me off"]
            if any(keyword in user_input.lower() for keyword in dnc_keywords):
                state.wants_dnc = True
                response = "No problem at all. I've noted your preference and you won't receive any more calls from us. Have a great day!"
                state.add_message("assistant", response)
                return response
        
        # Generate response using GPT
        try:
            chat = LlmChat(
                api_key=self.llm_key,
                model="gpt-5.2",
                system_message=system_prompt
            )
            
            # Add conversation history
            for msg in state.messages:
                if msg["role"] == "user":
                    chat.add_message(UserMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    # Add as context in the system
                    pass
            
            # Get response
            response = await chat.chat(user_input or "Hello")
            
            # Keep response short for phone
            if len(response) > 200:
                response = response[:200].rsplit(' ', 1)[0] + "..."
            
            state.add_message("assistant", response)
            
            # Check if qualified
            qualified_signals = ["yes", "interested", "tell me more", "sure", "okay"]
            if user_input and any(signal in user_input.lower() for signal in qualified_signals):
                state.is_qualified = True
            
            return response
            
        except Exception as e:
            logger.error(f"GPT response error: {e}")
            return "I apologize, I'm having trouble hearing you. Could you repeat that?"
    
    async def text_to_speech(self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> bytes:
        """Convert text to speech using ElevenLabs"""
        try:
            from elevenlabs import ElevenLabs
            
            client = ElevenLabs(api_key=self.elevenlabs_key)
            
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,  # Sarah - professional female
                model_id="eleven_turbo_v2_5",  # Fastest model for real-time
                output_format="pcm_16000"  # 16kHz PCM for processing
            )
            
            audio_data = b""
            for chunk in audio_generator:
                audio_data += chunk
            
            return audio_data
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return b""
    
    def pcm_to_mulaw(self, pcm_data: bytes, sample_rate: int = 16000) -> bytes:
        """Convert PCM audio to μ-law format for Twilio (8kHz)"""
        try:
            import audioop
            
            # Resample from input rate to 8000Hz if needed
            if sample_rate != 8000:
                pcm_data, _ = audioop.ratecv(pcm_data, 2, 1, sample_rate, 8000, None)
            
            # Convert to μ-law
            mulaw_data = audioop.lin2ulaw(pcm_data, 2)
            return mulaw_data
            
        except ImportError:
            # Fallback: manual μ-law encoding
            logger.warning("audioop not available, using manual μ-law encoding")
            return self._manual_mulaw_encode(pcm_data, sample_rate)
    
    def _manual_mulaw_encode(self, pcm_data: bytes, sample_rate: int) -> bytes:
        """Manual μ-law encoding fallback"""
        # Simple downsampling if needed
        if sample_rate != 8000:
            ratio = sample_rate // 8000
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            downsampled = samples[::ratio]
            pcm_data = struct.pack(f'<{len(downsampled)}h', *downsampled)
        
        # μ-law encoding lookup
        MULAW_MAX = 0x1FFF
        MULAW_BIAS = 33
        
        samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
        mulaw_bytes = []
        
        for sample in samples:
            sign = 0x80 if sample < 0 else 0
            sample = min(abs(sample), MULAW_MAX)
            sample += MULAW_BIAS
            
            # Find segment
            exponent = 7
            for exp in range(8):
                if sample < (1 << (exp + 8)):
                    exponent = exp
                    break
            
            mantissa = (sample >> (exponent + 3)) & 0x0F
            mulaw_byte = ~(sign | (exponent << 4) | mantissa) & 0xFF
            mulaw_bytes.append(mulaw_byte)
        
        return bytes(mulaw_bytes)
    
    def mulaw_to_pcm(self, mulaw_data: bytes) -> bytes:
        """Convert μ-law audio from Twilio to PCM"""
        try:
            import audioop
            return audioop.ulaw2lin(mulaw_data, 2)
        except ImportError:
            logger.warning("audioop not available, using manual μ-law decoding")
            return self._manual_mulaw_decode(mulaw_data)
    
    def _manual_mulaw_decode(self, mulaw_data: bytes) -> bytes:
        """Manual μ-law decoding fallback"""
        MULAW_BIAS = 33
        
        samples = []
        for byte in mulaw_data:
            byte = ~byte & 0xFF
            sign = byte & 0x80
            exponent = (byte >> 4) & 0x07
            mantissa = byte & 0x0F
            
            sample = ((mantissa << 3) + MULAW_BIAS) << exponent
            sample -= MULAW_BIAS
            
            if sign:
                sample = -sample
            
            samples.append(sample)
        
        return struct.pack(f'<{len(samples)}h', *samples)


# Global instance
realtime_voice_ai = RealtimeVoiceAI()


async def handle_twilio_media_stream(websocket: WebSocket, call_sid: str, lead: Dict, campaign: Dict):
    """
    Handle Twilio Media Stream WebSocket connection for real-time AI conversation.
    
    Flow:
    1. Receive audio from caller
    2. Transcribe with Whisper
    3. Generate response with GPT
    4. Convert to speech with ElevenLabs
    5. Stream back to caller
    """
    await websocket.accept()
    
    state = realtime_voice_ai.create_conversation(call_sid, lead, campaign)
    audio_buffer = b""
    stream_sid = None
    
    logger.info(f"Media stream started for call {call_sid}")
    
    try:
        # Send initial greeting
        greeting = await realtime_voice_ai.generate_response(state)
        await send_audio_to_twilio(websocket, greeting, stream_sid, state)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            event = message.get("event")
            
            if event == "start":
                stream_sid = message.get("streamSid")
                logger.info(f"Stream started: {stream_sid}")
                
            elif event == "media":
                # Receive audio from caller
                payload = message["media"]["payload"]
                audio_chunk = base64.b64decode(payload)
                audio_buffer += audio_chunk
                
                # Process when we have enough audio (about 1 second)
                if len(audio_buffer) >= 8000:  # 1 second at 8kHz
                    # Transcribe
                    transcript = await transcribe_audio(audio_buffer, state)
                    
                    if transcript and transcript.strip():
                        logger.info(f"Caller said: {transcript}")
                        
                        # Generate AI response
                        response = await realtime_voice_ai.generate_response(state, transcript)
                        logger.info(f"AI response: {response}")
                        
                        # Send audio response
                        await send_audio_to_twilio(websocket, response, stream_sid, state)
                        
                        # Check if should end call
                        if state.wants_dnc:
                            await asyncio.sleep(2)  # Let goodbye play
                            break
                    
                    audio_buffer = b""
                    
            elif event == "stop":
                logger.info(f"Stream stopped for call {call_sid}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for call {call_sid}")
    except Exception as e:
        logger.error(f"Error in media stream handler: {e}")
    finally:
        # Save conversation state
        final_state = realtime_voice_ai.end_conversation(call_sid)
        if final_state:
            logger.info(f"Call ended. Qualified: {final_state.is_qualified}, DNC: {final_state.wants_dnc}")
            # Return state for database update
            return {
                "is_qualified": final_state.is_qualified,
                "wants_dnc": final_state.wants_dnc,
                "transcript": final_state.transcript
            }


async def transcribe_audio(audio_data: bytes, state: ConversationState) -> str:
    """Transcribe audio using Whisper"""
    try:
        # Convert μ-law to PCM
        pcm_data = realtime_voice_ai.mulaw_to_pcm(audio_data)
        
        # Use OpenAI Whisper for transcription
        # For production, consider using Deepgram for lower latency
        import httpx
        
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Create WAV header for the PCM data
        wav_data = create_wav_header(pcm_data, 8000, 1, 16) + pcm_data
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {llm_key}"},
                files={"file": ("audio.wav", wav_data, "audio/wav")},
                data={"model": "whisper-1"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                logger.error(f"Whisper API error: {response.status_code}")
                return ""
                
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""


def create_wav_header(pcm_data: bytes, sample_rate: int, channels: int, bits_per_sample: int) -> bytes:
    """Create WAV file header"""
    data_size = len(pcm_data)
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,
        1,  # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )
    return header


async def send_audio_to_twilio(websocket: WebSocket, text: str, stream_sid: str, state: ConversationState):
    """Generate TTS and send audio back to Twilio"""
    try:
        # Generate speech with ElevenLabs
        pcm_audio = await realtime_voice_ai.text_to_speech(text)
        
        if not pcm_audio:
            logger.error("No audio generated from TTS")
            return
        
        # Convert to μ-law for Twilio
        mulaw_audio = realtime_voice_ai.pcm_to_mulaw(pcm_audio, 16000)
        
        # Send in chunks (Twilio expects ~20ms chunks = 160 bytes at 8kHz)
        chunk_size = 160
        for i in range(0, len(mulaw_audio), chunk_size):
            chunk = mulaw_audio[i:i + chunk_size]
            payload = base64.b64encode(chunk).decode()
            
            message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload
                }
            }
            
            await websocket.send_text(json.dumps(message))
            await asyncio.sleep(0.02)  # 20ms pacing
            
    except Exception as e:
        logger.error(f"Error sending audio to Twilio: {e}")
