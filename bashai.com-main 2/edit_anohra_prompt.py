#!/usr/bin/env python3
"""
Edit Anohra's prompt within the BhashAI project using RelevanceAI API
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class AnohraPromptEditor:
    def __init__(self):
        self.api_key = os.getenv('RELEVANCE_AI_API_KEY')
        self.region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
        self.project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
        self.anohra_id = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
        
        # Working authentication format from our successful call
        self.auth_header = f"{self.project_id}:{self.api_key}"
        self.base_url = f"https://api-{self.region}.stack.tryrelevance.com"
        
    def get_current_prompt(self):
        """Get Anohra's current system prompt"""
        print("📋 Getting Anohra's current prompt...")
        
        try:
            from relevanceai import RelevanceAI
            client = RelevanceAI(
                api_key=self.api_key,
                region=self.region,
                project=self.project_id
            )
            
            agent = client.agents.retrieve_agent(agent_id=self.anohra_id)
            current_prompt = getattr(agent.metadata, 'system_prompt', 'No prompt found')
            
            print("✅ Current Anohra System Prompt:")
            print("-" * 50)
            print(current_prompt)
            print("-" * 50)
            
            return current_prompt
            
        except Exception as e:
            print(f"❌ Error getting current prompt: {e}")
            return None
    
    def update_prompt(self, new_prompt):
        """Update Anohra's system prompt"""
        print("🔄 Updating Anohra's prompt...")
        
        try:
            # Try using the upsert_agent method to update the prompt
            from relevanceai import RelevanceAI
            client = RelevanceAI(
                api_key=self.api_key,
                region=self.region,
                project=self.project_id
            )
            
            # Get current agent data first
            current_agent = client.agents.retrieve_agent(agent_id=self.anohra_id)
            
            # Update the system prompt
            updated_agent_data = {
                "agent_id": self.anohra_id,
                "name": getattr(current_agent.metadata, 'name', 'Anohra'),
                "system_prompt": new_prompt,
                # Keep other existing settings
                "model": getattr(current_agent.metadata, 'model', 'openai-gpt-4o-mini'),
                "temperature": getattr(current_agent.metadata, 'temperature', 0),
            }
            
            # Update the agent
            result = client.agents.upsert_agent(**updated_agent_data)
            
            print(f"✅ Anohra's prompt updated successfully!")
            print(f"📝 New prompt preview: {new_prompt[:100]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating prompt via SDK: {e}")
            
            # Try raw API approach
            return self._update_prompt_raw_api(new_prompt)
    
    def _update_prompt_raw_api(self, new_prompt):
        """Update prompt using raw API calls"""
        print("🔄 Trying raw API update...")
        
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }
        
        # Try different endpoints for updating agent
        endpoints = [
            f"{self.base_url}/latest/agents/{self.anohra_id}",
            f"{self.base_url}/agents/{self.anohra_id}",
            f"{self.base_url}/latest/agents/{self.anohra_id}/update"
        ]
        
        update_data = {
            "system_prompt": new_prompt,
            "agent_id": self.anohra_id
        }
        
        for endpoint in endpoints:
            try:
                # Try PATCH method
                response = requests.patch(endpoint, headers=headers, json=update_data, timeout=30)
                
                if response.status_code in [200, 201]:
                    print(f"✅ Raw API update successful!")
                    return True
                elif response.status_code == 405:
                    # Try PUT method
                    response = requests.put(endpoint, headers=headers, json=update_data, timeout=30)
                    if response.status_code in [200, 201]:
                        print(f"✅ Raw API update successful!")
                        return True
                        
            except Exception as e:
                continue
        
        print(f"❌ Raw API update failed")
        return False
    
    def interactive_prompt_editor(self):
        """Interactive prompt editing interface"""
        print("🤖 Anohra Prompt Editor")
        print("=" * 40)
        
        # Get current prompt
        current_prompt = self.get_current_prompt()
        
        if not current_prompt:
            print("❌ Could not retrieve current prompt")
            return
        
        print(f"\n📝 Current prompt length: {len(current_prompt)} characters")
        
        while True:
            print(f"\n🔧 Options:")
            print(f"1. View full current prompt")
            print(f"2. Edit prompt (replace entirely)")
            print(f"3. Add to existing prompt") 
            print(f"4. Quick templates")
            print(f"5. Test prompt with sample call")
            print(f"6. Exit")
            
            choice = input(f"\nSelect option (1-6): ").strip()
            
            if choice == "1":
                print(f"\n📄 Full Current Prompt:")
                print("=" * 60)
                print(current_prompt)
                print("=" * 60)
                
            elif choice == "2":
                print(f"\n✏️  Enter new prompt (type 'DONE' on a new line when finished):")
                new_lines = []
                while True:
                    line = input()
                    if line.strip() == "DONE":
                        break
                    new_lines.append(line)
                
                new_prompt = "\n".join(new_lines)
                
                if new_prompt.strip():
                    print(f"\n🔍 Preview new prompt:")
                    print("-" * 40)
                    print(new_prompt)
                    print("-" * 40)
                    
                    confirm = input(f"\n✅ Update Anohra's prompt? (y/n): ").lower()
                    if confirm == 'y':
                        if self.update_prompt(new_prompt):
                            current_prompt = new_prompt
                            print(f"✅ Prompt updated successfully!")
                        else:
                            print(f"❌ Failed to update prompt")
                
            elif choice == "3":
                addition = input(f"\n📝 Enter text to add to current prompt: ")
                new_prompt = current_prompt + "\n\n" + addition
                
                if self.update_prompt(new_prompt):
                    current_prompt = new_prompt
                    print(f"✅ Addition successful!")
                
            elif choice == "4":
                self._show_prompt_templates()
                
            elif choice == "5":
                self._test_prompt()
                
            elif choice == "6":
                print(f"👋 Goodbye!")
                break
                
            else:
                print(f"❌ Invalid choice")
    
    def _show_prompt_templates(self):
        """Show prompt templates for common modifications"""
        templates = {
            "1": {
                "name": "Add Hindi Fluency",
                "text": "\n• Always respond in Hindi when the caller speaks Hindi\n• Use professional medical Hindi terminology\n• Be warm and empathetic in Hindi conversations"
            },
            "2": {
                "name": "Emergency Handling",
                "text": "\n• For emergency cases, immediately escalate to Dr. Murali\n• Ask for emergency contact details\n• Provide calm, reassuring guidance while arranging immediate care"
            },
            "3": {
                "name": "Appointment Scheduling",
                "text": "\n• Check Dr. Murali's availability before confirming appointments\n• Always confirm date, time, and patient details\n• Send appointment confirmation via SMS/email"
            },
            "4": {
                "name": "Professional Closing",
                "text": "\n• End every call with: 'Thank you for calling Dr. Murali's clinic'\n• Offer assistance for any follow-up questions\n• Mention clinic hours and emergency contact if needed"
            }
        }
        
        print(f"\n📋 Quick Templates:")
        for key, template in templates.items():
            print(f"{key}. {template['name']}")
        
        choice = input(f"\nSelect template to add (1-4) or 'back': ").strip()
        
        if choice in templates:
            return templates[choice]['text']
        else:
            return None
    
    def _test_prompt(self):
        """Test the current prompt with a sample call"""
        print(f"\n📞 Testing current prompt with sample call...")
        
        # Use our working call method
        try:
            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "agent_id": self.anohra_id,
                "message": {
                    "role": "user",
                    "content": "Hello, I need to book an appointment with Dr. Murali for knee pain"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/latest/agents/trigger",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test initiated successfully!")
                print(f"📞 Conversation ID: {result.get('conversation_id')}")
                print(f"💡 This would start a conversation using the current prompt")
            else:
                print(f"❌ Test failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")

def main():
    """Main function"""
    editor = AnohraPromptEditor()
    
    print(f"🤖 Welcome to Anohra Prompt Editor!")
    print(f"Agent ID: {editor.anohra_id}")
    print(f"Project: {editor.project_id}")
    
    # Start interactive editor
    editor.interactive_prompt_editor()

if __name__ == "__main__":
    main()