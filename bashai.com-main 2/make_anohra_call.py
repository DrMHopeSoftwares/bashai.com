#!/usr/bin/env python3
"""
Make Anohra call using the correct RelevanceAI phone call API
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

try:
    from relevanceai import RelevanceAI
    
    print("📞 Making Anohra Call You!")
    print("=" * 30)
    
    client = RelevanceAI(
        api_key=os.getenv('RELEVANCE_AI_API_KEY'),
        region=os.getenv('RELEVANCE_AI_REGION'),
        project=os.getenv('RELEVANCE_AI_PROJECT_ID')
    )
    
    ANOHRA_ID = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
    YOUR_PHONE = "+919373111709"
    
    print(f"🎯 Agent: Anohra ({ANOHRA_ID})")
    print(f"📱 Calling: {YOUR_PHONE}")
    
    # Method 1: Try outbound phone call endpoint
    print(f"\n1️⃣ Attempting outbound call...")
    try:
        response = client.post(
            f"/agents/{ANOHRA_ID}/phone_call",
            json={
                "phone_number": YOUR_PHONE,
                "direction": "outbound"
            }
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Call initiated!")
            print(f"   Response: {result}")
            print(f"\n📞 Anohra is calling you at {YOUR_PHONE}!")
            print(f"📱 Please answer your phone...")
        else:
            print(f"❌ Call failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Phone call endpoint error: {e}")
        
        # Method 2: Try runtime/phone endpoint
        print(f"\n2️⃣ Trying runtime phone endpoint...")
        try:
            response = client.post(
                f"/agents/{ANOHRA_ID}/runtime/phone",
                json={
                    "phone_number": YOUR_PHONE,
                    "type": "outbound"
                }
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Runtime call initiated!")
                print(f"   Response: {result}")
            else:
                print(f"❌ Runtime call failed: {response.status_code} - {response.text}")
                
        except Exception as e2:
            print(f"❌ Runtime endpoint error: {e2}")
            
            # Method 3: Try direct phone trigger
            print(f"\n3️⃣ Trying direct phone trigger...")
            try:
                response = client.post(
                    f"/agents/{ANOHRA_ID}/trigger",
                    json={
                        "params": {
                            "phone_number": YOUR_PHONE,
                            "action": "outbound_call",
                            "immediate": True
                        }
                    }
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✅ Trigger call initiated!")
                    print(f"   Response: {result}")
                else:
                    print(f"❌ Trigger failed: {response.status_code} - {response.text}")
                    
            except Exception as e3:
                print(f"❌ Trigger endpoint error: {e3}")
                
                # Method 4: Try async run with phone context
                print(f"\n4️⃣ Trying async run with phone context...")
                try:
                    response = client.post(
                        f"/agents/{ANOHRA_ID}/async_run",
                        json={
                            "params": {
                                "runtime": "phone_call",
                                "phone_number": YOUR_PHONE,
                                "direction": "outbound",
                                "context": {
                                    "caller": "System Test",
                                    "purpose": "Integration Test"
                                }
                            }
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        print(f"✅ Async run initiated!")
                        print(f"   Response: {result}")
                        print(f"\n🎉 Call request sent successfully!")
                        print(f"📞 Anohra should call {YOUR_PHONE} shortly...")
                    else:
                        print(f"❌ Async run failed: {response.status_code} - {response.text}")
                        
                except Exception as e4:
                    print(f"❌ Async run error: {e4}")
                    print(f"\n💡 All automatic methods failed.")
                    print(f"   Manual option: Use RelevanceAI dashboard 'Call agent' button")
    
    print(f"\n📋 Call Summary:")
    print(f"   Agent: Anohra (Dr. Murali's Orthopaedic Clinic)")
    print(f"   Target: {YOUR_PHONE}")
    print(f"   Language: Hindi/English support")
    print(f"   Voice: ElevenLabs (Female, Hindi)")
    print(f"   Purpose: Test integration")
    
except Exception as e:
    print(f"❌ Setup error: {e}")
    print(f"\n💡 Backup plan:")
    print(f"   1. Go to RelevanceAI dashboard")
    print(f"   2. Open Anohra agent")
    print(f"   3. Click 'Call agent' button")
    print(f"   4. Enter {YOUR_PHONE} as target")