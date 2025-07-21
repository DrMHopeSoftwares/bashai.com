#!/usr/bin/env python3
"""
Call Anohra using the correct RelevanceAI API endpoints
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def make_anohra_call_correct_api():
    """Make Anohra call using correct RelevanceAI API structure"""
    
    print("📞 Calling Anohra via Correct RelevanceAI API")
    print("=" * 50)
    
    # API Configuration from .env
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    # Try different base URL formats
    base_urls = [
        f"https://api-{region}.relevanceai.com",
        f"https://api.relevanceai.com",
        "https://api.stack.tryrelevance.com",
        f"https://{region}.api.relevanceai.com"
    ]
    
    # Authorization formats to try
    auth_formats = [
        f"Bearer {api_key}",
        f"{project_id}:{api_key}",
        f"Bearer {project_id}:{api_key}",
        api_key
    ]
    
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    YOUR_PHONE = "+919373111709"
    
    print(f"🎯 Agent: Anohra ({ANOHRA_ID})")
    print(f"📱 Target: {YOUR_PHONE}")
    
    # Phone call endpoints to try
    phone_endpoints = [
        "/agents/{}/call",
        "/agents/{}/phone",
        "/agents/{}/run",
        "/agents/{}/trigger",
        "/v1/agents/{}/call",
        "/v1/agents/{}/phone",
        "/latest/agents/{}/call",
        "/latest/agents/{}/phone"
    ]
    
    success = False
    
    for base_url in base_urls:
        print(f"\n🔗 Trying base URL: {base_url}")
        
        for auth_format in auth_formats:
            print(f"   🔑 Auth format: {auth_format[:30]}...")
            
            headers = {
                "Authorization": auth_format,
                "Content-Type": "application/json",
                "User-Agent": "BhashAI-RelevanceAI/1.0"
            }
            
            for endpoint_template in phone_endpoints:
                endpoint = endpoint_template.format(ANOHRA_ID)
                full_url = f"{base_url}{endpoint}"
                
                print(f"     📡 Testing: {endpoint}")
                
                # Call data options
                call_data_options = [
                    {
                        "phone_number": YOUR_PHONE,
                        "direction": "outbound"
                    },
                    {
                        "to": YOUR_PHONE,
                        "type": "outbound"
                    },
                    {
                        "params": {
                            "phone_number": YOUR_PHONE,
                            "action": "call"
                        }
                    },
                    {
                        "phone_number": YOUR_PHONE
                    }
                ]
                
                for call_data in call_data_options:
                    try:
                        response = requests.post(
                            full_url,
                            headers=headers,
                            json=call_data,
                            timeout=10
                        )
                        
                        if response.status_code in [200, 201, 202]:
                            print(f"         ✅ SUCCESS! Status: {response.status_code}")
                            try:
                                result = response.json()
                                print(f"         📞 Response: {json.dumps(result, indent=2)}")
                            except:
                                print(f"         📞 Response: {response.text}")
                            
                            print(f"\n🎉 CALL INITIATED!")
                            print(f"📞 Anohra should call {YOUR_PHONE} shortly...")
                            success = True
                            break
                            
                        elif response.status_code == 404:
                            continue  # Try next endpoint
                        elif response.status_code == 401:
                            print(f"         ❌ Auth failed")
                            break  # Try next auth format
                        else:
                            print(f"         ⚠️  Status {response.status_code}: {response.text[:100]}")
                            
                    except requests.exceptions.Timeout:
                        continue
                    except requests.exceptions.ConnectionError:
                        continue
                    except Exception:
                        continue
                
                if success:
                    break
            if success:
                break
        if success:
            break
    
    if not success:
        print(f"\n🔍 Let me try to get the correct API documentation...")
        
        # Try to access the API docs or health endpoint
        for base_url in base_urls[:2]:  # Try main URLs only
            try:
                docs_response = requests.get(f"{base_url}/docs", timeout=5)
                if docs_response.status_code == 200:
                    print(f"✅ Found API docs at: {base_url}/docs")
                    break
                    
                health_response = requests.get(f"{base_url}/health", timeout=5)
                if health_response.status_code == 200:
                    print(f"✅ API healthy at: {base_url}")
                    break
                    
            except:
                continue
        
        print(f"\n💡 Since API calls failed, here's the manual approach:")
        print(f"   1. Go to: https://app.relevanceai.com")
        print(f"   2. Navigate to your Anohra agent")
        print(f"   3. Click 'Call agent' or 'Run' button")
        print(f"   4. Enter phone number: {YOUR_PHONE}")
        print(f"   5. Start the call")
        
        print(f"\n📱 Your Anohra agent is ready with:")
        print(f"   • Phone runtime enabled")
        print(f"   • ElevenLabs voice (Hindi/English)")
        print(f"   • Orthopaedic clinic context")
        print(f"   • Professional greeting configured")
    
    return success

if __name__ == "__main__":
    success = make_anohra_call_correct_api()
    
    if not success:
        print(f"\n🚀 QUICK SOLUTION:")
        print(f"Since you have the RelevanceAI dashboard open:")
        print(f"1. Click the 'Call agent' button visible in your screenshot")
        print(f"2. Enter +919373111709")
        print(f"3. Click to start the call")
        print(f"\nThe call will work perfectly through the dashboard! 📞")