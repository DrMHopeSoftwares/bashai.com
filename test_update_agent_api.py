#!/usr/bin/env python3
"""
Test script to verify the agent details API endpoint
"""

import requests
import json

def test_agent_details_api():
    """Test the agent details API endpoint"""
    
    # Test agent ID (actual agent ID from bolna_integration.py)
    test_agent_id = "15554373-b8e1-4b00-8c25-c4742dc8e480"  # From bolna_integration.py
    
    # API endpoint
    url = f"http://localhost:5003/api/bolna/agents/{test_agent_id}/details"
    
    print(f"🔍 Testing agent details API for agent: {test_agent_id}")
    print(f"📡 Making request to: {url}")
    
    try:
        response = requests.get(url)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Agent details retrieved:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check specific fields we need for the update modal
            required_fields = ['agent_id', 'name', 'language', 'voice', 'sales_approach', 'welcome_message', 'prompt']
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    print(f"✅ {field}: {data[field]}")
            
            if missing_fields:
                print(f"⚠️ Missing fields: {missing_fields}")
            else:
                print(f"🎉 All required fields are present!")
                
        else:
            print(f"❌ Error response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_agent_details_api()
