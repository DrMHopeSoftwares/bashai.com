#!/usr/bin/env python3
"""
Simple test to figure out RelevanceAI SDK usage
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevanceai import RelevanceAI
    print("✅ RelevanceAI SDK imported successfully")
    
    # Try different ways to initialize
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")
    
    # Method 1: Set environment variable
    os.environ['RELEVANCE_API_KEY'] = api_key
    
    # Method 2: Try different initialization methods
    try:
        client = RelevanceAI()
        print("✅ Client initialized with default constructor")
    except Exception as e:
        print(f"❌ Default constructor failed: {e}")
        
        # Try with API key parameter
        try:
            client = RelevanceAI(api_key=api_key)
            print("✅ Client initialized with api_key parameter")
        except Exception as e2:
            print(f"❌ API key parameter failed: {e2}")
            
            # Try with token parameter
            try:
                client = RelevanceAI(token=api_key)
                print("✅ Client initialized with token parameter")
            except Exception as e3:
                print(f"❌ Token parameter failed: {e3}")
                
                # Check what parameters are available
                print("\nChecking RelevanceAI constructor signature:")
                import inspect
                sig = inspect.signature(RelevanceAI.__init__)
                print(f"Parameters: {list(sig.parameters.keys())}")
    
    # If we have a client, try to test it
    if 'client' in locals():
        try:
            # Test connection by listing agents
            agents = client.agents.list()
            print(f"✅ Connection test successful - found {len(agents)} agents")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print("This might be normal if no agents exist yet")

except ImportError as e:
    print(f"❌ Failed to import RelevanceAI: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")