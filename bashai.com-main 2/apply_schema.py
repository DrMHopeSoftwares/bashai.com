#!/usr/bin/env python3
"""
Script to apply the updated schema to Supabase
"""

import os
import requests
from dotenv import load_dotenv

def apply_schema():
    """Apply the updated schema to Supabase"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    print(f"🔗 Applying schema to: {supabase_url}")
    
    # Read the schema file
    try:
        with open('supabase_schema.sql', 'r') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print("❌ supabase_schema.sql file not found")
        return False
    
    # Apply schema via Supabase SQL API
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/sql'
    }
    
    try:
        print("📝 Applying database schema...")
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/exec_sql",
            headers=headers,
            data=schema_sql,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Schema applied successfully!")
            return True
        else:
            print(f"❌ Error applying schema: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Applying Supabase Schema for Contact Management")
    print("=" * 50)
    
    success = apply_schema()
    
    if success:
        print("\n✅ Schema application completed successfully!")
        print("You can now use the contact management features with Supabase backend.")
    else:
        print("\n❌ Schema application failed!")
        print("Please check your Supabase credentials and try again.")
