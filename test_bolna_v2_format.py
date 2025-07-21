#!/usr/bin/env python3
"""
Test different formats for Bolna v2 API
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_v2_formats():
    """Test different data formats for v2 API"""
    
    api_key = os.getenv('BOLNA_API_KEY')
    base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print("🧪 Testing Bolna v2 API Formats")
    print("="*40)
    
    # Format 1: Simple format
    simple_format = {
        "agent_name": "Test Simple Agent",
        "description": "Simple test agent",
        "agent_type": "voice"
    }
    
    # Format 2: Minimal config format
    minimal_format = {
        "agent_name": "Test Minimal Agent",
        "agent_config": {
            "agent_name": "Test Minimal Agent",
            "agent_type": "voice",
            "tasks": []
        }
    }
    
    # Format 3: Basic conversation format
    basic_format = {
        "agent_name": "Test Basic Agent",
        "agent_config": {
            "agent_name": "Test Basic Agent",
            "agent_type": "voice",
            "tasks": [
                {
                    "task_type": "conversation"
                }
            ]
        }
    }
    
    formats = [
        ("Simple Format", simple_format),
        ("Minimal Format", minimal_format),
        ("Basic Format", basic_format)
    ]
    
    for name, data in formats:
        print(f"\n🔄 Testing: {name}")
        print(f"📋 Data: {json.dumps(data, indent=2)}")
        
        try:
            response = requests.post(
                f"{base_url}/v2/agent",
                headers=headers,
                json=data,
                timeout=15
            )
            
            print(f"📊 Status: {response.status_code}")
            print(f"📝 Response: {response.text[:300]}...")
            
            if response.status_code in [200, 201]:
                print("✅ Format accepted!")
                result = response.json()
                agent_id = result.get('agent_id') or result.get('id')
                if agent_id:
                    print(f"🎯 Created Agent ID: {agent_id}")
                break
            elif response.status_code == 422:
                print("⚠️ Validation error - checking required fields")
                try:
                    error_detail = response.json()
                    print(f"📋 Error Details: {json.dumps(error_detail, indent=2)}")
                except:
                    pass
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n📚 Checking API Documentation...")
    
    # Try to get existing agents to see the format
    try:
        response = requests.get(f"{base_url}/v2/agent/all", headers=headers)
        if response.status_code == 200:
            agents = response.json()
            if agents and len(agents) > 0:
                print(f"📋 Example existing agent structure:")
                print(json.dumps(agents[0], indent=2))
            else:
                print("📭 No existing agents found")
        else:
            print(f"❌ Could not fetch existing agents: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching agents: {e}")

if __name__ == "__main__":
    test_v2_formats()
