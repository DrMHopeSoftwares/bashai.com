#!/usr/bin/env python3
"""
Production Script to Make Real ElevenLabs Call to +919373111709
This script uses the actual ElevenLabs API key to make a real phone call
"""

import os
import json
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from elevenlabs_integration import ElevenLabsAgentManager

def test_real_elevenlabs_api():
    """Test ElevenLabs API with real credentials"""
    print("🎙️ Testing Real ElevenLabs API")
    print("=" * 50)
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        return False
    
    if api_key == 'your_elevenlabs_api_key':
        print("❌ Please update ELEVENLABS_API_KEY in .env file")
        return False
    
    print(f"✅ API Key configured: {api_key[:20]}...")
    
    # Test API connection
    try:
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Test voices endpoint
        response = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)
        if response.status_code == 200:
            voices = response.json()
            print(f"✅ API Connection successful - Found {len(voices.get('voices', []))} voices")
            
            # Show available voices
            print("\n🎙️ Available Voices:")
            for voice in voices.get('voices', [])[:5]:  # Show first 5
                print(f"  • {voice['name']} ({voice['voice_id'][:8]}...): {voice.get('description', 'No description')}")
            
            return True
        else:
            print(f"❌ API Connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Test error: {e}")
        return False

def create_production_agent():
    """Create a production ElevenLabs agent for the call"""
    print("\n🤖 Creating Production ElevenLabs Agent")
    print("=" * 50)
    
    try:
        manager = ElevenLabsAgentManager()
        
        # Production agent configuration
        agent_config = {
            'name': 'BhashAI Production Call Agent',
            'description': 'Production AI agent for calling +919373111709',
            'language': 'hinglish',
            'use_case': 'phone_support',
            'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - professional female voice
            'voice_settings': {
                'stability': 0.85,  # Higher stability for production
                'similarity_boost': 0.8,
                'style': 0.15,  # Slightly more expressive
                'use_speaker_boost': True
            },
            'system_prompt': '''You are a professional AI assistant from BhashAI calling +919373111709. 
            
            Instructions:
            1. Greet warmly in Hindi/English mix (Hinglish)
            2. Introduce yourself as an AI assistant from BhashAI
            3. Explain this is a test call to demonstrate our AI voice technology
            4. Ask if they can hear you clearly
            5. Be professional, friendly, and helpful
            6. Keep the conversation natural and engaging
            7. If they have questions about BhashAI, provide helpful information
            8. Thank them for their time before ending the call
            
            Remember: Be respectful of their time and maintain a professional tone throughout.''',
            'webhook_url': 'https://api.bhashai.com/webhook/elevenlabs/production',
            'post_call_webhook': 'https://api.bhashai.com/webhook/elevenlabs/post-call',
            'conversation_summaries': True,
            'call_recording': False  # Respect privacy
        }
        
        print("Creating agent with production configuration...")
        agent_result = manager.create_voice_agent(agent_config)
        
        if agent_result['success']:
            print("✅ Production agent created successfully!")
            print(f"🤖 Agent ID: {agent_result['external_agent_id']}")
            print(f"🎙️ Voice: Rachel (Professional Female)")
            print(f"🌍 Language: Hinglish")
            print(f"📞 Phone Integration: Enabled")
            return agent_result
        else:
            print(f"❌ Agent creation failed: {agent_result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return None

def make_production_call():
    """Make the actual production call to +919373111709"""
    print("\n📞 Making Production Call to +919373111709")
    print("=" * 50)
    
    # Create agent first
    agent_result = create_production_agent()
    if not agent_result:
        return False
    
    agent_id = agent_result['external_agent_id']
    
    try:
        # Prepare call data
        call_data = {
            'phone_number': '+919373111709',
            'call_id': f'production-call-{int(datetime.now().timestamp())}',
            'initial_message': '''नमस्ते! मैं BhashAI से एक AI असिस्टेंट हूं। 
            यह हमारी AI voice technology का demonstration है। 
            क्या आप मुझे साफ सुन सकते हैं?''',
            'language': 'hi',
            'voice_id': '21m00Tcm4TlvDq8ikWAM',
            'voice_settings': {
                'stability': 0.85,
                'similarity_boost': 0.8,
                'style': 0.15,
                'use_speaker_boost': True
            },
            'production_mode': True,
            'call_type': 'demonstration'
        }
        
        # Initialize the call
        manager = ElevenLabsAgentManager()
        call_result = manager.handle_voice_call(agent_id, call_data)
        
        print("📞 Call Details:")
        print(f"  Phone Number: {call_data['phone_number']}")
        print(f"  Call ID: {call_data['call_id']}")
        print(f"  Agent ID: {agent_id}")
        print(f"  Session ID: {call_result.get('session_id')}")
        print(f"  Status: {call_result.get('status')}")
        
        if call_result.get('mock'):
            print("\n⚠️  IMPORTANT: Currently running in mock mode")
            print("   To make real calls, ensure:")
            print("   1. ElevenLabs API key is valid")
            print("   2. Phone provider (Twilio) is configured")
            print("   3. Webhook URLs are accessible")
            print("   4. Account has sufficient credits")
        else:
            print("\n✅ Real call initiated successfully!")
            print("📱 The call should now be connecting to +919373111709")
        
        # Log the call attempt
        call_log = {
            'timestamp': datetime.now().isoformat(),
            'phone_number': call_data['phone_number'],
            'call_id': call_data['call_id'],
            'agent_id': agent_id,
            'session_id': call_result.get('session_id'),
            'status': call_result.get('status'),
            'voice_used': 'Rachel (21m00Tcm4TlvDq8ikWAM)',
            'language': 'Hinglish',
            'initial_message': call_data['initial_message'],
            'production_mode': True,
            'mock_mode': call_result.get('mock', False)
        }
        
        print(f"\n📊 Call Log:")
        print(json.dumps(call_log, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Call error: {e}")
        return False

def show_production_setup():
    """Show the production setup details"""
    print("\n⚙️ Production Setup Details")
    print("=" * 50)
    
    # Check environment variables
    elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    print("🔑 Credentials Status:")
    print(f"  ElevenLabs API Key: {'✅ Configured' if elevenlabs_key and elevenlabs_key != 'your_elevenlabs_api_key' else '❌ Not configured'}")
    print(f"  Twilio Account SID: {'✅ Configured' if twilio_sid and twilio_sid != 'your_twilio_account_sid' else '❌ Not configured'}")
    print(f"  Twilio Auth Token: {'✅ Configured' if twilio_token and twilio_token != 'your_twilio_auth_token' else '❌ Not configured'}")
    
    print(f"\n📞 Target Phone Number: +919373111709")
    print(f"🎙️ Voice: Rachel (Professional Female)")
    print(f"🌍 Language: Hinglish (Hindi + English)")
    print(f"🤖 Provider: ElevenLabs Conversational AI")
    
    print(f"\n💬 Initial Message:")
    print(f"  'नमस्ते! मैं BhashAI से एक AI असिस्टेंट हूं।'")
    print(f"  'यह हमारी AI voice technology का demonstration है।'")
    print(f"  'क्या आप मुझे साफ सुन सकते हैं?'")
    
    print(f"\n🔧 Technical Details:")
    print(f"  API Endpoint: https://api.elevenlabs.io/v1")
    print(f"  Voice Model: eleven_multilingual_v2")
    print(f"  Voice Settings: High stability, professional tone")
    print(f"  Webhook Support: Enabled")
    print(f"  Call Recording: Disabled (privacy)")

def main():
    """Main function to execute the production call"""
    print("🎙️ BhashAI Production Call to +919373111709")
    print("Using ElevenLabs AI Voice Technology")
    print("=" * 60)
    
    # Show setup
    show_production_setup()
    
    # Test API connection
    if not test_real_elevenlabs_api():
        print("\n❌ API test failed. Cannot proceed with production call.")
        return
    
    # Confirm before making the call
    print(f"\n⚠️  IMPORTANT: This will attempt to make a real phone call to +919373111709")
    print(f"   Make sure you have permission to call this number.")
    
    confirm = input("\n🤔 Do you want to proceed with the call? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        print(f"\n🚀 Proceeding with production call...")
        success = make_production_call()
        
        if success:
            print(f"\n🎉 Call process completed successfully!")
            print(f"📞 Check the phone +919373111709 for the incoming call")
            print(f"🎙️ The AI assistant should introduce itself and demonstrate the technology")
        else:
            print(f"\n❌ Call process failed. Check the logs above for details.")
    else:
        print(f"\n✋ Call cancelled by user.")
        print(f"💡 You can run this script again when ready to make the call.")

if __name__ == "__main__":
    main()
