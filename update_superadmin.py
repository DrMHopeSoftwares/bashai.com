#!/usr/bin/env python3
"""
Update superadmin user from admin@drmhope.com to murali@drmhope.com
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

SUPABASE_HEADERS = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def supabase_request(method, endpoint, data=None, params=None):
    """Make a request to Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=SUPABASE_HEADERS, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=SUPABASE_HEADERS, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=SUPABASE_HEADERS, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=SUPABASE_HEADERS, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=SUPABASE_HEADERS)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Supabase API error ({method} {endpoint}): {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response content: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def update_superadmin():
    """Update superadmin from admin@drmhope.com to murali@drmhope.com"""
    
    print("=" * 60)
    print(" DrM Hope SaaS Platform - Superadmin Update")
    print("=" * 60)
    
    # 1. Check current admin user
    print("\n1. Checking current admin user...")
    current_admin = supabase_request('GET', 'users', params={'email': 'eq.admin@drmhope.com'})
    
    if current_admin and len(current_admin) > 0:
        admin_user = current_admin[0]
        print(f"✅ Found current admin: {admin_user['name']} ({admin_user['email']})")
        print(f"   Role: {admin_user['role']}")
        print(f"   Enterprise ID: {admin_user.get('enterprise_id', 'None')}")
        
        # 2. Check if murali@drmhope.com already exists
        print("\n2. Checking if murali@drmhope.com exists...")
        existing_murali = supabase_request('GET', 'users', params={'email': 'eq.murali@drmhope.com'})
        
        if existing_murali and len(existing_murali) > 0:
            print("✅ murali@drmhope.com already exists - updating role to admin")
            # Update existing user to admin
            update_data = {
                'role': 'admin',
                'status': 'active',
                'name': 'Dr. Murali B.K.',
                'organization': 'DrM Hope Softwares',
                'enterprise_id': admin_user.get('enterprise_id')
            }
            result = supabase_request('PATCH', f'users?email=eq.murali@drmhope.com', data=update_data)
            if result:
                print("✅ Successfully updated murali@drmhope.com to admin")
            else:
                print("❌ Failed to update murali@drmhope.com")
                return False
        else:
            print("📝 murali@drmhope.com not found - creating new admin user")
            # Create new admin user
            new_admin_data = {
                'email': 'murali@drmhope.com',
                'name': 'Dr. Murali B.K.',
                'organization': 'DrM Hope Softwares',
                'role': 'admin',
                'status': 'active',
                'enterprise_id': admin_user.get('enterprise_id'),
                'created_at': admin_user.get('created_at'),
                'updated_at': admin_user.get('updated_at')
            }
            result = supabase_request('POST', 'users', data=new_admin_data)
            if result:
                print("✅ Successfully created murali@drmhope.com as admin")
            else:
                print("❌ Failed to create murali@drmhope.com")
                return False
        
        # 3. Update admin@drmhope.com role to regular user or delete
        print("\n3. Updating admin@drmhope.com...")
        # Option 1: Change to regular user
        downgrade_data = {
            'role': 'user',
            'status': 'inactive'
        }
        result = supabase_request('PATCH', f'users?email=eq.admin@drmhope.com', data=downgrade_data)
        if result:
            print("✅ Successfully downgraded admin@drmhope.com to regular user")
        else:
            print("❌ Failed to downgrade admin@drmhope.com")
            return False
        
        # 4. Verify the changes
        print("\n4. Verifying changes...")
        new_admin = supabase_request('GET', 'users', params={'email': 'eq.murali@drmhope.com'})
        old_admin = supabase_request('GET', 'users', params={'email': 'eq.admin@drmhope.com'})
        
        if new_admin and len(new_admin) > 0:
            user = new_admin[0]
            print(f"✅ New admin verified: {user['name']} ({user['email']})")
            print(f"   Role: {user['role']}")
            print(f"   Status: {user['status']}")
        
        if old_admin and len(old_admin) > 0:
            user = old_admin[0]
            print(f"✅ Old admin updated: {user['name']} ({user['email']})")
            print(f"   Role: {user['role']}")
            print(f"   Status: {user['status']}")
        
        print("\n🎉 Superadmin update completed successfully!")
        print("📧 New superadmin: murali@drmhope.com")
        print("🔑 You can now use murali@drmhope.com to sign up in Clerk")
        return True
        
    else:
        print("❌ Current admin user not found")
        return False

if __name__ == "__main__":
    success = update_superadmin()
    if not success:
        exit(1)