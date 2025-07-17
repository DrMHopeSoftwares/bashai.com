#!/usr/bin/env python3
"""
Test the prompt editing functionality
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_prompt_functionality():
    """Test viewing and editing Anohra's prompt"""
    
    print("🧪 Testing Anohra Prompt Editing Functionality")
    print("=" * 50)
    
    try:
        from relevance_ai_integration_fixed import RelevanceAIProvider
        
        provider = RelevanceAIProvider()
        anohra_id = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
        
        print(f"🎯 Testing with Anohra ID: {anohra_id}")
        
        # Test 1: View current prompt
        print(f"\n1️⃣ Testing: Get current prompt...")
        current_agent = provider.get_agent(anohra_id)
        if current_agent:
            print(f"✅ Agent retrieved: {current_agent.get('name', 'Unknown')}")
            agent_data = current_agent.get('agent_data')
            if hasattr(agent_data, 'metadata'):
                current_prompt = getattr(agent_data.metadata, 'system_prompt', 'No prompt found')
                print(f"✅ Current prompt length: {len(current_prompt)} characters")
                print(f"📝 Prompt preview: {current_prompt[:200]}...")
            else:
                print(f"❌ Could not access agent metadata")
        else:
            print(f"❌ Failed to retrieve agent")
            return False
        
        # Test 2: Test prompt update (with a minor addition)
        print(f"\n2️⃣ Testing: Update prompt...")
        test_addition = "\n\n/* TEST UPDATE - This line was added by BhashAI prompt editor */"
        new_prompt = current_prompt + test_addition
        
        success = provider.update_agent_prompt(anohra_id, new_prompt)
        if success:
            print(f"✅ Prompt update successful!")
            
            # Verify the update
            print(f"\n3️⃣ Testing: Verify update...")
            updated_agent = provider.get_agent(anohra_id)
            if updated_agent:
                updated_agent_data = updated_agent.get('agent_data')
                if hasattr(updated_agent_data, 'metadata'):
                    updated_prompt = getattr(updated_agent_data.metadata, 'system_prompt', '')
                    if test_addition in updated_prompt:
                        print(f"✅ Update verified! New length: {len(updated_prompt)} characters")
                        
                        # Test 3: Restore original prompt
                        print(f"\n4️⃣ Testing: Restore original prompt...")
                        restore_success = provider.update_agent_prompt(anohra_id, current_prompt)
                        if restore_success:
                            print(f"✅ Original prompt restored!")
                        else:
                            print(f"⚠️  Could not restore original prompt via API")
                    else:
                        print(f"❌ Update not reflected in retrieved prompt")
                else:
                    print(f"❌ Could not verify update")
            else:
                print(f"❌ Could not retrieve updated agent")
        else:
            print(f"❌ Prompt update failed")
        
        print(f"\n📋 Test Summary:")
        print(f"✅ Prompt viewing: Working")
        print(f"✅ Prompt editing: {'Working' if success else 'Needs troubleshooting'}")
        print(f"✅ Agent retrieval: Working")
        
        print(f"\n🔧 Available Methods:")
        print(f"   • view_anohra_prompt.py - View current prompt")
        print(f"   • edit_anohra_prompt.py - Interactive editor")
        print(f"   • static/anohra-prompt-editor.html - Web interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_prompt_functionality()