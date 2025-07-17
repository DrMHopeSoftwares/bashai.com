#!/usr/bin/env python3
"""
Explore all available methods in the RelevanceAI SDK
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevanceai import RelevanceAI
    
    print("🔍 Exploring RelevanceAI SDK Methods")
    print("=" * 40)
    
    client = RelevanceAI(
        api_key=os.getenv('RELEVANCE_AI_API_KEY'),
        region=os.getenv('RELEVANCE_AI_REGION'),
        project=os.getenv('RELEVANCE_AI_PROJECT_ID')
    )
    
    # Explore all modules
    print("📋 Main Client Methods:")
    main_methods = [method for method in dir(client) if not method.startswith('_')]
    for method in main_methods:
        print(f"   - {method}")
    
    # Explore agents module
    print(f"\n🤖 Agents Module Methods:")
    agent_methods = [method for method in dir(client.agents) if not method.startswith('_')]
    for method in agent_methods:
        print(f"   - {method}")
    
    # Explore tasks module
    print(f"\n📝 Tasks Module Methods:")
    task_methods = [method for method in dir(client.tasks) if not method.startswith('_')]
    for method in task_methods:
        print(f"   - {method}")
    
    # Explore tools module
    if hasattr(client, 'tools'):
        print(f"\n🔧 Tools Module Methods:")
        tool_methods = [method for method in dir(client.tools) if not method.startswith('_')]
        for method in tool_methods:
            print(f"   - {method}")
    
    # Try to list agents using correct method
    print(f"\n🔍 Testing agent listing...")
    try:
        agents = client.agents.list_agents()
        print(f"✅ Found {len(agents)} agents using list_agents()")
        
        for agent in agents:
            # Check agent attributes
            print(f"\n🤖 Agent Details:")
            for attr in dir(agent):
                if not attr.startswith('_'):
                    try:
                        value = getattr(agent, attr)
                        if not callable(value):
                            print(f"   {attr}: {value}")
                    except:
                        pass
            break  # Just show first agent details
            
    except Exception as e:
        print(f"❌ list_agents failed: {e}")
    
    # Test tasks methods
    print(f"\n📝 Testing tasks methods...")
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    
    # Check what tasks methods actually exist
    for method_name in task_methods:
        if method_name in ['create', 'run', 'trigger', 'execute']:
            print(f"   Testing {method_name}...")
            try:
                method = getattr(client.tasks, method_name)
                print(f"     ✅ {method_name} method exists: {method}")
                # Don't actually call it yet, just verify it exists
            except Exception as e:
                print(f"     ❌ {method_name} error: {e}")
    
    print(f"\n🔗 Available HTTP Methods:")
    for method in ['get', 'post', 'put', 'patch', 'delete']:
        if hasattr(client, method):
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method}")
            
except Exception as e:
    print(f"❌ Error: {e}")