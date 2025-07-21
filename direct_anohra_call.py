#!/usr/bin/env python3
"""
Direct API call to RelevanceAI to trigger Anohra agent
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def call_anohra_direct():
    """Make direct API calls to RelevanceAI"""
    
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    print("📞 Direct RelevanceAI API Call to Anohra")
    print("=" * 45)
    
    # Base URL for RelevanceAI API
    base_url = f"https://api-{region}.stack.tryrelevance.com/latest"
    
    headers = {
        'Authorization': f'Bearer {project_id}:{api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'BhashAI-RelevanceAI-Integration/1.0'
    }
    
    print(f"🔗 API Base URL: {base_url}")
    print(f"🔑 Project ID: {project_id}")
    
    # Step 1: List agents to find Anohra
    print("\n1️⃣ Fetching agents...")
    try:
        agents_response = requests.get(
            f"{base_url}/agents",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {agents_response.status_code}")
        
        if agents_response.status_code == 200:
            agents_data = agents_response.json()
            print(f"✅ Found {len(agents_data)} agents")
            
            # Look for Anohra
            anohra_agent = None
            for agent in agents_data:
                agent_name = agent.get('name', '').lower()
                print(f"   - {agent.get('name', 'Unknown')} (ID: {agent.get('agent_id', 'Unknown')})")
                
                if 'anohra' in agent_name:
                    anohra_agent = agent
                    print(f"   🎯 Found Anohra: {agent}")
                    break
            
            if anohra_agent:
                agent_id = anohra_agent.get('agent_id')
                print(f"\n2️⃣ Creating session with Anohra (ID: {agent_id})...")
                
                # Step 2: Create a session with Anohra
                session_data = {
                    "session_id": f"call_session_{int(time.time())}",
                    "params": {
                        "user_phone": "+919373111709",
                        "request_type": "voice_call",
                        "caller": "Murali",
                        "priority": "high"
                    }
                }
                
                session_response = requests.post(
                    f"{base_url}/agents/{agent_id}/async_run",
                    headers=headers,
                    json=session_data,
                    timeout=30
                )
                
                print(f"Session Status: {session_response.status_code}")
                
                if session_response.status_code in [200, 201]:
                    session_result = session_response.json()
                    print(f"✅ Session created: {session_result}")
                    
                    # Step 3: Send call request message
                    print(f"\n3️⃣ Sending call request to Anohra...")
                    
                    call_message = {
                        "message": "Hello Anohra! This is Murali. Please make a voice call to +919373111709 immediately. I want to test our voice integration system. Call me now!",
                        "params": {
                            "action": "voice_call",
                            "phone_number": "+919373111709",
                            "immediate": True
                        }
                    }
                    
                    # Try different endpoints for messaging
                    endpoints_to_try = [
                        f"{base_url}/agents/{agent_id}/trigger",
                        f"{base_url}/agents/{agent_id}/run", 
                        f"{base_url}/agents/{agent_id}/async_run"
                    ]
                    
                    for endpoint in endpoints_to_try:
                        print(f"   Trying: {endpoint}")
                        message_response = requests.post(
                            endpoint,
                            headers=headers,
                            json=call_message,
                            timeout=30
                        )
                        
                        print(f"   Status: {message_response.status_code}")
                        
                        if message_response.status_code in [200, 201]:
                            result = message_response.json()
                            print(f"   ✅ Success: {result}")
                            
                            print(f"\n🎉 Call request sent to Anohra!")
                            print(f"📞 Anohra should now call +919373111709")
                            print(f"⏰ Please wait for the call...")
                            return True
                        else:
                            print(f"   ❌ Failed: {message_response.text}")
                    
                else:
                    print(f"❌ Session creation failed: {session_response.text}")
            else:
                print("❌ Anohra agent not found in the list")
                
        else:
            print(f"❌ Failed to fetch agents: {agents_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return False

if __name__ == "__main__":
    import time
    success = call_anohra_direct()
    
    if success:
        print("\n✅ Request completed successfully!")
        print("📱 Your phone should ring shortly...")
    else:
        print("\n❌ Request failed. Please check:")
        print("   1. RelevanceAI credentials in .env")
        print("   2. Anohra agent configuration")
        print("   3. API permissions")