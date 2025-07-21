#!/usr/bin/env python3
"""
Explore RelevanceAI SDK to understand available methods
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevanceai import RelevanceAI
    
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    client = RelevanceAI(
        api_key=api_key,
        region=region,
        project=project_id
    )
    
    print("✅ Client initialized successfully")
    print(f"Client type: {type(client)}")
    
    # Explore available attributes
    print("\n📋 Available client attributes:")
    for attr in dir(client):
        if not attr.startswith('_'):
            print(f"  - {attr}: {type(getattr(client, attr))}")
    
    # Check agents manager
    if hasattr(client, 'agents'):
        print(f"\n🤖 Agents manager type: {type(client.agents)}")
        print("Available agents methods:")
        for method in dir(client.agents):
            if not method.startswith('_'):
                print(f"  - {method}")
    
    # Try some methods
    print("\n🧪 Testing methods:")
    
    # Try listing agents
    try:
        if hasattr(client.agents, 'list_agents'):
            agents = client.agents.list_agents()
            print(f"✅ list_agents() worked: {len(agents)} agents found")
        elif hasattr(client.agents, 'get_all'):
            agents = client.agents.get_all()
            print(f"✅ get_all() worked: {len(agents)} agents found")
        elif hasattr(client.agents, 'list'):
            agents = client.agents.list()
            print(f"✅ list() worked: {len(agents)} agents found")
        else:
            print("❌ No list method found for agents")
    except Exception as e:
        print(f"❌ Listing agents failed: {e}")
    
    # Try creating an agent
    try:
        if hasattr(client.agents, 'create'):
            test_agent = client.agents.create(
                name="Test Agent",
                description="Test agent for exploration"
            )
            print(f"✅ Agent creation worked: {test_agent}")
        else:
            print("❌ No create method found for agents")
    except Exception as e:
        print(f"❌ Creating agent failed: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()