#!/usr/bin/env python3

import requests
import json

# Test the agent listing and sync endpoints
base_url = "http://localhost:5003"

def test_list_agents():
    """Test listing agents from Bolna"""
    try:
        # First login to get session
        login_data = {
            "email": "b@gmail.com",
            "password": "bhupendra"
        }
        
        session = requests.Session()
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login successful")
            
            # Now test list agents
            agents_response = session.get(f"{base_url}/api/bolna/agents/list")
            
            if agents_response.status_code == 200:
                agents_data = agents_response.json()
                print(f"✅ Agents listed successfully:")
                print(json.dumps(agents_data, indent=2))
                return agents_data
            else:
                print(f"❌ Failed to list agents: {agents_response.status_code}")
                print(agents_response.text)
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_sync_agents():
    """Test syncing agents from Bolna to database"""
    try:
        # First login to get session
        login_data = {
            "email": "b@gmail.com",
            "password": "bhupendra"
        }

        session = requests.Session()
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)

        if login_response.status_code == 200:
            print("✅ Login successful")

            # Now test sync agents
            sync_response = session.post(f"{base_url}/api/bolna/agents/sync")

            if sync_response.status_code == 200:
                sync_data = sync_response.json()
                print(f"✅ Agents synced successfully:")
                print(json.dumps(sync_data, indent=2))
                return sync_data
            else:
                print(f"❌ Failed to sync agents: {sync_response.status_code}")
                print(sync_response.text)
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

    return None

def test_assign_agent():
    """Test manually assigning an agent to a phone number"""
    try:
        # First login to get session
        login_data = {
            "email": "b@gmail.com",
            "password": "bhupendra"
        }

        session = requests.Session()
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)

        if login_response.status_code == 200:
            print("✅ Login successful")

            # Test assigning agent to phone number
            assign_data = {
                "phone_number": "+918035315404",
                "agent_id": "491325fa-4323-4e39-8536-a1a66cd8d437"  # pooja agent
            }

            assign_response = session.post(f"{base_url}/api/bolna/agents/assign", json=assign_data)

            if assign_response.status_code == 200:
                assign_result = assign_response.json()
                print(f"✅ Agent assigned successfully:")
                print(json.dumps(assign_result, indent=2))
                return assign_result
            else:
                print(f"❌ Failed to assign agent: {assign_response.status_code}")
                print(assign_response.text)
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

    return None

if __name__ == "__main__":
    print("🔍 Testing Bolna agent endpoints...")
    print("\n1. Testing list agents:")
    agents = test_list_agents()

    print("\n2. Testing sync agents:")
    sync_result = test_sync_agents()

    print("\n3. Testing assign agent:")
    assign_result = test_assign_agent()

    print("\n✅ Test completed!")
