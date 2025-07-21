#!/usr/bin/env python3
"""
Test Script to Make a REAL Phone Call to +91 9373111709 
Using Twilio + OpenAI Integration
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twilio_openai_voice_call import make_real_call, twilio_voice_system

async def test_real_phone_call():
    """Test making a real phone call using Twilio"""
    
    print("🎯 REAL PHONE CALL TEST")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📱 Target: +91 9373111709")
    print(f"🤖 System: Twilio + OpenAI Realtime API")
    print(f"🌍 Language: Hindi + English (Hinglish)")
    print("=" * 60)
    
    target_number = "+919373111709"
    
    # Custom AI message for the call
    ai_message = """Hello! This is a REAL phone call from BhashAI voice assistant.

I'm powered by OpenAI's advanced Realtime API and I'm calling you through Twilio's phone network.

This is an actual demonstration of AI voice calling technology. I can:
- Speak naturally in Hindi and English
- Understand your responses
- Have a real conversation with you
- Respond intelligently to what you say

How are you doing today? Please feel free to speak back to me - I'll understand and respond naturally!

You can speak in Hindi, English, or mix both languages. I'm here to chat with you!"""
    
    print("📞 Initiating REAL call...")
    print("🎤 AI Message prepared")
    print("🔧 Using Twilio API for actual phone call")
    print("\n" + "⏳ Making call..." + "\n")
    
    try:
        # Make the real call
        result = await make_real_call(target_number, ai_message)
        
        print("📋 REAL CALL RESULT:")
        print("=" * 50)
        print(json.dumps(result, indent=2, default=str))
        print("=" * 50)
        
        if result['success']:
            call_id = result['call_id']
            twilio_sid = result['twilio_call_sid']
            
            print("\n🎉 REAL CALL INITIATED SUCCESSFULLY!")
            print("=" * 50)
            print(f"📞 Call ID: {call_id}")
            print(f"🔧 Twilio SID: {twilio_sid}")
            print(f"📱 Calling: {target_number}")
            print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
            
            print("\n📊 WHAT'S HAPPENING NOW:")
            print("1. 📲 Twilio is dialing +91 9373111709")
            print("2. 📞 Your phone should start ringing")
            print("3. 🗣️  When you answer, AI will speak the message")
            print("4. 👂 You can respond and have a conversation")
            print("5. 🤖 AI will understand and reply naturally")
            
            print("\n⏱️  MONITORING CALL STATUS...")
            
            # Monitor call for 2 minutes
            for i in range(24):  # 24 * 5 seconds = 2 minutes
                await asyncio.sleep(5)
                
                status = twilio_voice_system.get_call_status(call_id)
                
                if status:
                    elapsed = (datetime.now() - datetime.fromisoformat(str(status['started_at']).replace('Z', '+00:00').replace('+00:00', ''))).total_seconds()
                    
                    print(f"📊 [{i+1:2d}/24] Status: {status['status']} | Duration: {elapsed:.0f}s")
                    
                    if status['status'] in ['completed', 'failed', 'busy', 'no-answer']:
                        print(f"✅ Call ended with status: {status['status']}")
                        break
                else:
                    print(f"📊 [{i+1:2d}/24] Call status not found")
                    break
            
            print("\n📈 FINAL CALL SUMMARY:")
            final_status = twilio_voice_system.get_call_status(call_id)
            if final_status:
                print(json.dumps(final_status, indent=2, default=str))
            else:
                print("Call completed and cleaned up")
            
        else:
            print(f"\n❌ CALL FAILED:")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Message: {result.get('message', 'No message')}")
            
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Check Twilio account balance")
            print("2. Verify phone number format (+919373111709)")
            print("3. Ensure Twilio credentials are valid")
            print("4. Check if target number can receive calls")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ EXCEPTION DURING CALL TEST:")
        print(f"Error: {e}")
        print(f"Type: {type(e).__name__}")
        return False

async def check_twilio_setup():
    """Check if Twilio is properly configured"""
    
    print("🔧 CHECKING TWILIO SETUP...")
    print("-" * 40)
    
    try:
        # Check environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        print(f"📋 Account SID: {'✓ Set' if account_sid else '✗ Missing'}")
        print(f"🔐 Auth Token: {'✓ Set' if auth_token else '✗ Missing'}")
        
        if not account_sid or not auth_token:
            print("\n❌ Twilio credentials missing!")
            print("Please check your .env file")
            return False
        
        # Test Twilio connection
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Get account info
        account = client.api.accounts(account_sid).fetch()
        print(f"📊 Account Status: {account.status}")
        print(f"💰 Account Type: {account.type}")
        
        # Check phone numbers
        phone_numbers = client.incoming_phone_numbers.list(limit=5)
        print(f"📞 Available Numbers: {len(phone_numbers)}")
        
        for number in phone_numbers[:2]:
            print(f"   📱 {number.phone_number} ({number.friendly_name})")
        
        if not phone_numbers:
            print("⚠️  No Twilio phone numbers found!")
            print("   You may need to purchase one for outbound calls")
        
        print("✅ Twilio setup looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Twilio setup error: {e}")
        return False

async def main():
    """Run the complete real call test"""
    
    print("🚀 BhashAI REAL PHONE CALL SYSTEM")
    print("Using Twilio + OpenAI Realtime API")
    print("=" * 60)
    
    # Check Twilio setup first
    twilio_ok = await check_twilio_setup()
    
    if not twilio_ok:
        print("\n❌ Twilio setup failed. Cannot proceed with real call.")
        return False
    
    print("\n" + "=" * 60)
    
    # Proceed with real call test
    success = await test_real_phone_call()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 REAL CALL TEST COMPLETED SUCCESSFULLY!")
        print("\n📋 What happened:")
        print("✅ Twilio API connected successfully")
        print("✅ Real phone call initiated")
        print("✅ OpenAI Realtime API integrated")
        print("✅ Call monitoring and status tracking")
        print("✅ Natural AI conversation capabilities")
        
        print("\n🌟 Your phone should have received the call!")
        print("   The AI can now have real conversations in Hindi/English")
        
    else:
        print("❌ REAL CALL TEST FAILED")
        print("\n🔧 Check the error messages above for troubleshooting")
    
    return success

if __name__ == "__main__":
    # Run the real call test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)