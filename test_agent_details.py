#!/usr/bin/env python3
"""
Test agent details fetch API
"""

import requests
import json

def test_agent_details():
    """Test the agent details fetch endpoint"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🤖 **TESTING AGENT DETAILS FETCH**")
    print("=" * 60)
    
    # Test agent ID from the screenshot
    agent_id = "9ede5ecf-9cac-4123-8cab-f644f99f1f73"
    
    print(f"🔍 **Testing Agent Details Fetch**")
    print(f"   Agent ID: {agent_id}")
    
    # Test the agent details endpoint
    details_response = requests.get(f"{base_url}/api/bolna/agents/{agent_id}/details")
    
    print(f"\n📊 **Response Status:** {details_response.status_code}")
    
    if details_response.status_code == 200:
        details_result = details_response.json()
        print(f"✅ **Agent Details Retrieved Successfully!**")
        print(f"📋 **Agent Details:**")
        print(json.dumps(details_result, indent=2))
        
        # Check specific fields
        agent_name = details_result.get('name')
        welcome_message = details_result.get('welcome_message')
        prompt = details_result.get('prompt')
        agent_type = details_result.get('type')
        
        print(f"\n🎯 **Parsed Fields:**")
        print(f"   🏷️ Name: {agent_name}")
        print(f"   💬 Welcome Message: {welcome_message[:100] if welcome_message else 'None'}...")
        print(f"   📝 Prompt: {prompt[:100] if prompt else 'None'}...")
        print(f"   📊 Type: {agent_type}")
        
        return True
    else:
        print(f"❌ Failed to get agent details: {details_response.status_code}")
        print(f"Response: {details_response.text}")
        return False

if __name__ == "__main__":
    test_agent_details()
