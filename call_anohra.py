#!/usr/bin/env python3
"""
Connect with Anohra agent and initiate communication
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevance_ai_integration_fixed import RelevanceAIProvider
    
    print("📞 Connecting to Anohra Agent")
    print("=" * 40)
    
    provider = RelevanceAIProvider()
    
    # Since we know Anohra exists but names weren't showing in our API calls,
    # let's try each agent and look for the one that responds as Anohra
    agents = provider.list_agents()
    print(f"🔍 Testing {len(agents)} agents to find Anohra...")
    
    anohra_found = False
    
    for i, agent in enumerate(agents):
        agent_id = agent.get('id')
        print(f"\n🤖 Testing agent {i+1}: {agent_id[:8]}...")
        
        try:
            # Create session
            session = provider.create_session(agent_id, {
                'context': {
                    'user_phone': '+919373111709',
                    'request_type': 'voice_call',
                    'caller': 'Murali'
                }
            })
            
            if session and 'session_id' in session:
                session_id = session['session_id']
                print(f"   ✅ Session created: {session_id}")
                
                # Test with a simple greeting to see if this responds as Anohra
                try:
                    response = provider.send_message(
                        agent_id=agent_id,
                        session_id=session_id,
                        message="Hello! Are you Anohra? I'm Murali and I want to test our voice connection.",
                        context={
                            'channel': 'voice',
                            'phone_number': '+919373111709',
                            'action': 'identify'
                        }
                    )
                    
                    if response and 'response' in response:
                        response_text = response['response']
                        print(f"   💬 Agent response: {response_text}")
                        
                        # Check if this seems like Anohra based on the response
                        if any(keyword in response_text.lower() for keyword in ['anohra', 'yes', 'i am', 'hello murali']):
                            print(f"   🎯 *** FOUND ANOHRA! Agent ID: {agent_id} ***")
                            anohra_found = True
                            
                            # Now request a voice call
                            print("\n📞 Requesting voice call to +919373111709...")
                            call_request = provider.send_message(
                                agent_id=agent_id,
                                session_id=session_id,
                                message="Please initiate a voice call to +919373111709. I want to test our voice integration. Call me now.",
                                context={
                                    'channel': 'voice',
                                    'phone_number': '+919373111709',
                                    'action': 'call',
                                    'priority': 'high'
                                }
                            )
                            
                            if call_request and 'response' in call_request:
                                print(f"   📞 Call response: {call_request['response']}")
                            
                            print(f"\n✅ Session established with Anohra!")
                            print(f"   Agent ID: {agent_id}")
                            print(f"   Session ID: {session_id}")
                            print(f"   Phone: +919373111709")
                            
                            # Keep the session active for continued conversation
                            print("\n🔄 Session is now active. You can:")
                            print("   1. Wait for Anohra to call you")
                            print("   2. Use this session for text communication")
                            print("   3. Send additional instructions")
                            
                            break
                            
                except Exception as msg_error:
                    print(f"   ❌ Messaging error: {msg_error}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Session error: {e}")
            continue
    
    if not anohra_found:
        print("\n❌ Could not identify Anohra from the available agents")
        print("💡 You may need to:")
        print("   1. Check that Anohra is properly configured in RelevanceAI")
        print("   2. Verify the agent has voice capabilities enabled")
        print("   3. Ensure your RelevanceAI project has phone integration")
    
    print("\n" + "=" * 40)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Make sure:")
    print("   1. RelevanceAI SDK is installed: pip install relevanceai")
    print("   2. Environment variables are set in .env")
    print("   3. You have access to the RelevanceAI project")