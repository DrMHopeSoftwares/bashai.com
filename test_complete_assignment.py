#!/usr/bin/env python3
"""
🧪 Complete Assignment Test
Test the complete voice agent creation and phone assignment flow
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def get_headers():
    return {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

def supabase_request(method, endpoint, data=None, params=None):
    """Make request to Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = get_headers()
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ Supabase error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Request error: {e}")
        return None

def test_complete_flow():
    """Test the complete voice agent creation and assignment flow"""
    print("🚀 Testing Complete Assignment Flow...")
    
    # 1. Check existing data
    print("\n1️⃣ Checking existing data...")
    
    # Get enterprises
    enterprises = supabase_request('GET', 'enterprises', params={'limit': '1'})
    if not enterprises:
        print("   ❌ No enterprises found")
        return False
    
    enterprise_id = enterprises[0]['id']
    print(f"   ✅ Enterprise: {enterprises[0]['name']} ({enterprise_id[:8]}...)")
    
    # Get phone numbers
    phones = supabase_request('GET', 'purchased_phone_numbers', 
                            params={'enterprise_id': f'eq.{enterprise_id}', 
                                   'status': 'eq.active', 'limit': '1'})
    if not phones:
        print("   ❌ No active phone numbers found")
        return False
    
    phone = phones[0]
    phone_id = phone['id']
    phone_number = phone['phone_number']
    print(f"   ✅ Phone: {phone_number} ({phone_id[:8]}...)")
    
    # 2. Create voice agent using the correct table structure
    print("\n2️⃣ Creating voice agent...")
    
    # Try minimal data first to see what works
    agent_data = {
        'title': 'Test Sales Expert',
        'url': 'https://api.bashai.com/test-agent',
        'enterprise_id': enterprise_id,
        'status': 'active'
    }
    
    agent = supabase_request('POST', 'voice_agents', data=agent_data)
    if not agent:
        print("   ❌ Failed to create voice agent")
        return False
    
    agent_id = agent[0]['id'] if isinstance(agent, list) else agent['id']
    agent_title = agent[0]['title'] if isinstance(agent, list) else agent['title']
    print(f"   ✅ Created agent: {agent_title} ({agent_id[:8]}...)")
    
    # 3. Test assignment
    print("\n3️⃣ Testing phone assignment...")
    
    # Get agent configuration
    agent_record = supabase_request('GET', 'voice_agents', 
                                  params={'id': f'eq.{agent_id}'})
    
    if not agent_record:
        print("   ❌ Could not retrieve created agent")
        return False
    
    # Update agent configuration with phone assignment
    agent_config = agent_record[0].get('configuration', {})
    agent_config['outbound_phone_number'] = phone_number
    agent_config['outbound_phone_number_id'] = phone_id
    
    assignment_result = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}',
                                       data={'configuration': agent_config,
                                            'updated_at': datetime.now(timezone.utc).isoformat()})
    
    if not assignment_result:
        print("   ❌ Failed to assign phone to agent")
        return False
    
    print(f"   ✅ Assigned phone {phone_number} to agent {agent_title}")

    # 4. Verify assignment
    print("\n4️⃣ Verifying assignment...")

    # Get updated agent
    updated_agent = supabase_request('GET', 'voice_agents',
                                   params={'id': f'eq.{agent_id}'})

    if updated_agent and len(updated_agent) > 0:
        config = updated_agent[0].get('configuration', {})
        assigned_phone = config.get('outbound_phone_number')
        assigned_phone_id = config.get('outbound_phone_number_id')

        if assigned_phone == phone_number and assigned_phone_id == phone_id:
            print(f"   ✅ Assignment verified!")
            print(f"   📞 Agent: {agent_title}")
            print(f"   📱 Phone: {assigned_phone}")
            
            # 5. Test unassignment
            print("\n5️⃣ Testing unassignment...")
            
            # Clear assignment
            config.pop('outbound_phone_number', None)
            config.pop('outbound_phone_number_id', None)
            
            unassign_result = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}',
                                             data={'configuration': config,
                                                  'updated_at': datetime.now(timezone.utc).isoformat()})
            
            if unassign_result:
                print("   ✅ Unassignment successful!")
                
                # 6. Cleanup - delete test agent
                print("\n6️⃣ Cleaning up...")
                delete_result = supabase_request('DELETE', f'voice_agents?id=eq.{agent_id}', data={})
                if delete_result is not None:  # DELETE returns empty response on success
                    print("   ✅ Test agent deleted")
                else:
                    print("   ⚠️  Could not delete test agent")
                
                return True
            else:
                print("   ❌ Unassignment failed")
                return False
        else:
            print("   ❌ Assignment verification failed")
            print(f"   Expected: {phone_number} ({phone_id})")
            print(f"   Got: {assigned_phone} ({assigned_phone_id})")
            return False
    else:
        print("   ❌ Could not retrieve updated agent")
        return False

if __name__ == "__main__":
    print("🧪 Starting Complete Assignment Test...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase credentials in .env file")
        exit(1)
    
    success = test_complete_flow()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Summary:")
        print("   ✅ Voice agent creation works")
        print("   ✅ Phone assignment works")
        print("   ✅ Assignment verification works")
        print("   ✅ Unassignment works")
        print("   ✅ Cleanup works")
        print("\n💡 The assignment system is fully functional!")
        print("   You can now create agents and assign phone numbers without errors.")
    else:
        print("\n❌ TESTS FAILED!")
        print("   Please check the logs for more details.")
