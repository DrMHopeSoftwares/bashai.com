#!/usr/bin/env python3
"""
Twilio + ElevenLabs Phone Call to +919373111709
Uses Twilio for calling and ElevenLabs for voice synthesis
"""

import os
import requests
import json
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from your .env file
TWILIO_ACCOUNT_SID = "ACb4f43ae70f647972a12b7c27ef1c0c0f"
TWILIO_AUTH_TOKEN = "b2aded6b5f18ee02da593f9a7019a153"
TWILIO_PHONE_NUMBER = "+19896621396"
ELEVENLABS_API_KEY = "sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c"
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Target phone number
TARGET_PHONE = "+919373111709"

def generate_elevenlabs_audio():
    """Generate audio using ElevenLabs for the call"""
    
    print("🎵 Generating ElevenLabs audio...")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    # Message in Hindi and English
    message = """
    Namaste! Main BhashAI company ka AI assistant hun. 
    
    Hello! I am an AI assistant from BhashAI. This is a demonstration of our voice AI technology.
    
    Aaj main aapko hamare advanced voice AI capabilities ka demonstration de raha hun. 
    
    We can create natural-sounding voices in multiple languages including Hindi and English.
    
    Kya aap hamare AI voice services ke baare mein aur jaanna chahenge?
    
    Thank you for your time. Have a great day! Dhanyawad!
    """
    
    data = {
        "text": message,
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
            # Save audio file
            audio_filename = "bhashai_demo_call.mp3"
            with open(audio_filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Audio generated: {audio_filename}")
            return audio_filename
        else:
            print(f"❌ Audio generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating audio: {str(e)}")
        return None

def make_twilio_call():
    """Make phone call using Twilio"""
    
    print(f"📞 Making Twilio call to {TARGET_PHONE}...")
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Create TwiML for the call
        twiml_url = create_twiml_response()
        
        if not twiml_url:
            print("❌ Failed to create TwiML response")
            return False
        
        # Make the call
        call = client.calls.create(
            twiml=f'<Response><Say voice="alice" language="hi-IN">Namaste! Main BhashAI company ka AI assistant hun. Aaj main aapko hamare voice AI technology ka demonstration de raha hun. Aap kaise hain? We are demonstrating our advanced AI voice capabilities. Thank you for your time!</Say></Response>',
            to=TARGET_PHONE,
            from_=TWILIO_PHONE_NUMBER
        )
        
        print(f"✅ Call initiated successfully!")
        print(f"📋 Call SID: {call.sid}")
        print(f"📱 From: {TWILIO_PHONE_NUMBER}")
        print(f"📱 To: {TARGET_PHONE}")
        print(f"🎯 Status: {call.status}")
        
        # Monitor call status
        monitor_twilio_call(client, call.sid)
        
        return True
        
    except Exception as e:
        print(f"❌ Error making Twilio call: {str(e)}")
        return False

def create_twiml_response():
    """Create TwiML response for the call"""
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice" language="hi-IN">
            Namaste! Main BhashAI company ka AI assistant hun.
        </Say>
        <Say voice="alice" language="en-IN">
            Hello! I am an AI assistant from BhashAI. This is a demonstration of our voice AI technology.
        </Say>
        <Say voice="alice" language="hi-IN">
            Aaj main aapko hamare advanced voice AI capabilities ka demonstration de raha hun.
        </Say>
        <Say voice="alice" language="en-IN">
            We can create natural-sounding voices in multiple languages including Hindi and English.
        </Say>
        <Say voice="alice" language="hi-IN">
            Kya aap hamare AI voice services ke baare mein aur jaanna chahenge?
        </Say>
        <Say voice="alice" language="en-IN">
            Thank you for your time. Have a great day!
        </Say>
        <Say voice="alice" language="hi-IN">
            Dhanyawad!
        </Say>
    </Response>'''
    
    return twiml

def monitor_twilio_call(client, call_sid):
    """Monitor the Twilio call status"""
    
    print(f"📊 Monitoring call: {call_sid}")
    
    import time
    
    for i in range(20):  # Monitor for up to 2 minutes
        try:
            call = client.calls(call_sid).fetch()
            
            print(f"📈 Status: {call.status} | Duration: {call.duration or 0}s")
            
            if call.status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                print(f"🏁 Call ended: {call.status}")
                if call.duration:
                    print(f"⏱️ Total duration: {call.duration} seconds")
                break
                
            time.sleep(6)  # Check every 6 seconds
            
        except Exception as e:
            print(f"⚠️ Error monitoring call: {str(e)}")
            break

def test_twilio_connection():
    """Test Twilio connection"""
    
    print("🔍 Testing Twilio connection...")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        
        print("✅ Twilio connection successful!")
        print(f"📱 Account: {account.friendly_name}")
        print(f"💰 Status: {account.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Twilio connection failed: {str(e)}")
        return False

def main():
    """Main execution function"""
    
    print("📞 Twilio + ElevenLabs Call to +919373111709")
    print("=" * 60)
    print(f"📱 From: {TWILIO_PHONE_NUMBER}")
    print(f"📱 To: {TARGET_PHONE}")
    print(f"🎵 Voice: ElevenLabs Rachel")
    print("=" * 60)
    
    # Test connections
    if not test_twilio_connection():
        print("❌ Cannot proceed - Twilio connection failed")
        return
    
    # Generate ElevenLabs audio (optional)
    print("\n🎵 Preparing voice content...")
    audio_file = generate_elevenlabs_audio()
    
    # Make the call
    print("\n📞 Initiating phone call...")
    success = make_twilio_call()
    
    if success:
        print("\n✅ Call process completed!")
        print("📝 The call has been initiated to +919373111709")
        print("🎙️ Using Twilio's built-in Hindi voice synthesis")
    else:
        print("\n❌ Call failed!")
    
    print("\n📋 Call Details:")
    print(f"   - Target: {TARGET_PHONE}")
    print(f"   - From: {TWILIO_PHONE_NUMBER}")
    print(f"   - Message: BhashAI AI voice demo in Hindi & English")
    print(f"   - Duration: ~30-45 seconds")
    
    # Cleanup
    if audio_file and os.path.exists(audio_file):
        os.remove(audio_file)
        print(f"🧹 Cleaned up: {audio_file}")

if __name__ == "__main__":
    main()
