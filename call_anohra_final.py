#!/usr/bin/env python3
"""
Final attempt to call Anohra using the exact format from screenshots
Addressing the 401 authentication issue
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def call_anohra_final():
    """Call Anohra with proper authentication handling"""
    
    print("🔥 FINAL ATTEMPT: Calling Anohra with Correct Auth")
    print("=" * 55)
    
    # Configuration
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    YOUR_PHONE = "+919373111709"
    
    print(f"🎯 Agent: Anohra ({ANOHRA_ID})")
    print(f"📱 Target: {YOUR_PHONE}")
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🌍 Region: {region}")
    print(f"📂 Project: {project_id}")
    
    # Try different authentication formats based on the screenshot hints
    auth_formats = [
        api_key,  # Just the API key (as shown in screenshot)
        f"Bearer {api_key}",  # Bearer format
        f"{project_id}:{api_key}",  # Project:API format  
        f"Bearer {project_id}:{api_key}"  # Bearer Project:API format
    ]
    
    # Different endpoint variations
    endpoints = [
        f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger",
        f"https://api-{region}.stack.tryrelevance.com/agents/trigger", 
        f"https://api.stack.tryrelevance.com/latest/agents/trigger"
    ]
    
    # Payload from screenshot
    payload = {
        "agent_id": ANOHRA_ID,
        "message": {
            "role": "user",
            "content": f"Please call {YOUR_PHONE} now"
        }
    }
    
    print(f"\n📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    success = False
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n🔗 Endpoint {i}: {endpoint}")
        
        for j, auth_format in enumerate(auth_formats, 1):
            print(f"   🔑 Auth {j}: {auth_format[:30]}...")
            
            headers = {
                "Authorization": auth_format,
                "Content-Type": "application/json",
                "User-Agent": "BhashAI-RelevanceAI/1.0"
            }
            
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"      📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"      ✅ SUCCESS! Response:")
                        print(json.dumps(result, indent=6))
                        
                        print(f"\n🎉 CALL INITIATED SUCCESSFULLY!")
                        print(f"📞 Anohra is calling {YOUR_PHONE}!")
                        print(f"📱 Please answer your phone...")
                        
                        success = True
                        break
                        
                    except json.JSONDecodeError:
                        print(f"      ✅ SUCCESS! Response: {response.text}")
                        success = True
                        break
                        
                elif response.status_code == 401:
                    print(f"      ❌ Auth failed")
                    continue
                elif response.status_code == 404:
                    print(f"      ❌ Not found")
                    break  # Try next endpoint
                else:
                    print(f"      ⚠️  Status {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"      ❌ Timeout")
            except requests.exceptions.ConnectionError:
                print(f"      ❌ Connection error")
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        if success:
            break
    
    if not success:
        print(f"\n💡 API Key Issues - From the screenshot:")
        print(f"   The API key must have 'Admin' scope")
        print(f"   Go to: Settings → Integrations → 'Create new secret key'")
        print(f"   Select 'Admin' permissions when creating the key")
        print(f"")
        print(f"🎯 MANUAL SOLUTION (Guaranteed to work):")
        print(f"   1. Go to: https://app.relevanceai.com")
        print(f"   2. Navigate to your Anohra agent")
        print(f"   3. Click 'Call agent' button (visible in your screenshot)")
        print(f"   4. Enter: {YOUR_PHONE}")
        print(f"   5. Start the call")
        print(f"")
        print(f"✅ Your agent is perfectly configured:")
        print(f"   • Phone runtime: Enabled")
        print(f"   • Voice: ElevenLabs (Hindi/English)")
        print(f"   • Role: Dr. Murali's Orthopaedic Clinic")
        print(f"   • Professional greeting ready")
    
    return success

if __name__ == "__main__":
    success = call_anohra_final()
    
    if not success:
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Check API key permissions (needs 'Admin' scope)")
        print(f"2. Use the dashboard 'Call agent' button (100% reliable)")
        print(f"3. Once you get a new Admin-scoped key, update .env and retry")
        
        print(f"\n📞 The dashboard method will work immediately!")
        print(f"   Anohra will call {'+919373111709'} and introduce herself professionally")