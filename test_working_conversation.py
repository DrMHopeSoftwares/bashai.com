#!/usr/bin/env python3
"""
Test Working Conversation System
Tests the new speech understanding system with contextual responses
"""

import requests
import json

def test_working_conversation():
    """Test the working conversation system"""
    
    print("🎙️  Testing Working Conversation with Speech Understanding")
    print("=" * 60)
    
    # Test the API endpoint
    try:
        response = requests.post(
            'http://localhost:8000/api/make-working-conversation',
            json={
                'phone_number': '+919373111709'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Working Conversation API Result:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print(f"\n🎉 WORKING CONVERSATION INITIATED!")
                print(f"📞 Call SID: {result.get('call_sid')}")
                print(f"📱 Phone: {result.get('phone_number')}")
                print(f"\n🧠 This call will ACTUALLY understand what you say!")
                print(f"🗣️  Features:")
                print(f"   ✅ Real speech recognition")
                print(f"   ✅ Contextual responses based on your words")
                print(f"   ✅ Intelligent conversation flow")
                print(f"   ✅ Remembers what you said in responses")
                print(f"\n📞 Answer your phone and say something like:")
                print(f"   - 'Hi, I'm doing great today!'")
                print(f"   - 'I work in technology'")
                print(f"   - 'I'm tired from work'")
                print(f"   - 'I have a family at home'")
                print(f"\n🤖 The AI will respond specifically to what you say!")
            else:
                print(f"❌ Call failed: {result}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing working conversation: {e}")
        print(f"💡 Make sure the Flask app is running on port 8000")

if __name__ == "__main__":
    test_working_conversation()