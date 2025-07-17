#!/usr/bin/env python3
"""
Complete test for enterprise signup flow
"""

import requests
import time
import json

def test_complete_enterprise_flow():
    """Test complete enterprise signup flow"""
    
    base_url = "http://127.0.0.1:3000"
    
    print("🧪 Testing Complete Enterprise Signup Flow...")
    print("=" * 60)
    
    # Step 1: Test enterprises API
    print("\n📋 Step 1: Testing Enterprises API...")
    try:
        enterprises_response = requests.get(f"{base_url}/api/public/enterprises")
        
        if enterprises_response.status_code == 200:
            enterprises_data = enterprises_response.json()
            if enterprises_data.get('success') and enterprises_data.get('enterprises'):
                enterprises = enterprises_data['enterprises']
                print(f"✅ Found {len(enterprises)} enterprises")
                
                # Show first 5 enterprises
                print("📋 Available enterprises:")
                for i, ent in enumerate(enterprises[:5]):
                    print(f"  {i+1}. {ent['name']} (ID: {ent['id'][:8]}...)")
                
                selected_enterprise = enterprises[0]
                enterprise_id = selected_enterprise['id']
                enterprise_name = selected_enterprise['name']
                
            else:
                print("❌ No enterprises found")
                return False
        else:
            print(f"❌ Failed to get enterprises: {enterprises_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting enterprises: {e}")
        return False
    
    # Step 2: Test signup with enterprise_id
    print(f"\n👤 Step 2: Testing Signup with Enterprise ID...")
    try:
        test_email = f"testuser_{int(time.time())}@example.com"
        
        signup_data = {
            "name": "Test Enterprise Company",
            "owner_name": "Test Owner",
            "contact_email": test_email,
            "contact_phone": "+91 9876543210",
            "password": "test123456",
            "type": enterprise_id,
            "enterprise_id": enterprise_id,
            "status": "trial"
        }
        
        print(f"📧 Test Email: {test_email}")
        print(f"🏢 Enterprise: {enterprise_name}")
        print(f"🆔 Enterprise ID: {enterprise_id[:8]}...")
        
        response = requests.post(
            f"{base_url}/api/public/signup",
            headers={'Content-Type': 'application/json'},
            json=signup_data
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Validate response structure
            if response_data.get('success'):
                user_data = response_data.get('user', {})
                token = response_data.get('token')
                
                print("✅ Signup successful!")
                print(f"👤 User ID: {user_data.get('id', 'N/A')[:8]}...")
                print(f"📧 Email: {user_data.get('email', 'N/A')}")
                print(f"👑 Role: {user_data.get('role', 'N/A')}")
                print(f"🏢 Enterprise ID: {user_data.get('enterprise_id', 'N/A')[:8] if user_data.get('enterprise_id') else 'N/A'}...")
                print(f"🔑 Token: {'✅ Present' if token else '❌ Missing'}")
                
                # Validate enterprise_id
                if user_data.get('enterprise_id') == enterprise_id:
                    print("✅ Enterprise ID correctly stored!")
                else:
                    print("❌ Enterprise ID mismatch!")
                    return False
                
                # Step 3: Test login with created user
                print(f"\n🔐 Step 3: Testing Login with Created User...")
                login_data = {
                    "email": test_email,
                    "password": "test123456"
                }
                
                login_response = requests.post(
                    f"{base_url}/api/auth/login",
                    headers={'Content-Type': 'application/json'},
                    json=login_data
                )
                
                if login_response.status_code == 200:
                    login_response_data = login_response.json()
                    if login_response_data.get('success'):
                        print("✅ Login successful!")
                        
                        # Step 4: Test profile API
                        print(f"\n👤 Step 4: Testing Profile API...")
                        profile_headers = {
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        }
                        
                        profile_response = requests.get(
                            f"{base_url}/api/auth/profile",
                            headers=profile_headers
                        )
                        
                        if profile_response.status_code == 200:
                            profile_data = profile_response.json()
                            print("✅ Profile API working!")
                            print(f"👤 Profile Enterprise ID: {profile_data.get('enterprise_id', 'N/A')[:8] if profile_data.get('enterprise_id') else 'N/A'}...")
                            
                            if profile_data.get('enterprise_id') == enterprise_id:
                                print("✅ Profile enterprise_id matches!")
                            else:
                                print("❌ Profile enterprise_id mismatch!")
                                return False
                        else:
                            print(f"❌ Profile API failed: {profile_response.status_code}")
                            return False
                    else:
                        print("❌ Login failed!")
                        return False
                else:
                    print(f"❌ Login request failed: {login_response.status_code}")
                    return False
                
            else:
                print("❌ Signup failed!")
                print(response_data.get('message', 'Unknown error'))
                return False
        else:
            print(f"❌ Signup request failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error during signup: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Enterprise API working")
    print("✅ Signup with enterprise_id working")
    print("✅ Login working")
    print("✅ Profile API working")
    print("✅ Enterprise ID properly stored and retrieved")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_complete_enterprise_flow()
    if not success:
        print("\n💥 SOME TESTS FAILED!")
        exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED!")
        exit(0)
