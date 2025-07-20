#!/usr/bin/env python3
# Quick Production Test - Auto-generated
import os
from dotenv import load_dotenv
load_dotenv()

def quick_test():
    print("🧪 Quick Production Test")
    print("=" * 30)
    
    # Test environment variables
    elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
    
    print(f"ElevenLabs API Key: {'✅ Set' if elevenlabs_key else '❌ Missing'}")
    print(f"Twilio Account SID: {'✅ Set' if twilio_sid else '❌ Missing'}")
    
    if elevenlabs_key and twilio_sid:
        print("\n🎉 Ready to make production calls!")
        print("Run: python3 make_real_elevenlabs_call.py")
    else:
        print("\n⚠️  Missing credentials. Check .env file.")

if __name__ == "__main__":
    quick_test()
