#!/usr/bin/env python3
"""
🔧 Fix Enterprise Assignment Issue
Ye script user ko enterprise assign karega aur assignment issue solve karega
"""

import os
import requests
from dotenv import load_dotenv

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
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ Supabase error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Request error: {e}")
        return None

def fix_enterprise_assignment():
    """Fix enterprise assignment issue"""
    print("🔧 Fixing Enterprise Assignment Issue...")
    
    # 1. Get all users without enterprise_id
    print("\n1️⃣ Checking users without enterprise...")
    users_without_enterprise = supabase_request('GET', 'users', params={
        'enterprise_id': 'is.null',
        'select': 'id,email,name'
    })
    
    if users_without_enterprise:
        print(f"   Found {len(users_without_enterprise)} users without enterprise")
        
        # 2. Get or create default enterprise
        print("\n2️⃣ Getting/Creating default enterprise...")
        enterprises = supabase_request('GET', 'enterprises', params={
            'name': 'eq.Default Enterprise',
            'select': 'id,name'
        })
        
        if enterprises and len(enterprises) > 0:
            enterprise_id = enterprises[0]['id']
            print(f"   ✅ Using existing enterprise: {enterprise_id}")
        else:
            # Create default enterprise
            enterprise_data = {
                'name': 'Default Enterprise',
                'type': 'business',
                'contact_email': 'admin@bashai.com',
                'status': 'active'
            }
            
            enterprise = supabase_request('POST', 'enterprises', data=enterprise_data)
            if enterprise:
                enterprise_id = enterprise[0]['id'] if isinstance(enterprise, list) else enterprise['id']
                print(f"   ✅ Created new enterprise: {enterprise_id}")
            else:
                print("   ❌ Failed to create enterprise")
                return False
        
        # 3. Assign users to enterprise
        print("\n3️⃣ Assigning users to enterprise...")
        for user in users_without_enterprise:
            user_id = user['id']
            email = user.get('email', 'Unknown')
            
            update_result = supabase_request('PATCH', f'users?id=eq.{user_id}', data={
                'enterprise_id': enterprise_id
            })
            
            if update_result:
                print(f"   ✅ Assigned {email} to enterprise")
            else:
                print(f"   ❌ Failed to assign {email}")
    
    else:
        print("   ✅ All users already have enterprise assigned")
    
    # 4. Check voice agents without enterprise
    print("\n4️⃣ Checking voice agents without enterprise...")
    agents_without_enterprise = supabase_request('GET', 'voice_agents', params={
        'enterprise_id': 'is.null',
        'select': 'id,title,user_id'
    })
    
    if agents_without_enterprise:
        print(f"   Found {len(agents_without_enterprise)} agents without enterprise")
        
        for agent in agents_without_enterprise:
            agent_id = agent['id']
            user_id = agent.get('user_id')
            title = agent.get('title', 'Unknown')
            
            if user_id:
                # Get user's enterprise_id
                user = supabase_request('GET', 'users', params={
                    'id': f'eq.{user_id}',
                    'select': 'enterprise_id'
                })
                
                if user and len(user) > 0 and user[0].get('enterprise_id'):
                    enterprise_id = user[0]['enterprise_id']
                    
                    update_result = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}', data={
                        'enterprise_id': enterprise_id
                    })
                    
                    if update_result:
                        print(f"   ✅ Assigned agent '{title}' to enterprise")
                    else:
                        print(f"   ❌ Failed to assign agent '{title}'")
    else:
        print("   ✅ All voice agents already have enterprise assigned")
    
    print("\n✅ Enterprise assignment fix completed!")
    return True

def test_assignment_endpoint():
    """Test the assignment endpoint"""
    print("\n🧪 Testing Assignment Endpoint...")
    
    # Get a voice agent and phone number for testing
    agents = supabase_request('GET', 'voice_agents', params={
        'status': 'eq.active',
        'select': 'id,title,enterprise_id',
        'limit': '1'
    })
    
    phones = supabase_request('GET', 'purchased_phone_numbers', params={
        'status': 'eq.active',
        'select': 'id,phone_number,enterprise_id',
        'limit': '1'
    })
    
    if agents and phones:
        agent = agents[0]
        phone = phones[0]
        
        print(f"   Agent: {agent['title']} (Enterprise: {agent.get('enterprise_id', 'None')})")
        print(f"   Phone: {phone['phone_number']} (Enterprise: {phone.get('enterprise_id', 'None')})")
        
        if agent.get('enterprise_id') and phone.get('enterprise_id'):
            print("   ✅ Both have enterprise_id - assignment should work")
        else:
            print("   ⚠️  Missing enterprise_id - assignment may fail")
    else:
        print("   ⚠️  No agents or phones found for testing")

if __name__ == "__main__":
    print("🚀 Starting Enterprise Assignment Fix...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase credentials in .env file")
        exit(1)
    
    success = fix_enterprise_assignment()
    
    if success:
        test_assignment_endpoint()
        print("\n🎉 Fix completed! Try the assignment again.")
    else:
        print("\n❌ Fix failed. Please check the logs.")
