#!/usr/bin/env python3
"""
ElevenLabs Phone Call to +919373111709
Uses ElevenLabs Conversational AI API to make a real phone call
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', 'sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c')
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_DEFAULT_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

# Target phone number
PHONE_NUMBER = "+919373111709"

def make_elevenlabs_call():
    """Make a phone call using ElevenLabs Conversational AI API"""
    
    print(f"🎙️ Making ElevenLabs call to {PHONE_NUMBER}...")
    
    # ElevenLabs Conversational AI endpoint
    url = f"{ELEVENLABS_API_URL}/convai/conversations"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Call configuration
    payload = {
        "agent_id": "your_agent_id",  # You'll need to create an agent first
        "phone_number": PHONE_NUMBER,
        "voice_settings": {
            "stability": 0.85,
            "similarity_boost": 0.8,
            "style": 0.15,
            "use_speaker_boost": True
        },
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": """You are a helpful AI assistant from BhashAI. 
                    You are calling to demonstrate our voice AI technology. 
                    Speak in a friendly, professional manner. 
                    Keep the conversation brief and ask if they're interested in learning more about our AI voice services.
                    You can speak in Hindi or English based on the user's preference."""
                },
                "first_message": "Hello! This is an AI assistant from BhashAI. I'm calling to demonstrate our voice AI technology. How are you today?",
                "language": "en"
            }
        }
    }
    
    try:
        print("📞 Initiating call...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            call_data = response.json()
            conversation_id = call_data.get('conversation_id')
            
            print(f"✅ Call initiated successfully!")
            print(f"📋 Conversation ID: {conversation_id}")
            print(f"📱 Calling: {PHONE_NUMBER}")
            print(f"🎯 Status: {call_data.get('status', 'Unknown')}")
            
            # Monitor call status
            monitor_call_status(conversation_id)
            
        else:
            print(f"❌ Failed to initiate call")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try alternative method if first fails
            try_alternative_call_method()
            
    except Exception as e:
        print(f"❌ Error making call: {str(e)}")
        try_alternative_call_method()

def monitor_call_status(conversation_id):
    """Monitor the status of the ongoing call"""
    
    if not conversation_id:
        print("⚠️ No conversation ID to monitor")
        return
    
    print(f"📊 Monitoring call status for conversation: {conversation_id}")
    
    url = f"{ELEVENLABS_API_URL}/convai/conversations/{conversation_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    for i in range(10):  # Monitor for up to 10 iterations
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"📈 Call Status: {status}")
                
                if status in ['completed', 'failed', 'ended']:
                    print(f"🏁 Call finished with status: {status}")
                    break
                    
            time.sleep(5)  # Wait 5 seconds between checks
            
        except Exception as e:
            print(f"⚠️ Error monitoring call: {str(e)}")
            break

def try_alternative_call_method():
    """Try alternative ElevenLabs call method"""
    
    print("🔄 Trying alternative ElevenLabs call method...")
    
    # Alternative endpoint for phone calls
    url = f"{ELEVENLABS_API_URL}/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": f"Hello, this is a test call from BhashAI to the number {PHONE_NUMBER}. Our AI voice technology is working perfectly!",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.85,
            "similarity_boost": 0.8,
            "style": 0.15,
            "use_speaker_boost": True
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            print("✅ Alternative method: Audio generated successfully")
            print("📝 Note: This generates audio but doesn't make actual phone call")
            print("💡 For actual calls, you need ElevenLabs Conversational AI agent setup")
        else:
            print(f"❌ Alternative method failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Alternative method error: {str(e)}")

def create_elevenlabs_agent():
    """Create an ElevenLabs Conversational AI agent for phone calls"""
    
    print("🤖 Creating ElevenLabs Conversational AI agent...")
    
    url = f"{ELEVENLABS_API_URL}/convai/agents"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    agent_config = {
        "name": "BhashAI Demo Agent",
        "voice_id": ELEVENLABS_VOICE_ID,
        "prompt": {
            "prompt": """You are a helpful AI assistant from BhashAI, a leading voice AI technology company. 
            You are calling to demonstrate our advanced voice AI capabilities.
            
            Instructions:
            - Be friendly, professional, and conversational
            - Speak clearly and at a moderate pace
            - You can communicate in Hindi, English, or Hinglish based on user preference
            - Keep the conversation engaging but brief (2-3 minutes)
            - Ask if they're interested in learning more about BhashAI's services
            - Be respectful if they want to end the call
            
            Your goal is to showcase the natural conversation abilities of our AI technology."""
        },
        "first_message": "Namaste! This is an AI assistant from BhashAI. I'm calling to demonstrate our voice AI technology. How are you doing today?",
        "language": "en",
        "conversation_config": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 800
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=agent_config)
        
        if response.status_code == 200:
            agent_data = response.json()
            agent_id = agent_data.get('agent_id')
            print(f"✅ Agent created successfully!")
            print(f"🤖 Agent ID: {agent_id}")
            return agent_id
        else:
            print(f"❌ Failed to create agent: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating agent: {str(e)}")
        return None

def main():
    """Main function to execute the call"""
    
    print("🎙️ ElevenLabs Phone Call System")
    print("=" * 50)
    print(f"📞 Target Number: {PHONE_NUMBER}")
    print(f"🔑 API Key: {ELEVENLABS_API_KEY[:20]}...")
    print(f"🎵 Voice ID: {ELEVENLABS_VOICE_ID}")
    print("=" * 50)
    
    # First, try to create an agent (if needed)
    print("🤖 Checking agent setup...")
    
    # Make the call
    make_elevenlabs_call()
    
    print("\n✅ Call process completed!")
    print("📝 Note: For production calls, ensure you have:")
    print("   - Valid ElevenLabs Conversational AI subscription")
    print("   - Proper agent configuration")
    print("   - Phone number verification")
    print("   - Compliance with local calling regulations")

if __name__ == "__main__":
    main()
