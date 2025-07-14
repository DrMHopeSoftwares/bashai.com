#!/usr/bin/env python3
"""
Create enterprise directly via Supabase API
Bypasses the broken deployment completely
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def create_enterprise_direct(name, contact_email, enterprise_type="healthcare"):
    """Create enterprise directly via Supabase API"""
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    enterprise_data = {
        "name": name,
        "type": enterprise_type,
        "contact_email": contact_email,
        "status": "trial",
        "created_at": "now()"
    }
    
    print(f"🏢 Creating enterprise: {name}")
    print(f"📧 Contact email: {contact_email}")
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/enterprises",
            headers=headers,
            json=enterprise_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            enterprise_id = result[0]['id'] if isinstance(result, list) else result['id']
            
            print(f"✅ SUCCESS! Enterprise created")
            print(f"   ID: {enterprise_id}")
            print(f"   Name: {name}")
            print(f"   Email: {contact_email}")
            print(f"   Status: trial")
            
            return enterprise_id
            
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return None

def create_admin_user(enterprise_id, email="cmd@hopehospital.com"):
    """Create admin user for the enterprise"""
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    user_data = {
        "id": f"admin_{enterprise_id}",
        "email": email,
        "role": "admin",
        "enterprise_id": enterprise_id,
        "trial_expires_at": "2024-12-31T23:59:59Z",
        "created_at": "now()"
    }
    
    print(f"👤 Creating admin user: {email}")
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            json=user_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Admin user created: {email}")
            return True
        else:
            print(f"❌ User creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 User creation error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Direct Enterprise Creation (Bypassing Deployment)")
    print("=" * 60)
    
    # Create test enterprise with defaults
    enterprise_name = "Hope Hospital"
    contact_email = "cmd@hopehospital.com"
    
    # Create enterprise
    enterprise_id = create_enterprise_direct(enterprise_name, contact_email)
    
    if enterprise_id:
        # Create admin user
        create_admin_user(enterprise_id, contact_email)
        
        print("\n" + "=" * 60)
        print("🎉 COMPLETE! Enterprise setup finished")
        print(f"   Enterprise: {enterprise_name}")
        print(f"   Admin: {contact_email}")
        print(f"   ID: {enterprise_id}")
        print("\nNext: Fix deployment to access the dashboard")
    else:
        print("\n❌ Enterprise creation failed")