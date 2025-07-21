#!/usr/bin/env python3
"""
Direct ElevenLabs Phone Call to +919373111709
Uses ElevenLabs Phone Calling API directly
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ElevenLabs Configuration from your .env
ELEVENLABS_API_KEY = "sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c"
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
PHONE_NUMBER = "+919373111709"

def make_direct_elevenlabs_call():
    """Make a direct phone call using ElevenLabs API"""
    
    print(f"📞 Making direct ElevenLabs call to {PHONE_NUMBER}")
    
    # ElevenLabs Phone Call API endpoint
    url = "https://api.elevenlabs.io/v1/convai/conversations/phone"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Call payload with Indian phone number
    payload = {
        "phone_number": PHONE_NUMBER,
        "agent": {
            "prompt": {
                "prompt": """You are a friendly AI assistant from BhashAI, calling to demonstrate our voice AI technology. 
                
                Instructions:
                - Greet the person warmly in Hindi or English
                - Introduce yourself as an AI from BhashAI
                - Explain this is a demonstration of voice AI technology
                - Ask how they are doing today
                - Keep the conversation natural and brief (2-3 minutes)
                - Be respectful and end the call politely if requested
                - You can switch between Hindi and English based on user preference
                
                Sample greeting: "Namaste! Main BhashAI company ka AI assistant hun. Aaj main aapko hamare voice AI technology ka demonstration dene ke liye call kar raha hun. Aap kaise hain?"
                """
            },
            "first_message": "Namaste! This is an AI assistant from BhashAI. I'm calling to demonstrate our advanced voice AI technology. How are you today?",
            "language": "en",
            "voice": {
                "voice_id": ELEVENLABS_VOICE_ID,
                "stability": 0.85,
                "similarity_boost": 0.8,
                "style": 0.15,
                "use_speaker_boost": True
            }
        },
        "conversation_config": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 800
            },
            "agent_config": {
                "thinking_enabled": True,
                "interruption_threshold": 100,
                "responsiveness": 0.8,
                "llm_websocket_timeout_ms": 15000
            }
        },
        "analysis_config": {
            "summary_enabled": True,
            "transcript_enabled": True
        }
    }
    
    try:
        print("🚀 Initiating ElevenLabs phone call...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            call_data = response.json()
            conversation_id = call_data.get('conversation_id')
            
            print("✅ Call initiated successfully!")
            print(f"📋 Conversation ID: {conversation_id}")
            print(f"📱 Calling: {PHONE_NUMBER}")
            print(f"🎯 Status: {call_data.get('status', 'initiated')}")
            
            if conversation_id:
                monitor_call_progress(conversation_id)
            
            return True
            
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key")
            print("🔑 Please check your ElevenLabs API key")
            
        elif response.status_code == 402:
            print("❌ Payment required - Insufficient credits")
            print("💳 Please add credits to your ElevenLabs account")
            
        elif response.status_code == 422:
            print("❌ Invalid request parameters")
            print(f"📝 Response: {response.text}")
            
        else:
            print(f"❌ Call failed with status: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
        return False
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - ElevenLabs API might be slow")
        return False
        
    except Exception as e:
        print(f"❌ Error making call: {str(e)}")
        return False

def monitor_call_progress(conversation_id):
    """Monitor the progress of the phone call"""
    
    print(f"📊 Monitoring call progress: {conversation_id}")
    
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    for attempt in range(20):  # Monitor for up to 2 minutes
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                duration = data.get('duration_seconds', 0)
                
                print(f"📈 Status: {status} | Duration: {duration}s")
                
                if status in ['completed', 'ended', 'failed']:
                    print(f"🏁 Call finished: {status}")
                    
                    # Get call summary if available
                    if 'analysis' in data:
                        analysis = data['analysis']
                        if 'summary' in analysis:
                            print(f"📋 Summary: {analysis['summary']}")
                    
                    break
                    
            else:
                print(f"⚠️ Status check failed: {response.status_code}")
                
            time.sleep(6)  # Check every 6 seconds
            
        except Exception as e:
            print(f"⚠️ Error monitoring call: {str(e)}")
            break

def test_elevenlabs_connection():
    """Test ElevenLabs API connection"""
    
    print("🔍 Testing ElevenLabs API connection...")
    
    url = "https://api.elevenlabs.io/v1/user"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ API connection successful!")
            print(f"👤 User: {user_data.get('email', 'Unknown')}")
            print(f"💰 Credits: {user_data.get('subscription', {}).get('character_count', 'Unknown')}")
            return True
        else:
            print(f"❌ API connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def main():
    """Main execution function"""
    
    print("🎙️ ElevenLabs Direct Phone Call System")
    print("=" * 60)
    print(f"📞 Target: {PHONE_NUMBER}")
    print(f"🎵 Voice: {ELEVENLABS_VOICE_ID} (Rachel)")
    print(f"🔑 API Key: {ELEVENLABS_API_KEY[:20]}...")
    print("=" * 60)
    
    # Test API connection first
    if not test_elevenlabs_connection():
        print("❌ Cannot proceed - API connection failed")
        return
    
    # Make the call
    print("\n🚀 Starting phone call process...")
    success = make_direct_elevenlabs_call()
    
    if success:
        print("\n✅ Call process completed successfully!")
    else:
        print("\n❌ Call process failed!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify ElevenLabs API key is valid")
        print("   2. Check account has sufficient credits")
        print("   3. Ensure phone number format is correct")
        print("   4. Verify ElevenLabs Conversational AI is enabled")
    
    print("\n📝 Important Notes:")
    print("   - This uses ElevenLabs Conversational AI")
    print("   - Requires active ElevenLabs subscription")
    print("   - International calling rates may apply")
    print("   - Ensure compliance with local regulations")

if __name__ == "__main__":
    main()
