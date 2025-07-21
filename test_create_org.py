#!/usr/bin/env python3
"""
Test organization creation
"""

import requests
import json
import time

def test_create_organization():
    """Test the organization creation endpoint"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🏢 **TESTING ORGANIZATION CREATION**")
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
    
    # Step 2: Create Organization
    print(f"\n2. 🏢 **Creating New Organization**")
    
    org_data = {
        "name": f"Test Organization {int(time.time())}",
        "description": "Test organization created via API",
        "type": "education",
        "status": "active",
        "email": "test@example.com",
        "phone": "+918035315322",
        "address": "Test Address, Test City"
    }
    
    print(f"📋 **Organization Data:**")
    print(f"   🏢 Name: {org_data['name']}")
    print(f"   📊 Type: {org_data['type']}")
    print(f"   📧 Email: {org_data['email']}")
    print(f"   📞 Phone: {org_data['phone']}")
    print(f"   📍 Address: {org_data['address']}")
    
    create_response = requests.post(f"{base_url}/api/organizations", json=org_data, headers=headers)
    
    print(f"\n📊 **Response Status:** {create_response.status_code}")
    
    if create_response.status_code == 201:
        response_data = create_response.json()
        print(f"✅ **Organization Created Successfully!**")
        print(f"📋 **Response Data:**")
        print(json.dumps(response_data, indent=2))
        
        org = response_data.get('organization')
        if org:
            print(f"\n🎯 **Created Organization:**")
            print(f"   🆔 ID: {org.get('id')}")
            print(f"   🏢 Name: {org.get('name')}")
            print(f"   📊 Type: {org.get('type')}")
            print(f"   🔄 Status: {org.get('status')}")
        
        return True
    else:
        print(f"❌ Failed to create organization: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False

if __name__ == "__main__":
    test_create_organization()
