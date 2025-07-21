#!/usr/bin/env python3
"""
Test phone numbers API with proper authentication
"""

import requests
import json

def test_with_login():
    """Test API after logging in"""
    
    print("🔐 Testing with Login Authentication")
    print("="*45)
    
    # First, try to login to get a token
    login_data = {
        "email": "admin@bhashai.com",  # Use an existing admin email
        "password": "admin123"  # Use the correct password
    }
    
    try:
        # Login first
        print("🔑 Attempting login...")
        login_response = requests.post(
            'http://127.0.0.1:5001/api/auth/login',
            headers={'Content-Type': 'application/json'},
            json=login_data,
            timeout=10
        )
        
        print(f"📊 Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                token = login_result.get('token')
                print(f"✅ Login successful! Token: {token[:20]}...")
                
                # Now test the phone numbers API
                print(f"\n📱 Testing phone numbers API...")
                phone_response = requests.get(
                    'http://127.0.0.1:5001/api/bolna/phone-numbers',
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=15
                )
                
                print(f"📊 Phone API Status: {phone_response.status_code}")
                
                if phone_response.status_code == 200:
                    result = phone_response.json()
                    print("✅ Phone numbers API working!")
                    
                    if result.get('success'):
                        summary = result.get('summary', {})
                        print(f"\n📊 Summary:")
                        print(f"   📞 Total Numbers: {summary.get('total_numbers', 0)}")
                        print(f"   💰 Monthly Cost: ${summary.get('monthly_cost', 0):.2f}")
                        print(f"   🏢 Active Providers: {summary.get('active_providers', 0)}")
                        print(f"   🌍 Countries: {summary.get('countries', 0)}")
                        
                        phone_numbers = result.get('phone_numbers', [])
                        if phone_numbers:
                            print(f"\n📱 Your Phone Numbers:")
                            for i, number in enumerate(phone_numbers, 1):
                                status = "🟢 Active" if number.get('rented') else "🔴 Inactive"
                                print(f"   {i}. {number.get('phone_number', 'N/A')} - {number.get('telephony_provider', 'Unknown')} - {status}")
                        
                        return True
                    else:
                        print(f"⚠️ API returned error: {result.get('message')}")
                else:
                    print(f"❌ Phone API failed: {phone_response.text[:200]}...")
            else:
                print(f"❌ Login failed: {login_result.get('error')}")
        else:
            print(f"❌ Login request failed: {login_response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Cannot connect to Flask app. Make sure it's running on port 5001")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    return False

def test_direct_access():
    """Test direct access to the phone management page"""
    
    print(f"\n🌐 Testing Direct Page Access")
    print("="*35)
    
    try:
        response = requests.get(
            'http://127.0.0.1:5001/phone-numbers.html',
            timeout=10
        )
        
        print(f"📊 Page Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Phone management page accessible!")
            print(f"📄 Page size: {len(response.text)} characters")
        else:
            print(f"❌ Page not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Page access failed: {e}")

if __name__ == "__main__":
    success = test_with_login()
    test_direct_access()
    
    if success:
        print(f"\n🎉 All tests passed!")
        print(f"🌐 Access your phone management at:")
        print(f"   http://127.0.0.1:5001/phone-numbers.html")
    else:
        print(f"\n⚠️ Some tests failed. Check the errors above.")
