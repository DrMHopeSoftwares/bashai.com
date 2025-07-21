#!/usr/bin/env python3
"""
Check the actual structure of voice_agents table
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_voice_agents_structure():
    """Check the structure of voice_agents table"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("🔍 Checking Voice Agents Table Structure...")
        
        # Get all voice agents to see structure
        result = supabase.table('voice_agents').select('*').execute()
        
        print(f"📊 Total Voice Agents: {len(result.data)}")
        
        if result.data:
            print("\n📋 Sample Voice Agent Structure:")
            sample_agent = result.data[0]
            for key, value in sample_agent.items():
                print(f"  {key}: {value} ({type(value).__name__})")
        else:
            print("📋 No voice agents found")
            
            # Try to insert a minimal record to see what columns are required
            print("\n🧪 Testing minimal insert to discover required columns...")
            
            minimal_data = {
                'name': 'Test Discovery Agent'
            }
            
            try:
                insert_result = supabase.table('voice_agents').insert(minimal_data).execute()
                if insert_result.data:
                    print("✅ Minimal insert successful!")
                    agent = insert_result.data[0]
                    print("📋 Created agent structure:")
                    for key, value in agent.items():
                        print(f"  {key}: {value} ({type(value).__name__})")
                    
                    # Clean up
                    supabase.table('voice_agents').delete().eq('id', agent['id']).execute()
                    print("🧹 Test record cleaned up")
                    
                    return agent
                else:
                    print("❌ Minimal insert failed")
                    return None
            except Exception as insert_error:
                print(f"❌ Minimal insert error: {insert_error}")
                return None
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"❌ Structure check error: {e}")
        return None

def test_simple_agent_storage():
    """Test storing agent with only existing columns"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🧪 Testing Simple Agent Storage...")
        
        # Simple agent data with only basic columns
        agent_data = {
            'name': 'Test Agent राज',
            'description': 'Test sales agent for database storage',
            'prompt': 'आप एक helpful sales assistant हैं।',
            'welcome_message': 'नमस्ते! मैं राज हूं, आपका sales assistant।',
            'voice': 'Aditi',
            'language': 'hi',
            'max_duration': 180,
            'phone_number': '+918035315404',
            'status': 'active'
        }
        
        print(f"📋 Simple Agent Data:")
        print(json.dumps(agent_data, indent=2, ensure_ascii=False))
        
        # Insert into voice_agents table
        insert_result = supabase.table('voice_agents').insert(agent_data).execute()
        
        if insert_result.data:
            print(f"✅ Simple agent stored successfully!")
            stored_agent = insert_result.data[0]
            print(f"📊 Stored Agent:")
            print(f"  ID: {stored_agent.get('id')}")
            print(f"  Name: {stored_agent.get('name')}")
            print(f"  Phone: {stored_agent.get('phone_number')}")
            print(f"  Created: {stored_agent.get('created_at')}")
            
            return stored_agent.get('id')
        else:
            print(f"❌ Failed to store simple agent")
            return None
            
    except Exception as e:
        print(f"❌ Simple storage error: {e}")
        return None

def test_update_with_bolna_id():
    """Test updating agent with Bolna agent ID"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🔄 Testing Update with Bolna Agent ID...")
        
        # Get the first agent
        result = supabase.table('voice_agents').select('*').limit(1).execute()
        
        if result.data:
            agent = result.data[0]
            agent_id = agent.get('id')
            
            print(f"📋 Updating agent: {agent.get('name')} ({agent_id})")
            
            # Try to update with bolna_agent_id
            bolna_agent_id = f"bolna-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            update_data = {
                'bolna_agent_id': bolna_agent_id,
                'description': f"Updated with Bolna ID at {datetime.now().isoformat()}"
            }
            
            update_result = supabase.table('voice_agents').update(update_data).eq('id', agent_id).execute()
            
            if update_result.data:
                print(f"✅ Agent updated with Bolna ID successfully!")
                updated_agent = update_result.data[0]
                print(f"📊 Updated Agent:")
                print(f"  Bolna Agent ID: {updated_agent.get('bolna_agent_id')}")
                print(f"  Description: {updated_agent.get('description')}")
                return True
            else:
                print(f"❌ Failed to update agent with Bolna ID")
                return False
        else:
            print(f"⚠️ No agents found to update")
            return False
            
    except Exception as e:
        print(f"❌ Update error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Voice Agents Table Structure Analysis")
    print("="*40)
    
    # Test 1: Check structure
    structure = check_voice_agents_structure()
    
    # Test 2: Simple storage
    stored_id = test_simple_agent_storage()
    
    # Test 3: Update with Bolna ID
    update_success = test_update_with_bolna_id()
    
    # Summary
    print("\n📊 Test Results:")
    print("="*30)
    print(f"Structure Check: {'✅ PASS' if structure else '❌ FAIL'}")
    print(f"Simple Storage: {'✅ PASS' if stored_id else '❌ FAIL'}")
    print(f"Bolna ID Update: {'✅ PASS' if update_success else '❌ FAIL'}")
    
    if stored_id and update_success:
        print(f"\n🎉 SUCCESS! Voice agents table can store Bolna agent data!")
        print(f"🎯 Stored agent ID: {stored_id}")
        print(f"\n💡 Strategy: Store in voice_agents table and update with bolna_agent_id")
    else:
        print(f"\n⚠️ Some issues found. Check the logs above.")

if __name__ == "__main__":
    main()
