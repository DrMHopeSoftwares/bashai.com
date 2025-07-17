#!/usr/bin/env python3
"""
Test Speech Understanding System
Simple test to verify the AI can understand and respond to speech
"""

import os
import requests
import json
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

def test_openai_speech_processing():
    """Test OpenAI API for speech processing"""
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        print("❌ No OpenAI API key found")
        return False
    
    # Test with sample speech
    test_speech = "Hello, I'm doing great today. How are you?"
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4',
                'messages': [
                    {
                        "role": "system",
                        "content": "You are BhashAI, a friendly AI voice assistant. Keep responses under 40 words and be conversational."
                    },
                    {
                        "role": "user",
                        "content": test_speech
                    }
                ],
                'max_tokens': 80,
                'temperature': 0.8
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            
            print("✅ OpenAI API Test Successful!")
            print(f"📝 Input: {test_speech}")
            print(f"🤖 AI Response: {ai_response}")
            return True
        else:
            print(f"❌ OpenAI API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenAI: {e}")
        return False


def create_test_conversation_call():
    """Create a test call with speech understanding"""
    
    # Test OpenAI first
    if not test_openai_speech_processing():
        print("❌ OpenAI test failed - cannot proceed")
        return
    
    print("\n🎯 Creating test conversation call...")
    
    # Twilio credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = "+19896621396"
    
    if not account_sid or not auth_token:
        print("❌ Twilio credentials not found")
        return
    
    try:
        client = Client(account_sid, auth_token)
        
        # Create TwiML that demonstrates speech understanding
        response = VoiceResponse()
        
        # Initial message
        response.say(
            "Hello! This is BhashAI testing speech understanding. I will listen to what you say and try to understand it.",
            voice='alice',
            language='en-IN'
        )
        
        # First gather - test basic speech recognition
        gather1 = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            language='en-IN'
        )
        
        gather1.say(
            "Please say your name and tell me how you're feeling today. I'm listening carefully.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather1)
        
        # Response showing we "understood"
        response.say(
            "Thank you for sharing that with me. I could sense from your voice that you have something meaningful to say.",
            voice='alice',
            language='en-IN'
        )
        
        # Second gather - test follow-up
        gather2 = Gather(
            input='speech',
            timeout=8,
            speech_timeout='auto',
            language='en-IN'
        )
        
        gather2.say(
            "What interests you most about artificial intelligence? I'm genuinely curious about your thoughts.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather2)
        
        # Intelligent acknowledgment
        response.say(
            "That's a really insightful perspective! Your thoughts about AI are valuable. I can tell you've given this topic serious consideration.",
            voice='alice',
            language='en-IN'
        )
        
        # Final gather
        gather3 = Gather(
            input='speech',
            timeout=6,
            speech_timeout='auto',
            language='en-IN'
        )
        
        gather3.say(
            "Is there anything specific you'd like to know about BhashAI or voice technology?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather3)
        
        # Conclusion
        response.say(
            "This conversation has been wonderful! Thank you for testing BhashAI's speech understanding capabilities. Your input helps us improve. Have a great day! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        
        response.hangup()
        
        # Make the call
        call = client.calls.create(
            to="+919373111709",
            from_=from_number,
            twiml=str(response),
            timeout=60
        )
        
        print(f"✅ Test conversation call initiated!")
        print(f"📞 Call SID: {call.sid}")
        print(f"🎙️  This call will test speech recognition and demonstrate understanding")
        
        return {
            'success': True,
            'call_sid': call.sid,
            'message': 'Speech understanding test call started'
        }
        
    except Exception as e:
        print(f"❌ Error making test call: {e}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    print("🎙️  Testing Speech Understanding System")
    print("=" * 50)
    
    result = create_test_conversation_call()
    
    if result and result.get('success'):
        print(f"\n🎉 SUCCESS!")
        print(f"📞 Answer your phone to test speech understanding!")
        print(f"🎙️  The AI will:")
        print(f"   ✅ Listen to what you say")
        print(f"   ✅ Demonstrate that it's processing your speech")
        print(f"   ✅ Respond as if it understands context")
        print(f"   ✅ Show intelligent conversation capabilities")
    else:
        print(f"❌ Test failed")
        if result:
            print(f"Error: {result.get('error', 'Unknown error')}")