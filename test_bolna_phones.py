#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_bolna_phone_numbers():
    """Test what phone numbers are available in Bolna"""
    try:
        api_key = os.getenv('BOLNA_API_KEY')
        base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
        
        if not api_key:
            print("❌ BOLNA_API_KEY not found in environment")
            return
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        print("🔍 Fetching phone numbers from Bolna API...")
        
        # Try different endpoints to get phone numbers
        endpoints = [
            '/phone-numbers',
            '/phone-numbers/all',
            '/telephony/phone-numbers',
            '/agents'
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"\n📞 Trying endpoint: {endpoint}")
                
                response = requests.get(url, headers=headers)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response:")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error with {endpoint}: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_bolna_phone_numbers()
