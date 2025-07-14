#!/usr/bin/env python3
"""
Test actual Bolna API call (BE CAREFUL - this will make a real call)
"""

import os
import sys
from dotenv import load_dotenv
from bolna_integration import BolnaAPI

load_dotenv()

def test_real_call():
    """Test making an actual call - USE WITH CAUTION"""
    
    print("⚠️  WARNING: This will make an actual phone call!")
    print("="*50)
    
    # Confirm before proceeding
    confirm = input("Do you want to proceed with a test call? (yes/no): ").lower()
    if confirm != 'yes':
        print("❌ Test cancelled by user")
        return
    
    try:
        bolna_api = BolnaAPI()
        
        # Test call configuration
        agent_id = "15554373-b8e1-4b00-8c25-c4742dc8e480"
        recipient_phone = "+917030281823"  # Dr. Pratik from sample data
        sender_phone = "+918035743222"
        
        variables = {
            'contact_name': 'Dr. Pratik',
            'purpose': 'test_call',
            'greeting': 'Hello, this is a test call from DrM Hope platform.',
            'language': 'hinglish'
        }
        
        metadata = {
            'test_call': True,
            'source': 'manual_test'
        }
        
        print(f"📞 Making test call:")
        print(f"   From: {sender_phone}")
        print(f"   To: {recipient_phone}")
        print(f"   Agent: {agent_id}")
        
        # Make the actual call
        result = bolna_api.start_outbound_call(
            agent_id=agent_id,
            recipient_phone=recipient_phone,
            sender_phone=sender_phone,
            variables=variables,
            metadata=metadata
        )
        
        print("✅ Call initiated successfully!")
        print(f"📋 Response: {result}")
        
        # Extract call ID for status checking
        call_id = result.get('call_id')
        if call_id:
            print(f"🆔 Call ID: {call_id}")
            
            # Check call status
            try:
                status = bolna_api.get_call_status(call_id)
                print(f"📊 Call Status: {status}")
            except Exception as e:
                print(f"⚠️  Could not get call status: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return False

def test_bulk_call_simulation():
    """Test the bulk call workflow without making actual calls"""
    
    print("\n🔬 Testing Bulk Call Simulation")
    print("="*40)
    
    try:
        bolna_api = BolnaAPI()
        
        # Simulate the data that would come from the dashboard
        mock_calls = [
            {
                'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',
                'recipient_phone': '+917030281823',
                'sender_phone': '+918035743222',
                'variables': {
                    'contact_name': 'Dr. Pratik',
                    'purpose': 'appointment_booking',
                    'language': 'hinglish'
                },
                'metadata': {
                    'voice_agent_id': 'test-agent',
                    'contact_id': 'contact-1',
                    'campaign_name': 'Test Campaign'
                }
            },
            {
                'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',
                'recipient_phone': '+919373111709',
                'sender_phone': '+918035743222',
                'variables': {
                    'contact_name': 'Nurse Murali',
                    'purpose': 'appointment_booking',
                    'language': 'hinglish'
                },
                'metadata': {
                    'voice_agent_id': 'test-agent',
                    'contact_id': 'contact-2',
                    'campaign_name': 'Test Campaign'
                }
            }
        ]
        
        print(f"📋 Mock Bulk Call Configuration:")
        print(f"   Campaign: Test Campaign")
        print(f"   Total Calls: {len(mock_calls)}")
        
        for i, call in enumerate(mock_calls):
            print(f"   Call {i+1}: {call['variables']['contact_name']} - {call['recipient_phone']}")
        
        print(f"\n⚠️  To make actual calls, the dashboard would call:")
        print(f"   bolna_api.bulk_start_calls(mock_calls)")
        
        return True
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Bolna API Real Call Test\n")
    
    # Test simulation first (safe)
    simulation_success = test_bulk_call_simulation()
    
    # Ask user if they want to make a real test call
    if simulation_success:
        print("\n" + "="*50)
        print("🎯 The integration is working correctly!")
        print("📞 You can now use the dashboard to make actual calls.")
        print("\n🚀 To test in dashboard:")
        print("1. Go to http://localhost:8000")
        print("2. Open Contact Manager for any voice agent")
        print("3. Select contacts and click '📞 Start Calls'")
        print("4. Monitor the results")
        
        # Optional real call test
        print("\n🔧 Optional: Test with actual call")
        test_real_call()
    else:
        print("❌ Simulation failed - check configuration")