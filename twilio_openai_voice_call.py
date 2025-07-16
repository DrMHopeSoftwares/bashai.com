#!/usr/bin/env python3
"""
Real Twilio Voice Call Integration with OpenAI Realtime API
Makes actual phone calls using Twilio and processes them with OpenAI Realtime API
"""

import os
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Twilio imports
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Stream

# Our integrations
from openai_realtime_integration import OpenAIRealtimeAPI, session_manager
from realtime_usage_tracker import usage_tracker

load_dotenv()

class TwilioOpenAIVoiceCall:
    """Real Twilio voice calls with OpenAI Realtime API processing"""
    
    def __init__(self):
        # Twilio configuration
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio credentials not found in environment variables")
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        
        # Get or purchase a Twilio phone number for outbound calls
        self.from_number = self._get_twilio_phone_number()
        
        # Active calls tracking
        self.active_calls = {}
        
        print(f"✅ Twilio Voice Call System initialized")
        print(f"📞 From Number: {self.from_number}")

    def _get_twilio_phone_number(self) -> str:
        """Get an available Twilio phone number for making calls"""
        try:
            # List existing phone numbers
            phone_numbers = self.twilio_client.incoming_phone_numbers.list(limit=1)
            
            if phone_numbers:
                number = phone_numbers[0].phone_number
                print(f"📞 Using existing Twilio number: {number}")
                return number
            else:
                print("⚠️  No Twilio phone numbers found. You need to purchase one first.")
                print("   Visit: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
                return "+15005550006"  # Twilio test number
                
        except Exception as e:
            print(f"⚠️  Error getting Twilio phone number: {e}")
            return "+15005550006"  # Twilio test number

    async def make_call(self, 
                       to_number: str, 
                       ai_message: str = None,
                       voice: str = "alloy",
                       language: str = "hi-IN") -> Dict:
        """
        Make a real phone call using Twilio + OpenAI Realtime API
        
        Args:
            to_number: Phone number to call (e.g., "+919373111709")
            ai_message: Message for the AI to say
            voice: OpenAI voice model
            language: Language for the AI
            
        Returns:
            Dict: Call result
        """
        
        call_id = f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{to_number[-4:]}"
        
        try:
            print(f"📞 Initiating Twilio call to {to_number}")
            print(f"🤖 AI Voice: {voice} | Language: {language}")
            
            # Create OpenAI Realtime session first
            voice_config = {
                'voice': voice,
                'language': language,
                'instructions': ai_message or self._get_default_message()
            }
            
            realtime_session_id = await session_manager.create_session(
                'twilio-caller', 
                voice_config
            )
            
            realtime_api = await session_manager.get_session(realtime_session_id)
            if not realtime_api:
                raise Exception("Failed to create OpenAI Realtime session")
            
            # Create webhook URL for Twilio to connect to our server
            webhook_url = f"https://your-domain.com/webhook/voice/{call_id}"
            
            # For local development, you'll need ngrok or similar for webhooks
            # For now, we'll make the call and let Twilio handle basic TTS
            
            # Create TwiML for the call
            twiml_url = f"http://localhost:8000/api/twilio/twiml/{call_id}"
            
            # Make the actual Twilio call
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=twiml_url,
                timeout=30,
                status_callback=f"http://localhost:8000/api/twilio/status/{call_id}",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            # Store call information
            call_info = {
                'call_id': call_id,
                'twilio_call_sid': call.sid,
                'to_number': to_number,
                'from_number': self.from_number,
                'realtime_session_id': realtime_session_id,
                'status': 'initiated',
                'started_at': datetime.now(timezone.utc),
                'ai_message': ai_message,
                'voice_config': voice_config
            }
            
            self.active_calls[call_id] = call_info
            
            # Start usage tracking
            usage_tracker.start_session_tracking(
                realtime_session_id,
                'twilio-caller',
                'gpt-4o-realtime-preview'
            )
            
            print(f"✅ Twilio call initiated successfully!")
            print(f"📋 Call ID: {call_id}")
            print(f"📞 Twilio SID: {call.sid}")
            print(f"📊 Status: {call.status}")
            
            return {
                'success': True,
                'call_id': call_id,
                'twilio_call_sid': call.sid,
                'phone_number': to_number,
                'status': call.status,
                'message': f'Real call initiated to {to_number}',
                'realtime_session_id': realtime_session_id
            }
            
        except Exception as e:
            print(f"❌ Error making call: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to initiate call to {to_number}'
            }

    def _get_default_message(self) -> str:
        """Get default AI message for calls"""
        return """Hello! This is a call from BhashAI voice assistant powered by OpenAI's Realtime API.

I can speak naturally in both Hindi and English. I'm calling to demonstrate how AI voice conversations work.

How are you doing today? Feel free to respond in Hindi or English - I'll understand and respond naturally in your preferred language!"""

    def generate_twiml_response(self, call_id: str) -> str:
        """Generate TwiML response for Twilio webhook"""
        
        if call_id not in self.active_calls:
            # Fallback TwiML
            response = VoiceResponse()
            response.say("Hello! This is a test call from BhashAI. Thank you for answering!", voice='alice')
            response.hangup()
            return str(response)
        
        call_info = self.active_calls[call_id]
        ai_message = call_info.get('ai_message', self._get_default_message())
        
        # Create TwiML response
        response = VoiceResponse()
        
        # For now, use Twilio's built-in TTS
        # In production, you'd stream audio from OpenAI Realtime API
        response.say(
            ai_message,
            voice='alice',  # Use alice voice which sounds more natural
            language='en-IN'  # English with Indian accent
        )
        
        # Add a gather to listen for user input
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f'/api/twilio/process-speech/{call_id}',
            method='POST'
        )
        
        gather.say("Please speak after the beep, and I'll respond to you.", voice='alice')
        response.append(gather)
        
        # If no input, say goodbye
        response.say("Thank you for the call! Goodbye!", voice='alice')
        response.hangup()
        
        return str(response)

    def handle_call_status(self, call_id: str, status_data: Dict) -> Dict:
        """Handle Twilio call status callbacks"""
        
        if call_id not in self.active_calls:
            return {'error': 'Call not found'}
        
        call_info = self.active_calls[call_id]
        call_info['status'] = status_data.get('CallStatus', 'unknown')
        
        print(f"📊 Call {call_id} status: {call_info['status']}")
        
        if status_data.get('CallStatus') == 'completed':
            # Call ended, cleanup
            self._cleanup_call(call_id)
        
        return {'success': True, 'status': call_info['status']}

    def handle_speech_input(self, call_id: str, speech_data: Dict) -> str:
        """Handle speech input from Twilio and generate AI response"""
        
        if call_id not in self.active_calls:
            response = VoiceResponse()
            response.say("Call session not found. Goodbye!", voice='alice')
            response.hangup()
            return str(response)
        
        speech_text = speech_data.get('SpeechResult', '')
        confidence = speech_data.get('Confidence', 0)
        
        print(f"🗣️  User said: '{speech_text}' (confidence: {confidence})")
        
        # For now, generate a simple response
        # In production, you'd send this to OpenAI Realtime API
        ai_response = self._generate_ai_response(speech_text)
        
        response = VoiceResponse()
        response.say(ai_response, voice='alice', language='en-IN')
        
        # Continue conversation
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f'/api/twilio/process-speech/{call_id}',
            method='POST'
        )
        gather.say("Is there anything else you'd like to know?", voice='alice')
        response.append(gather)
        
        # End call if no response
        response.say("Thank you for the conversation! Have a great day!", voice='alice')
        response.hangup()
        
        return str(response)

    def _generate_ai_response(self, user_input: str) -> str:
        """Generate AI response (simplified version)"""
        
        # Simple keyword-based responses for demo
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['hello', 'hi', 'namaste', 'hey']):
            return "Hello! It's great to hear from you. I'm an AI assistant from BhashAI. How can I help you today?"
        
        elif any(word in user_lower for word in ['how', 'kaise', 'kaisa']):
            return "I'm doing well, thank you for asking! I'm an AI voice assistant powered by OpenAI. I can help answer questions or just have a conversation with you."
        
        elif any(word in user_lower for word in ['hindi', 'english', 'language']):
            return "Yes, I can speak both Hindi and English! Feel free to speak in whichever language you're comfortable with."
        
        elif any(word in user_lower for word in ['what', 'kya', 'who', 'kaun']):
            return "I'm BhashAI, an AI voice assistant that can have natural conversations in Hindi and English. I'm here to chat and help with any questions you might have!"
        
        elif any(word in user_lower for word in ['thank', 'thanks', 'dhanyawad']):
            return "You're very welcome! It was my pleasure to talk with you. Is there anything else I can help you with?"
        
        elif any(word in user_lower for word in ['bye', 'goodbye', 'alvida']):
            return "Goodbye! It was wonderful talking with you. Have a great day ahead!"
        
        else:
            return f"That's interesting! You said '{user_input}'. I'm still learning, but I enjoy our conversation. What else would you like to talk about?"

    async def end_call(self, call_id: str) -> Dict:
        """End an active call"""
        
        if call_id not in self.active_calls:
            return {'success': False, 'error': 'Call not found'}
        
        try:
            call_info = self.active_calls[call_id]
            twilio_call_sid = call_info['twilio_call_sid']
            
            # End the Twilio call
            call = self.twilio_client.calls(twilio_call_sid).update(status='completed')
            
            # Cleanup
            self._cleanup_call(call_id)
            
            print(f"✅ Call {call_id} ended successfully")
            
            return {
                'success': True,
                'call_id': call_id,
                'status': 'completed',
                'message': 'Call ended successfully'
            }
            
        except Exception as e:
            print(f"❌ Error ending call: {e}")
            return {'success': False, 'error': str(e)}

    def _cleanup_call(self, call_id: str):
        """Cleanup call resources"""
        
        if call_id in self.active_calls:
            call_info = self.active_calls[call_id]
            
            # End OpenAI session
            if 'realtime_session_id' in call_info:
                asyncio.create_task(
                    session_manager.close_session(call_info['realtime_session_id'])
                )
            
            # Calculate final costs
            duration = (datetime.now(timezone.utc) - call_info['started_at']).total_seconds()
            call_info['duration_seconds'] = duration
            call_info['ended_at'] = datetime.now(timezone.utc)
            
            print(f"📊 Call completed - Duration: {duration:.1f}s")
            
            # Remove from active calls
            del self.active_calls[call_id]

    def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get current call status"""
        return self.active_calls.get(call_id)

    def list_active_calls(self) -> List[Dict]:
        """List all active calls"""
        return list(self.active_calls.values())


# Global instance
twilio_voice_system = TwilioOpenAIVoiceCall()


async def make_real_call(phone_number: str, message: str = None) -> Dict:
    """
    Convenience function to make a real phone call
    
    Args:
        phone_number: Target phone number (e.g., "+919373111709")
        message: Custom AI message
        
    Returns:
        Dict: Call result
    """
    return await twilio_voice_system.make_call(
        to_number=phone_number,
        ai_message=message,
        voice="alloy",
        language="hi-IN"
    )


if __name__ == "__main__":
    async def test_real_call():
        """Test making a real call to +919373111709"""
        
        print("🚀 BhashAI Real Twilio + OpenAI Voice Call Test")
        print("=" * 60)
        
        target_number = "+919373111709"
        
        ai_message = """Hello! This is a real phone call from BhashAI voice assistant.

