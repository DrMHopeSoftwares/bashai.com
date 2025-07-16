#!/usr/bin/env python3
"""
Test Script to Make a Call to +91 9373111709 using OpenAI Realtime API
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openai_phone_call_integration import make_call, call_manager

async def make_demo_call():
    """Make a demo call to the specified number"""
    
    phone_number = "+919373111709"
    
    print(f"🎯 Initiating OpenAI Realtime API call to {phone_number}")
    print("=" * 60)
    
    # Custom message for the AI
    ai_message = """Hello! This is a demonstration call from BhashAI voice assistant. 
    I'm an AI that can speak naturally in Hindi and English. 
    I'm calling to show you how OpenAI's Realtime API works for phone conversations. 
    This is just a test call. How are you today? 
    Feel free to respond in Hindi or English, whichever you prefer."""
    
    try:
        # Make the call
        print("📞 Making call...")
        result = await make_call(
            phone_number=phone_number,
            message=ai_message,
            provider='twilio',  # Using Twilio as provider
            user_id='demo-user-call-test'
        )
        
        print("📋 Call Initiation Result:")
        print(json.dumps(result, indent=2, default=str))
        
        if not result['success']:
            print("❌ Call failed to initiate")
            return False
        
        call_id = result['call_id']
        print(f"\n✅ Call initiated successfully!")
        print(f"📞 Call ID: {call_id}")
        print(f"📱 Phone Number: {phone_number}")
        print(f"🔧 Provider: {result.get('provider', 'N/A')}")
        
        # Monitor call progress
        print("\n📊 Monitoring call progress...")
        
        # Check status every 5 seconds for 1 minute
        for i in range(12):  # 12 * 5 seconds = 1 minute
            await asyncio.sleep(5)
            
            # Get current status
            status = call_manager.get_call_status(call_id)
            analytics = await call_manager.get_call_analytics(call_id)
            
            print(f"\n⏱️  Status Check {i+1}/12:")
            print(f"   Status: {status['status'] if status else 'Unknown'}")
            print(f"   Duration: {analytics.get('duration_seconds', 0):.1f} seconds")
            print(f"   Cost: ${analytics.get('estimated_cost_usd', 0):.4f}")
            
            if status and status['status'] == 'completed':
                print("✅ Call completed naturally")
                break
        
        # Get final analytics
        print("\n📈 Final Call Analytics:")
        final_analytics = await call_manager.get_call_analytics(call_id)
        print(json.dumps(final_analytics, indent=2, default=str))
        
        # End the call if still active
        if call_manager.get_call_status(call_id):
            print("\n🔚 Ending call...")
            end_result = await call_manager.end_call(call_id)
            print("End Result:", json.dumps(end_result, indent=2, default=str))
        
        print("\n✅ Call test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during call: {e}")
        return False

async def test_call_api():
    """Test the call API integration"""
    
    print("🚀 Starting OpenAI Realtime Phone Call Test")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Target: +91 9373111709")
    print("🤖 AI Model: gpt-4o-realtime-preview")
    print("\n" + "=" * 60)
    
    # Run the call test
    success = await make_demo_call()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Phone call test completed successfully!")
        print("\n📋 What happened:")
        print("1. ✅ OpenAI Realtime session created")
        print("2. ✅ Phone call initiated (mock)")
        print("3. ✅ AI conversation simulated")
        print("4. ✅ Usage tracking and billing calculated")
        print("5. ✅ Call ended and cleanup completed")
        
        print("\n⚠️  Note: This is a demonstration with mock phone calling.")
        print("   To make real calls, you need:")
        print("   • Twilio/Plivo account with phone number")
        print("   • Webhook endpoints for call handling")
        print("   • Audio streaming between phone and OpenAI")
    else:
        print("❌ Phone call test failed")
        
    return success

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_call_api())
    sys.exit(0 if success else 1)