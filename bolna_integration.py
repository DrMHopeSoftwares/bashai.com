"""
Bolna API Integration Module
Handles outbound calls through Bolna AI voice agent platform
"""

import os
import requests
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class BolnaAPI:
    def __init__(self):
        self.base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
        self.api_key = os.getenv('BOLNA_API_KEY')
        self.default_sender_phone = os.getenv('BOLNA_SENDER_PHONE', '+918035743222')
        
        if not self.api_key:
            raise ValueError("BOLNA_API_KEY environment variable is required")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to Bolna API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Bolna API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise
    
    def start_outbound_call(self, 
                           agent_id: str,
                           recipient_phone: str,
                           sender_phone: str = None,
                           variables: Dict[str, Any] = None,
                           metadata: Dict[str, Any] = None) -> Dict:
        """
        Start an outbound call using Bolna API
        
        Args:
            agent_id: Bolna agent ID (e.g., "15554373-b8e1-4b00-8c25-c4742dc8e480")
            recipient_phone: Phone number to call (in E.164 format)
            sender_phone: Phone number to call from (defaults to configured sender)
            variables: Key-value pairs for agent conversation context
            metadata: Additional metadata for the call
            
        Returns:
            Dict containing call response from Bolna API
        """
        if not sender_phone:
            sender_phone = self.default_sender_phone
        
        # Ensure phone numbers are in E.164 format
        if not recipient_phone.startswith('+'):
            recipient_phone = f'+{recipient_phone}'
        if not sender_phone.startswith('+'):
            sender_phone = f'+{sender_phone}'
        
        call_data = {
            'agent_id': agent_id,
            'recipient_phone_number': recipient_phone,
            'from_phone_number': sender_phone,
            'variables': variables or {},
            'metadata': {
                'call_initiated_at': datetime.utcnow().isoformat(),
                'source': 'drmhope_saas_platform',
                **(metadata or {})
            }
        }
        
        try:
            response = self._make_request('POST', '/call', call_data)
            print(f"Bolna call started successfully: {response}")
            return response
        except Exception as e:
            print(f"Failed to start Bolna call: {e}")
            raise
    
    def get_call_status(self, call_id: str) -> Dict:
        """Get status of a specific call"""
        try:
            response = self._make_request('GET', f'/call/{call_id}/status')
            return response
        except Exception as e:
            print(f"Failed to get call status: {e}")
            raise
    
    def list_agents(self) -> List[Dict]:
        """List all available Bolna agents"""
        try:
            response = self._make_request('GET', '/v2/agent/all')
            return response.get('agents', []) if isinstance(response, dict) else response
        except Exception as e:
            print(f"Failed to list agents: {e}")
            raise
    
    def get_agent_details(self, agent_id: str) -> Dict:
        """Get details of a specific agent"""
        try:
            response = self._make_request('GET', f'/v2/agent?agent_id={agent_id}')
            return response
        except Exception as e:
            print(f"Failed to get agent details: {e}")
            raise
    
    def bulk_start_calls(self, calls: List[Dict]) -> List[Dict]:
        """
        Start multiple outbound calls
        
        Args:
            calls: List of call configurations, each containing:
                - agent_id: str
                - recipient_phone: str
                - sender_phone: str (optional)
                - variables: Dict (optional)
                - metadata: Dict (optional)
        
        Returns:
            List of call responses
        """
        results = []
        
        for i, call_config in enumerate(calls):
            try:
                print(f"Starting call {i+1}/{len(calls)} to {call_config.get('recipient_phone')}")
                
                result = self.start_outbound_call(
                    agent_id=call_config['agent_id'],
                    recipient_phone=call_config['recipient_phone'],
                    sender_phone=call_config.get('sender_phone'),
                    variables=call_config.get('variables', {}),
                    metadata=call_config.get('metadata', {})
                )
                
                result['success'] = True
                result['original_config'] = call_config
                results.append(result)
                
            except Exception as e:
                error_result = {
                    'success': False,
                    'error': str(e),
                    'original_config': call_config
                }
                results.append(error_result)
                print(f"Failed to start call to {call_config.get('recipient_phone')}: {e}")
        
        return results

