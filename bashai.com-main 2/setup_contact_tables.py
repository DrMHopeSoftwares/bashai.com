#!/usr/bin/env python3
"""
Script to create voice_agents and contacts tables in Supabase
"""

import os
import requests
from dotenv import load_dotenv

def setup_contact_tables():
    """Create the voice_agents and contacts tables in Supabase"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    print(f"🔗 Setting up contact tables in: {supabase_url}")
    
    # Read the SQL file
    try:
        with open('create_contact_tables.sql', 'r') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("❌ create_contact_tables.sql file not found")
        return False
    
    # Split SQL into individual statements
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    success_count = 0
    total_statements = len(statements)
    
    for i, statement in enumerate(statements, 1):
        if not statement:
            continue
            
        print(f"📝 Executing statement {i}/{total_statements}...")
        
        try:
            # Use the SQL RPC endpoint
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"sql": statement},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"✅ Statement {i} executed successfully")
            else:
                print(f"⚠️  Statement {i} warning: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                # Continue with other statements
                
        except Exception as e:
            print(f"❌ Error executing statement {i}: {e}")
            # Continue with other statements
    
    print(f"\n📊 Results: {success_count}/{total_statements} statements executed")
    
    # Test the tables
    print("\n🧪 Testing created tables...")
    
    try:
        # Test voice_agents table
        response = requests.get(f'{supabase_url}/rest/v1/voice_agents?limit=1', headers=headers)
        if response.status_code == 200:
            print("✅ voice_agents table accessible")
        else:
            print(f"❌ voice_agents table error: {response.status_code}")
        
        # Test contacts table
        response = requests.get(f'{supabase_url}/rest/v1/contacts?limit=1', headers=headers)
        if response.status_code == 200:
            print("✅ contacts table accessible")
        else:
            print(f"❌ contacts table error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing tables: {e}")
    
    return success_count > 0

if __name__ == "__main__":
    print("🚀 Setting up Contact Management Tables")
    print("=" * 50)
    
    success = setup_contact_tables()
    
    if success:
        print("\n✅ Contact tables setup completed!")
        print("You can now use the contact management features with Supabase backend.")
        print("\nNext steps:")
        print("1. Start the Flask server: python3 main.py")
        print("2. Open the dashboard and test contact management")
    else:
        print("\n❌ Contact tables setup failed!")
        print("Please check your Supabase credentials and try again.")
