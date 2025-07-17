#!/usr/bin/env python3
"""
Test communication with RelevanceAI agents to find anohra
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevance_ai_integration_fixed import RelevanceAIProvider
    
    print("🔍 Testing RelevanceAI Agents for Anohra")
    print("=" * 50)
    
    provider = RelevanceAIProvider()
    
    # Get all agents
    agents = provider.list_agents()
    print(f"📋 Found {len(agents)} agents to test")
    
    # Test each agent by creating a session and asking "Are you anohra?"
    for i, agent in enumerate(agents, 1):
        agent_id = agent.get('id')
        print(f"\n🤖 Testing Agent #{i} (ID: {agent_id[:8]}...)")
        
        try:
            # Create session
            session = provider.create_session(agent_id, {
                'context': {'test': True, 'looking_for': 'anohra'}
            })
            
            if session and 'session_id' in session:
                session_id = session['session_id']
                print(f"   ✅ Session created: {session_id}")
                
                # Ask if this is anohra
                response = provider.send_message(
                    agent_id=agent_id,
                    session_id=session_id,
                    message="Are you anohra? Please identify yourself.",
                    context={'channel': 'test'}
                )
                
                if response and 'response' in response:
                    response_text = response['response'].lower()
                    print(f"   💬 Response: {response['response']}")
                    
                    # Check if response indicates this is anohra
                    if 'anohra' in response_text or 'yes' in response_text:
                        print(f"   🎯 *** FOUND ANOHRA! Agent ID: {agent_id} ***")
                        
                        # Try to make a call to you
                        print("\n📞 Attempting to initiate call...")
                        call_response = provider.send_message(
                            agent_id=agent_id,
                            session_id=session_id,
                            message="Please make a call to +919373111709 now.",
                            context={'channel': 'phone', 'action': 'call'}
                        )
                        print(f"   📞 Call response: {call_response.get('response', 'No response')}")
                        break
                else:
                    print("   ❌ No response received")
            else:
                print("   ❌ Failed to create session")
                
        except Exception as e:
            print(f"   ❌ Error testing agent: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Testing complete")
    
except Exception as e:
    print(f"❌ Error: {e}")