#!/usr/bin/env python3
"""
Create a test user for testing the phone numbers API
"""

import requests
import json

def create_test_user():
    """Create a test user via the registration API"""
    
    print("👤 Creating Test User")
    print("="*25)
    
    # Test user data for public signup
    user_data = {
        "name": "Test Phone Company",  # Enterprise name
        "owner_name": "Phone Test User",  # Owner's name
        "contact_email": "test@phonetest.com",
        "contact_phone": "+919876543210",
        "password": "test123",
        "type": "other",
        "enterprise_id": "other"
    }

    try:
        # Register the user via public signup
        print("📝 Registering test user via public signup...")
        response = requests.post(
            'http://127.0.0.1:5001/api/public/signup',
            headers={'Content-Type': 'application/json'},
            json=user_data,
            timeout=10
        )
        
        print(f"📊 Registration Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success'):
                print("✅ Test user created successfully!")
                return user_data
            else:
                print(f"⚠️ Registration failed: {result.get('error')}")
        else:
            print(f"❌ Registration request failed")
            
    except Exception as e:
        print(f"❌ User creation failed: {e}")
    
    return None

def test_login_and_phone_api():
    """Test login and phone API with the test user"""
    
    print(f"\n🔐 Testing Login and Phone API")
    print("="*35)
    
    # Login data
    login_data = {
        "email": "test@phonetest.com",
        "password": "test123"
    }
    
    try:
        # Login
        print("🔑 Logging in...")
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
                print(f"✅ Login successful!")
                
                # Test phone numbers API
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
                        print(f"\n📊 Phone Numbers Summary:")
                        print(f"   📞 Total Numbers: {summary.get('total_numbers', 0)}")
                        print(f"   💰 Monthly Cost: ${summary.get('monthly_cost', 0):.2f}")
                        print(f"   🏢 Active Providers: {summary.get('active_providers', 0)}")
                        print(f"   🌍 Countries: {summary.get('countries', 0)}")
                        
                        phone_numbers = result.get('phone_numbers', [])
                        if phone_numbers:
                            print(f"\n📱 Available Phone Numbers:")
                            for i, number in enumerate(phone_numbers, 1):
                                status = "🟢 Active" if number.get('rented') else "🔴 Inactive"
                                provider = number.get('telephony_provider', 'Unknown')
                                cost = number.get('price', '$0.00')
                                renewal = number.get('renewal_at', 'N/A')
                                print(f"   {i}. {number.get('phone_number', 'N/A')}")
                                print(f"      Provider: {provider} | Cost: {cost} | Status: {status}")
                                print(f"      Renewal: {renewal}")
                                print()
                        
                        return True
                    else:
                        print(f"⚠️ API returned error: {result.get('message')}")
                else:
                    print(f"❌ Phone API failed: {phone_response.text[:200]}...")
            else:
                print(f"❌ Login failed: {login_result.get('error')}")
        else:
            print(f"❌ Login request failed: {login_response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    return False

if __name__ == "__main__":
    # Create test user
    user_created = create_test_user()
    
    if user_created:
        # Test the API
        success = test_login_and_phone_api()
        
        if success:
            print(f"\n🎉 All tests passed!")
            print(f"🌐 You can now access:")
            print(f"   📱 Phone Management: http://127.0.0.1:5001/phone-numbers.html")
            print(f"   🤖 Agent Management: http://127.0.0.1:5001/bolna-agents.html")
            print(f"   📊 Dashboard: http://127.0.0.1:5001/dashboard.html")
            print(f"\n🔑 Test Login Credentials:")
            print(f"   Email: test@phonetest.com")
            print(f"   Password: test123")
        else:
            print(f"\n⚠️ API tests failed. Check the errors above.")
    else:
        print(f"\n❌ Could not create test user. Check the errors above.")
