#!/usr/bin/env python3
"""
Debug login to check enterprise_id in JWT token
"""

import requests
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

def debug_login_enterprise_id():
    """Debug login to check enterprise_id"""
    
    base_url = "http://127.0.0.1:3000"
    
    # Use a test user that we know has enterprise_id
    test_email = "testuser_1752555737@example.com"
    test_password = "test123456"
    
    print("🔍 Debugging Login Enterprise ID...")
    print(f"📧 Test Email: {test_email}")
    
    try:
        # Step 1: Login
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            json=login_data
        )
        
        print(f"📊 Login Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('success'):
                token = response_data.get('token')
                print("✅ Login successful!")
                print(f"🔑 Token: {token[:50]}...")
                
                # Decode JWT token to see payload
                try:
                    # Get JWT secret from environment
                    jwt_secret = os.getenv('JWT_SECRET_KEY', 'default-secret')
                    
                    # Try to decode without verification first
                    decoded_payload = jwt.decode(token, options={"verify_signature": False})
                    print("\n🔍 JWT Payload:")
                    for key, value in decoded_payload.items():
                        if key == 'enterprise_id':
                            print(f"  🏢 {key}: {value}")
                        elif key == 'exp':
                            print(f"  ⏰ {key}: {value}")
                        else:
                            print(f"  📝 {key}: {value}")
                    
                    # Check if enterprise_id is present
                    if decoded_payload.get('enterprise_id'):
                        print(f"\n✅ Enterprise ID found in JWT: {decoded_payload['enterprise_id']}")
                    else:
                        print(f"\n❌ Enterprise ID missing from JWT!")
                        
                except Exception as e:
                    print(f"❌ Error decoding JWT: {e}")
                
                # Step 2: Test profile API
                print(f"\n👤 Testing Profile API...")
                profile_headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                profile_response = requests.get(
                    f"{base_url}/api/auth/profile",
                    headers=profile_headers
                )
                
                print(f"📊 Profile Response Status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print("✅ Profile API successful!")
                    print(f"🏢 Profile Enterprise ID: {profile_data.get('enterprise_id', 'N/A')}")
                else:
                    print(f"❌ Profile API failed: {profile_response.text}")
                    
            else:
                print("❌ Login failed!")
                print(response_data.get('message', 'Unknown error'))
        else:
            print(f"❌ Login request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_login_enterprise_id()
