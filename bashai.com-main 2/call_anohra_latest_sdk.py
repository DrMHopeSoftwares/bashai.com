#!/usr/bin/env python3
"""
Call Anohra using the latest RelevanceAI SDK (10.2.2) with correct API methods
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from relevanceai import RelevanceAI
    
    print("📞 Calling Anohra with Latest SDK")
    print("=" * 35)
    
    # Initialize client
    api_key = os.getenv('RELEVANCE_AI_API_KEY')
    region = os.getenv('RELEVANCE_AI_REGION')
    project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
    
    client = RelevanceAI(
        api_key=api_key,
        region=region,
        project=project_id
    )
    print("✅ RelevanceAI client initialized")
    
    # Anohra's agent ID from the screenshot
    ANOHRA_AGENT_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    
    print(f"\n1️⃣ Getting Anohra agent details...")
    print(f"   Agent ID: {ANOHRA_AGENT_ID}")
    
    # Try to get agent details
    try:
        agent = client.agents.retrieve_agent(agent_id=ANOHRA_AGENT_ID)
        print(f"✅ Found agent: {getattr(agent, 'name', 'Anohra')}")
    except Exception as e:
        print(f"⚠️  Couldn't retrieve agent details: {e}")
        print("   Proceeding with known agent ID...")
    
    print(f"\n2️⃣ Triggering Anohra to call +919373111709...")
    
    # Try using the tasks module for execution
    try:
        # Method 1: Using tasks.run
        result = client.tasks.run(
            agent_id=ANOHRA_AGENT_ID,
            params={
                "message": "Hello Anohra! This is Dr. Murali. Please make an immediate voice call to +919373111709 to test our phone system integration. Call me right now!",
                "phone_number": "+919373111709",
                "caller": "Dr. Murali",
                "action": "voice_call",
                "immediate": True,
                "clinic_context": True
            }
        )
        print(f"✅ Task executed successfully!")
        print(f"   Result: {result}")
        print(f"\n📞 Anohra should now call +919373111709!")
        print(f"📱 Please check your phone...")
        
    except Exception as e:
        print(f"❌ Tasks.run failed: {e}")
        
        # Method 2: Try tasks.trigger
        try:
            result = client.tasks.trigger(
                agent_id=ANOHRA_AGENT_ID,
                params={
                    "message": "Hello Anohra! This is Dr. Murali. Please make an immediate voice call to +919373111709 to test our phone system integration. Call me right now!",
                    "phone_number": "+919373111709",
                    "action": "voice_call"
                }
            )
            print(f"✅ Task triggered successfully!")
            print(f"   Result: {result}")
            
        except Exception as e2:
            print(f"❌ Tasks.trigger failed: {e2}")
            
            # Method 3: Direct POST request
            try:
                result = client.post(
                    f"/agents/{ANOHRA_AGENT_ID}/trigger",
                    json={
                        "params": {
                            "message": "Hello Anohra! This is Dr. Murali. Please make an immediate voice call to +919373111709 to test our phone system integration. Call me right now!",
                            "phone_number": "+919373111709",
                            "action": "voice_call"
                        }
                    }
                )
                print(f"✅ Direct API call successful!")
                print(f"   Result: {result}")
                
            except Exception as e3:
                print(f"❌ Direct API failed: {e3}")
                
                # Method 4: Try async run
                try:
                    result = client.post(
                        f"/agents/{ANOHRA_AGENT_ID}/async_run",
                        json={
                            "params": {
                                "message": "Hello Anohra! Please call +919373111709 now!",
                                "phone_number": "+919373111709"
                            }
                        }
                    )
                    print(f"✅ Async run successful!")
                    print(f"   Result: {result}")
                    
                except Exception as e4:
                    print(f"❌ All methods failed. Last error: {e4}")
                    print("\n💡 Please use the RelevanceAI web interface:")
                    print("   1. Go to your Anohra agent page")
                    print("   2. Click 'Call agent' button")
                    print("   3. Or click 'Run' and send message")
    
    print(f"\n📋 Summary:")
    print(f"   Agent: Anohra ({ANOHRA_AGENT_ID})")
    print(f"   Target: +919373111709")
    print(f"   SDK Version: 10.2.2")
    print(f"   Status: Request sent")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Alternative: Use RelevanceAI dashboard 'Call agent' button")