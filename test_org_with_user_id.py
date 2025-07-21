#!/usr/bin/env python3
"""
Test organization creation with user_id
"""

import requests
import json
import time

def test_org_with_user_id():
    """Test organization creation with proper user_id"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🏢 **TESTING ORGANIZATION CREATION WITH USER_ID**")
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
    
    # Step 2: Get User Profile to see user_id
    print(f"\n2. 👤 **Getting User Profile**")
    profile_response = requests.get(f"{base_url}/api/auth/profile", headers=headers)
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        user_id = profile_data.get('user', {}).get('id')
        print(f"   🆔 User ID: {user_id}")
    
    # Step 3: Create Organization with form data format
    print(f"\n3. 🏢 **Creating Organization (Dashboard Format)**")
    
    org_data = {
        "name": "bhupendra",
        "type": "retail",
        "status": "inactive",
        "email": "p@g.c",
        "phone": "222222222222",
        "address": "a",
        "description": "sssss"
    }
    
    print(f"📋 **Organization Data:**")
    for key, value in org_data.items():
        print(f"   {key}: {value}")
    
    create_response = requests.post(f"{base_url}/api/organizations", json=org_data, headers=headers)
    
    print(f"\n📊 **Response Status:** {create_response.status_code}")
    
    if create_response.status_code == 201:
        response_data = create_response.json()
        print(f"✅ **Organization Created Successfully!**")
        print(f"📋 **Response Data:**")
        print(json.dumps(response_data, indent=2))
        
        org = response_data.get('organization')
        if org:
            print(f"\n🎯 **Created Organization Details:**")
            print(f"   🆔 ID: {org.get('id')}")
            print(f"   🏢 Name: {org.get('name')}")
            print(f"   📊 Type: {org.get('type')}")
            print(f"   🔄 Status: {org.get('status')}")
            print(f"   👤 User ID: {org.get('user_id')}")
            print(f"   📧 Email: {org.get('email')}")
            print(f"   📞 Phone: {org.get('phone')}")
            print(f"   📍 Address: {org.get('address')}")
        
        return True
    else:
        print(f"❌ Failed to create organization: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False

if __name__ == "__main__":
    test_org_with_user_id()
