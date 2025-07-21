#!/usr/bin/env python3
"""
Test exact form data from screenshot
"""

import requests
import json

def test_exact_form_data():
    """Test with exact data from user's form"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🎯 **TESTING EXACT FORM DATA FROM SCREENSHOT**")
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
    
    # Step 2: Test with exact form data from screenshot
    print(f"\n2. 🏢 **Creating Organization with Exact Form Data**")
    
    # Exact data from screenshot
    org_data = {
        "name": "bhupendra",                    # Organization Name from form
        "type": "retail",                       # Value from "Retail / E-commerce" option
        "status": "inactive",                   # Status from dropdown
        "contact_email": "ag@gmail.com",        # Contact Email from form
        "contact_phone": "8412030400",          # Contact Phone from form
        "address": "fdfdfd",                    # Address from form
        "description": "fdfdfd"                 # Description from form
    }
    
    print(f"📋 **Exact Form Data:**")
    print(f"   🏢 Name: '{org_data['name']}'")
    print(f"   📊 Type: '{org_data['type']}'")
    print(f"   🔄 Status: '{org_data['status']}'")
    print(f"   📧 Email: '{org_data['contact_email']}'")
    print(f"   📞 Phone: '{org_data['contact_phone']}'")
    print(f"   📍 Address: '{org_data['address']}'")
    print(f"   📝 Description: '{org_data['description']}'")
    
    # Create organization
    print(f"\n📤 **Sending POST request to /api/organizations**")
    create_response = requests.post(f"{base_url}/api/organizations", json=org_data, headers=headers)
    
    print(f"📥 **Response Status**: {create_response.status_code}")
    
    if create_response.status_code == 201:
        create_result = create_response.json()
        print(f"\n✅ **ORGANIZATION CREATED SUCCESSFULLY!**")
        
        if 'organization' in create_result:
            org = create_result['organization']
            print(f"   🆔 Organization ID: {org.get('id')}")
            print(f"   🏢 Name: {org.get('name')}")
            print(f"   📊 Type: {org.get('type')}")
            print(f"   🔄 Status: {org.get('status')}")
            print(f"   📅 Created: {org.get('created_at')}")
            
            print(f"\n🍞 **TOAST MESSAGE WILL APPEAR:**")
            print(f"   '🎉 Organization created successfully!'")
            print(f"   Green background, 3 seconds duration")
            
            return True
        else:
            print(f"   📋 Response: {create_result}")
            return True
            
    else:
        print(f"\n❌ **ORGANIZATION CREATION FAILED**")
        print(f"   Status Code: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        
        try:
            error_data = create_response.json()
            print(f"   Error Message: {error_data.get('message', 'Unknown error')}")
        except:
            pass
        
        print(f"\n🍞 **ERROR TOAST MESSAGE WILL APPEAR:**")
        print(f"   '❌ Error saving organization: [error details]'")
        print(f"   Red background, 3 seconds duration")
        
        return False

if __name__ == "__main__":
    success = test_exact_form_data()
    
    print(f"\n📊 **RESULT**")
    print(f"=" * 30)
    if success:
        print(f"✅ Form data is valid and organization created!")
        print(f"🎯 User should see green success toast")
        print(f"📋 Organization will appear in dashboard list")
    else:
        print(f"❌ Form data has issues")
        print(f"🎯 User should see red error toast")
        print(f"🔧 Check server logs for details")
    
    exit(0 if success else 1)