# Default agent configurations based on your voice agents
DEFAULT_AGENT_CONFIGS = {
    'patient_appointment_booking': {
        'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',
        'sender_phone': '+918035743222',
        'default_variables': {
            'greeting': 'Hello, this is an automated call from Ayushmann Healthcare for appointment booking.',
            'purpose': 'appointment_booking',
            'language': 'hinglish'
        }
    },
    'prescription_reminder': {
        'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',  # Same agent, different context
        'sender_phone': '+918035743222',
        'default_variables': {
            'greeting': 'Hello, this is a reminder call from Ayushmann Healthcare about your prescription.',
            'purpose': 'prescription_reminder',
            'language': 'hinglish'
        }
    },
    'delivery_followup': {
        'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',  # Same agent, different context
        'sender_phone': '+918035743222',
        'default_variables': {
            'greeting': 'Hello, this is a call from Raftaar Logistics regarding your delivery.',
            'purpose': 'delivery_followup',
            'language': 'hinglish'
        }
    }
}

def get_agent_config_for_voice_agent(voice_agent, custom_config: Dict = None) -> Dict:
    """Get Bolna agent configuration based on voice agent data and custom configuration
    
    Args:
        voice_agent: Can be either a string (title) or dict (voice agent object)
        custom_config: Optional custom configuration to override defaults
    """
    # Handle both string (legacy) and dict (new) inputs
    if isinstance(voice_agent, str):
        title_lower = voice_agent.lower()
        calling_number = None
    else:
        title_lower = voice_agent.get('title', '').lower()
        calling_number = voice_agent.get('calling_number')
    
    # Get base configuration
    if 'appointment' in title_lower or 'booking' in title_lower:
        base_config = DEFAULT_AGENT_CONFIGS['patient_appointment_booking'].copy()
    elif 'prescription' in title_lower or 'reminder' in title_lower:
        base_config = DEFAULT_AGENT_CONFIGS['prescription_reminder'].copy()
    elif 'delivery' in title_lower or 'followup' in title_lower or 'follow-up' in title_lower:
        base_config = DEFAULT_AGENT_CONFIGS['delivery_followup'].copy()
    else:
        # Default to appointment booking if no match
        base_config = DEFAULT_AGENT_CONFIGS['patient_appointment_booking'].copy()
    
    # Use agent's calling number if available, otherwise use default
    if calling_number:
        base_config['sender_phone'] = calling_number
    
    # Override with custom configuration if provided
    if custom_config:
        # Update default variables with custom ones
        if 'welcome_message' in custom_config and custom_config['welcome_message']:
            base_config['default_variables']['greeting'] = custom_config['welcome_message']
        
        if 'agent_prompt' in custom_config and custom_config['agent_prompt']:
            base_config['default_variables']['agent_prompt'] = custom_config['agent_prompt']
        
        if 'conversation_style' in custom_config and custom_config['conversation_style']:
            base_config['default_variables']['conversation_style'] = custom_config['conversation_style']
        
        if 'language_preference' in custom_config and custom_config['language_preference']:
            base_config['default_variables']['language'] = custom_config['language_preference']
            
        # Allow custom calling number override
        if 'calling_number' in custom_config and custom_config['calling_number']:
            base_config['sender_phone'] = custom_config['calling_number']
    
    return base_config

def create_personalized_variables(base_variables: Dict, contact: Dict, agent_config: Dict, custom_config: Dict = None) -> Dict:
    """Create personalized variables for each contact including custom prompts"""
    variables = {
        **base_variables,
        'contact_name': contact.get('name', 'User'),
        'contact_phone': contact.get('phone', ''),
    }
    
    # Add custom configuration if provided
    if custom_config:
        if custom_config.get('welcome_message'):
            # Personalize welcome message with contact name
            welcome_msg = custom_config['welcome_message']
            if '{contact_name}' in welcome_msg:
                variables['greeting'] = welcome_msg.replace('{contact_name}', contact.get('name', 'User'))
            else:
                variables['greeting'] = welcome_msg
        
        if custom_config.get('agent_prompt'):
            variables['system_prompt'] = custom_config['agent_prompt']
        
        if custom_config.get('conversation_style'):
            variables['conversation_style'] = custom_config['conversation_style']
        
        if custom_config.get('language_preference'):
            variables['language'] = custom_config['language_preference']
    
    return variables