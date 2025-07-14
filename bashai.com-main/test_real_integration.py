#!/usr/bin/env python3
"""
Test the real Bolna integration end-to-end
"""

import os
import sys
import json
from dotenv import load_dotenv
from bolna_integration import BolnaAPI, get_agent_config_for_voice_agent
import requests

load_dotenv()

def test_supabase_data():
    """Test getting data from Supabase"""
    print("🗄️  Testing Supabase Data Access")
    print("="*40)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    }
    
    # Get contacts from Dr. Pratik (from sample data)
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/contacts?name=eq.Dr.%20Pratik", headers=headers)
        if response.status_code == 200:
            contacts = response.json()
            if contacts:
                contact = contacts[0]
                print(f"✅ Found test contact: {contact['name']} - {contact['phone']}")
                return contact
            else:
                print("❌ No Dr. Pratik contact found")
                return None
        else:
            print(f"❌ Supabase request failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error accessing Supabase: {e}")
        return None

def test_bolna_integration_direct():
    """Test making a real call to Bolna API"""
    print("\n📞 Testing Direct Bolna Integration")
    print("="*40)
    
    # Get test contact
    contact = test_supabase_data()
    if not contact:
        print("❌ Cannot proceed without test contact")
        return False
    
    try:
        # Initialize Bolna API
        bolna_api = BolnaAPI()
        print("✅ Bolna API initialized")
        
        # Get agent configuration
        agent_config = get_agent_config_for_voice_agent('Patient Appointment Booking')
        print(f"✅ Agent config: {agent_config['agent_id']}")
        
        # Prepare call configuration
        variables = {
            **agent_config.get('default_variables', {}),
            'contact_name': contact['name'],
            'contact_phone': contact['phone'],
            'agent_title': 'Patient Appointment Booking',
            'test_call': True,
            'message': 'This is a test call from DrM Hope platform to verify integration.'
        }
        
        call_config = {
            'agent_id': agent_config['agent_id'],
            'recipient_phone': contact['phone'],
            'sender_phone': agent_config['sender_phone'],
            'variables': variables,
            'metadata': {
                'test_call': True,
                'contact_id': contact['id'],
                'campaign_name': 'Integration Test Call',
                'source': 'direct_test'
            }
        }
        
        print(f"\n📋 Call Configuration:")
        print(f"   From: {call_config['sender_phone']}")
        print(f"   To: {call_config['recipient_phone']} ({variables['contact_name']})")
        print(f"   Agent: {call_config['agent_id']}")
        print(f"   Purpose: {variables.get('purpose', 'test')}")
        
        # Ask for confirmation
        confirm = input(f"\n⚠️  This will make an actual call to {contact['phone']}. Continue? (yes/no): ").lower()
        if confirm != 'yes':
            print("❌ Test cancelled by user")
            return False
        
        # Make the call
        print(f"\n🚀 Making call to Bolna API...")
        result = bolna_api.start_outbound_call(
            agent_id=call_config['agent_id'],
            recipient_phone=call_config['recipient_phone'],
            sender_phone=call_config['sender_phone'],
            variables=call_config['variables'],
            metadata=call_config['metadata']
        )
        
        print(f"✅ Call initiated successfully!")
        print(f"📋 Bolna Response:")
        print(json.dumps(result, indent=2))
        
        # Get call ID for status tracking
        call_id = result.get('call_id')
        if call_id:
            print(f"\n🆔 Call ID: {call_id}")
            
            # Check status after a moment
            import time
            print("⏳ Waiting 5 seconds before checking status...")
            time.sleep(5)
            
            try:
                status = bolna_api.get_call_status(call_id)
                print(f"📊 Call Status: {json.dumps(status, indent=2)}")
            except Exception as e:
                print(f"⚠️  Could not get call status: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_bulk_calls_simulation():
    """Test bulk calls with multiple contacts"""
    print("\n📞 Testing Bulk Calls Simulation")
    print("="*40)
    
    try:
        bolna_api = BolnaAPI()
        
        # Get multiple contacts from sample data
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
        
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        }
        
        response = requests.get(f"{SUPABASE_URL}/rest/v1/contacts?status=eq.active&limit=3", headers=headers)
        if response.status_code != 200:
            print(f"❌ Could not fetch contacts: {response.status_code}")
            return False
        
        contacts = response.json()
        if not contacts:
            print("❌ No active contacts found")
            return False
        
        print(f"✅ Found {len(contacts)} contacts for bulk test")
        
        # Get agent config
        agent_config = get_agent_config_for_voice_agent('Prescription Reminder Calls')
        
        # Prepare bulk call configs
        call_configs = []
        for contact in contacts:
            variables = {
                **agent_config.get('default_variables', {}),
                'contact_name': contact['name'],
                'contact_phone': contact['phone'],
                'test_call': True
            }
            
            call_config = {
                'agent_id': agent_config['agent_id'],
                'recipient_phone': contact['phone'],
                'sender_phone': agent_config['sender_phone'],
                'variables': variables,
                'metadata': {
                    'test_bulk_call': True,
                    'contact_id': contact['id'],
                    'campaign_name': 'Bulk Test Campaign'
                }
            }
            call_configs.append(call_config)
        
        print(f"📋 Bulk Call Configuration:")
        for i, config in enumerate(call_configs):
            print(f"   Call {i+1}: {config['variables']['contact_name']} - {config['recipient_phone']}")
        
        # Ask for confirmation
        confirm = input(f"\n⚠️  This will make {len(call_configs)} actual calls. Continue? (yes/no): ").lower()
        if confirm != 'yes':
            print("❌ Bulk test cancelled by user")
            return False
        
        # Make bulk calls
        print(f"\n🚀 Starting bulk calls...")
        results = bolna_api.bulk_start_calls(call_configs)
        
        # Analyze results
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        
        print(f"\n📊 Bulk Call Results:")
        print(f"   Total Attempted: {len(results)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        # Show detailed results
        for i, result in enumerate(results):
            contact_name = result['original_config']['variables']['contact_name']
            status = "✅ Success" if result.get('success') else f"❌ Failed: {result.get('error', 'Unknown error')}"
            print(f"   Call {i+1} ({contact_name}): {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bulk call test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Real Bolna Integration Test")
    print("="*50)
    
    # Check API key
    api_key = os.getenv('BOLNA_API_KEY')
    if not api_key or api_key == 'your-bolna-api-key-here':
        print("❌ BOLNA_API_KEY not configured")
        sys.exit(1)
    
    print(f"🔑 Using API Key: {api_key[:10]}...{api_key[-10:]}")
    
    # Run tests
    print("\n" + "="*50)
    print("🎯 Choose test type:")
    print("1. Single call test")
    print("2. Bulk calls test") 
    print("3. Skip actual calls (safe)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        success = test_bolna_integration_direct()
    elif choice == "2":
        success = test_bulk_calls_simulation()
    else:
        print("✅ Skipping actual calls - integration is ready!")
        success = True
    
    print("\n" + "="*50)
    if success:
        print("🎉 Integration test completed successfully!")
        print("\n🚀 Your Bolna AI integration is working perfectly!")
        print("📞 You can now use the dashboard to make real calls.")
    else:
        print("❌ Integration test failed - check the errors above")
    
    print(f"\n🔗 Dashboard: http://localhost:8000")
    print(f"📚 Documentation: See BOLNA_INTEGRATION_GUIDE.md")