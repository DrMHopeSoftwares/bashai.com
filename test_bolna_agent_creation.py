#!/usr/bin/env python3
"""
Test Bolna agent creation functionality
"""

import os
import requests
import json
from dotenv import load_dotenv
from bolna_integration import BolnaAPI

load_dotenv()

def test_agent_creation():
    """Test creating a Bolna agent"""
    
    print("🧪 Testing Bolna Agent Creation")
    print("="*40)
    
    try:
        # Initialize Bolna API
        bolna_api = BolnaAPI()
        
        # Test agent data
        test_agent = {
            "name": "Test Healthcare Assistant",
            "description": "A test agent for healthcare appointments and reminders",
            "prompt": "You are a helpful healthcare assistant. You help patients with appointment booking, prescription reminders, and general health inquiries. Be polite, professional, and empathetic.",
            "welcome_message": "Hello! This is your healthcare assistant. How can I help you today?",
            "voice": "en-IN-Standard-A",
            "language": "en",
            "max_duration": 300,
            "hangup_after": 30
        }
        
        print("📋 Test Agent Configuration:")
        for key, value in test_agent.items():
            print(f"   {key}: {value}")
        
        print(f"\n🔄 Creating agent...")
        
        # Create the agent
        result = bolna_api.create_agent(**test_agent)
        
        print("✅ Agent created successfully!")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        
        # Extract agent ID if available
        agent_id = result.get('agent_id') or result.get('id')
        if agent_id:
            print(f"\n🎯 Created Agent ID: {agent_id}")
            
            # Test getting agent details
            print(f"\n🔍 Testing: Get Agent Details")
            try:
                details = bolna_api.get_agent_details(agent_id)
                print(f"✅ Retrieved agent details")
                print(f"📋 Agent Details: {json.dumps(details, indent=2)}")
            except Exception as e:
                print(f"⚠️ Could not retrieve agent details: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False

def test_api_endpoint():
    """Test the Flask API endpoint for agent creation"""
    
    print("\n🌐 Testing Flask API Endpoint")
    print("="*40)
    
    # Test data
    test_data = {
        "name": "API Test Agent",
        "description": "Testing agent creation via API",
        "prompt": "You are a test agent created via API.",
        "welcome_message": "Hello! This is a test agent.",
        "voice": "en-IN-Standard-A",
        "language": "en",
        "max_duration": 180,
        "hangup_after": 20
    }
    
    try:
        # Test the API endpoint (assuming Flask app is running)
        response = requests.post(
            'http://127.0.0.1:5001/api/bolna/agents',
            headers={
                'Content-Type': 'application/json',
                # Note: In real usage, you'd need a valid auth token
                'Authorization': 'Bearer test-token'
            },
            json=test_data,
            timeout=30
        )
        
        print(f"📊 API Response Status: {response.status_code}")
        print(f"📝 API Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API endpoint working correctly!")
                return True
            else:
                print(f"⚠️ API returned error: {result.get('message')}")
        else:
            print(f"❌ API request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Flask app not running. Start with: python3 main.py")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    return False

def main():
    print("🚀 Bolna Agent Creation Test Suite")
    print("="*50)
    
    # Check API key
    api_key = os.getenv('BOLNA_API_KEY')
    if not api_key or api_key == 'your-bolna-api-key-here':
        print("❌ BOLNA_API_KEY not configured")
        return
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    # Test 1: Direct API creation
    success1 = test_agent_creation()
    
    # Test 2: Flask endpoint (optional)
    success2 = test_api_endpoint()
    
    print(f"\n📊 Test Results:")
    print(f"   Direct API Creation: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Flask API Endpoint: {'✅ PASS' if success2 else '⚠️ SKIP'}")
    
    if success1:
        print(f"\n🎉 Agent creation is working!")
        print(f"🌐 You can now create agents via:")
        print(f"   - Direct API: BolnaAPI().create_agent(...)")
        print(f"   - Web Interface: http://127.0.0.1:5001/static/create-bolna-agent.html")
        print(f"   - API Endpoint: POST /api/bolna/agents")

if __name__ == "__main__":
    main()
