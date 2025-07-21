#!/usr/bin/env python3
"""
Test direct database storage for agents
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_direct_database_storage():
    """Test storing agent data directly in database"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("🧪 Testing Direct Database Storage...")
        
        # Test agent data
        agent_data = {
            'bolna_agent_id': 'test-agent-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'agent_name': 'Test Agent राज',
            'agent_type': 'sales',
            'description': 'Test sales agent for database storage',
            'prompt': 'आप एक helpful sales assistant हैं।',
            'welcome_message': 'नमस्ते! मैं राज हूं, आपका sales assistant।',
            'voice': 'Aditi',
            'language': 'hi',
            'max_duration': 180,
            'hangup_after': 15,
            'phone_number': '+918035315404',
            'status': 'active',
            'bolna_response': {
                'test': True,
                'created_at': datetime.now().isoformat()
            }
        }
        
        print(f"📋 Agent Data to Store:")
        print(json.dumps(agent_data, indent=2, ensure_ascii=False))
        
        # Insert into database
        result = supabase.table('bolna_agents').insert(agent_data).execute()
        
        if result.data:
            print(f"✅ Agent stored successfully!")
            stored_agent = result.data[0]
            print(f"📊 Stored Agent:")
            print(f"  ID: {stored_agent.get('id')}")
            print(f"  Bolna Agent ID: {stored_agent.get('bolna_agent_id')}")
            print(f"  Name: {stored_agent.get('agent_name')}")
            print(f"  Type: {stored_agent.get('agent_type')}")
            print(f"  Phone: {stored_agent.get('phone_number')}")
            print(f"  Created: {stored_agent.get('created_at')}")
            
            return stored_agent.get('id')
        else:
            print(f"❌ Failed to store agent")
            return None
            
    except Exception as e:
        print(f"❌ Database storage error: {e}")
        return None

def test_retrieve_agents():
    """Test retrieving agents from database"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🔍 Testing Agent Retrieval...")
        
        # Get all agents
        result = supabase.table('bolna_agents').select('*').execute()
        
        print(f"📊 Total Agents in Database: {len(result.data)}")
        
        if result.data:
            print("\n📋 Agents in Database:")
            for i, agent in enumerate(result.data, 1):
                print(f"  {i}. {agent.get('agent_name')} ({agent.get('bolna_agent_id')})")
                print(f"     Type: {agent.get('agent_type')}")
                print(f"     Phone: {agent.get('phone_number')}")
                print(f"     Status: {agent.get('status')}")
                print(f"     Created: {agent.get('created_at')}")
                print()
        
        return len(result.data)
        
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return 0

def test_update_existing_agent():
    """Test updating an existing agent"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🔄 Testing Agent Update...")
        
        # Get first agent
        result = supabase.table('bolna_agents').select('*').limit(1).execute()
        
        if result.data:
            agent = result.data[0]
            agent_id = agent.get('id')
            
            print(f"📋 Updating agent: {agent.get('agent_name')} ({agent_id})")
            
            # Update agent
            update_data = {
                'description': f"Updated at {datetime.now().isoformat()}",
                'updated_at': datetime.now().isoformat()
            }
            
            update_result = supabase.table('bolna_agents').update(update_data).eq('id', agent_id).execute()
            
            if update_result.data:
                print(f"✅ Agent updated successfully!")
                return True
            else:
                print(f"❌ Failed to update agent")
                return False
        else:
            print(f"⚠️ No agents found to update")
            return False
            
    except Exception as e:
        print(f"❌ Update error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Direct Database Operations")
    print("="*40)
    
    # Test 1: Store agent
    stored_id = test_direct_database_storage()
    
    # Test 2: Retrieve agents
    agent_count = test_retrieve_agents()
    
    # Test 3: Update agent
    update_success = test_update_existing_agent()
    
    # Summary
    print("\n📊 Test Results:")
    print("="*30)
    print(f"Agent Storage: {'✅ PASS' if stored_id else '❌ FAIL'}")
    print(f"Agent Retrieval: {'✅ PASS' if agent_count > 0 else '❌ FAIL'}")
    print(f"Agent Update: {'✅ PASS' if update_success else '❌ FAIL'}")
    
    if stored_id and agent_count > 0:
        print(f"\n🎉 SUCCESS! Database operations working properly!")
        print(f"📋 Total agents in database: {agent_count}")
        print(f"🎯 Last stored agent ID: {stored_id}")
    else:
        print(f"\n⚠️ Some issues found. Check the logs above.")

if __name__ == "__main__":
    main()
