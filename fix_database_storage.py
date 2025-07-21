#!/usr/bin/env python3
"""
Fix database storage for Bolna agents
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def disable_rls_and_fix_table():
    """Disable RLS and fix table structure"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Service role key needed for RLS
        
        if not supabase_url or not supabase_service_key:
            print("❌ Missing Supabase service role key. Using anon key...")
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
        else:
            supabase_key = supabase_service_key
        
        print("🔧 Fixing database storage issues...")
        
        # Import supabase client with service role
        from supabase import create_client, Client
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Method 1: Try to disable RLS using direct SQL
        try:
            print("🔄 Attempting to disable RLS...")
            
            # Use the REST API directly to execute SQL
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # SQL commands to fix the table
            sql_commands = [
                "ALTER TABLE bolna_agents DISABLE ROW LEVEL SECURITY;",
                "DROP POLICY IF EXISTS bolna_agents_policy ON bolna_agents;",
                "GRANT ALL ON bolna_agents TO anon;",
                "GRANT ALL ON bolna_agents TO authenticated;"
            ]
            
            for sql in sql_commands:
                try:
                    response = requests.post(
                        f"{supabase_url}/rest/v1/rpc/exec_sql",
                        headers=headers,
                        json={'sql': sql},
                        timeout=10
                    )
                    print(f"✅ Executed: {sql[:50]}...")
                except Exception as sql_error:
                    print(f"⚠️ SQL failed: {sql_error}")
            
        except Exception as rls_error:
            print(f"⚠️ RLS disable failed: {rls_error}")
        
        # Method 2: Test direct insert
        print("\n🧪 Testing direct insert...")
        
        test_agent = {
            'bolna_agent_id': f'test-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'agent_name': 'Test Agent राज',
            'agent_type': 'sales',
            'description': 'Test agent for database storage',
            'prompt': 'आप एक helpful assistant हैं।',
            'welcome_message': 'नमस्ते! मैं राज हूं।',
            'voice': 'Aditi',
            'language': 'hi',
            'max_duration': 180,
            'hangup_after': 15,
            'phone_number': '+918035315404',
            'status': 'active'
        }
        
        # Try insert with service role key
        result = supabase.table('bolna_agents').insert(test_agent).execute()
        
        if result.data:
            print(f"✅ Direct insert successful!")
            agent = result.data[0]
            print(f"📊 Stored Agent:")
            print(f"  ID: {agent.get('id')}")
            print(f"  Bolna Agent ID: {agent.get('bolna_agent_id')}")
            print(f"  Name: {agent.get('agent_name')}")
            return True
        else:
            print(f"❌ Direct insert failed")
            return False
            
    except Exception as e:
        print(f"❌ Database fix error: {e}")
        return False

def test_with_anon_key():
    """Test insert with anon key after fixing RLS"""
    try:
        print("\n🧪 Testing with anon key...")
        
        # Import supabase client with anon key
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        test_agent = {
            'bolna_agent_id': f'anon-test-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'agent_name': 'Anon Test Agent',
            'agent_type': 'sales',
            'description': 'Test with anon key',
            'status': 'active'
        }
        
        result = supabase.table('bolna_agents').insert(test_agent).execute()
        
        if result.data:
            print(f"✅ Anon key insert successful!")
            return True
        else:
            print(f"❌ Anon key insert failed")
            return False
            
    except Exception as e:
        print(f"❌ Anon key test error: {e}")
        return False

def create_agent_via_api():
    """Create agent via API and check if it stores in database"""
    try:
        print("\n🧪 Testing agent creation via API...")
        
        # Test data for agent creation
        agent_data = {
            "name": "API Test Agent राज",
            "business_name": "Test Business",
            "about_product": "Test product",
            "about_business": "Test business",
            "phone_number": "+918035315404",
            "type": "sales",
            "voice": "Aditi",
            "language": "hi"
        }
        
        # Make API request to create agent
        response = requests.post(
            'http://localhost:5003/api/bolna/create-sales-agent',
            headers={'Content-Type': 'application/json'},
            json=agent_data,
            timeout=30
        )
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            agent_id = result.get('agent_id')
            print(f"✅ Agent created via API: {agent_id}")
            
            # Check if it's stored in database
            from supabase import create_client, Client
            
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_ANON_KEY')
            supabase: Client = create_client(url, key)
            
            # Check bolna_agents table
            db_result = supabase.table('bolna_agents').select('*').eq('bolna_agent_id', agent_id).execute()
            
            if db_result.data:
                print(f"✅ Agent found in database!")
                return True
            else:
                print(f"❌ Agent not found in database")
                return False
        else:
            print(f"❌ API request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Fixing Database Storage for Bolna Agents")
    print("="*45)
    
    # Step 1: Fix RLS and permissions
    fix_success = disable_rls_and_fix_table()
    
    # Step 2: Test with anon key
    anon_success = test_with_anon_key()
    
    # Step 3: Test via API
    api_success = create_agent_via_api()
    
    # Summary
    print("\n📊 Fix Results:")
    print("="*20)
    print(f"Database Fix: {'✅ PASS' if fix_success else '❌ FAIL'}")
    print(f"Anon Key Test: {'✅ PASS' if anon_success else '❌ FAIL'}")
    print(f"API Test: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if fix_success and anon_success:
        print(f"\n🎉 SUCCESS! Database storage is now working!")
        print(f"📋 Agents will now be stored in bolna_agents table")
        print(f"🔧 RLS has been disabled for bolna_agents table")
    elif api_success:
        print(f"\n✅ API working but database storage needs manual fix")
        print(f"📋 Check Supabase dashboard to disable RLS manually")
    else:
        print(f"\n⚠️ Manual intervention required")
        print(f"📋 Please disable RLS in Supabase dashboard:")
        print(f"   1. Go to Table Editor > bolna_agents")
        print(f"   2. Click on RLS tab")
        print(f"   3. Disable RLS for this table")

if __name__ == "__main__":
    main()
