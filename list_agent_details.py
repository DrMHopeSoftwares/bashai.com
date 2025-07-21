#!/usr/bin/env python3
"""
List detailed information about all RelevanceAI agents
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevance_ai_integration_fixed import RelevanceAIProvider
    
    print("🔍 RelevanceAI Agent Details")
    print("=" * 50)
    
    provider = RelevanceAIProvider()
    
    # Get all agents
    agents = provider.list_agents()
    print(f"📋 Found {len(agents)} agents")
    print("-" * 50)
    
    for i, agent in enumerate(agents, 1):
        print(f"\n🤖 Agent #{i}")
        print(f"   ID: {agent.get('id', 'Unknown')}")
        
        # Get detailed info for each agent
        try:
            detailed_agent = provider.get_agent(agent.get('id'))
            print(f"   Name: {getattr(detailed_agent, 'name', 'Unknown')}")
            print(f"   Description: {getattr(detailed_agent, 'description', 'No description')}")
            print(f"   Model: {getattr(detailed_agent, 'model', 'Unknown')}")
            print(f"   Created: {getattr(detailed_agent, 'created_at', 'Unknown')}")
            
            # Check if this could be anohra
            name = getattr(detailed_agent, 'name', '').lower()
            description = getattr(detailed_agent, 'description', '').lower()
            
            if 'anohra' in name or 'anohra' in description:
                print("   🎯 *** THIS MIGHT BE ANOHRA! ***")
                
        except Exception as e:
            print(f"   ❌ Error getting details: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Agent listing complete")
    
except Exception as e:
    print(f"❌ Error: {e}")