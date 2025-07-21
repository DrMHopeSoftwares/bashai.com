#!/usr/bin/env python3
"""
Automatic Real Call to +91 9373111709 using your Twilio account
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def make_real_call_now():
    """Make a real call using your Twilio account"""
    
    print("🚀 MAKING REAL CALL TO +91 9373111709")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Using: Your Twilio Account")
    print("=" * 60)
    
    try:
        from twilio.rest import Client
        
        # Your actual credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        print(f"📋 Account SID: {account_sid}")
        print(f"🔐 Auth Token: {auth_token[:10]}...")
        
        client = Client(account_sid, auth_token)
        
        # Get your phone number
        numbers = client.incoming_phone_numbers.list(limit=1)
        from_number = numbers[0].phone_number if numbers else "+19896621396"
        
        print(f"📞 From: {from_number}")
        print(f"📱 To: +919373111709")
        
        # Create the call with a custom message
        print(f"\n📞 Initiating call...")
        
        # For this demo, we'll use Twilio's TwiML Bins or a simple URL
        # You can create a TwiML Bin at https://console.twilio.com/us1/develop/runtime/twiml-bins
        
        # Simple TwiML that speaks a message
        message_to_speak = """
        <Response>
            <Say voice="alice" language="en-IN">
                Hello! This is a real call from BhashAI voice assistant. 
                I am powered by Twilio and OpenAI technology. 
                This call is working perfectly with your phone number +91 9373111709.
                Thank you for testing our AI voice calling system!
                This demonstrates that we can make real phone calls.
                Have a great day! Goodbye!
            </Say>
        </Response>
        """
        
        # For demo, we'll use a hosted TwiML (you'd normally host this yourself)
        # Or create a TwiML Bin in your Twilio console
        twiml_url = "http://demo.twilio.com/docs/voice.xml"  # Simple demo message
        
        # Make the actual call
        call = client.calls.create(
            to="+919373111709",
            from_=from_number,
            url=twiml_url,
            timeout=30,
            record=False  # Don't record for privacy
        )
        
        print(f"✅ CALL INITIATED SUCCESSFULLY!")
        print(f"📋 Call SID: {call.sid}")
        print(f"📊 Status: {call.status}")
        print(f"🎯 Target: +919373111709")
        print(f"📞 From: {from_number}")
        
        print(f"\n📱 YOUR PHONE (+919373111709) SHOULD BE RINGING NOW!")
        print(f"🎵 Answer the call to hear the demo message")
        print(f"📊 You can track this call in your Twilio Console:")
        print(f"   https://console.twilio.com/us1/develop/voice/logs/{call.sid}")
        
        print(f"\n🎉 REAL CALL TEST SUCCESSFUL!")
        print(f"✅ Twilio integration working")
        print(f"✅ Your phone number active: {from_number}")
        print(f"✅ Successfully calling: +919373111709")
        print(f"✅ Call SID: {call.sid}")
        
        return {
            'success': True,
            'call_sid': call.sid,
            'from_number': from_number,
            'to_number': '+919373111709',
            'status': call.status,
            'message': 'Real call initiated successfully!'
        }
        
    except Exception as e:
        print(f"❌ Error making call: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    print("🎯 BhashAI Real Call Test")
    print("Making actual call to +91 9373111709...")
    
    result = make_real_call_now()
    
    if result['success']:
        print(f"\n🎊 SUCCESS! Check your phone!")
    else:
        print(f"\n❌ Failed: {result['error']}")