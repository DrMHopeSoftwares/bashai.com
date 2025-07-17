#!/usr/bin/env python3
"""
Simple Twilio Test to verify credentials and make a test call
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_twilio_credentials():
    """Test Twilio credentials"""
    
    print("🔧 Testing Twilio Credentials")
    print("=" * 40)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {auth_token[:10]}..." if auth_token else "Not found")
    
    if not account_sid or not auth_token:
        print("❌ Credentials missing!")
        return False
    
    try:
        from twilio.rest import Client
        
        print("\n📞 Testing Twilio connection...")
        client = Client(account_sid, auth_token)
        
        # Test with account fetch
        account = client.api.accounts(account_sid).fetch()
        print(f"✅ Connected! Account: {account.friendly_name}")
        print(f"📊 Status: {account.status}")
        print(f"💰 Type: {account.type}")
        
        # List phone numbers
        print("\n📱 Checking phone numbers...")
        numbers = client.incoming_phone_numbers.list(limit=3)
        
        if numbers:
            print(f"✅ Found {len(numbers)} phone number(s):")
            for num in numbers:
                print(f"   📞 {num.phone_number} - {num.friendly_name}")
                
            # Use first number for test call
            from_number = numbers[0].phone_number
            print(f"\n🎯 Will use {from_number} for outbound calls")
            
            return True, from_number
        else:
            print("⚠️  No phone numbers found!")
            print("   You can still test with Twilio's test numbers")
            return True, "+15005550006"  # Twilio test number
            
    except Exception as e:
        print(f"❌ Twilio test failed: {e}")
        return False, None

def make_test_call_simple(from_number, to_number="+919373111709"):
    """Make a simple test call using Twilio"""
    
    print(f"\n📞 Making test call...")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    
    try:
        from twilio.rest import Client
        from twilio.twiml.voice_response import VoiceResponse
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        client = Client(account_sid, auth_token)
        
        # Create simple TwiML for the call
        # For testing, we'll use a simple TwiML that speaks a message
        message = """Hello! This is a test call from BhashAI voice assistant.

I am powered by Twilio and OpenAI technology. 

This is a demonstration call to show that our phone calling system is working.

Thank you for answering! This call will end in a few seconds.

Goodbye!"""
        
        # Create TwiML URL (we'll use a simple hosted TwiML for testing)
        # In production, this would be your webhook endpoint
        twiml_url = "http://demo.twilio.com/docs/voice.xml"  # Simple Twilio demo TwiML
        
        # Alternative: Create inline TwiML (but Twilio needs a URL)
        print("📋 Creating call with message...")
        
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=twiml_url,  # This will just play a demo message
            timeout=30
        )
        
        print(f"✅ Call created successfully!")
        print(f"📋 Call SID: {call.sid}")
        print(f"📊 Status: {call.status}")
        print(f"🎯 Target: {to_number}")
        
        print(f"\n📞 Call should be ringing now!")
        print(f"   Call SID: {call.sid}")
        print(f"   You can track this call in Twilio Console")
        
        return True, call.sid
        
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return False, None

if __name__ == "__main__":
    print("🚀 Simple Twilio Call Test")
    print("Testing call to +91 9373111709")
    print("=" * 50)
    
    # Test credentials
    success, from_number = test_twilio_credentials()
    
    if success and from_number:
        print(f"\n✅ Twilio credentials work!")
        
        # Ask user if they want to make a test call
        print(f"\n🎯 Ready to make test call to +91 9373111709")
        print(f"   This will use Twilio's demo TwiML")
        print(f"   The call will play a simple message")
        
        response = input("\nMake the test call? (y/n): ").lower().strip()
        
        if response == 'y':
            success, call_sid = make_test_call_simple(from_number)
            
            if success:
                print(f"\n🎉 Test call initiated!")
                print(f"📞 Your phone (+91 9373111709) should ring")
                print(f"🎵 Answer to hear the demo message")
                print(f"📊 Track call at: https://console.twilio.com/us1/develop/voice/logs")
            else:
                print(f"\n❌ Test call failed")
        else:
            print("Test call skipped.")
    else:
        print("\n❌ Twilio credentials test failed")
        print("Please check your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")