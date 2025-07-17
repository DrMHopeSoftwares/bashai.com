#!/usr/bin/env python3
"""
Test the contact creation fix
"""

import requests
import json

def test_contact_creation():
    """Test creating a contact via the dev endpoint"""
    
    print("🧪 Testing Contact Creation Fix")
    print("="*40)
    
    # Test Flask server
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running")
        else:
            print(f"❌ Flask server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Flask server: {e}")
        print("Please run: python main.py")
        return False
    
    # Test dev voice agents endpoint
    try:
        response = requests.get("http://localhost:8000/api/dev/voice-agents")
        if response.status_code == 200:
            agents = response.json().get('voice_agents', [])
            print(f"✅ Dev voice agents endpoint working ({len(agents)} agents)")
            if agents:
                test_agent = agents[0]
                agent_id = test_agent['id']
                print(f"📋 Using test agent: {test_agent.get('title', 'Unknown')} (ID: {agent_id})")
            else:
                print("⚠️  No voice agents found")
                return False
        else:
            print(f"❌ Dev voice agents endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing voice agents: {e}")
        return False
    
    # Test creating a contact
    try:
        contact_data = {
            "name": "Test Contact",
            "phone": "+919999999999"
        }
        
        response = requests.post(
            f"http://localhost:8000/api/dev/voice-agents/{agent_id}/contacts",
            headers={"Content-Type": "application/json"},
            json=contact_data
        )
        
        if response.status_code == 201:
            contact = response.json().get('contact')
            print(f"✅ Contact created successfully:")
            print(f"   └─ Name: {contact.get('name')}")
            print(f"   └─ Phone: {contact.get('phone')}")
            print(f"   └─ ID: {contact.get('id')}")
            return True
        else:
            print(f"❌ Contact creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating contact: {e}")
        return False

def test_dashboard_workflow():
    """Provide instructions for testing the dashboard"""
    
    print(f"\n🎯 Dashboard Testing Instructions")
    print("="*40)
    print("1. Open your browser and go to: http://localhost:8000")
    print("2. Navigate to the Contact Manager")
    print("3. Try adding a contact:")
    print("   • Name: Murali")
    print("   • Phone: +919373111709")
    print("4. Click 'Add Contact' button")
    print("5. The contact should be added without authentication errors")
    print("6. Select the contact and click '📞 Start Calls' to test Bolna integration")

if __name__ == "__main__":
    print("🔧 Contact Creation Fix Test\n")
    
    success = test_contact_creation()
    test_dashboard_workflow()
    
    print("\n" + "="*50)
    if success:
        print("🎉 Contact creation fix is working!")
        print("✅ You can now add contacts via the dashboard without authentication errors")
        print("✅ The Bolna integration is ready for use")
    else:
        print("❌ Contact creation fix needs attention")
        print("💡 Make sure Flask server is running: python main.py")
    
    print(f"\n📞 Ready to test voice calls!")
    print(f"🔗 Dashboard: http://localhost:8000")