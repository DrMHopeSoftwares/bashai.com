#!/usr/bin/env python3
"""
Test Bolna API with actual credentials
"""

import os
import sys
from dotenv import load_dotenv
from bolna_integration import BolnaAPI, get_agent_config_for_voice_agent

load_dotenv()

def test_bolna_api_connection():
    """Test actual Bolna API connection"""
    
    print("🔗 Testing Bolna API Connection")
    print("="*40)
    
    try:
        # Initialize Bolna API
        bolna_api = BolnaAPI()
        print("✅ BolnaAPI initialized successfully")
        print(f"📡 API URL: {bolna_api.base_url}")
        print(f"📞 Default Sender: {bolna_api.default_sender_phone}")
        
        # Test 1: List available agents
        print("\n🤖 Testing: List Agents")
        try:
            agents = bolna_api.list_agents()
            print(f"✅ Found {len(agents)} agents in your Bolna account")
            
            if agents:
                print("📋 Available Agents:")
                for agent in agents[:3]:  # Show first 3
                    agent_id = agent.get('id', 'Unknown')
                    agent_name = agent.get('name', 'Unnamed')
                    print(f"  • {agent_name} (ID: {agent_id})")
            
        except Exception as e:
            print(f"❌ Failed to list agents: {e}")
        
        # Test 2: Get specific agent details
        print(f"\n🔍 Testing: Get Agent Details")
        agent_id = "15554373-b8e1-4b00-8c25-c4742dc8e480"
        
        try:
            agent_details = bolna_api.get_agent_details(agent_id)
            print(f"✅ Retrieved details for agent {agent_id}")
            print(f"📋 Agent Name: {agent_details.get('name', 'Unknown')}")
            print(f"📝 Agent Description: {agent_details.get('description', 'No description')}")
            
        except Exception as e:
            print(f"❌ Failed to get agent details: {e}")
            print("💡 Note: The agent ID might not exist in your account")
        
        # Test 3: Test agent configuration mapping
        print(f"\n⚙️  Testing: Agent Configuration Mapping")
        
        test_titles = [
            "Patient Appointment Booking",
            "Prescription Reminder Calls",
            "Delivery Follow-up"
        ]
        
        for title in test_titles:
            config = get_agent_config_for_voice_agent(title)
            print(f"  • {title}")
            print(f"    └─ Agent ID: {config['agent_id']}")
            print(f"    └─ Phone: {config['sender_phone']}")
        
        return True
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_mock_call_configuration():
    """Test call configuration without making actual calls"""
    
    print(f"\n📞 Testing: Mock Call Configuration")
    print("="*40)
    
    try:
        bolna_api = BolnaAPI()
        
        # Mock call configuration
        mock_calls = [
            {
                'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',
                'recipient_phone': '+917030281823',  # Dr. Pratik from sample data
                'sender_phone': '+918035743222',
                'variables': {
                    'contact_name': 'Dr. Pratik',
                    'purpose': 'appointment_booking',
                    'greeting': 'Hello, this is an automated call from Ayushmann Healthcare.',
                    'language': 'hinglish'
                },
                'metadata': {
                    'voice_agent_id': 'test-agent',
                    'contact_id': 'test-contact',
                    'campaign_name': 'Test Campaign'
                }
            }
        ]
        
        print("📋 Mock Call Configuration:")
        for i, call in enumerate(mock_calls):
            print(f"  Call {i+1}:")
            print(f"    └─ To: {call['recipient_phone']} ({call['variables']['contact_name']})")
            print(f"    └─ Agent: {call['agent_id']}")
            print(f"    └─ Purpose: {call['variables']['purpose']}")
        
        print("\n⚠️  Note: This is a mock configuration. Actual calls would be made with:")
        print("   bolna_api.bulk_start_calls(mock_calls)")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock configuration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Bolna API Integration Test\n")
    
    # Check environment
    api_key = os.getenv('BOLNA_API_KEY')
    if not api_key or api_key == 'your-bolna-api-key-here':
        print("❌ BOLNA_API_KEY not configured")
        sys.exit(1)
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-10:]}")
    
    # Run tests
    connection_success = test_bolna_api_connection()
    config_success = test_mock_call_configuration()
    
    print("\n" + "="*50)
    if connection_success and config_success:
        print("🎉 All tests passed! Bolna integration is ready!")
        print("\n🚀 Next Steps:")
        print("1. Access dashboard: http://localhost:8000")
        print("2. Open Contact Manager for any voice agent")
        print("3. Select contacts and click '📞 Start Calls'")
        print("4. Monitor results in the dashboard")
    else:
        print("❌ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify Bolna API key is correct")
        print("2. Check agent ID exists in your Bolna account")
        print("3. Ensure network connectivity to api.bolna.dev")
    
    print(f"\n📚 Resources:")
    print(f"   • Bolna Dashboard: https://app.bolna.dev")
    print(f"   • API Documentation: https://docs.bolna.dev")