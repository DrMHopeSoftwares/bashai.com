#!/usr/bin/env python3
"""
Fix the admin authentication issue for cmd@hopehospital.com
"""

import os
import requests
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
        elif method == 'PATCH':
            response = requests.patch(url, headers=SUPABASE_HEADERS, json=data)
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

def check_and_fix_admin_access():
    """Check if admin user is properly configured for local authentication"""
    
    print("=" * 60)
    print(" Fixing Admin Authentication Access")
    print("=" * 60)
    
    # 1. Check current admin user
    print("\n1. Checking admin user in database...")
    admin_user = supabase_request('GET', 'users', params={'email': 'eq.cmd@hopehospital.com'})
    
    if admin_user and len(admin_user) > 0:
        user = admin_user[0]
        print(f"✅ Admin user found: {user['name']} ({user['email']})")
        print(f"   Role: {user['role']}")
        print(f"   Status: {user['status']}")
        print(f"   Current ID: {user.get('id', 'None')}")
        print(f"   Enterprise ID: {user.get('enterprise_id', 'None')}")
        
        # 2. Using local authentication system instead of Clerk
        # We need to update the authentication flow to handle this
        print("\n2. Issue identified:")
        print("   - Admin user exists in database with local ID")
        print("   - When signing up via Clerk, it creates new user with Clerk ID")
        print("   - This causes role mismatch and access issues")
        
        print("\n3. Recommended solutions:")
        print("   A) Update the authentication flow in main.py")
        print("   B) Link Clerk user to existing admin record")
        print("   C) Use email-based authentication for admin users")
        
        return user
    else:
        print("❌ Admin user not found in database")
        return None

def create_auth_fix_patch():
    """Create a patch for the authentication flow"""
    
    patch_content = '''
# Add this to main.py in the get_current_user() function, before creating new trial user

# Check if user exists by email (for admin users who signed up via Clerk)
user_email = clerk_user.get('email_addresses', [{}])[0].get('email_address', '')
existing_users_by_email = supabase_request('GET', 'users', params={'email': f'eq.{user_email}'})

if existing_users_by_email and len(existing_users_by_email) > 0:
    existing_user = existing_users_by_email[0]
    
    # If it's an admin user, update their ID to match Clerk user_id
    if existing_user.get('role') == 'admin':
        print(f"Linking existing admin user {user_email} to Clerk ID {user_id}")
        
        # Update the existing admin user with Clerk user_id
        update_data = {
            'id': user_id,  # Update to Clerk user_id
            'status': 'active'  # Ensure they're active
        }
        
        # Update by email since ID is changing
        result = supabase_request('PATCH', f'users?email=eq.{user_email}', data=update_data)
        
        if result and len(result) > 0:
            updated_user = result[0]
            trial_status = check_trial_status(updated_user)
            
            return jsonify({
                'user': updated_user,
                'trial_status': trial_status,
                'clerk_data': clerk_user,
                'admin_linked': True
            })
'''
    
    with open('/Users/murali/bhashai.com for git push/bashai.com/auth_fix_patch.txt', 'w') as f:
        f.write(patch_content)
    
    print("\n4. Created patch file: auth_fix_patch.txt")
    print("   This shows the code changes needed in main.py")

if __name__ == "__main__":
    admin_user = check_and_fix_admin_access()
    if admin_user:
        create_auth_fix_patch()
        
        print("\n🎯 SOLUTION:")
        print("   The issue is that Clerk creates users with different IDs")
        print("   than your existing admin user in the database.")
        print()
        print("   When cmd@hopehospital.com signs up via Clerk:")
        print("   1. Clerk assigns them a new user_id")
        print("   2. System creates new 'trial_user' instead of using existing admin")
        print("   3. Admin permissions are lost")
        print()
        print("🔧 FIX NEEDED:")
        print("   Update main.py to check for existing admin users by EMAIL")
        print("   before creating new trial users.")
        print()
        print("📧 After fix: cmd@hopehospital.com will have full admin access")