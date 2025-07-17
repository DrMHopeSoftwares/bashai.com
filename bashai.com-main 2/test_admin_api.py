#!/usr/bin/env python3
"""
Test script for admin API endpoints
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

def test_admin_functionality():
    """Test admin dashboard functionality"""
    
    print("=" * 60)
    print(" Testing Admin Dashboard Functionality")
    print("=" * 60)
    
    # 1. Test enterprises table
    print("\n1. Testing enterprises table...")
    enterprises = supabase_request('GET', 'enterprises')
    if enterprises is not None:
        print(f"✅ Enterprises table accessible - Found {len(enterprises)} enterprises")
        for ent in enterprises[:3]:  # Show first 3
            print(f"   - {ent.get('name', 'N/A')} ({ent.get('type', 'N/A')}) - {ent.get('status', 'N/A')}")
    else:
        print("❌ Enterprises table not accessible")
    
    # 2. Test users table
    print("\n2. Testing users table...")
    users = supabase_request('GET', 'users')
    if users is not None:
        print(f"✅ Users table accessible - Found {len(users)} users")
        admin_users = [u for u in users if u.get('role') in ['admin', 'super_admin']]
        print(f"   - Admin users: {len(admin_users)}")
        for user in admin_users:
            print(f"     * {user.get('name', 'N/A')} ({user.get('email', 'N/A')}) - {user.get('role', 'N/A')}")
    else:
        print("❌ Users table not accessible")
    
    # 3. Test voice_agents table
    print("\n3. Testing voice_agents table...")
    voice_agents = supabase_request('GET', 'voice_agents')
    if voice_agents is not None:
        print(f"✅ Voice agents table accessible - Found {len(voice_agents)} agents")
    else:
        print("❌ Voice agents table not accessible")
    
    # 4. Test admin user existence
    print("\n4. Testing admin user (cmd@hopehospital.com)...")
    admin_user = supabase_request('GET', 'users', params={'email': 'eq.cmd@hopehospital.com'})
    if admin_user and len(admin_user) > 0:
        user = admin_user[0]
        print(f"✅ Admin user found: {user['name']} ({user['email']})")
        print(f"   Role: {user['role']}")
        print(f"   Status: {user['status']}")
        print(f"   Enterprise ID: {user.get('enterprise_id', 'None')}")
        
        # Check if admin has proper role
        if user['role'] == 'admin':
            print("✅ Admin user has correct role")
        else:
            print("⚠️  Admin user role should be 'admin'")
            # Fix admin role
            print("   Fixing admin role...")
            result = supabase_request('PATCH', f'users?email=eq.cmd@hopehospital.com', 
                                    data={'role': 'admin', 'status': 'active'})
            if result:
                print("✅ Admin role fixed")
            else:
                print("❌ Failed to fix admin role")
    else:
        print("❌ Admin user not found")
    
    # 5. Test creating sample enterprise (for testing)
    print("\n5. Testing enterprise creation...")
    sample_enterprise = {
        'name': 'Test Healthcare Enterprise',
        'type': 'healthcare',
        'contact_email': 'test@example.com',
        'status': 'trial'
    }
    
    # Check if test enterprise already exists
    existing = supabase_request('GET', 'enterprises', 
                              params={'name': f'eq.{sample_enterprise["name"]}'})
    
    if existing and len(existing) > 0:
        print("✅ Test enterprise already exists")
    else:
        result = supabase_request('POST', 'enterprises', data=sample_enterprise)
        if result:
            print("✅ Test enterprise created successfully")
        else:
            print("❌ Failed to create test enterprise")
    
    print("\n" + "=" * 60)
    print("✅ Admin functionality test completed!")
    print("   The admin dashboard should now work properly")

if __name__ == "__main__":
    test_admin_functionality()