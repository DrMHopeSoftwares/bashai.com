#!/usr/bin/env python3
"""
Test what the Bolna API returns for the agent
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_bolna_api():
    """Test Bolna API response for the agent"""
    
    agent_id = "6af040f3-e4ac-4f91-8091-044ba1a3808f"
    api_key = os.getenv('BOLNA_API_KEY')
    base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
    
    if not api_key:
        print("❌ BOLNA_API_KEY not found")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔍 Testing Bolna API for agent: {agent_id}")
    print(f"🌐 API URL: {base_url}")
    
    try:
        # Test the agent details endpoint
        url = f"{base_url}/v2/agent/{agent_id}"
        print(f"\n📡 Making request to: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent found!")
            
            # Print the full response structure
            print(f"\n📋 Full API Response:")
            print(json.dumps(data, indent=2))
            
            # Extract key fields
            agent_config = data.get('agent_config', {})
            
            print(f"\n🔍 Key Fields Analysis:")
            print(f"  Agent Name: {data.get('agent_name', 'Not found')}")
            print(f"  Name: {data.get('name', 'Not found')}")
            print(f"  Welcome Message: {data.get('welcome_message', 'Not found')}")
            print(f"  Agent Welcome Message: {data.get('agent_welcome_message', 'Not found')}")
            
            print(f"\n🔍 Agent Config Fields:")
            print(f"  Agent Name: {agent_config.get('agent_name', 'Not found')}")
            print(f"  Welcome Message: {agent_config.get('welcome_message', 'Not found')}")
            print(f"  Agent Welcome Message: {agent_config.get('agent_welcome_message', 'Not found')}")
            
            # Check tasks for prompt
            tasks = agent_config.get('tasks', [])
            if tasks:
                task_config = tasks[0].get('task_config', {})
                llm_agent = task_config.get('llm_agent', {})
                system_prompt = llm_agent.get('system_prompt', 'Not found')
                print(f"  System Prompt: {system_prompt[:100]}..." if len(system_prompt) > 100 else f"  System Prompt: {system_prompt}")
            
        elif response.status_code == 404:
            print(f"❌ Agent not found in Bolna API")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_bolna_api()
