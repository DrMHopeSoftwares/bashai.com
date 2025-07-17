"""
Relevance AI Integration Module
Handles multi-agent AI workflows and automation through Relevance AI platform
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Try to import the official RelevanceAI SDK
try:
    from relevanceai import RelevanceAI
    RELEVANCE_SDK_AVAILABLE = True
except ImportError:
    print("⚠️  RelevanceAI SDK not installed. Run: pip install relevanceai")
    RELEVANCE_SDK_AVAILABLE = False

class RelevanceAIProvider:
    def __init__(self):
        self.api_key = os.getenv('RELEVANCE_AI_API_KEY')
        self.region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c')
        self.project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
        
        if not self.api_key:
            raise ValueError("RELEVANCE_AI_API_KEY environment variable is required")
        
        if not RELEVANCE_SDK_AVAILABLE:
            raise ImportError("RelevanceAI SDK not available. Install with: pip install relevanceai")
        
        # Initialize the RelevanceAI client
        try:
            # Set the API key as environment variable (RelevanceAI SDK expects this)
            os.environ['RELEVANCE_API_KEY'] = self.api_key
            self.client = RelevanceAI()
            print("✅ RelevanceAI SDK client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize RelevanceAI client: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to Relevance AI"""
        try:
            # Try to list agents to test connection
            agents = self.client.agents.list()
            print("✅ Relevance AI connection successful")
            return True
        except Exception as e:
            print(f"❌ Relevance AI connection failed: {e}")
            return False
    
    def create_agent(self, agent_config: Dict) -> Dict:
        """Create a new AI agent in Relevance AI"""
        payload = {
            "name": agent_config.get('name', 'BhashAI Agent'),
            "description": agent_config.get('description', 'AI agent created via BhashAI platform'),
            "type": agent_config.get('type', 'conversational'),
            "config": {
                "language": agent_config.get('language', 'hindi'),
                "personality": agent_config.get('personality', 'professional'),
                "use_case": agent_config.get('use_case', 'general'),
                "tools": agent_config.get('tools', []),
                "integrations": agent_config.get('integrations', [])
            },
            "project_id": self.project_id
        }
        
        try:
            response = self._make_request('POST', 'agents', data=payload)
            print(f"✅ Relevance AI agent created: {response.get('id', 'unknown')}")
            return response
        except Exception as e:
            print(f"❌ Failed to create Relevance AI agent: {e}")
            raise
    
    def get_agent(self, agent_id: str) -> Dict:
        """Get agent details by ID"""
        try:
            return self._make_request('GET', f'agents/{agent_id}')
        except Exception as e:
            print(f"❌ Failed to get agent {agent_id}: {e}")
            raise
    
    def update_agent(self, agent_id: str, updates: Dict) -> Dict:
        """Update an existing agent"""
        try:
            return self._make_request('PUT', f'agents/{agent_id}', data=updates)
        except Exception as e:
            print(f"❌ Failed to update agent {agent_id}: {e}")
            raise
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        try:
            self._make_request('DELETE', f'agents/{agent_id}')
            print(f"✅ Agent {agent_id} deleted successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to delete agent {agent_id}: {e}")
            return False
    
    def create_session(self, agent_id: str, session_config: Dict = None) -> Dict:
        """Create a new conversation session with an agent"""
        payload = {
            "agent_id": agent_id,
            "session_id": str(uuid.uuid4()),
            "config": session_config or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = self._make_request('POST', f'agents/{agent_id}/sessions', data=payload)
            print(f"✅ Session created for agent {agent_id}: {response.get('session_id')}")
            return response
        except Exception as e:
            print(f"❌ Failed to create session for agent {agent_id}: {e}")
            raise
    
    def send_message(self, agent_id: str, session_id: str, message: str, context: Dict = None) -> Dict:
        """Send a message to an agent in a session"""
        payload = {
            "message": message,
            "session_id": session_id,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = self._make_request('POST', f'agents/{agent_id}/sessions/{session_id}/messages', data=payload)
            print(f"✅ Message sent to agent {agent_id}")
            return response
        except Exception as e:
            print(f"❌ Failed to send message to agent {agent_id}: {e}")
            raise
    
    def get_session_history(self, agent_id: str, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        try:
            response = self._make_request('GET', f'agents/{agent_id}/sessions/{session_id}/messages')
            return response.get('messages', [])
        except Exception as e:
            print(f"❌ Failed to get session history: {e}")
            return []
    
    def trigger_workflow(self, workflow_id: str, inputs: Dict) -> Dict:
        """Trigger a predefined workflow"""
        payload = {
            "workflow_id": workflow_id,
            "inputs": inputs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = self._make_request('POST', f'workflows/{workflow_id}/trigger', data=payload)
            print(f"✅ Workflow {workflow_id} triggered successfully")
            return response
        except Exception as e:
            print(f"❌ Failed to trigger workflow {workflow_id}: {e}")
            raise
    
    def create_tool(self, tool_config: Dict) -> Dict:
        """Create a custom tool for agents"""
        payload = {
            "name": tool_config.get('name'),
            "description": tool_config.get('description'),
            "type": tool_config.get('type', 'api'),
            "config": tool_config.get('config', {}),
            "project_id": self.project_id
        }
        
        try:
            response = self._make_request('POST', 'tools', data=payload)
            print(f"✅ Tool created: {response.get('id')}")
            return response
        except Exception as e:
            print(f"❌ Failed to create tool: {e}")
            raise
    
    def list_agents(self, limit: int = 50) -> List[Dict]:
        """List all agents in the project"""
        params = {
            'project_id': self.project_id,
            'limit': limit
        }
        
        try:
            response = self._make_request('GET', 'agents', params=params)
            return response.get('agents', [])
        except Exception as e:
            print(f"❌ Failed to list agents: {e}")
            return []
    
    def get_analytics(self, agent_id: str, date_range: Dict = None) -> Dict:
        """Get analytics data for an agent"""
        params = {
            'agent_id': agent_id
        }
        
        if date_range:
            params.update(date_range)
        
        try:
            response = self._make_request('GET', f'analytics/agents/{agent_id}', params=params)
            return response
        except Exception as e:
            print(f"❌ Failed to get analytics for agent {agent_id}: {e}")
            return {}
    
    def create_integration(self, integration_config: Dict) -> Dict:
        """Create an integration with external services"""
        payload = {
            "name": integration_config.get('name'),
            "type": integration_config.get('type'),  # slack, sheets, email, etc.
            "config": integration_config.get('config', {}),
            "project_id": self.project_id
        }
        
        try:
            response = self._make_request('POST', 'integrations', data=payload)
            print(f"✅ Integration created: {response.get('id')}")
            return response
        except Exception as e:
            print(f"❌ Failed to create integration: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to Relevance AI"""
        try:
            response = self._make_request('GET', 'health')
            print("✅ Relevance AI connection successful")
            return True
        except Exception as e:
            print(f"❌ Relevance AI connection failed: {e}")
            return False


class RelevanceAIAgentManager:
    """High-level manager for Relevance AI agents integrated with BhashAI"""
    
    def __init__(self):
        self.provider = RelevanceAIProvider()
    
    def create_voice_agent(self, voice_agent_data: Dict) -> Dict:
        """Create a Relevance AI agent optimized for voice interactions"""
        agent_config = {
            'name': voice_agent_data.get('name', 'Voice Assistant'),
            'description': voice_agent_data.get('description', 'AI voice assistant'),
            'type': 'conversational',
            'language': voice_agent_data.get('language', 'hindi'),
            'personality': voice_agent_data.get('personality', 'professional'),
            'use_case': voice_agent_data.get('use_case', 'customer_support'),
            'tools': self._get_default_tools(voice_agent_data.get('use_case')),
            'integrations': voice_agent_data.get('integrations', [])
        }
        
        return self.provider.create_agent(agent_config)
    
    def create_workflow_agent(self, workflow_data: Dict) -> Dict:
        """Create a Relevance AI agent for workflow automation"""
        agent_config = {
            'name': workflow_data.get('name', 'Workflow Assistant'),
            'description': workflow_data.get('description', 'AI workflow automation agent'),
            'type': 'workflow',
            'language': workflow_data.get('language', 'english'),
            'use_case': 'automation',
            'tools': self._get_workflow_tools(workflow_data.get('workflow_type')),
            'integrations': workflow_data.get('integrations', [])
        }
        
        return self.provider.create_agent(agent_config)
    
    def _get_default_tools(self, use_case: str) -> List[str]:
        """Get default tools based on use case"""
        tool_mapping = {
            'customer_support': ['knowledge_base', 'ticket_creation', 'escalation'],
            'appointment_booking': ['calendar_access', 'availability_check', 'booking_confirmation'],
            'sales': ['lead_qualification', 'product_information', 'follow_up_scheduling'],
            'technical_support': ['troubleshooting', 'documentation_search', 'remote_assistance']
        }
        
        return tool_mapping.get(use_case, ['knowledge_base', 'general_conversation'])
    
    def _get_workflow_tools(self, workflow_type: str) -> List[str]:
        """Get tools for workflow automation"""
        workflow_tools = {
            'data_processing': ['data_extraction', 'data_validation', 'data_transformation'],
            'customer_onboarding': ['form_processing', 'document_verification', 'welcome_sequence'],
            'lead_nurturing': ['email_automation', 'lead_scoring', 'crm_integration'],
            'content_generation': ['content_creation', 'seo_optimization', 'social_media_posting']
        }
        
        return workflow_tools.get(workflow_type, ['general_automation'])
    
    def handle_voice_call(self, agent_id: str, call_data: Dict) -> Dict:
        """Handle an incoming voice call with Relevance AI agent"""
        session = self.provider.create_session(agent_id, {
            'channel': 'voice',
            'phone_number': call_data.get('phone_number'),
            'call_id': call_data.get('call_id')
        })
        
        # Process initial greeting
        initial_message = call_data.get('initial_message', 'नमस्ते! मैं आपकी कैसे सहायता कर सकता हूं?')
        
        response = self.provider.send_message(
            agent_id=agent_id,
            session_id=session['session_id'],
            message=initial_message,
            context={
                'channel': 'voice',
                'language': 'hindi',
                'call_metadata': call_data
            }
        )
        
        return {
            'session_id': session['session_id'],
            'response': response,
            'status': 'active'
        }
    
    def process_conversation_turn(self, agent_id: str, session_id: str, user_input: str, context: Dict = None) -> Dict:
        """Process a conversation turn in an ongoing session"""
        return self.provider.send_message(
            agent_id=agent_id,
            session_id=session_id,
            message=user_input,
            context=context or {}
        )


# Helper functions for easy integration
def create_relevance_agent_config(voice_agent_data: Dict) -> Dict:
    """Create Relevance AI configuration from BhashAI voice agent data"""
    return {
        'relevance_ai_config': {
            'agent_type': voice_agent_data.get('agent_type', 'single'),
            'tools': voice_agent_data.get('tools', []),
            'integrations': voice_agent_data.get('integrations', []),
            'personality': voice_agent_data.get('personality', 'professional'),
            'response_style': voice_agent_data.get('response_style', 'conversational')
        }
    }

def get_relevance_agent_for_voice_agent(voice_agent_id: str) -> Optional[Dict]:
    """Get Relevance AI agent configuration for a BhashAI voice agent"""
    try:
        manager = RelevanceAIAgentManager()
        # This would typically query your database to get the relevance_ai_agent_id
        # For now, we'll return a placeholder
        return {
            'agent_id': f'relevance_{voice_agent_id}',
            'status': 'active',
            'capabilities': ['conversation', 'workflow', 'integration']
        }
    except Exception as e:
        print(f"Error getting Relevance AI agent: {e}")
        return None

# Test function
def test_relevance_ai_integration():
    """Test the Relevance AI integration"""
    try:
        provider = RelevanceAIProvider()
        
        # Test connection
        if not provider.test_connection():
            print("❌ Connection test failed")
            return False
        
        # Test agent creation
        test_agent = provider.create_agent({
            'name': 'Test BhashAI Agent',
            'description': 'Test agent for integration verification',
            'language': 'hindi',
            'use_case': 'testing'
        })
        
        print(f"✅ Test agent created: {test_agent.get('id')}")
        
        # Clean up test agent
        if test_agent.get('id'):
            provider.delete_agent(test_agent['id'])
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Run integration test
    print("🧪 Testing Relevance AI Integration...")
    success = test_relevance_ai_integration()
    print(f"{'✅ Integration test passed!' if success else '❌ Integration test failed!'}")