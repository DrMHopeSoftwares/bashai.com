#!/usr/bin/env python3
"""
Call Anohra using the SECRET SAUCE - Raw RelevanceAI API endpoint from the screenshots!
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def call_anohra_with_secret_sauce():
    """Make Anohra call using the exact API format from the screenshots"""
    
    print("🔥 CALLING ANOHRA WITH THE SECRET SAUCE!")
    print("=" * 50)
    
    # From the screenshot - exact configuration
    API_KEY = os.getenv('RELEVANCE_AI_API_KEY')
    CLUSTER = "f1db6c"  # From your region
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"  # Anohra's ID
    YOUR_PHONE = "+919373111709"
    
    # The SECRET SAUCE endpoint from the screenshot
    ENDPOINT = f"https://api-{CLUSTER}.stack.tryrelevance.com/latest/agents/trigger"
    
    print(f"🎯 Agent: Anohra ({ANOHRA_ID})")
    print(f"📱 Calling: {YOUR_PHONE}")
    print(f"🔗 Endpoint: {ENDPOINT}")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    
    # Exact payload format from the screenshot
    payload = {
        "agent_id": ANOHRA_ID,  # Anohra's ID
        "message": {
            "role": "user",
            "content": f"Please call {YOUR_PHONE} now"
        }
    }
    
    # Headers from the screenshot
    headers = {
        "Authorization": API_KEY,  # Just the API key as shown
        "Content-Type": "application/json"
    }
    
    print(f"\n📋 Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        print(f"\n🚀 Sending request...")
        response = requests.post(
            ENDPOINT, 
            headers=headers, 
            json=payload, 
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Response:")
            print(json.dumps(result, indent=2))
            
            print(f"\n🎉 CALL TRIGGERED!")
            print(f"📞 Anohra is now calling {YOUR_PHONE}!")
            print(f"📱 Please answer your phone...")
            print(f"🕐 The call should arrive shortly...")
            
            return True
            
        elif response.status_code == 401:
            print(f"❌ Authentication failed")
            print(f"💡 Tip: Ensure API key has 'Admin' scope (Settings → Integrations → 'Create new secret key')")
            
        elif response.status_code == 404:
            print(f"❌ Resource not found")
            print(f"💡 Tip: Double-check the cluster substring '{CLUSTER}' matches your dashboard URL")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
            # Check common issues from the screenshot
            if "Authorization header must be in the format" in response.text:
                print(f"💡 Fix: Ensure header is literally 'Authorization: <api_key>' - no project/region prefixes")
            elif "Resource not found" in response.text:
                print(f"💡 Fix: Double-check the cluster substring in the base URL must match your dashboard's sub-domain")
    
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout")
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - check internet connection")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return False

def call_anohra_with_variables():
    """Alternative method using template variables as shown in screenshot"""
    
    print(f"\n🔄 Trying alternative method with template variables...")
    
    API_KEY = os.getenv('RELEVANCE_AI_API_KEY')
    CLUSTER = "f1db6c"
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    YOUR_PHONE = "+919373111709"
    
    ENDPOINT = f"https://api-{CLUSTER}.stack.tryrelevance.com/latest/agents/trigger"
    
    # Alternative payload with variables (from screenshot)
    payload = {
        "agent_id": ANOHRA_ID,
        "message": {
            "role": "user", 
            "content": f"Call {YOUR_PHONE} now"
        },
        "variables": {
            "phone_number": YOUR_PHONE
        }
    }
    
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Variables method SUCCESS!")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Variables method failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Variables method error: {e}")
    
    return False

if __name__ == "__main__":
    print("🎯 Using the SECRET SAUCE from your screenshots!")
    print("This is the raw HTTP endpoint RelevanceAI exposes for programmatic phone calls")
    print("-" * 80)
    
    # Try the main method
    success = call_anohra_with_secret_sauce()
    
    if not success:
        # Try alternative method
        success = call_anohra_with_variables()
    
    if success:
        print(f"\n🎉 SUCCESS! Anohra should be calling you now!")
        print(f"📞 Check your phone at {'+919373111709'}")
        print(f"🤖 You'll hear Anohra's professional greeting for Dr. Murali's clinic")
    else:
        print(f"\n❌ All methods failed. Fallback options:")
        print(f"   1. Use RelevanceAI dashboard 'Call agent' button")
        print(f"   2. Verify API key has 'Admin' scope")
        print(f"   3. Check that Anohra's Mode is set to 'Phone Call' in Advanced Settings")
        print(f"   4. Ensure ElevenLabs voice is configured under 'Voice settings'")