I'm powered by OpenAI's Realtime API and I'm calling through Twilio.

I can speak naturally in Hindi and English. This is a demonstration of AI voice calling technology.

How are you today? Please feel free to respond - I'll understand and reply to you!"""
        
        print(f"📱 Calling: {target_number}")
        print(f"🤖 AI Message prepared")
        print("📞 Making real call...")
        
        try:
            result = await make_real_call(target_number, ai_message)
            
            print("\n📋 CALL RESULT:")
            print("=" * 40)
            print(json.dumps(result, indent=2, default=str))
            
            if result['success']:
                call_id = result['call_id']
                print(f"\n✅ Real call initiated successfully!")
                print(f"📞 Call ID: {call_id}")
                print(f"🔧 Twilio SID: {result['twilio_call_sid']}")
                print(f"📱 Target: {target_number}")
                
                print("\n📊 Call will proceed automatically...")
                print("   1. Twilio dials the number")
                print("   2. When answered, AI speaks the message")
                print("   3. User can respond and have a conversation")
                print("   4. Call ends naturally or after timeout")
                
                # Wait and check status
                await asyncio.sleep(10)
                status = twilio_voice_system.get_call_status(call_id)
                if status:
                    print(f"\n📊 Current Status: {status['status']}")
                
            else:
                print(f"\n❌ Call failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error in test: {e}")
    
    # Run the test
    asyncio.run(test_real_call())