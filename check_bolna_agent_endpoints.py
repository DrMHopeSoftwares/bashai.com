#!/usr/bin/env python3
"""
Check Bolna API endpoints for agent creation and management
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_bolna_agent_endpoints():
    """Test various Bolna API endpoints for agent management"""
    
    api_key = os.getenv('BOLNA_API_KEY')
    base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
    
    if not api_key:
        print("❌ BOLNA_API_KEY not found")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print("🔍 Testing Bolna Agent Management Endpoints")
    print("="*50)
    
    # Test endpoints for agent management
    endpoints_to_test = [
        ('GET', '/v2/agent/all', 'List all agents'),
        ('GET', '/agent/all', 'List all agents (v1)'),
        ('GET', '/agents', 'List agents (simple)'),
        ('POST', '/v2/agent', 'Create agent (v2)'),
        ('POST', '/agent', 'Create agent (v1)'),
        ('GET', '/v2/agent/templates', 'Get agent templates'),
        ('GET', '/agent/templates', 'Get agent templates (v1)'),
    ]
    
    for method, endpoint, description in endpoints_to_test:
        print(f"\n📡 Testing: {method} {endpoint}")
        print(f"📝 Description: {description}")
        
        try:
            if method == 'GET':
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            elif method == 'POST':
                # For POST requests, we'll just check if the endpoint exists (expect 400/422 for missing data)
                test_data = {"test": "data"}
                response = requests.post(f"{base_url}{endpoint}", headers=headers, json=test_data, timeout=10)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint available and working")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"📋 Returned {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"📋 Returned object with keys: {list(data.keys())}")
                except:
                    print("📋 Response is not JSON")
            elif response.status_code in [400, 422]:
                print("⚠️ Endpoint exists but requires proper data")
            elif response.status_code == 404:
                print("❌ Endpoint not found")
            elif response.status_code == 401:
                print("🔐 Authentication required")
            else:
                print(f"⚠️ Unexpected status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    print("\n" + "="*50)
    print("🎯 Testing Agent Creation with Sample Data")
    
    # Test agent creation with sample data
    sample_agent_data = {
        "name": "Test Healthcare Agent",
        "description": "A test agent for healthcare appointments",
        "voice": "en-US-Standard-A",
        "language": "en",
        "prompt": "You are a helpful healthcare assistant for appointment booking.",
        "welcome_message": "Hello! I'm calling to help you with your healthcare appointment.",
        "max_duration": 300,
        "hangup_after": 30
    }
    
    creation_endpoints = [
        '/v2/agent',
        '/agent',
        '/agents'
    ]
    
    for endpoint in creation_endpoints:
        print(f"\n🧪 Testing agent creation at: {endpoint}")
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                headers=headers,
                json=sample_agent_data,
                timeout=15
            )
            
            print(f"📊 Status: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}...")
            
            if response.status_code in [200, 201]:
                print("✅ Agent creation endpoint working!")
                try:
                    created_agent = response.json()
                    print(f"🎉 Created agent ID: {created_agent.get('id', 'Unknown')}")
                except:
                    print("📋 Agent created but response not JSON")
            elif response.status_code == 422:
                print("⚠️ Validation error - need to check required fields")
            
        except Exception as e:
            print(f"❌ Creation test failed: {e}")

if __name__ == "__main__":
    test_bolna_agent_endpoints()
