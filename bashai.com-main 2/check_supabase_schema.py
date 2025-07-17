#!/usr/bin/env python3
"""
Check Supabase users table schema
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_users_table_schema():
    """Check the schema of users table in Supabase"""
    
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
        # Get table schema information
        print("🔍 Checking users table schema...")
        
        # Try to get a sample user to see the structure
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'limit': 1}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            if users:
                print("✅ Sample user structure:")
                sample_user = users[0]
                for key, value in sample_user.items():
                    print(f"  - {key}: {type(value).__name__}")
            else:
                print("📝 No users found in table")
                
                # Try to create a test user to see what columns are expected
                test_user = {
                    'id': 'test-schema-check',
                    'email': 'test@schema.com',
                    'name': 'Test User',
                    'organization': 'Test Org',
                    'role': 'user',
                    'status': 'active',
                    'password': 'test123'  # Try with 'password' instead of 'password_hash'
                }
                
                print("🧪 Testing with 'password' column...")
                test_response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=headers,
                    json=test_user
                )
                
                print(f"📊 Test Response Status: {test_response.status_code}")
                print(f"📊 Test Response: {test_response.text}")
                
                # Clean up test user
                if test_response.status_code == 201:
                    requests.delete(
                        f"{SUPABASE_URL}/rest/v1/users",
                        headers=headers,
                        params={'id': f'eq.test-schema-check'}
                    )
                    print("🧹 Cleaned up test user")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_users_table_schema()
