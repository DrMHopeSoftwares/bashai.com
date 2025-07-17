#!/usr/bin/env python3
"""
Call Anohra using the specific agent ID from the screenshot
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevance_ai_integration_fixed import RelevanceAIProvider
    
    # Anohra's agent ID from the screenshot URL
    ANOHRA_AGENT_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    
    print("📞 Calling Anohra Directly")
    print("=" * 30)
    print(f"🎯 Agent ID: {ANOHRA_AGENT_ID}")
    
    provider = RelevanceAIProvider()
    
    # Create session with Anohra
    print("\n1️⃣ Creating session with Anohra...")
    session = provider.create_session(ANOHRA_AGENT_ID, {
        'context': {
            'caller': 'Murali',
            'phone_number': '+919373111709',
            'clinic': 'Dr. Murali Orthopaedic Clinic',
            'request_type': 'test_call',
            'priority': 'immediate'
        }
    })
    
    if session and 'session_id' in session:
        session_id = session['session_id']
        print(f"✅ Session created: {session_id}")
        
        # Send call request
        print("\n2️⃣ Requesting call to +919373111709...")
        
        # Since Anohra is configured for Dr. Murali's clinic, use appropriate context
        message = """Hello Anohra! This is Dr. Murali. I need you to make a test call to my personal number +919373111709 right now to verify our phone system is working properly. Please call immediately."""
        
        try:
            # Try to send the message (even though we had SDK issues before)
            response = provider.send_message(
                agent_id=ANOHRA_AGENT_ID,
                session_id=session_id,
                message=message,
                context={
                    'action': 'voice_call',
                    'phone_number': '+919373111709',
                    'immediate': True,
                    'caller_id': 'Dr_Murali',
                    'clinic_context': True
                }
            )
            
            if response and 'response' in response:
                print(f"✅ Anohra response: {response['response']}")
                print("\n📞 Call should be initiated!")
                print("📱 Please check your phone (+919373111709)")
            else:
                print("⚠️  Message sent but no response received")
                
        except Exception as e:
            print(f"⚠️  SDK messaging issue: {e}")
            print("\n💡 Alternative approaches:")
            print("1. Use the RelevanceAI web interface 'Call agent' button")
            print("2. Start a conversation in the RelevanceAI dashboard")
            print("3. Use the 'Run' button in your Anohra agent page")
            
        print(f"\n📋 Session Details:")
        print(f"   Agent: Anohra ({ANOHRA_AGENT_ID})")
        print(f"   Session: {session_id}")
        print(f"   Target: +919373111709")
        print(f"   Status: Active")
        
    else:
        print("❌ Failed to create session with Anohra")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Quick solution:")
    print("   Go to your RelevanceAI dashboard and click 'Call agent' button")