#!/usr/bin/env python3

import requests
import json

base_url = "http://localhost:5003"

def test_phone_numbers_endpoint():
    """Test the phone numbers endpoint"""
    try:
        # First login to get session
        login_data = {
            "email": "b@gmail.com",
            "password": "bhupendra"
        }
        
        session = requests.Session()
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login successful")
            
            # Now test phone numbers endpoint
            phone_response = session.get(f"{base_url}/api/phone-numbers/owned-simple")
            
            if phone_response.status_code == 200:
                phone_data = phone_response.json()
                print(f"✅ Phone numbers fetched successfully:")
                print(json.dumps(phone_data, indent=2))
                
                # Check if agent names are showing
                if phone_data.get('data'):
                    for phone in phone_data['data']:
                        agent_name = phone.get('agent_name')
                        phone_number = phone.get('phone_number')
                        print(f"📞 {phone_number} -> Agent: {agent_name or 'No Agent'}")
                
                return phone_data
            else:
                print(f"❌ Failed to fetch phone numbers: {phone_response.status_code}")
                print(phone_response.text)
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    print("🔍 Testing phone numbers endpoint...")
    result = test_phone_numbers_endpoint()
    print("\n✅ Test completed!")
