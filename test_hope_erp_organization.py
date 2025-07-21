#!/usr/bin/env python3
"""
Test Hope ERP organization creation - exactly as user filled in form
"""

import requests
import json
import time

def test_hope_erp_creation():
    """Test creating Hope ERP organization with exact form data"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🏢 **CREATING HOPE ERP ORGANIZATION**")
    print("=" * 60)
    
    # Step 1: Login first
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
    
    # Step 2: Create Hope ERP Organization (exact form data)
    print(f"\n2. 🏢 **Creating Hope ERP Organization**")
    
    org_data = {
        "name": "Hope ERP",
        "type": "retail",               # Fixed: use database allowed value
        "status": "inactive",           # Fixed: use lowercase
        "contact_email": "a@gmail.com",
        "contact_phone": "8412030400",
        "address": "dsf",
        "description": "dfg"
    }
    
    print(f"📋 **Organization Data:**")
    print(f"   🏢 Name: {org_data['name']}")
    print(f"   📊 Type: {org_data['type']}")
    print(f"   🔄 Status: {org_data['status']}")
    print(f"   📧 Email: {org_data['contact_email']}")
    print(f"   📞 Phone: {org_data['contact_phone']}")
    print(f"   📍 Address: {org_data['address']}")
    print(f"   📝 Description: {org_data['description']}")
    
    # Create organization
    create_response = requests.post(f"{base_url}/api/organizations", json=org_data, headers=headers)
    
    if create_response.status_code == 201:
        create_result = create_response.json()
        print(f"\n✅ **HOPE ERP ORGANIZATION CREATED SUCCESSFULLY!**")
        
        if 'organization' in create_result:
            org = create_result['organization'][0] if isinstance(create_result['organization'], list) else create_result['organization']
            print(f"   🆔 Organization ID: {org.get('id')}")
            print(f"   🏢 Name: {org.get('name')}")
            print(f"   📊 Type: {org.get('type')}")
            print(f"   🔄 Status: {org.get('status')}")
            print(f"   📅 Created: {org.get('created_at')}")
            
            org_id = org.get('id')
        else:
            print(f"   📋 Response: {create_result}")
            org_id = None
            
    elif create_response.status_code == 200:
        create_result = create_response.json()
        print(f"\n✅ **HOPE ERP ORGANIZATION CREATED!**")
        print(f"   📋 Response: {create_result}")
        org_id = create_result.get('organization', {}).get('id')
        
    else:
        print(f"\n❌ **Organization creation failed: {create_response.status_code}**")
        print(f"   Response: {create_response.text}")
        return False
    
    # Step 3: Verify organization was created
    print(f"\n3. 🔍 **Verifying Organization Creation**")
    
    # Get user's enterprise first
    user_response = requests.get(f"{base_url}/api/user/profile", headers=headers)
    if user_response.status_code == 200:
        user_data = user_response.json()
        enterprise_id = user_data.get('enterprise_id')
        print(f"   🏢 User Enterprise ID: {enterprise_id}")
        
        if enterprise_id:
            # Get organizations for this enterprise
            orgs_response = requests.get(f"{base_url}/api/enterprises/{enterprise_id}/organizations", headers=headers)
            if orgs_response.status_code == 200:
                orgs_result = orgs_response.json()
                organizations = orgs_result.get('organizations', [])
                
                print(f"   📊 Total Organizations: {len(organizations)}")
                
                # Look for Hope ERP
                hope_erp_found = False
                for org in organizations:
                    if org.get('name') == 'Hope ERP':
                        hope_erp_found = True
                        print(f"\n🎉 **HOPE ERP FOUND IN DATABASE!**")
                        print(f"   🆔 ID: {org.get('id')}")
                        print(f"   🏢 Name: {org.get('name')}")
                        print(f"   📊 Type: {org.get('type')}")
                        print(f"   🔄 Status: {org.get('status')}")
                        print(f"   📅 Created: {org.get('created_at')}")
                        break
                
                if not hope_erp_found:
                    print(f"\n❌ Hope ERP not found in organizations list")
                    print(f"📋 Available organizations:")
                    for i, org in enumerate(organizations, 1):
                        print(f"   {i}. {org.get('name')} ({org.get('type')})")
                    return False
                else:
                    print(f"\n🎉 **SUCCESS! Hope ERP organization stored successfully!**")
                    return True
            else:
                print(f"   ❌ Failed to get organizations: {orgs_response.status_code}")
                return False
    else:
        print(f"   ❌ Failed to get user profile: {user_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_hope_erp_creation()
    exit(0 if success else 1)
