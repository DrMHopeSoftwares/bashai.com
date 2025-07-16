#!/usr/bin/env python3
"""
Smart Conversation Call System
Implements proper turn-taking and speech detection to prevent talking over the user
"""

import os
import requests
import json
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Pause
from dotenv import load_dotenv

load_dotenv()

class SmartConversationCall:
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        print(f"🎙️  Smart Conversation Call System")
        print(f"📞 Twilio: {self.from_number}")
        print(f"🧠 OpenAI: {'✅' if self.openai_api_key else '❌'}")

    def create_smart_conversation_twiml(self) -> str:
        """Create TwiML with proper turn-taking and speech detection"""
        
        response = VoiceResponse()
        
        # Very brief initial greeting
        response.say(
            "Hi! BhashAI here.",
            voice='alice',
            language='en-IN'
        )
        
        # Short pause to allow for interruption
        response.pause(length=1)
        
        # First listening phase - immediate listening after brief intro
        gather1 = Gather(
            input='speech',
            timeout=10,  # Give user 10 seconds to start speaking
            speech_timeout='auto',  # Automatically detect when user stops
            enhanced=True,  # Better speech recognition
            language='en-IN'
        )
        
        # Very short prompt
        gather1.say(
            "How's your day?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather1)
        
        # Brief acknowledgment
        response.say(
            "Nice!",
            voice='alice',
            language='en-IN'
        )
        
        response.pause(length=0.5)
        
        # Second listening phase with immediate transition
        gather2 = Gather(
            input='speech',
            timeout=8,
            speech_timeout='auto',
            enhanced=True,
            language='en-IN'
        )
        
        gather2.say(
            "Tell me about yourself.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather2)
        
        # Quick response
        response.say(
            "Interesting!",
            voice='alice',
            language='en-IN'
        )
        
        response.pause(length=0.5)
        
        # Third phase - very responsive
        gather3 = Gather(
            input='speech',
            timeout=6,
            speech_timeout='auto',
            enhanced=True,
            language='en-IN'
        )
        
        gather3.say(
            "What do you think about AI?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather3)
        
        # Final acknowledgment
        response.say(
            "Great perspective! Thanks for chatting with BhashAI. Goodbye!",
            voice='alice',
            language='en-IN'
        )
        
        response.hangup()
        return str(response)

    def create_ultra_responsive_twiml(self) -> str:
        """Create ultra-responsive TwiML that prioritizes user speech"""
        
        response = VoiceResponse()
        
        # Minimal greeting
        response.say("Hi! BhashAI.", voice='alice', language='en-IN')
        
        # Immediate listening with very sensitive detection
        gather_main = Gather(
            input='speech',
            timeout=15,  # Long timeout for user comfort
            speech_timeout=1,  # Very quick silence detection (1 second)
            enhanced=True,
            language='en-IN'
        )
        
        # Just ask one open question and listen
        gather_main.say(
            "What would you like to talk about?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather_main)
        
        # If they don't speak, give them another chance
        gather_second = Gather(
            input='speech',
            timeout=10,
            speech_timeout=1,
            enhanced=True,
            language='en-IN'
        )
        
        gather_second.say(
            "I'm listening.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather_second)
        
        # Final fallback
        response.say(
            "Thanks for calling BhashAI! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        
        response.hangup()
        return str(response)

    def make_smart_conversation_call(self, phone_number: str) -> dict:
        """Make a call with smart turn-taking"""
        
        try:
            print(f"🎯 Making smart conversation call to {phone_number}")
            
            # Use ultra-responsive TwiML
            twiml_content = self.create_ultra_responsive_twiml()
            print(f"🎵 Generated responsive TwiML: {len(twiml_content)} characters")
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=60
            )
            
            print(f"✅ Smart conversation call initiated!")
            print(f"📞 Call SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'phone_number': phone_number,
                'status': call.status,
                'message': 'Smart conversation call with proper turn-taking started'
            }
            
        except Exception as e:
            print(f"❌ Error making smart call: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def test_smart_conversation():
    """Test the smart conversation system"""
    
    print("🎙️  Testing Smart Conversation with Proper Turn-Taking")
    print("=" * 70)
    
    smart_system = SmartConversationCall()
    
    result = smart_system.make_smart_conversation_call("+919373111709")
    
    print(f"\n📋 RESULT:")
    print(json.dumps(result, indent=2, default=str))
    
    if result['success']:
        print(f"\n🎉 SMART CONVERSATION INITIATED!")
        print(f"📞 Answer your phone for improved experience:")
        print(f"   ✅ AI stops talking when you start speaking")
        print(f"   ✅ Quick speech detection (1 second silence)")
        print(f"   ✅ No talking over each other")
        print(f"   ✅ Natural turn-taking")
        print(f"   ✅ Responsive listening")


if __name__ == "__main__":
    test_smart_conversation()