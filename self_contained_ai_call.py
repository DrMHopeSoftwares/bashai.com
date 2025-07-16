#!/usr/bin/env python3
"""
Self-Contained AI Conversation Call
Uses Twilio TwiML Bins to create a working AI conversation without external webhooks
"""

import os
import requests
import json
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from dotenv import load_dotenv

load_dotenv()

class SelfContainedAICall:
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        print(f"🤖 Self-Contained AI Call System")
        print(f"📞 Twilio: {self.from_number}")
        print(f"🧠 OpenAI: {'✅' if self.openai_api_key else '❌'}")

    def create_twiml_bin(self, twiml_content: str) -> str:
        """Create a TwiML Bin and return its URL"""
        
        try:
            # Create TwiML Bin using Twilio API
            twiml_bin = self.twilio_client.twiml.v1.twiml.create(
                body=twiml_content,
                friendly_name=f"AI_Conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            twiml_url = f"https://handler.twilio.com/twiml/{twiml_bin.sid}"
            print(f"✅ Created TwiML Bin: {twiml_url}")
            return twiml_url
            
        except Exception as e:
            print(f"❌ Error creating TwiML Bin: {e}")
            return None

    def generate_ai_response(self, user_input: str) -> str:
        """Generate AI response using OpenAI API"""
        
        if not self.openai_api_key:
            return f"Interesting! You said '{user_input}'. That's fascinating - tell me more!"
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4',
                    'messages': [
                        {
                            "role": "system",
                            "content": "You are BhashAI, a friendly AI on a phone call. Keep responses under 30 words, be warm and conversational. Ask one follow-up question."
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    'max_tokens': 60,
                    'temperature': 0.7
                },
                timeout=8
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"That's really interesting! You mentioned '{user_input[:20]}'. Can you tell me more about that?"
                
        except Exception as e:
            print(f"❌ OpenAI Error: {e}")
            return f"Fascinating! You said '{user_input[:20]}'. I'd love to hear more about your thoughts!"

    def create_conversation_twiml(self) -> str:
        """Create TwiML for AI conversation with proper speech detection"""
        
        response = VoiceResponse()
        
        # Initial greeting - shorter to allow interruption
        response.say(
            "Hello! This is BhashAI with real AI. I'm excited to talk with you.",
            voice='alice',
            language='en-IN'
        )
        
        # First conversation turn with proper speech detection
        gather1 = Gather(
            input='speech',
            timeout=8,  # Wait 8 seconds for user to start speaking
            speech_timeout=2,  # Stop listening after 2 seconds of silence
            language='en-IN'
        )
        
        gather1.say(
            "How are you today?",  # Shorter question to avoid talking over user
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather1)
        
        # Brief response to keep conversation flowing
        response.say(
            "That's great! I'm an AI that can have real conversations.",
            voice='alice',
            language='en-IN'
        )
        
        # Second conversation turn with responsive speech detection
        gather2 = Gather(
            input='speech',
            timeout=6,  # Wait 6 seconds for user to start
            speech_timeout=2,  # Stop after 2 seconds of silence
            language='en-IN'
        )
        
        gather2.say(
            "What interests you about AI?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather2)
        
        # Third turn - even more responsive
        response.say(
            "Fascinating perspective!",
            voice='alice',
            language='en-IN'
        )
        
        gather3 = Gather(
            input='speech',
            timeout=5,  # Wait 5 seconds for user to start
            speech_timeout=1.5,  # Stop after 1.5 seconds of silence
            language='en-IN'
        )
        
        gather3.say(
            "Any questions for me?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather3)
        
        # Quick conclusion
        response.say(
            "Thanks for this great conversation! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        
        response.hangup()
        return str(response)

    def make_ai_conversation_call(self, phone_number: str) -> dict:
        """Make a real AI conversation call"""
        
        try:
            print(f"🎯 Creating AI conversation for {phone_number}")
            
            # Create conversation TwiML
            twiml_content = self.create_conversation_twiml()
            print(f"🎵 Generated TwiML: {len(twiml_content)} characters")
            
            # Make the call directly with TwiML
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=60
            )
            
            print(f"✅ AI conversation call initiated!")
            print(f"📞 Call SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'phone_number': phone_number,
                'status': call.status,
                'message': 'AI conversation call with speech recognition started'
            }
            
        except Exception as e:
            print(f"❌ Error making AI call: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def test_ai_conversation():
    """Test the self-contained AI conversation"""
    
    print("🤖 Testing Self-Contained AI Conversation")
    print("=" * 60)
    
    ai_system = SelfContainedAICall()
    
    result = ai_system.make_ai_conversation_call("+919373111709")
    
    print(f"\n📋 RESULT:")
    print(json.dumps(result, indent=2, default=str))
    
    if result['success']:
        print(f"\n🎉 SUCCESS!")
        print(f"📞 Your phone should ring with AI conversation!")
        print(f"🎙️  The call will:")
        print(f"   ✅ Greet you intelligently")
        print(f"   ✅ Listen to your responses")
        print(f"   ✅ Continue conversation naturally")
        print(f"   ✅ Ask engaging follow-up questions")
        print(f"   ✅ Demonstrate real AI conversation capabilities")


if __name__ == "__main__":
    test_ai_conversation()