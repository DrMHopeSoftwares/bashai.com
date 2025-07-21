#!/usr/bin/env python3
"""
Test the agent update functionality to verify field mapping
"""

import requests
import json

def test_agent_update_fields():
    """Test agent details fetch and field mapping"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🔧 **TESTING AGENT UPDATE FIELD MAPPING**")
    print("=" * 60)
    
    # Test with a known agent ID from your screenshot
    test_agent_ids = [
        "9ede5ecf-9cac-4123-8cab-f644f99f1f73",  # agent AI
        "pooja",  # pooja agent
        "bablu"   # bablu agent
    ]
    
    for agent_id in test_agent_ids:
        print(f"\n🔍 **Testing Agent ID:** {agent_id}")
        print("-" * 40)
        
        try:
            # Test the agent details endpoint
            response = requests.get(f"{base_url}/api/bolna/agents/{agent_id}/details")
            
            print(f"📊 **Response Status:** {response.status_code}")
            
            if response.status_code == 200:
                details = response.json()
                print(f"✅ **Agent Details Retrieved Successfully!**")
                
                # Check the fields that the frontend expects
                expected_fields = {
                    'name': details.get('name'),
                    'welcome_message': details.get('welcome_message'),
                    'prompt': details.get('prompt'),
                    'language': details.get('language'),
                    'voice': details.get('voice'),
                    'sales_approach': details.get('sales_approach'),
                    'type': details.get('type')
                }
                
                print(f"📋 **Field Mapping Check:**")
                for field, value in expected_fields.items():
                    status = "✅" if value is not None else "❌"
                    display_value = str(value)[:50] + "..." if value and len(str(value)) > 50 else value
                    print(f"   {status} {field}: {display_value}")
                
                # Show raw response for debugging
                print(f"\n🔍 **Raw Response:**")
                print(json.dumps(details, indent=2))
                
            elif response.status_code == 404:
                print(f"⚠️ **Agent not found:** {agent_id}")
            else:
                print(f"❌ **Error:** {response.status_code}")
                try:
                    error_details = response.json()
                    print(f"   Error details: {error_details}")
                except:
                    print(f"   Error text: {response.text}")
                    
        except Exception as e:
            print(f"❌ **Exception:** {e}")
    
    print(f"\n🎯 **Test Complete!**")
    print("=" * 60)

if __name__ == "__main__":
    test_agent_update_fields()
