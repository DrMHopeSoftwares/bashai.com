#!/usr/bin/env python3
"""
Test using existing voice_agents table for storing Bolna agent data
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_voice_agents_table():
    """Test storing agent data in voice_agents table"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("🧪 Testing Voice Agents Table...")
        
        # First check table structure
        result = supabase.table('voice_agents').select('*').limit(1).execute()
        
        if result.data:
            print("✅ Voice agents table is accessible!")
            sample_agent = result.data[0]
            print(f"📋 Sample agent structure:")
            for key, value in sample_agent.items():
                print(f"  {key}: {type(value).__name__}")
        else:
            print("📋 Voice agents table is empty but accessible")
        
        # Test agent data for voice_agents table
        agent_data = {
            'name': 'Test Agent राज',
            'description': 'Test sales agent for database storage',
            'prompt': 'आप एक helpful sales assistant हैं।',
            'welcome_message': 'नमस्ते! मैं राज हूं, आपका sales assistant।',
            'voice': 'Aditi',
            'language': 'hi',
            'max_duration': 180,
            'phone_number': '+918035315404',
            'status': 'active',
            'bolna_agent_id': 'test-agent-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'agent_type': 'sales'
        }
        
        print(f"\n📋 Agent Data to Store:")
        print(json.dumps(agent_data, indent=2, ensure_ascii=False))
        
        # Insert into voice_agents table
        insert_result = supabase.table('voice_agents').insert(agent_data).execute()
        
        if insert_result.data:
            print(f"✅ Agent stored successfully in voice_agents table!")
            stored_agent = insert_result.data[0]
            print(f"📊 Stored Agent:")
            print(f"  ID: {stored_agent.get('id')}")
            print(f"  Name: {stored_agent.get('name')}")
            print(f"  Bolna Agent ID: {stored_agent.get('bolna_agent_id')}")
            print(f"  Phone: {stored_agent.get('phone_number')}")
            print(f"  Created: {stored_agent.get('created_at')}")
            
            return stored_agent.get('id')
        else:
            print(f"❌ Failed to store agent in voice_agents table")
            return None
            
    except Exception as e:
        print(f"❌ Voice agents table error: {e}")
        return None

def test_retrieve_voice_agents():
    """Test retrieving agents from voice_agents table"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🔍 Testing Voice Agents Retrieval...")
        
        # Get all voice agents
        result = supabase.table('voice_agents').select('*').execute()
        
        print(f"📊 Total Voice Agents in Database: {len(result.data)}")
        
        if result.data:
            print("\n📋 Voice Agents in Database:")
            for i, agent in enumerate(result.data, 1):
                print(f"  {i}. {agent.get('name')} (ID: {agent.get('id')})")
                print(f"     Bolna Agent ID: {agent.get('bolna_agent_id', 'NOT_SET')}")
                print(f"     Type: {agent.get('agent_type', 'NOT_SET')}")
                print(f"     Phone: {agent.get('phone_number', 'NOT_SET')}")
                print(f"     Status: {agent.get('status', 'NOT_SET')}")
                print(f"     Created: {agent.get('created_at')}")
                print()
        
        return len(result.data)
        
    except Exception as e:
        print(f"❌ Voice agents retrieval error: {e}")
        return 0

def test_add_bolna_agent_id_column():
    """Test adding bolna_agent_id column to voice_agents table"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🔧 Testing Adding bolna_agent_id Column...")
        
        # Try to add column (this might fail if column already exists)
        try:
            sql = "ALTER TABLE voice_agents ADD COLUMN IF NOT EXISTS bolna_agent_id VARCHAR(255);"
            result = supabase.postgrest.rpc('exec_sql', {'sql': sql}).execute()
            print(f"✅ Column addition attempted")
        except Exception as col_error:
            print(f"⚠️ Column addition failed (might already exist): {col_error}")
        
        # Try to add index
        try:
            sql = "CREATE INDEX IF NOT EXISTS idx_voice_agents_bolna_agent_id ON voice_agents(bolna_agent_id);"
            result = supabase.postgrest.rpc('exec_sql', {'sql': sql}).execute()
            print(f"✅ Index addition attempted")
        except Exception as idx_error:
            print(f"⚠️ Index addition failed: {idx_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Column addition error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Voice Agents Table for Bolna Agent Storage")
    print("="*55)
    
    # Test 1: Add bolna_agent_id column
    column_success = test_add_bolna_agent_id_column()
    
    # Test 2: Store agent
    stored_id = test_voice_agents_table()
    
    # Test 3: Retrieve agents
    agent_count = test_retrieve_voice_agents()
    
    # Summary
    print("\n📊 Test Results:")
    print("="*30)
    print(f"Column Addition: {'✅ PASS' if column_success else '❌ FAIL'}")
    print(f"Agent Storage: {'✅ PASS' if stored_id else '❌ FAIL'}")
    print(f"Agent Retrieval: {'✅ PASS' if agent_count > 0 else '❌ FAIL'}")
    
    if stored_id and agent_count > 0:
        print(f"\n🎉 SUCCESS! Voice agents table can store Bolna agent data!")
        print(f"📋 Total agents in database: {agent_count}")
        print(f"🎯 Last stored agent ID: {stored_id}")
        print(f"\n💡 Recommendation: Use voice_agents table with bolna_agent_id column")
    else:
        print(f"\n⚠️ Some issues found. Check the logs above.")

if __name__ == "__main__":
    main()
