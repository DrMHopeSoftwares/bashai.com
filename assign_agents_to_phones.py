#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def assign_agents_to_phone_numbers():
    """Assign agents to phone numbers in Bolna"""
    try:
        api_key = os.getenv('BOLNA_API_KEY')
        base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
        
        if not api_key:
            print("❌ BOLNA_API_KEY not found in environment")
            return
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Phone number to agent mapping
        phone_agent_mapping = {
            # '+918035315404': '491325fa-4323-4e39-8536-a1a66cd8d437',  # pooja
            # '+918035315390': '2f1b28b6-d2e6-4074-9c8e-ba9594947afa',  # bbbb
            # '+918035315328': '9ede5ecf-9cac-4123-8cab-f644f99f1f73',  # agent Ai
            # '+918035315322': 'c0357194-c863-4796-a825-d6de6e0707a5',  # hope
        }
        
        print("🔍 Getting current phone numbers from Bolna...")
        
        # Get current phone numbers
        response = requests.get(f"{base_url}/phone-numbers/all", headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get phone numbers: {response.text}")
            return
        
        phone_numbers = response.json()
        print(f"📞 Found {len(phone_numbers)} phone numbers in Bolna")
        
        # Update each phone number with agent assignment
        for phone_data in phone_numbers:
            phone_number = phone_data.get('phone_number')
            phone_id = phone_data.get('id')
            current_agent = phone_data.get('agent_id')
            
            if phone_number in phone_agent_mapping:
                new_agent_id = phone_agent_mapping[phone_number]
                
                if current_agent != new_agent_id:
                    print(f"\n📞 Updating {phone_number} (ID: {phone_id})")
                    print(f"   Current agent: {current_agent}")
                    print(f"   New agent: {new_agent_id}")
                    
                    # Try to update the phone number
                    update_data = {
                        'agent_id': new_agent_id
                    }
                    
                    # Try different endpoints for updating
                    endpoints_to_try = [
                        f'/phone-numbers/{phone_id}',
                        f'/phone-numbers/{phone_id}/agent',
                        f'/telephony/phone-numbers/{phone_id}',
                        f'/phone-numbers/{phone_number}/assign-agent'
                    ]
                    
                    updated = False
                    for endpoint in endpoints_to_try:
                        try:
                            print(f"   Trying endpoint: {endpoint}")
                            
                            # Try PATCH first, then PUT, then POST
                            for method in ['PATCH', 'PUT', 'POST']:
                                try:
                                    if method == 'PATCH':
                                        update_response = requests.patch(f"{base_url}{endpoint}", headers=headers, json=update_data)
                                    elif method == 'PUT':
                                        update_response = requests.put(f"{base_url}{endpoint}", headers=headers, json=update_data)
                                    else:  # POST
                                        update_response = requests.post(f"{base_url}{endpoint}", headers=headers, json=update_data)
                                    
                                    print(f"   {method} {endpoint}: {update_response.status_code}")
                                    
                                    if update_response.status_code in [200, 201, 204]:
                                        print(f"   ✅ Successfully updated {phone_number}")
                                        updated = True
                                        break
                                    else:
                                        print(f"   Response: {update_response.text}")
                                        
                                except Exception as e:
                                    print(f"   {method} failed: {e}")
                            
                            if updated:
                                break
                                
                        except Exception as e:
                            print(f"   Endpoint {endpoint} failed: {e}")
                    
                    if not updated:
                        print(f"   ❌ Failed to update {phone_number}")
                else:
                    print(f"✅ {phone_number} already has correct agent: {current_agent}")
            else:
                print(f"⚠️ No agent mapping found for {phone_number}")
        
        print("\n🔍 Verifying updates...")
        
        # Verify the updates
        response = requests.get(f"{base_url}/phone-numbers/all", headers=headers)
        if response.status_code == 200:
            updated_phones = response.json()
            print("\n📞 Updated phone numbers:")
            for phone in updated_phones:
                phone_number = phone.get('phone_number')
                agent_id = phone.get('agent_id')
                print(f"   {phone_number} -> Agent: {agent_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    assign_agents_to_phone_numbers()
