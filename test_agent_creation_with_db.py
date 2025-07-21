#!/usr/bin/env python3
"""
Test agent creation and verify database storage
"""

import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_agent_creation_api():
    """Test agent creation via API endpoint"""
    try:
        print("🧪 Testing Agent Creation via API...")

        # First login to get authentication
        login_data = {
            "email": "b@gmail.com",
            "password": "123456"
        }

        print("🔐 Logging in...")
        login_response = requests.post(
            'http://localhost:5003/api/auth/login',
            headers={'Content-Type': 'application/json'},
            json=login_data,
            timeout=10
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return None

        # Get session cookies
        session_cookies = login_response.cookies
        print("✅ Login successful")

        # Test data for agent creation
        agent_data = {
            "name": "Test Agent राज",
            "business_name": "Test Business",
            "about_product": "Test product for healthcare",
            "about_business": "Test business description",
            "phone_number": "+918035315404",
            "type": "sales",
            "voice": "Aditi",
            "language": "hi",
            "prompt": "आप एक helpful sales assistant हैं।",
            "welcome_message": "नमस्ते! मैं राज हूं, आपका sales assistant।"
        }

        print(f"📋 Agent Data: {json.dumps(agent_data, indent=2, ensure_ascii=False)}")

        # Make API request with authentication
        response = requests.post(
            'http://localhost:5003/api/bolna/create-sales-agent',
            headers={'Content-Type': 'application/json'},
            json=agent_data,
            cookies=session_cookies,
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Agent Created Successfully!")
            print(f"📊 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Extract agent_id if available
            agent_id = result.get('agent_id')
            if agent_id:
                print(f"🎯 Agent ID: {agent_id}")
                return agent_id
            else:
                print("⚠️ No agent_id in response")
                return None
        else:
            print(f"❌ Agent Creation Failed: {response.status_code}")
            print(f"📋 Error Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API Test Error: {e}")
        return None

def check_database_storage(agent_id=None):
    """Check if agent is stored in database"""
    try:
        print("\n🔍 Checking Database Storage...")
        
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        # Query all agents
        result = supabase.table('bolna_agents').select('*').execute()
        
        print(f"📊 Total Agents in Database: {len(result.data)}")
        
        if result.data:
            print("\n📋 Agents in Database:")
            for i, agent in enumerate(result.data, 1):
                print(f"  {i}. ID: {agent.get('id')}")
                print(f"     Bolna Agent ID: {agent.get('bolna_agent_id')}")
                print(f"     Name: {agent.get('agent_name')}")
                print(f"     Type: {agent.get('agent_type')}")
                print(f"     Phone: {agent.get('phone_number')}")
                print(f"     Status: {agent.get('status')}")
                print(f"     Created: {agent.get('created_at')}")
                print()
                
                # Check if this is our test agent
                if agent_id and agent.get('bolna_agent_id') == agent_id:
                    print(f"✅ Found our test agent in database!")
                    return True
        else:
            print("📋 No agents found in database")
            
        return len(result.data) > 0
        
    except Exception as e:
        print(f"❌ Database Check Error: {e}")
        return False

def test_database_endpoint():
    """Test the database API endpoint"""
    try:
        print("\n🧪 Testing Database API Endpoint...")

        # Login first
        login_data = {
            "email": "b@gmail.com",
            "password": "123456"
        }

        login_response = requests.post(
            'http://localhost:5003/api/auth/login',
            headers={'Content-Type': 'application/json'},
            json=login_data,
            timeout=10
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed for database API test: {login_response.status_code}")
            return False

        session_cookies = login_response.cookies

        response = requests.get(
            'http://localhost:5003/api/database/agents',
            cookies=session_cookies,
            timeout=10
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Database API Working!")
            print(f"📊 Total Agents: {result.get('total', 0)}")
            
            agents = result.get('agents', [])
            if agents:
                print(f"📋 Sample Agent: {json.dumps(agents[0], indent=2, ensure_ascii=False)}")
            
            return True
        else:
            print(f"❌ Database API Failed: {response.status_code}")
            print(f"📋 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Database API Test Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Agent Creation & Database Storage")
    print("="*50)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5003/api/auth/profile', timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running. Please start the server first:")
        print("   python3 main.py")
        return
    
    # Test 1: Create agent via API
    agent_id = test_agent_creation_api()
    
    # Wait a moment for database storage
    if agent_id:
        print("\n⏳ Waiting for database storage...")
        time.sleep(2)
    
    # Test 2: Check database storage
    db_success = check_database_storage(agent_id)
    
    # Test 3: Test database API endpoint
    api_success = test_database_endpoint()
    
    # Summary
    print("\n📊 Test Results:")
    print("="*30)
    print(f"Agent Creation: {'✅ PASS' if agent_id else '❌ FAIL'}")
    print(f"Database Storage: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"Database API: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if agent_id and db_success:
        print(f"\n🎉 SUCCESS! Agent creation aur database storage dono working hain!")
        print(f"🎯 Created Agent ID: {agent_id}")
        print(f"📋 Agent successfully stored in bolna_agents table")
    else:
        print(f"\n⚠️ Some issues found. Check the logs above.")

if __name__ == "__main__":
    main()
