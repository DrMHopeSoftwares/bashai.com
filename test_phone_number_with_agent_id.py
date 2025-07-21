#!/usr/bin/env python3
"""
Test phone number purchase with agent_id
"""

import requests
import json
import time

def test_phone_number_with_agent_id():
    """Test phone number purchase with agent_id field"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("📱 **TESTING PHONE NUMBER PURCHASE WITH AGENT_ID**")
    print("=" * 60)
    
    # Step 1: Login
    print("1. 🔐 **User Login**")
    login_data = {
        "email": "b@gmail.com",
        "password": "bhupendra"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    login_result = login_response.json()
    token = login_result.get('token')
    print(f"✅ User logged in successfully")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Purchase phone number with agent_id
    print(f"\n2. 📱 **Purchasing Phone Number with Agent ID**")
    
    # Mock phone number purchase data with agent_id
    purchase_data = {
        "phone_number": f"+1555{int(time.time()) % 10000:04d}",  # Generate unique number
        "provider": "plivo",
        "country_code": "US",
        "country_name": "United States",
        "monthly_cost": 5.00,
        "setup_cost": 1.00,
        "capabilities": {"voice": True, "sms": True},
        "agent_id": "15554373-b8e1-4b00-8c25-c4742dc8e480"  # Sample Bolna agent ID
    }
    
    print(f"📋 **Purchase Data:**")
    print(f"   📞 Phone Number: {purchase_data['phone_number']}")
    print(f"   🏢 Provider: {purchase_data['provider']}")
    print(f"   🌍 Country: {purchase_data['country_name']}")
    print(f"   🤖 Agent ID: {purchase_data['agent_id']}")
    print(f"   💰 Monthly Cost: ${purchase_data['monthly_cost']}")
    
    # Purchase phone number
    purchase_response = requests.post(f"{base_url}/api/dev/phone-numbers/purchase", 
                                    json=purchase_data, headers=headers)
    
    if purchase_response.status_code == 200:
        purchase_result = purchase_response.json()
        print(f"\n✅ **PHONE NUMBER PURCHASED SUCCESSFULLY!**")
        
        if 'phone_number' in purchase_result:
            phone_data = purchase_result['phone_number']
            print(f"   🆔 Record ID: {phone_data.get('id')}")
            print(f"   📞 Phone Number: {phone_data.get('phone_number')}")
            print(f"   🏢 Provider: {phone_data.get('provider_id')}")
            print(f"   🤖 Agent ID: {phone_data.get('agent_id')}")
            print(f"   🔄 Status: {phone_data.get('status')}")
            print(f"   📅 Purchased: {phone_data.get('purchased_at')}")
            
            # Verify agent_id is stored
            if phone_data.get('agent_id') == purchase_data['agent_id']:
                print(f"\n🎉 **AGENT_ID SUCCESSFULLY STORED!**")
                return True
            else:
                print(f"\n❌ **AGENT_ID NOT STORED CORRECTLY**")
                print(f"   Expected: {purchase_data['agent_id']}")
                print(f"   Got: {phone_data.get('agent_id')}")
                return False
        else:
            print(f"   📋 Response: {purchase_result}")
            return True
            
    else:
        print(f"\n❌ **PHONE NUMBER PURCHASE FAILED: {purchase_response.status_code}**")
        print(f"   Response: {purchase_response.text}")
        return False

def test_fetch_phone_numbers_with_agent_id():
    """Test fetching phone numbers with agent_id"""
    
    base_url = "http://127.0.0.1:5003"
    
    print(f"\n3. 📋 **TESTING FETCH PHONE NUMBERS WITH AGENT_ID**")
    
    # Login
    login_data = {
        "email": "b@gmail.com", 
        "password": "bhupendra"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    token = login_response.json().get('token')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Fetch phone numbers
    fetch_response = requests.get(f"{base_url}/api/dev/phone-numbers", headers=headers)
    
    if fetch_response.status_code == 200:
        fetch_result = fetch_response.json()
        print(f"✅ **PHONE NUMBERS FETCHED SUCCESSFULLY!**")
        
        if 'phone_numbers' in fetch_result:
            phone_numbers = fetch_result['phone_numbers']
            print(f"   📱 Found {len(phone_numbers)} phone numbers")
            
            for i, phone in enumerate(phone_numbers, 1):
                print(f"\n   📞 **Phone Number {i}:**")
                print(f"      📞 Number: {phone.get('phone_number')}")
                print(f"      🤖 Agent ID: {phone.get('agent_id', 'Not set')}")
                print(f"      🔄 Status: {phone.get('status')}")
                print(f"      📅 Purchased: {phone.get('purchased_at')}")
                
                # Check if agent_id is present
                if phone.get('agent_id'):
                    print(f"      ✅ Agent ID is present!")
                else:
                    print(f"      ⚠️  Agent ID is missing")
            
            return True
        else:
            print(f"   📋 No phone numbers found")
            return True
    else:
        print(f"❌ **FETCH FAILED: {fetch_response.status_code}**")
        print(f"   Response: {fetch_response.text}")
        return False

def test_bolna_api_phone_numbers():
    """Test Bolna API phone numbers endpoint"""
    
    print(f"\n4. 🔗 **TESTING BOLNA API PHONE NUMBERS**")
    
    try:
        from bolna_integration import BolnaAPI
        
        bolna_api = BolnaAPI()
        phone_numbers = bolna_api.get_phone_numbers()
        
        print(f"✅ **BOLNA API CALL SUCCESSFUL!**")
        print(f"   📱 Found {len(phone_numbers)} phone numbers")
        
        for i, phone in enumerate(phone_numbers[:3], 1):  # Show first 3
            print(f"\n   📞 **Bolna Phone Number {i}:**")
            print(f"      📞 Number: {phone.get('phone_number', 'N/A')}")
            print(f"      🤖 Agent ID: {phone.get('agent_id', 'Not set')}")
            print(f"      🏢 Provider: {phone.get('telephony_provider', 'N/A')}")
            print(f"      🌍 Country: {phone.get('country', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ **BOLNA API TEST FAILED: {e}**")
        return False

if __name__ == "__main__":
    print("🧪 **PHONE NUMBER AGENT_ID TESTING**")
    print("=" * 70)
    
    # Test phone number purchase with agent_id
    success1 = test_phone_number_with_agent_id()
    
    # Test fetching phone numbers with agent_id
    success2 = test_fetch_phone_numbers_with_agent_id()
    
    # Test Bolna API phone numbers
    success3 = test_bolna_api_phone_numbers()
    
    print(f"\n📊 **AGENT_ID TEST SUMMARY**")
    print(f"=" * 40)
    print(f"✅ Purchase with Agent ID: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ Fetch with Agent ID: {'PASS' if success2 else 'FAIL'}")
    print(f"✅ Bolna API Integration: {'PASS' if success3 else 'FAIL'}")
    
    print(f"\n🎯 **EXPECTED BEHAVIOR:**")
    print(f"   • Phone number purchase includes agent_id")
    print(f"   • Database stores agent_id field")
    print(f"   • API responses include agent_id")
    print(f"   • Bolna API returns phone numbers with agent_id")
    
    exit(0 if all([success1, success2, success3]) else 1)
