#!/usr/bin/env python3
"""
Test the new agent that was created
"""

import requests
import json

def test_new_agent():
    """Test the new agent functionality"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🧪 **TESTING NEW AGENT FUNCTIONALITY**")
    print("=" * 60)
    
    # The new agent ID from the logs
    new_agent_id = "6af040f3-e4ac-4f91-8091-044ba1a3808f"
    
    print(f"🤖 Testing agent: {new_agent_id}")
    
    # Test 1: Try to fetch agent details
    print(f"\n1. 🔍 Testing agent details fetch...")
    try:
        response = requests.get(f"{base_url}/api/bolna/agents/{new_agent_id}/details")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            details = response.json()
            print(f"   ✅ Agent details retrieved!")
            print(f"   📋 Agent Name: {details.get('name')}")
            print(f"   💬 Welcome Message: {details.get('welcome_message', 'None')[:50]}...")
            print(f"   📝 Prompt: {details.get('prompt', 'None')[:50]}...")
            print(f"   🗣️ Language: {details.get('language')}")
            print(f"   🎵 Voice: {details.get('voice')}")
        else:
            print(f"   ❌ Failed to fetch agent details")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Try to update the agent
    print(f"\n2. 🔄 Testing agent update...")
    try:
        update_data = {
            "agent_id": new_agent_id,
            "name": "Updated Test Agent",
            "welcome_message": "नमस्ते! मैं आपका updated AI assistant हूं।",
            "prompt": "You are an updated helpful AI assistant for sales.",
            "language": "hi",
            "voice": "Aditi",
            "sales_approach": "consultative"
        }
        
        response = requests.post(f"{base_url}/api/bolna/update-sales-agent", json=update_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Agent updated successfully!")
            print(f"   📊 Result: {result}")
        else:
            print(f"   ❌ Failed to update agent")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Test complete!")

if __name__ == "__main__":
    test_new_agent()
