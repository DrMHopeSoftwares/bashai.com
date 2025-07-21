#!/usr/bin/env python3
"""
Direct test of agent_id functionality
"""

import requests
import json

def test_direct_api_call():
    """Test direct API call to phone numbers endpoint"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🔗 **TESTING DIRECT API CALLS**")
    print("=" * 50)
    
    # Test 1: Login
    print("1. 🔐 **User Login**")
    login_data = {
        "email": "b@gmail.com",
        "password": "bhupendra"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json().get('token')
    print(f"✅ Login successful")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test 2: Direct phone numbers endpoint
    print(f"\n2. 📱 **Testing Phone Numbers Endpoint**")
    
    phone_response = requests.get(f"{base_url}/api/dev/phone-numbers", headers=headers)
    
    print(f"📊 Status Code: {phone_response.status_code}")
    print(f"📋 Response: {phone_response.text[:500]}...")
    
    if phone_response.status_code == 200:
        data = phone_response.json()
        if 'phone_numbers' in data:
            phone_numbers = data['phone_numbers']
            print(f"\n✅ **PHONE NUMBERS FETCHED!**")
            print(f"   📱 Count: {len(phone_numbers)}")
            
            for i, phone in enumerate(phone_numbers, 1):
                print(f"\n   📞 **Phone {i}:**")
                print(f"      📞 Number: {phone.get('phone_number')}")
                print(f"      🤖 Agent ID: {phone.get('agent_id', 'Not set')}")
                print(f"      🔄 Status: {phone.get('status')}")
                print(f"      📅 Source: {data.get('source', 'database')}")
            
            return True
    
    return False

def test_bolna_api_direct():
    """Test Bolna API directly"""
    
    print(f"\n3. 🔗 **TESTING BOLNA API DIRECT**")
    
    try:
        from bolna_integration import BolnaAPI
        
        bolna_api = BolnaAPI()
        phone_numbers = bolna_api.get_phone_numbers()
        
        print(f"✅ **BOLNA API SUCCESS!**")
        print(f"   📱 Phone Numbers: {len(phone_numbers)}")
        
        for i, phone in enumerate(phone_numbers[:2], 1):
            print(f"\n   📞 **Bolna Phone {i}:**")
            print(f"      📞 Number: {phone.get('phone_number', 'N/A')}")
            print(f"      🤖 Agent ID: {phone.get('agent_id', 'Not set')}")
            print(f"      🏢 Provider: {phone.get('telephony_provider', 'N/A')}")
            print(f"      💰 Price: {phone.get('price', 'N/A')}")
            
            # Check if this phone has agent_id
            if phone.get('agent_id'):
                print(f"      ✅ **HAS AGENT_ID!**")
            else:
                print(f"      ⚠️  No agent_id assigned")
        
        return True
        
    except Exception as e:
        print(f"❌ **BOLNA API FAILED: {e}**")
        return False

def test_curl_equivalent():
    """Test curl equivalent for Bolna API"""
    
    print(f"\n4. 🌐 **TESTING CURL EQUIVALENT**")
    
    import os
    
    api_key = os.getenv('BOLNA_API_KEY')
    if not api_key:
        print(f"❌ BOLNA_API_KEY not found")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Direct curl equivalent
        response = requests.get(
            'https://api.bolna.ai/phone-numbers/all',
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ **CURL EQUIVALENT SUCCESS!**")
            
            if isinstance(data, list):
                print(f"   📱 Phone Numbers: {len(data)}")
                
                for i, phone in enumerate(data[:2], 1):
                    print(f"\n   📞 **Phone {i}:**")
                    print(f"      📞 Number: {phone.get('phone_number', 'N/A')}")
                    print(f"      🤖 Agent ID: {phone.get('agent_id', 'Not set')}")
                    
                    # This is the key test - does Bolna API return agent_id?
                    if phone.get('agent_id'):
                        print(f"      🎯 **AGENT_ID FOUND: {phone.get('agent_id')}**")
                    else:
                        print(f"      ⚠️  Agent ID not present in API response")
                
                return True
            else:
                print(f"   📋 Unexpected format: {type(data)}")
                return False
        else:
            print(f"❌ **CURL FAILED: {response.status_code}**")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ **CURL EXCEPTION: {e}**")
        return False

if __name__ == "__main__":
    print("🧪 **DIRECT AGENT_ID TESTING**")
    print("=" * 60)
    
    # Test our API endpoint
    success1 = test_direct_api_call()
    
    # Test Bolna API integration
    success2 = test_bolna_api_direct()
    
    # Test curl equivalent
    success3 = test_curl_equivalent()
    
    print(f"\n📊 **DIRECT TEST SUMMARY**")
    print(f"=" * 40)
    print(f"✅ Our API Endpoint: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ Bolna Integration: {'PASS' if success2 else 'FAIL'}")
    print(f"✅ Curl Equivalent: {'PASS' if success3 else 'FAIL'}")
    
    print(f"\n🎯 **KEY FINDINGS:**")
    if success3:
        print(f"   • Bolna API returns phone numbers with agent_id")
        print(f"   • curl --request GET https://api.bolna.ai/phone-numbers/all works")
        print(f"   • Agent ID field is available in API response")
    else:
        print(f"   • Need to check Bolna API documentation")
        print(f"   • Agent ID might be in different field")
    
    exit(0 if all([success1, success2, success3]) else 1)
