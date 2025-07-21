#!/usr/bin/env python3

import requests
import json

base_url = "http://localhost:5003"

def test_manual_call():
    """Test the manual call endpoint"""
    try:
        # Test data - try with different phone numbers
        test_cases = [
            {
                "recipient_phone": "+918035315390",  # Test number
                "sender_phone": "+918035315404",     # Phone with pooja agent
                "call_type": "manual",
                "contact_name": "Test Call Contact - pooja"
            },
            {
                "recipient_phone": "+918035315404",  # Test number
                "sender_phone": "+918035315390",     # Phone with bbbb agent
                "call_type": "manual",
                "contact_name": "Test Call Contact - bbbb"
            },
            {
                "recipient_phone": "+918035315322",  # Test number
                "sender_phone": "+918035315328",     # Phone with agent Ai
                "call_type": "manual",
                "contact_name": "Test Call Contact - agent Ai"
            }
        ]

        for i, call_data in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: Testing manual call from {call_data['sender_phone']} to {call_data['recipient_phone']}...")
            print(f"   Contact: {call_data['contact_name']}")

            # Make the call
            response = requests.post(f"{base_url}/api/manual-call", json=call_data)

            print(f"📞 Response Status: {response.status_code}")
            print(f"📞 Response Body:")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))

            # Check if the call used the requested phone or fallback
            if response_data.get('sender_phone') != call_data['sender_phone']:
                print(f"⚠️ Call used fallback phone: {response_data.get('sender_phone')} instead of {call_data['sender_phone']}")
            else:
                print(f"✅ Call used requested phone: {call_data['sender_phone']}")

            print("-" * 80)

        return "All tests completed"
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    print("🔍 Testing manual call endpoint...")
    result = test_manual_call()
    print("\n✅ Test completed!")
