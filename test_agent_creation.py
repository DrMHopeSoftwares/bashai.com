#!/usr/bin/env python3
"""
Test agent creation parameters for RelevanceAI
"""

import os
import inspect
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
    
    # Check create_agent signature
    print("🔍 Checking create_agent method signature:")
    try:
        sig = inspect.signature(client.agents.create_agent)
        print(f"Parameters: {list(sig.parameters.keys())}")
        print(f"Full signature: {sig}")
    except Exception as e:
        print(f"Could not inspect signature: {e}")
    
    # Try different parameter combinations
    print("\n🧪 Testing different parameter combinations:")
    
    # Test 1: Just name
    try:
        agent = client.agents.create_agent(name="Test Agent 1")
        print(f"✅ Created with just name: {agent.get('agent_id')}")
        
        # Clean up
        if agent.get('agent_id'):
            client.agents.delete_agent(agent['agent_id'])
            print(f"🧹 Cleaned up test agent: {agent['agent_id']}")
            
    except Exception as e:
        print(f"❌ Name only failed: {e}")
    
    # Test 2: Name and system_prompt
    try:
        agent = client.agents.create_agent(
            name="Test Agent 2",
            system_prompt="You are a helpful assistant."
        )
        print(f"✅ Created with name and system_prompt: {agent.get('agent_id')}")
        
        # Clean up
        if agent.get('agent_id'):
            client.agents.delete_agent(agent['agent_id'])
            print(f"🧹 Cleaned up test agent: {agent['agent_id']}")
            
    except Exception as e:
        print(f"❌ Name + system_prompt failed: {e}")
    
    # Test 3: Various combinations
    test_params = [
        {'name': 'Test3'},
        {'name': 'Test4', 'prompt': 'You are helpful'},
        {'name': 'Test5', 'instructions': 'Be helpful'},
        {'name': 'Test6', 'system_message': 'You are an AI'},
    ]
    
    for i, params in enumerate(test_params, 3):
        try:
            agent = client.agents.create_agent(**params)
            print(f"✅ Test {i} worked with params: {params}")
            
            # Clean up
            if agent.get('agent_id'):
                client.agents.delete_agent(agent['agent_id'])
                
        except Exception as e:
            print(f"❌ Test {i} failed with params {params}: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()