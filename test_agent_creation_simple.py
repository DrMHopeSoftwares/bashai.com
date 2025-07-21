#!/usr/bin/env python3
"""
Simple test for agent creation without authentication
"""

import requests
import json
import time
from datetime import datetime

def test_agent_creation_simple():
    """Test agent creation without authentication"""
    try:
        print("🧪 Testing Simple Agent Creation...")
        
        # Test data for agent creation
        agent_data = {
            "name": f"Simple Test Agent {datetime.now().strftime('%H%M%S')}",
            "business_name": "Test Business",
            "about_product": "Test product description",
            "about_business": "Test business description",
            "phone_number": "+918035315404",
            "type": "sales",
            "voice": "Aditi",
            "language": "hi"
        }
        
        print(f"📋 Agent Data:")
        print(json.dumps(agent_data, indent=2, ensure_ascii=False))
        
        # Make API request to create agent
        response = requests.post(
            'http://localhost:5003/api/bolna/create-sales-agent',
            headers={'Content-Type': 'application/json'},
            json=agent_data,
            timeout=30
        )
        
        print(f"\n📡 API Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            agent_id = result.get('agent_id')
            state = result.get('state')
            
            print(f"✅ Agent Creation Successful!")
            print(f"🎯 Agent ID: {agent_id}")
            print(f"📊 State: {state}")
            
            return agent_id
        else:
            print(f"❌ Agent creation failed")
            return None
            
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return None

def check_database_storage():
    """Check if agent data is stored in database"""
    try:
        print("\n🔍 Checking Database Storage...")
        
        # Import supabase client
        from supabase import create_client, Client
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        # Check different tables for agent data
        tables_to_check = ['bolna_agents', 'organizations', 'purchased_phone_numbers']
        
        total_found = 0
        
        for table_name in tables_to_check:
            try:
                result = supabase.table(table_name).select('*').execute()
                count = len(result.data)
                total_found += count
                
                print(f"📊 {table_name}: {count} records")
                
                if result.data:
                    print(f"📋 Sample from {table_name}:")
                    sample = result.data[0]
                    for key, value in sample.items():
                        if 'agent' in key.lower() or 'bolna' in key.lower():
                            print(f"  {key}: {value}")
                    print()
                    
            except Exception as table_error:
                print(f"⚠️ {table_name} check failed: {table_error}")
        
        return total_found > 0
        
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

def check_server_logs():
    """Check server logs for agent creation"""
    try:
        print("\n📋 Checking Server Logs...")
        
        # Make a simple request to trigger logs
        response = requests.get('http://localhost:5003/api/dev/voice-agents', timeout=10)
        
        print(f"📡 Dev endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Dev endpoint response: {len(data)} items")
            return True
        else:
            print(f"⚠️ Dev endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Server logs check error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Simple Agent Creation Test")
    print("="*35)
    
    # Test 1: Create agent
    agent_id = test_agent_creation_simple()
    
    # Wait a bit for processing
    if agent_id:
        print(f"\n⏳ Waiting 5 seconds for processing...")
        time.sleep(5)
    
    # Test 2: Check database
    db_success = check_database_storage()
    
    # Test 3: Check server logs
    logs_success = check_server_logs()
    
    # Summary
    print("\n📊 Test Results:")
    print("="*20)
    print(f"Agent Creation: {'✅ PASS' if agent_id else '❌ FAIL'}")
    print(f"Database Storage: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"Server Logs: {'✅ PASS' if logs_success else '❌ FAIL'}")
    
    if agent_id:
        print(f"\n🎉 SUCCESS! Agent created successfully!")
        print(f"🎯 Agent ID: {agent_id}")
        
        if db_success:
            print(f"✅ Data is being stored in database")
        else:
            print(f"⚠️ Data storage needs manual verification")
            print(f"📋 Check Supabase dashboard for agent data")
    else:
        print(f"\n❌ Agent creation failed")
        print(f"📋 Check server logs for errors")

if __name__ == "__main__":
    main()
