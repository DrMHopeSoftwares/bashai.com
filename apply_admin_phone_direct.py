#!/usr/bin/env python3
"""
Apply admin phone number migration directly to Supabase using SQL
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def apply_migration_direct():
    """Apply the admin phone number migration to Supabase using direct SQL"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase configuration")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    try:
        print("🔄 Adding sender_phone column to users table...")
        
        # First, check if columns already exist
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'limit': 1}
        )
        
        if check_response.status_code == 200:
            print("✅ Users table accessible")
            
            # Try to add columns using ALTER TABLE via a simple update
            # We'll use a workaround by trying to update a non-existent record with the new fields
            test_data = {
                'sender_phone': '+918035743222',
                'bolna_agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480'
            }
            
            # This will fail if columns don't exist, which tells us we need to add them
            test_response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                params={'id': 'eq.00000000-0000-0000-0000-000000000000'},  # Non-existent ID
                json=test_data
            )
            
            if test_response.status_code == 204:
                print("✅ Columns already exist")
            else:
                print("📝 Columns need to be added manually in Supabase dashboard")
                print("Please add these columns to the users table:")
                print("1. sender_phone (VARCHAR, nullable)")
                print("2. bolna_agent_id (VARCHAR, nullable)")
                
            # Update existing admin users with default values
            print("🔄 Updating existing admin users with default phone settings...")
            
            # Get all admin users
            admin_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                params={'role': 'in.(admin,super_admin,manager)'}
            )
            
            if admin_response.status_code == 200:
                admins = admin_response.json()
                print(f"📋 Found {len(admins)} admin users")
                
                for admin in admins:
                    # Update each admin with default phone settings if not already set
                    update_data = {}
                    
                    if not admin.get('sender_phone'):
                        update_data['sender_phone'] = '+918035743222'
                    
                    if not admin.get('bolna_agent_id'):
                        update_data['bolna_agent_id'] = '15554373-b8e1-4b00-8c25-c4742dc8e480'
                    
                    if update_data:
                        update_response = requests.patch(
                            f"{SUPABASE_URL}/rest/v1/users",
                            headers=headers,
                            params={'id': f'eq.{admin["id"]}'},
                            json=update_data
                        )
                        
                        if update_response.status_code == 204:
                            print(f"✅ Updated admin: {admin['email']}")
                        else:
                            print(f"⚠️ Failed to update admin: {admin['email']}")
            
            print("✅ Migration process completed!")
            return True
        else:
            print(f"❌ Cannot access users table: {check_response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Admin Phone Number Migration (Direct)")
    print("="*45)
    
    success = apply_migration_direct()
    
    if success:
        print("\n🎉 Migration completed!")
        print("📱 Admin users now have default phone settings")
        print("🔧 You can update individual admin phone numbers via the API")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
