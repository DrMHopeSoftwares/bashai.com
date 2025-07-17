#!/usr/bin/env python3
"""
Check if users have enterprise_id in database
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_user_enterprise_id():
    """Check users table for enterprise_id"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase credentials not found")
        return
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("🔍 Checking users table for enterprise_id...")
        
        # Get recent users
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'select': 'id,email,name,enterprise_id,organization', 'order': 'created_at.desc', 'limit': 5}
        )
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Found {len(users)} recent users:")
            
            for user in users:
                print(f"\n👤 User: {user.get('email', 'N/A')}")
                print(f"   ID: {user.get('id', 'N/A')[:8]}...")
                print(f"   Name: {user.get('name', 'N/A')}")
                print(f"   Organization: {user.get('organization', 'N/A')}")
                print(f"   Enterprise ID: {user.get('enterprise_id', 'N/A')}")
                
                if user.get('enterprise_id'):
                    print(f"   ✅ Has enterprise_id")
                else:
                    print(f"   ❌ Missing enterprise_id")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_user_enterprise_id()
