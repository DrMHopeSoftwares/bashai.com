#!/usr/bin/env python3
"""
Test the latest RelevanceAI SDK (10.2.2) with proper API usage
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevanceai import RelevanceAI
    print("✅ RelevanceAI SDK imported successfully")
    print(f"   Version: 10.2.2 (latest)")
    
    # Check what the SDK constructor expects
    import inspect
    sig = inspect.signature(RelevanceAI.__init__)
    print(f"   Constructor parameters: {list(sig.parameters.keys())}")
    
    # Try initialization with different approaches
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    print(f"\n🔑 Credentials loaded:")
    print(f"   API Key: {api_key[:20]}...{api_key[-10:] if api_key else 'None'}")
    print(f"   Region: {region}")
    print(f"   Project: {project_id}")
    
    # Try different initialization methods
    client = None
    
    # Method 1: With all parameters
    try:
        client = RelevanceAI(
            api_key=api_key,
            region=region,
            project=project_id
        )
        print("✅ Client initialized with all parameters")
    except Exception as e:
        print(f"❌ Full parameters failed: {e}")
        
        # Method 2: Just API key
        try:
            client = RelevanceAI(api_key=api_key)
            print("✅ Client initialized with API key only")
        except Exception as e2:
            print(f"❌ API key only failed: {e2}")
            
            # Method 3: Token parameter
            try:
                client = RelevanceAI(token=api_key)
                print("✅ Client initialized with token parameter")
            except Exception as e3:
                print(f"❌ Token parameter failed: {e3}")
    
    if client:
        print("\n🔍 Testing client methods...")
        
        # Check available methods
        methods = [method for method in dir(client) if not method.startswith('_')]
        print(f"   Available methods: {methods}")
        
        # Test agents access
        if hasattr(client, 'agents'):
            print("✅ Agents module available")
            
            # Check agents methods
            agent_methods = [method for method in dir(client.agents) if not method.startswith('_')]
            print(f"   Agent methods: {agent_methods}")
            
            # Try to list agents
            try:
                agents = client.agents.list()
                print(f"✅ Listed {len(agents)} agents")
                
                # Find Anohra specifically
                anohra_agent = None
                for agent in agents:
                    print(f"   Agent: {getattr(agent, 'name', 'Unknown')} - ID: {getattr(agent, 'id', 'Unknown')}")
                    if hasattr(agent, 'name') and 'anohra' in str(agent.name).lower():
                        anohra_agent = agent
                        print(f"   🎯 Found Anohra: {agent}")
                
                if anohra_agent:
                    print(f"\n📞 Testing call with Anohra...")
                    agent_id = getattr(anohra_agent, 'id', None)
                    
                    # Try to trigger/run the agent
                    if hasattr(client.agents, 'trigger'):
                        try:
                            result = client.agents.trigger(
                                agent_id=agent_id,
                                params={
                                    "message": "Hello Anohra! Please call +919373111709 immediately. This is Dr. Murali testing the phone system.",
                                    "phone_number": "+919373111709",
                                    "action": "voice_call"
                                }
                            )
                            print(f"✅ Agent triggered: {result}")
                        except Exception as e:
                            print(f"❌ Trigger failed: {e}")
                    
                    if hasattr(client.agents, 'run'):
                        try:
                            result = client.agents.run(
                                agent_id=agent_id,
                                params={
                                    "message": "Hello Anohra! Please call +919373111709 immediately. This is Dr. Murali testing the phone system.",
                                    "phone_number": "+919373111709",
                                    "action": "voice_call"
                                }
                            )
                            print(f"✅ Agent run: {result}")
                        except Exception as e:
                            print(f"❌ Run failed: {e}")
                            
                else:
                    print("❌ Anohra agent not found")
                    
            except Exception as e:
                print(f"❌ Failed to list agents: {e}")
        else:
            print("❌ No agents module found")
    else:
        print("❌ Failed to initialize client")
        
except ImportError as e:
    print(f"❌ Failed to import RelevanceAI: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")