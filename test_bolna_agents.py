#!/usr/bin/env python3
"""
Test script to check available Bolna agents
"""

import os
from bolna_integration import BolnaAPI

def test_bolna_agents():
    """Test Bolna API and list available agents"""
    try:
        # Use admin settings for testing
        admin_user_data = {
            'sender_phone': '+918085315398',
            'bolna_agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480'
        }
        
        print("🔍 Initializing Bolna API...")
        bolna_api = BolnaAPI(admin_user_data=admin_user_data)
        
        print("📋 Listing available agents...")
        agents = bolna_api.list_agents()

        print(f"✅ Found {len(agents)} agents:")
        print(f"Raw response: {agents}")

        for i, agent in enumerate(agents, 1):
            print(f"  {i}. Full agent data: {agent}")
            print(f"     Agent ID: {agent.get('agent_id', agent.get('id', 'N/A'))}")
            print(f"     Name: {agent.get('agent_name', agent.get('name', 'N/A'))}")
            print(f"     Status: {agent.get('status', 'N/A')}")
            print()
        
        # Test specific agent
        test_agent_id = '15554373-b8e1-4b00-8c25-c4742dc8e480'
        print(f"🔍 Testing specific agent: {test_agent_id}")
        
        try:
            agent_details = bolna_api.get_agent_details(test_agent_id)
            print(f"✅ Agent exists: {agent_details.get('agent_name', 'N/A')}")
        except Exception as e:
            print(f"❌ Agent not found: {e}")
            
            # Try with first available agent if any
            if agents:
                first_agent_id = agents[0].get('agent_id')
                print(f"🔄 Trying first available agent: {first_agent_id}")
                try:
                    agent_details = bolna_api.get_agent_details(first_agent_id)
                    print(f"✅ First agent works: {agent_details.get('agent_name', 'N/A')}")
                    print(f"💡 Use this agent ID: {first_agent_id}")
                except Exception as e2:
                    print(f"❌ First agent also failed: {e2}")
        
    except Exception as e:
        print(f"❌ Bolna API test failed: {e}")

if __name__ == "__main__":
    test_bolna_agents()
