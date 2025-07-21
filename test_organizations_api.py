#!/usr/bin/env python3
"""
Test organizations API endpoint
"""

import requests
import json

def test_organizations_api():
    """Test the organizations API endpoint"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🏢 **TESTING ORGANIZATIONS API**")
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
    
    # Step 2: Get Organizations
    print(f"\n2. 🏢 **Getting Organizations**")
    
    org_response = requests.get(f"{base_url}/api/organizations", headers=headers)
    
    print(f"📊 **Response Status:** {org_response.status_code}")
    
    if org_response.status_code == 200:
        org_data = org_response.json()
        print(f"📋 **Response Data:**")
        print(json.dumps(org_data, indent=2))
        
        # Check if organizations are returned
        organizations = org_data.get('organizations', [])
        print(f"\n📈 **Summary:**")
        print(f"   🏢 Total Organizations: {len(organizations)}")
        
        if organizations:
            print(f"   📋 Organization Names:")
            for i, org in enumerate(organizations, 1):
                print(f"      {i}. {org.get('name')} ({org.get('type')})")
                print(f"         📧 Email: {org.get('email')}")
                print(f"         📞 Phone: {org.get('phone')}")
                print(f"         📍 Address: {org.get('address')}")
                print(f"         🔄 Status: {org.get('status')}")
                print()
        
        current_org = org_data.get('current_organization')
        if current_org:
            print(f"   🎯 Current Organization: {current_org.get('name')}")
        
        return True
    else:
        print(f"❌ Failed to get organizations: {org_response.status_code}")
        print(f"Response: {org_response.text}")
        return False

if __name__ == "__main__":
    test_organizations_api()
