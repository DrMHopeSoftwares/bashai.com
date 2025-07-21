#!/usr/bin/env python3
"""
Test user profile to see enterprise_id
"""

import requests
import json

def test_user_profile():
    """Test the user profile endpoint"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("👤 **TESTING USER PROFILE**")
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
    print(f"🔑 Token: {token[:50]}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Get User Profile
    print(f"\n2. 👤 **Getting User Profile**")
    
    profile_response = requests.get(f"{base_url}/api/auth/profile", headers=headers)
    
    print(f"📊 **Response Status:** {profile_response.status_code}")
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(f"📋 **Profile Data:**")
        print(json.dumps(profile_data, indent=2))
        
        # Check enterprise_id
        enterprise_id = profile_data.get('enterprise_id')
        print(f"\n📈 **Key Information:**")
        print(f"   🆔 User ID: {profile_data.get('user_id')}")
        print(f"   📧 Email: {profile_data.get('email')}")
        print(f"   👤 Role: {profile_data.get('role')}")
        print(f"   🏢 Enterprise ID: {enterprise_id}")
        print(f"   🏛️ Organization: {profile_data.get('organization')}")
        
        return True
    else:
        print(f"❌ Failed to get profile: {profile_response.status_code}")
        print(f"Response: {profile_response.text}")
        return False

if __name__ == "__main__":
    test_user_profile()
