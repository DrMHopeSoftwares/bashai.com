#!/usr/bin/env python3
"""
Test Real AI Conversation Call
"""

import requests
import json

def test_ai_conversation_call():
    """Test the real AI conversation system"""
    
    print("🤖 Testing Real AI Conversation Call")
    print("=" * 50)
    
    # Call the API to make an AI conversation call
    try:
        response = requests.post(
            'http://localhost:8000/api/make-ai-conversation-call',
            json={
                'phone_number': '+919373111709'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Conversation Call Result:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print(f"\n📞 REAL AI CALL INITIATED!")
                print(f"📋 Call SID: {result.get('call_sid')}")
                print(f"📱 Phone: {result.get('phone_number')}")
                print(f"\n🎙️  Answer your phone and have a REAL conversation with AI!")
                print(f"🤖 The AI will:")
                print(f"   - Listen to what you say")
                print(f"   - Generate intelligent responses using OpenAI")
                print(f"   - Continue the conversation naturally")
                print(f"   - Ask follow-up questions")
            else:
                print(f"❌ Call failed: {result}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing AI conversation: {e}")

if __name__ == "__main__":
    test_ai_conversation_call()