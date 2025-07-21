#!/usr/bin/env python3
"""
Call Anohra using Raw RelevanceAI API (bypassing SDK issues)
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def make_anohra_call_raw_api():
    """Make Anohra call using direct HTTP API calls"""
    
    print("📞 Calling Anohra via Raw RelevanceAI API")
    print("=" * 45)
    
    # API Configuration
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    # RelevanceAI API base URL structure
    base_url = f"https://api-{region}.stack.tryrelevance.com"
    
    # Authorization header (using the format from your screenshot)
    headers = {
        "Authorization": f"{project_id}:{api_key}",
        "Content-Type": "application/json",
        "User-Agent": "BhashAI-RelevanceAI-Integration/1.0"
    }
    
    # Anohra details
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    YOUR_PHONE = "+919373111709"
    
    print(f"🎯 Agent: Anohra ({ANOHRA_ID})")
    print(f"📱 Target: {YOUR_PHONE}")
    print(f"🔗 API Base: {base_url}")
    print(f"🔑 Auth: {project_id}:{api_key[:20]}...")
    
    # Try different API endpoints for phone calls
    endpoints_to_try = [
        # Phone call specific endpoints
        {
            "name": "Phone Call Endpoint",
            "url": f"{base_url}/agents/{ANOHRA_ID}/phone_call",
            "method": "POST",
            "data": {
                "phone_number": YOUR_PHONE,
                "direction": "outbound"
            }
        },
        {
            "name": "Runtime Phone Endpoint", 
            "url": f"{base_url}/agents/{ANOHRA_ID}/runtime/phone",
            "method": "POST",
            "data": {
                "phone_number": YOUR_PHONE,
                "type": "outbound",
                "immediate": True
            }
        },
        {
            "name": "Agent Run with Phone Context",
            "url": f"{base_url}/agents/{ANOHRA_ID}/run",
            "method": "POST", 
            "data": {
                "runtime": "phone_call",
                "phone_number": YOUR_PHONE,
                "direction": "outbound",
                "params": {
                    "caller": "Dr. Murali",
                    "purpose": "Test call"
                }
            }
        },
        {
            "name": "Agent Async Run",
            "url": f"{base_url}/agents/{ANOHRA_ID}/async_run",
            "method": "POST",
            "data": {
                "params": {
                    "phone_number": YOUR_PHONE,
                    "action": "outbound_call",
                    "immediate": True
                }
            }
        },
        {
            "name": "Agent Trigger",
            "url": f"{base_url}/agents/{ANOHRA_ID}/trigger",
            "method": "POST",
            "data": {
                "phone_number": YOUR_PHONE,
                "runtime": "phone_call",
                "direction": "outbound"
            }
        },
        {
            "name": "Direct Phone API",
            "url": f"{base_url}/phone/call",
            "method": "POST",
            "data": {
                "agent_id": ANOHRA_ID,
                "phone_number": YOUR_PHONE,
                "direction": "outbound"
            }
        }
    ]
    
    success = False
    
    for i, endpoint in enumerate(endpoints_to_try, 1):
        print(f"\n{i}️⃣ Trying {endpoint['name']}...")
        print(f"   URL: {endpoint['url']}")
        
        try:
            if endpoint['method'] == 'POST':
                response = requests.post(
                    endpoint['url'],
                    headers=headers,
                    json=endpoint['data'],
                    timeout=30
                )
            elif endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'],
                    headers=headers,
                    params=endpoint['data'],
                    timeout=30
                )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                try:
                    result = response.json()
                    print(f"   ✅ SUCCESS! Response: {json.dumps(result, indent=2)}")
                    success = True
                    
                    print(f"\n🎉 CALL INITIATED SUCCESSFULLY!")
                    print(f"📞 Anohra is now calling {YOUR_PHONE}")
                    print(f"📱 Please answer your phone...")
                    print(f"🕐 The call should come through shortly...")
                    break
                    
                except json.JSONDecodeError:
                    print(f"   ✅ SUCCESS! Response: {response.text}")
                    success = True
                    break
                    
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed")
            elif response.status_code == 403:
                print(f"   ❌ Permission denied")
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    if not success:
        print(f"\n💡 All API endpoints failed. Alternative approaches:")
        print(f"   1. Use RelevanceAI dashboard 'Call agent' button")
        print(f"   2. Check API documentation for correct endpoints")
        print(f"   3. Verify phone call permissions in your RelevanceAI account")
        print(f"   4. Contact RelevanceAI support for phone API access")
    
    print(f"\n📋 Call Summary:")
    print(f"   Agent: Anohra (Dr. Murali's Orthopaedic Clinic)")
    print(f"   Target: {YOUR_PHONE}")
    print(f"   Method: Raw API calls")
    print(f"   Status: {'SUCCESS' if success else 'FAILED - Use Dashboard'}")
    
    return success

if __name__ == "__main__":
    success = make_anohra_call_raw_api()
    
    if success:
        print(f"\n✅ Call request sent! Check your phone at +919373111709")
    else:
        print(f"\n❌ Automated call failed. Please use the RelevanceAI dashboard:")
        print(f"   1. Go to your Anohra agent page")
        print(f"   2. Click the 'Call agent' button")
        print(f"   3. Enter +919373111709 as the phone number")
        print(f"   4. Initiate the call manually")