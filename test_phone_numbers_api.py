#!/usr/bin/env python3
"""
Test the phone numbers API endpoint
"""

import requests
import json

def test_phone_numbers_api():
    """Test the phone numbers API endpoint"""
    
    print("🧪 Testing Phone Numbers API")
    print("="*40)
    
    # Test the API endpoint
    try:
        response = requests.get(
            'http://127.0.0.1:5001/api/bolna/phone-numbers',
            headers={
                'Authorization': 'Bearer test-token'  # You'd need a real token
            },
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API working correctly!")
                
                summary = result.get('summary', {})
                print(f"\n📊 Summary:")
                print(f"   Total Numbers: {summary.get('total_numbers', 0)}")
                print(f"   Monthly Cost: ${summary.get('monthly_cost', 0):.2f}")
                print(f"   Active Providers: {summary.get('active_providers', 0)}")
                print(f"   Countries: {summary.get('countries', 0)}")
                
                phone_numbers = result.get('phone_numbers', [])
                if phone_numbers:
                    print(f"\n📱 Phone Numbers ({len(phone_numbers)}):")
                    for i, number in enumerate(phone_numbers[:3], 1):  # Show first 3
                        print(f"   {i}. {number.get('phone_number', 'N/A')} ({number.get('telephony_provider', 'Unknown')})")
                    if len(phone_numbers) > 3:
                        print(f"   ... and {len(phone_numbers) - 3} more")
                
            else:
                print(f"⚠️ API returned error: {result.get('message')}")
        else:
            print(f"❌ API request failed")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Flask app not running. Start with: python3 main.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_direct_bolna_api():
    """Test direct Bolna API call"""
    
    print("\n🔗 Testing Direct Bolna API")
    print("="*40)
    
    try:
        from bolna_integration import BolnaAPI
        
        bolna_api = BolnaAPI()
        response = bolna_api._make_request('GET', '/phone-numbers/all')
        
        print("✅ Direct API call successful!")
        print(f"📊 Response type: {type(response)}")
        
        if isinstance(response, list):
            print(f"📱 Found {len(response)} phone numbers")
            for i, number in enumerate(response[:2], 1):
                print(f"   {i}. {number.get('phone_number', 'N/A')}")
        else:
            print(f"📋 Response: {json.dumps(response, indent=2)[:300]}...")
            
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")

if __name__ == "__main__":
    test_phone_numbers_api()
    test_direct_bolna_api()
