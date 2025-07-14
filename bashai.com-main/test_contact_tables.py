#!/usr/bin/env python3
"""
Test script to verify voice_agents and contacts tables
"""

import os
import requests
from dotenv import load_dotenv

def test_contact_tables():
    """Test the voice_agents and contacts tables"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    print(f"🔗 Testing contact tables in: {supabase_url}")
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    # Test voice_agents table
    try:
        print("\n📊 Testing voice_agents table...")
        response = requests.get(f'{supabase_url}/rest/v1/voice_agents', headers=headers)
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ voice_agents table accessible - Found {len(agents)} records")
            if agents:
                for agent in agents:
                    print(f"   • {agent['title']} ({agent['category']}) - {agent['status']}")
        else:
            print(f"❌ voice_agents error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ voice_agents error: {e}")
        return False
    
    # Test contacts table
    try:
        print("\n👥 Testing contacts table...")
        response = requests.get(f'{supabase_url}/rest/v1/contacts', headers=headers)
        if response.status_code == 200:
            contacts = response.json()
            print(f"✅ contacts table accessible - Found {len(contacts)} records")
            if contacts:
                # Group contacts by agent
                agent_contacts = {}
                for contact in contacts:
                    agent_id = contact['voice_agent_id']
                    if agent_id not in agent_contacts:
                        agent_contacts[agent_id] = []
                    agent_contacts[agent_id].append(contact)
                
                for agent_id, contacts_list in agent_contacts.items():
                    print(f"   Agent {agent_id}: {len(contacts_list)} contacts")
                    for contact in contacts_list[:3]:  # Show first 3
                        print(f"     • {contact['name']} ({contact['phone']}) - {contact['status']}")
        else:
            print(f"❌ contacts error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ contacts error: {e}")
        return False
    
    # Test API endpoints
    print("\n🔌 Testing API endpoints...")
    try:
        # Test voice agents API
        response = requests.get(f'http://127.0.0.1:8000/api/voice-agents', headers={'Content-Type': 'application/json'})
        if response.status_code == 401:
            print("✅ API endpoints are protected (401 Unauthorized as expected)")
        else:
            print(f"⚠️  API endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  API endpoint test failed: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 Testing Contact Management Tables")
    print("=" * 50)
    
    success = test_contact_tables()
    
    if success:
        print("\n✅ Contact tables test completed successfully!")
        print("The voice_agents and contacts tables are working correctly.")
        print("\nNext steps:")
        print("1. Open the dashboard: http://127.0.0.1:8000/dashboard.html")
        print("2. Sign in with Clerk authentication")
        print("3. Test the contact management features")
    else:
        print("\n❌ Contact tables test failed!")
        print("Please check the table creation and try again.")
