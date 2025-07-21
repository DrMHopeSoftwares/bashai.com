#!/usr/bin/env python3
"""
Test script to check if the agent with "priyanka" in prompt now returns the correct name
"""

import requests
import json

def test_priyanka_agent():
    """Test the agent that had the priyanka issue"""
    
    # Agent ID that had the "priyanka" issue
    agent_id = "9ede5ecf-9cac-4123-8cab-f644f99f1f73"
    
    print(f"🔍 Testing agent details API for agent with priyanka issue: {agent_id}")
    
    # Make request to the API
    url = f"http://localhost:5003/api/bolna/agents/{agent_id}/details"
    print(f"📡 Making request to: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Agent details retrieved:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check specific fields
            agent_name = data.get('name', 'NOT_FOUND')
            print(f"✅ agent_id: {data.get('agent_id', 'NOT_FOUND')}")
            print(f"✅ name: {agent_name}")
            print(f"✅ language: {data.get('language', 'NOT_FOUND')}")
            print(f"✅ voice: {data.get('voice', 'NOT_FOUND')}")
            print(f"✅ sales_approach: {data.get('sales_approach', 'NOT_FOUND')}")
            print(f"✅ welcome_message: {data.get('welcome_message', 'NOT_FOUND')}")
            
            # Check if we still get "priyanka" as the name
            if agent_name.lower() == 'priyanka':
                print("❌ ISSUE: Still getting 'priyanka' as agent name!")
            elif 'raj' in agent_name.lower():
                print("✅ SUCCESS: Got 'raj' or similar real name!")
            else:
                print(f"ℹ️  Got agent name: '{agent_name}' - check if this is correct")
            
            print("🎉 All required fields are present!")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_priyanka_agent()
