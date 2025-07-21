#!/usr/bin/env python3
"""
Correct ElevenLabs Phone Call to +919373111709
Uses the proper ElevenLabs Conversational AI API endpoints
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ElevenLabs Configuration
ELEVENLABS_API_KEY = "sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c"
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
PHONE_NUMBER = "+919373111709"

def create_conversational_agent():
    """Create a conversational AI agent for phone calls"""
    
    print("🤖 Creating ElevenLabs Conversational AI agent...")
    
    url = "https://api.elevenlabs.io/v1/convai/agents"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    agent_config = {
        "name": "BhashAI Demo Agent",
        "prompt": {
            "prompt": """You are a friendly AI assistant from BhashAI, a leading voice AI technology company in India. 
            
            You are calling to demonstrate our advanced voice AI capabilities. 
            
            Instructions:
            - Greet warmly in Hindi: "Namaste! Main BhashAI company ka AI assistant hun."
            - Explain you're demonstrating voice AI technology
            - Ask how they are doing today
            - Keep conversation natural and engaging (2-3 minutes)
            - You can speak in Hindi, English, or mix both (Hinglish)
            - Be respectful and polite throughout
            - If they want to end the call, do so gracefully
            
            Your goal is to showcase natural conversation abilities and represent BhashAI professionally."""
        },
        "first_message": "Namaste! Main BhashAI company ka AI assistant hun. Aaj main aapko hamare voice AI technology ka demonstration dene ke liye call kar raha hun. Aap kaise hain?",
        "voice": {
            "voice_id": ELEVENLABS_VOICE_ID,
            "stability": 0.85,
            "similarity_boost": 0.8,
            "style": 0.15,
            "use_speaker_boost": True
        },
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
        response = requests.post(url, headers=headers, json=agent_config, timeout=30)
        
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

def make_phone_call_with_agent(agent_id):
    """Make phone call using the created agent"""
    
    if not agent_id:
        print("❌ No agent ID available for call")
        return False
    
    print(f"📞 Making call with agent {agent_id} to {PHONE_NUMBER}")
    
    url = "https://api.elevenlabs.io/v1/convai/conversations"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    call_payload = {
        "agent_id": agent_id,
        "phone_number": PHONE_NUMBER
    }
    
    try:
        response = requests.post(url, headers=headers, json=call_payload, timeout=30)
        
        if response.status_code == 200:
            call_data = response.json()
            conversation_id = call_data.get('conversation_id')
            
            print("✅ Call initiated successfully!")
            print(f"📋 Conversation ID: {conversation_id}")
            print(f"📱 Calling: {PHONE_NUMBER}")
            
            if conversation_id:
                monitor_call_status(conversation_id)
            
            return True
            
        else:
            print(f"❌ Call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error making call: {str(e)}")
        return False

def monitor_call_status(conversation_id):
    """Monitor call status and progress"""
    
    print(f"📊 Monitoring call: {conversation_id}")
    
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    for i in range(30):  # Monitor for up to 3 minutes
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                duration = data.get('duration_seconds', 0)
                
                print(f"📈 Status: {status} | Duration: {duration}s")
                
                if status in ['completed', 'ended', 'failed', 'cancelled']:
                    print(f"🏁 Call ended: {status}")
                    
                    # Show call summary if available
                    if 'analysis' in data:
                        analysis = data['analysis']
                        if 'summary' in analysis:
                            print(f"📋 Call Summary: {analysis['summary']}")
                    
                    break
                    
            time.sleep(6)  # Check every 6 seconds
            
        except Exception as e:
            print(f"⚠️ Monitoring error: {str(e)}")
            break

def try_simple_elevenlabs_call():
    """Try a simpler approach using ElevenLabs phone API"""
    
    print("🔄 Trying simplified ElevenLabs call approach...")
    
    # Check available voices first
    voices_url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        voices_response = requests.get(voices_url, headers=headers)
        if voices_response.status_code == 200:
            voices = voices_response.json()
            print(f"✅ Found {len(voices.get('voices', []))} available voices")
        
        # Try direct conversation creation
        conv_url = "https://api.elevenlabs.io/v1/convai/conversations"
        
        simple_payload = {
            "phone_number": PHONE_NUMBER,
            "agent": {
                "prompt": {
                    "prompt": "You are calling from BhashAI to demonstrate voice AI. Greet in Hindi and keep it brief."
                },
                "first_message": "Namaste! This is BhashAI AI assistant calling for a demo. How are you?",
                "voice": {
                    "voice_id": ELEVENLABS_VOICE_ID
                },
                "language": "en"
            }
        }
        
        response = requests.post(conv_url, headers=headers, json=simple_payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ Simple call method successful!")
            call_data = response.json()
            conversation_id = call_data.get('conversation_id')
            if conversation_id:
                monitor_call_status(conversation_id)
            return True
        else:
            print(f"❌ Simple call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple call error: {str(e)}")
        return False

def main():
    """Main execution function"""
    
    print("🎙️ ElevenLabs Phone Call to +919373111709")
    print("=" * 60)
    print(f"📞 Target: {PHONE_NUMBER}")
    print(f"🎵 Voice: Rachel ({ELEVENLABS_VOICE_ID})")
    print(f"🔑 API Key: {ELEVENLABS_API_KEY[:20]}...")
    print("=" * 60)
    
    # Method 1: Try simple direct call
    print("\n🚀 Method 1: Direct conversation call...")
    if try_simple_elevenlabs_call():
        print("✅ Call completed successfully!")
        return
    
    # Method 2: Create agent then call
    print("\n🚀 Method 2: Agent-based call...")
    agent_id = create_conversational_agent()
    
    if agent_id:
        if make_phone_call_with_agent(agent_id):
            print("✅ Agent-based call completed!")
            return
    
    print("\n❌ All call methods failed!")
    print("\n💡 Possible issues:")
    print("   1. ElevenLabs Conversational AI not enabled on account")
    print("   2. Insufficient credits for international calls")
    print("   3. Phone number format or region restrictions")
    print("   4. API endpoint changes or service unavailable")
    
    print("\n📞 Alternative: Try ElevenLabs dashboard for manual call setup")

if __name__ == "__main__":
    main()
