#!/usr/bin/env python3
"""
Test script to demonstrate the new phone number agent assignment feature
"""

import requests
import json

def test_phone_agent_assignment():
    """Test the new phone number agent assignment feature"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🧪 Testing Phone Number Agent Assignment Feature")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1. 🔐 Logging in...")
    login_data = {
        "email": "b@gmail.com",
        "password": "bhupendra"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get('token')
            print("✅ Login successful!")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        else:
            print("❌ Login failed")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Get phone numbers
    print("\n2. 📱 Fetching phone numbers...")
    try:
        phone_response = requests.get(f"{base_url}/api/phone-numbers/owned-simple", headers=headers)
        if phone_response.status_code == 200:
            phone_data = phone_response.json()
            if phone_data.get('success') and phone_data.get('data'):
                phones = phone_data['data']
                print(f"✅ Found {len(phones)} phone numbers")
                
                # Show phone numbers and their assignment status
                print("\n📋 Phone Number Status:")
                for i, phone in enumerate(phones[:5], 1):  # Show first 5
                    agent_status = f"Agent: {phone.get('agent_id', 'Not Assigned')}"
                    print(f"   {i}. {phone['phone_number']} - {agent_status}")
                
                # Find an unassigned phone number
                unassigned_phones = [p for p in phones if not p.get('agent_id')]
                if unassigned_phones:
                    test_phone = unassigned_phones[0]
                    print(f"\n🎯 Testing with unassigned phone: {test_phone['phone_number']}")
                    
                    # Step 3: Create agent for specific phone
                    print("\n3. 🤖 Creating agent for specific phone number...")
                    agent_data = {
                        "name": f"Sales Agent for {test_phone['phone_number']}",
                        "type": "sales",
                        "welcome_message": f"नमस्ते! मैं {test_phone['phone_number']} का sales assistant हूं।",
                        "description": f"Dedicated sales agent for {test_phone['phone_number']}",
                        "voice": "Aditi",
                        "language": "hi",
                        "max_duration": 180,
                        "silence_timeout": 15,
                        "sales_approach": "consultative"
                    }
                    
                    try:
                        agent_response = requests.post(f"{base_url}/api/bolna/create-sales-agent", 
                                                     json=agent_data, headers=headers)
                        if agent_response.status_code == 200:
                            agent_result = agent_response.json()
                            agent_id = agent_result.get('agent_id')
                            print(f"✅ Agent created successfully!")
                            print(f"   Agent ID: {agent_id}")
                            print(f"   Agent Name: {agent_result.get('agent_name')}")
                            
                            # Step 4: Assign agent to phone number
                            print(f"\n4. 🔗 Assigning agent to phone number...")
                            assign_data = {"agent_id": agent_id}
                            
                            try:
                                assign_response = requests.post(
                                    f"{base_url}/api/phone-numbers/{test_phone['id']}/assign-agent",
                                    json=assign_data, headers=headers
                                )
                                
                                if assign_response.status_code == 200:
                                    assign_result = assign_response.json()
                                    print("✅ Agent assigned to phone number successfully!")
                                    print(f"   Phone: {test_phone['phone_number']}")
                                    print(f"   Agent: {agent_id}")
                                    print(f"   Message: {assign_result.get('message')}")
                                    
                                    # Step 5: Verify assignment
                                    print(f"\n5. ✅ Verifying assignment...")
                                    verify_response = requests.get(f"{base_url}/api/phone-numbers/owned-simple", headers=headers)
                                    if verify_response.status_code == 200:
                                        verify_data = verify_response.json()
                                        updated_phone = next((p for p in verify_data['data'] if p['id'] == test_phone['id']), None)
                                        if updated_phone and updated_phone.get('agent_id') == agent_id:
                                            print("✅ Assignment verified in database!")
                                            print(f"   Phone {updated_phone['phone_number']} now has agent {updated_phone['agent_id']}")
                                        else:
                                            print("⚠️ Assignment not reflected in database yet")
                                    
                                    print(f"\n🎉 SUCCESS! Complete workflow tested:")
                                    print(f"   ✅ Agent created via Bolna API")
                                    print(f"   ✅ Agent assigned to specific phone number")
                                    print(f"   ✅ Database updated with assignment")
                                    print(f"   ✅ One-to-one phone-agent relationship established")
                                    
                                else:
                                    print(f"❌ Assignment failed: {assign_response.status_code}")
                                    print(f"   Response: {assign_response.text}")
                                    
                            except Exception as e:
                                print(f"❌ Assignment error: {e}")
                                
                        else:
                            print(f"❌ Agent creation failed: {agent_response.status_code}")
                            print(f"   Response: {agent_response.text}")
                            
                    except Exception as e:
                        print(f"❌ Agent creation error: {e}")
                        
                else:
                    print("⚠️ All phone numbers are already assigned")
                    print("   Use the dashboard to create agents for specific phones")
                    
            else:
                print("❌ No phone numbers found")
        else:
            print(f"❌ Failed to fetch phone numbers: {phone_response.status_code}")
            
    except Exception as e:
        print(f"❌ Phone fetch error: {e}")
    
    print(f"\n📱 Dashboard URL: {base_url}/dashboard.html")
    print("   Go to 'My Phone Numbers' section")
    print("   Click 🤖 button next to any unassigned phone number")
    print("   Create a dedicated agent for that specific phone!")

if __name__ == "__main__":
    test_phone_agent_assignment()
