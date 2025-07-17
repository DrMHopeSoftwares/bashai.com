#!/usr/bin/env python3
"""
Find and Interact with "anohra" RelevanceAI Agent
This script searches for the "anohra" agent and demonstrates how to interact with it.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from relevance_ai_integration_fixed import RelevanceAIProvider, RelevanceAIAgentManager
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import RelevanceAI integration: {e}")
    INTEGRATION_AVAILABLE = False

class AnoiraAgentFinder:
    def __init__(self):
        if not INTEGRATION_AVAILABLE:
            raise ImportError("RelevanceAI integration not available")
        
        self.provider = RelevanceAIProvider()
        self.anohra_agent = None
        self.session_id = None
    
    def find_anohra_agent(self):
        """Find the 'anohra' agent by searching through all agents"""
        print("🔍 Searching for 'anohra' agent...")
        
        try:
            # Get all agents
            agents = self.provider.list_agents()
            print(f"📋 Found {len(agents)} total agents")
            
            # Search for anohra agent (case-insensitive)
            anohra_agents = []
            for agent in agents:
                agent_name = agent.get('name', '').lower()
                if 'anohra' in agent_name or 'anoira' in agent_name:
                    anohra_agents.append(agent)
                    print(f"✅ Found potential match: {agent.get('name')} (ID: {agent.get('id')})")
            
            if not anohra_agents:
                print("❌ No 'anohra' agent found")
                print("\n📋 Available agents:")
                for i, agent in enumerate(agents, 1):
                    print(f"   {i}. {agent.get('name')} (ID: {agent.get('id')})")
                return None
            
            # If multiple matches, use the first one or let user choose
            if len(anohra_agents) == 1:
                self.anohra_agent = anohra_agents[0]
                print(f"✅ Selected anohra agent: {self.anohra_agent.get('name')} (ID: {self.anohra_agent.get('id')})")
                return self.anohra_agent
            else:
                print(f"\n🔄 Found {len(anohra_agents)} potential anohra agents:")
                for i, agent in enumerate(anohra_agents, 1):
                    print(f"   {i}. {agent.get('name')} (ID: {agent.get('id')})")
                
                # Use first one for now
                self.anohra_agent = anohra_agents[0]
                print(f"✅ Using first match: {self.anohra_agent.get('name')}")
                return self.anohra_agent
        
        except Exception as e:
            print(f"❌ Error searching for anohra agent: {e}")
            return None
    
    def get_agent_details(self):
        """Get detailed information about the anohra agent"""
        if not self.anohra_agent:
            print("❌ No anohra agent selected")
            return None
        
        print(f"\n📊 Getting details for agent: {self.anohra_agent.get('name')}")
        
        try:
            agent_id = self.anohra_agent.get('id')
            agent_details = self.provider.get_agent(agent_id)
            
            print(f"📋 Agent Details:")
            print(f"   • ID: {agent_details.get('id')}")
            print(f"   • Name: {agent_details.get('name')}")
            print(f"   • Status: {agent_details.get('status')}")
            
            # Try to get additional info from agent_data
            agent_data = agent_details.get('agent_data')
            if agent_data:
                if hasattr(agent_data, '__dict__'):
                    print(f"   • Type: {type(agent_data).__name__}")
                    for attr in ['description', 'model', 'created_at', 'updated_at']:
                        if hasattr(agent_data, attr):
                            value = getattr(agent_data, attr)
                            print(f"   • {attr.title()}: {value}")
                elif isinstance(agent_data, dict):
                    for key in ['description', 'model', 'created_at', 'updated_at']:
                        if key in agent_data:
                            print(f"   • {key.title()}: {agent_data[key]}")
            
            return agent_details
        
        except Exception as e:
            print(f"❌ Error getting agent details: {e}")
            return None
    
    def create_session_with_anohra(self):
        """Create a conversation session with the anohra agent"""
        if not self.anohra_agent:
            print("❌ No anohra agent selected")
            return None
        
        print(f"\n🔄 Creating session with anohra agent...")
        
        try:
            agent_id = self.anohra_agent.get('id')
            
            session_config = {
                'purpose': 'testing_anohra_interaction',
                'created_by': 'find_anohra_script',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            session = self.provider.create_session(agent_id, session_config)
            self.session_id = session.get('session_id')
            
            print(f"✅ Session created successfully!")
            print(f"   • Session ID: {self.session_id}")
            print(f"   • Agent ID: {agent_id}")
            print(f"   • Status: {session.get('status')}")
            
            return session
        
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return None
    
    def send_test_message(self, message="Hello, anohra! How are you?"):
        """Send a test message to the anohra agent"""
        if not self.anohra_agent or not self.session_id:
            print("❌ No active session with anohra agent")
            return None
        
        print(f"\n💬 Sending message to anohra: '{message}'")
        
        try:
            agent_id = self.anohra_agent.get('id')
            
            context = {
                'channel': 'script',
                'purpose': 'testing',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = self.provider.send_message(
                agent_id=agent_id,
                session_id=self.session_id,
                message=message,
                context=context
            )
            
            print(f"✅ Message sent successfully!")
            print(f"📨 Response: {response.get('response', 'No response')}")
            print(f"📅 Timestamp: {response.get('timestamp')}")
            
            return response
        
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
    
    def interactive_chat(self):
        """Start an interactive chat session with anohra"""
        if not self.anohra_agent or not self.session_id:
            print("❌ No active session with anohra agent")
            return
        
        print(f"\n💬 Starting interactive chat with {self.anohra_agent.get('name')}")
        print("Type 'quit' to exit the chat")
        print("-" * 50)
        
        try:
            while True:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Send message to anohra
                response = self.send_test_message(user_input)
                
                if response:
                    agent_response = response.get('response', 'No response received')
                    print(f"🤖 Anohra: {agent_response}")
                else:
                    print("❌ Failed to get response from anohra")
        
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
        except Exception as e:
            print(f"❌ Chat error: {e}")
    
    def run_complete_demo(self):
        """Run a complete demonstration of finding and interacting with anohra"""
        print("🚀 Starting Anohra Agent Demo")
        print("=" * 60)
        
        # Step 1: Test connection
        print("\n1️⃣ Testing RelevanceAI connection...")
        if not self.provider.test_connection():
            print("❌ Failed to connect to RelevanceAI. Check your credentials.")
            return False
        
        # Step 2: Find anohra agent
        print("\n2️⃣ Finding anohra agent...")
        if not self.find_anohra_agent():
            print("❌ Could not find anohra agent")
            return False
        
        # Step 3: Get agent details
        print("\n3️⃣ Getting agent details...")
        self.get_agent_details()
        
        # Step 4: Create session
        print("\n4️⃣ Creating session...")
        if not self.create_session_with_anohra():
            print("❌ Failed to create session")
            return False
        
        # Step 5: Send test message
        print("\n5️⃣ Sending test message...")
        self.send_test_message("Hello anohra! I'm testing our connection.")
        
        # Step 6: Optional interactive chat
        print("\n6️⃣ Interactive Chat (optional)")
        user_choice = input("Would you like to start an interactive chat? (y/n): ").strip().lower()
        if user_choice in ['y', 'yes']:
            self.interactive_chat()
        
        print("\n✅ Demo completed successfully!")
        return True

def main():
    """Main function"""
    print("🔍 Anohra Agent Finder & Interaction Tool")
    print("This script helps you find and interact with the 'anohra' RelevanceAI agent")
    print("=" * 70)
    
    # Check environment
    required_vars = ['RELEVANCE_AI_API_KEY', 'RELEVANCE_AI_REGION', 'RELEVANCE_AI_PROJECT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return 1
    
    if not INTEGRATION_AVAILABLE:
        print("❌ RelevanceAI integration not available")
        print("Please ensure the integration module is properly installed")
        return 1
    
    try:
        # Create finder and run demo
        finder = AnoiraAgentFinder()
        success = finder.run_complete_demo()
        
        if success:
            print("\n🎉 Successfully found and interacted with anohra agent!")
            print("\n📋 What you can do next:")
            print("• Use the agent ID to integrate anohra into your application")
            print("• Create multiple sessions for different conversations")  
            print("• Send messages programmatically using the send_message method")
            print("• Monitor session analytics and performance")
            return 0
        else:
            print("\n❌ Demo failed. Please check the errors above.")
            return 1
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)