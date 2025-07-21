#!/usr/bin/env python3
"""
Apply admin phone number migration to add sender_phone and bolna_agent_id fields
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    """Apply the admin phone number migration to Supabase"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase configuration")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Read the SQL migration file
    try:
        with open('add_admin_phone_numbers.sql', 'r') as f:
            sql_content = f.read()
        
        print("🔄 Applying admin phone number migration...")
        
        # Split SQL commands and execute them one by one
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        for i, command in enumerate(sql_commands):
            if command:
                print(f"📝 Executing command {i+1}/{len(sql_commands)}")
                
                # Use Supabase SQL execution endpoint
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                    headers=headers,
                    json={'sql': command}
                )
                
                if response.status_code not in [200, 201, 204]:
                    print(f"⚠️ Command {i+1} response: {response.status_code}")
                    print(f"Response: {response.text}")
                else:
                    print(f"✅ Command {i+1} executed successfully")
        
        print("✅ Admin phone number migration completed!")
        return True
        
    except FileNotFoundError:
        print("❌ Migration file 'add_admin_phone_numbers.sql' not found")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Admin Phone Number Migration")
    print("="*40)
    
    success = apply_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("📱 Each admin can now have their own phone number for Bolna calls")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
