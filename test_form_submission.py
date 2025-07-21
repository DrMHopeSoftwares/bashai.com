#!/usr/bin/env python3
"""
Test form submission with exact form data
"""

import requests
import json

def test_form_submission():
    """Test organization creation with form data"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🏢 **TESTING FORM SUBMISSION**")
    print("=" * 50)
    
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
    
    # Step 2: Create Organization with exact form field names
    print(f"\n2. 🏢 **Creating Organization (Form Fields)**")
    
    # Exact data from form fields
    org_data = {
        "name": "Shopendra",
        "type": "retail",
        "status": "inactive", 
        "email": "p@g.c",
        "phone": "222222222222",
        "address": "good",
        "description": "sssss"
    }
    
    print(f"📋 **Form Data:**")
    for key, value in org_data.items():
        print(f"   {key}: '{value}'")
    
    create_response = requests.post(f"{base_url}/api/organizations", json=org_data, headers=headers)
    
    print(f"\n📊 **Response Status:** {create_response.status_code}")
    
    if create_response.status_code == 201:
        response_data = create_response.json()
        print(f"✅ **Organization Created Successfully!**")
        
        org = response_data.get('organization')
        if org:
            print(f"\n🎯 **Created Organization:**")
            print(f"   🆔 ID: {org.get('id')}")
            print(f"   🏢 Name: '{org.get('name')}'")
            print(f"   📊 Type: '{org.get('type')}'")
            print(f"   🔄 Status: '{org.get('status')}'")
            print(f"   👤 User ID: {org.get('user_id')}")
            
            # Check if name is null or empty
            if not org.get('name') or org.get('name') == 'null':
                print(f"❌ **ERROR: Organization name is null/empty!**")
                return False
            else:
                print(f"✅ **Organization name properly saved: '{org.get('name')}'**")
        
        return True
    else:
        print(f"❌ Failed to create organization: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False

if __name__ == "__main__":
    test_form_submission()
