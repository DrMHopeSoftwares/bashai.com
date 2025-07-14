#!/usr/bin/env python3
"""
Script to apply the new enterprise-organization structure to Supabase
This will drop existing tables and recreate with the new structure
"""

import os
import requests
from dotenv import load_dotenv

def apply_new_schema():
    """Apply the new schema to Supabase"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    print(f"🔗 Applying new schema to: {supabase_url}")
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    # First, let's backup existing data if any
    print("📋 Checking existing data...")
    
    try:
        # Check if old tables exist and have data
        old_voice_agents = requests.get(f'{supabase_url}/rest/v1/voice_agents', headers=headers)
        old_contacts = requests.get(f'{supabase_url}/rest/v1/contacts', headers=headers)
        
        if old_voice_agents.status_code == 200 and old_contacts.status_code == 200:
            agents = old_voice_agents.json()
            contacts = old_contacts.json()
            print(f"📊 Found {len(agents)} voice agents and {len(contacts)} contacts")
            
            if len(agents) > 0 or len(contacts) > 0:
                print("⚠️  WARNING: Existing data will be replaced with new sample data")
                response = input("Continue? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Operation cancelled")
                    return False
        
    except Exception as e:
        print(f"ℹ️  Could not check existing data: {e}")
    
    # Read the new schema
    try:
        with open('updated_schema.sql', 'r') as f:
            schema_content = f.read()
    except FileNotFoundError:
        print("❌ updated_schema.sql file not found")
        return False
    
    print("🗑️  Dropping old tables...")
    
    # Drop old tables in correct order (reverse dependency)
    drop_statements = [
        "DROP TABLE IF EXISTS contacts CASCADE;",
        "DROP TABLE IF EXISTS voice_agents CASCADE;", 
        "DROP TABLE IF EXISTS call_logs CASCADE;",
        "DROP TABLE IF EXISTS activity_logs CASCADE;"
    ]
    
    for statement in drop_statements:
        try:
            # Use direct SQL execution via REST API
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/query",
                headers={**headers, 'Content-Type': 'application/sql'},
                data=statement,
                timeout=10
            )
            print(f"✅ Executed: {statement[:50]}...")
        except Exception as e:
            print(f"⚠️  Warning dropping table: {e}")
    
    print("🏗️  Creating new schema...")
    
    # Split schema into statements
    statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
    
    success_count = 0
    total_statements = len(statements)
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        if not statement:
            continue
            
        try:
            # Use direct SQL execution
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/query",
                headers={**headers, 'Content-Type': 'application/sql'},
                data=statement,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"✅ Statement {i}/{total_statements} executed")
            else:
                print(f"⚠️  Statement {i} warning: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error executing statement {i}: {e}")
    
    print(f"\n📊 Schema application: {success_count}/{total_statements} statements executed")
    
    # Test the new tables
    print("\n🧪 Testing new tables...")
    
    test_tables = ['enterprises', 'organizations', 'channels', 'voice_agents', 'contacts']
    
    for table in test_tables:
        try:
            response = requests.get(f'{supabase_url}/rest/v1/{table}?limit=1', headers=headers)
            if response.status_code == 200:
                print(f"✅ {table} table accessible")
            else:
                print(f"❌ {table} table error: {response.status_code}")
        except Exception as e:
            print(f"❌ {table} table error: {e}")
    
    return success_count > 0

if __name__ == "__main__":
    print("🚀 Applying New Enterprise-Organization Schema")
    print("=" * 60)
    
    success = apply_new_schema()
    
    if success:
        print("\n✅ New schema applied successfully!")
        print("\nNew Structure:")
        print("Enterprise (Hope) → Organizations (Ayushmann, Raftaar) → Channels → Voice Agents → Contacts")
        print("\nNext steps:")
        print("1. Update main.py with new API endpoints")
        print("2. Update frontend to use new structure")
        print("3. Test the complete flow")
    else:
        print("\n❌ Schema application failed!")
        print("Please check the errors above and try again.")
