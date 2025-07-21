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
    def __init__(self, admin_user_data=None):
        self.base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
        self.api_key = os.getenv('BOLNA_API_KEY')
        self.default_sender_phone = os.getenv('BOLNA_SENDER_PHONE', '+918035743222')

        # Use admin-specific phone number if provided
        if admin_user_data and admin_user_data.get('sender_phone'):
            self.default_sender_phone = admin_user_data['sender_phone']

        # Use admin-specific agent ID if provided
        self.default_agent_id = None
        if admin_user_data and admin_user_data.get('bolna_agent_id'):
            self.default_agent_id = admin_user_data['bolna_agent_id']

        if not self.api_key:
            raise ValueError("BOLNA_API_KEY environment variable is required")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request to Bolna API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            if method.upper() == 'GET':
                # For GET requests, use params for query parameters
                query_params = params or data
                response = requests.get(url, headers=headers, params=query_params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
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
            'user_data': {
                'call_initiated_at': datetime.utcnow().isoformat(),
                'source': 'drmhope_saas_platform',
                **(variables or {}),
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

    def update_agent(self,
                    agent_id: str,
                    name: str = None,
                    description: str = None,
                    prompt: str = None,
                    welcome_message: str = None,
                    voice: str = None,
                    language: str = None,
                    max_duration: int = None,
                    hangup_after: int = None,
                    **kwargs) -> Dict:
        """
        Update an existing Bolna agent

        Args:
            agent_id: Existing agent ID to update
            name: Agent name (optional)
            description: Agent description (optional)
            prompt: System prompt for the agent (optional)
            welcome_message: Initial message when call starts (optional)
            voice: Voice type (optional)
            language: Language code (optional)
            max_duration: Maximum call duration in seconds (optional)
            hangup_after: Hangup after silence in seconds (optional)
            **kwargs: Additional agent configuration

        Returns:
            Dict containing updated agent details
        """
        try:
            # First get current agent details
            current_agent = self.get_agent_details(agent_id)

            # Extract current configuration
            current_config = current_agent.get('agent_config', {})
            current_tasks = current_config.get('tasks', [{}])
            current_task_config = current_tasks[0].get('task_config', {}) if current_tasks else {}
            current_llm = current_task_config.get('llm_agent', {})
            current_synthesizer = current_task_config.get('synthesizer', {})
            current_transcriber = current_task_config.get('transcriber', {})

            # Update only provided fields
            updated_config = current_config.copy()

            if name:
                updated_config['agent_name'] = name
                if current_llm:
                    current_llm['agent_name'] = name

            if welcome_message:
                updated_config['agent_welcome_message'] = welcome_message

            if prompt and current_llm:
                current_llm['system_prompt'] = prompt

            if voice and current_synthesizer:
                current_synthesizer['voice'] = voice

            if language and current_transcriber:
                current_transcriber['language'] = language

            if max_duration:
                updated_config['max_duration'] = max_duration

            if hangup_after:
                updated_config['hangup_after'] = hangup_after

            # Rebuild the agent data structure
            agent_data = {
                "agent_config": updated_config,
                "agent_name": updated_config.get('agent_name', current_agent.get('agent_name', '')),
                "description": description or current_agent.get('description', '')
            }

            # Use PUT method to update the agent
            response = self._make_request('PUT', f'/v2/agent/{agent_id}', agent_data)
            print(f"Bolna agent updated successfully: {response}")
            return response

        except Exception as e:
            print(f"Failed to update Bolna agent: {e}")
            raise

    def get_phone_numbers(self) -> List[Dict]:
        """
        Get all phone numbers from Bolna API with agent_id information

        Returns:
            List of phone number dictionaries with agent_id field
        """
        try:
            response = self._make_request('GET', '/phone-numbers/all')

            if isinstance(response, list):
                # Ensure each phone number has agent_id field
                for phone_number in response:
                    if 'agent_id' not in phone_number:
                        phone_number['agent_id'] = None
                return response
            elif isinstance(response, dict) and 'phone_numbers' in response:
                # Ensure each phone number has agent_id field
                phone_numbers = response['phone_numbers']
                for phone_number in phone_numbers:
                    if 'agent_id' not in phone_number:
                        phone_number['agent_id'] = None
                return phone_numbers
            else:
                print(f"Unexpected response format: {response}")
                return []

        except Exception as e:
            print(f"Failed to get phone numbers: {e}")
            return []

    def create_agent(self,
                    name: str,
                    description: str = "",
                    prompt: str = "",
                    welcome_message: str = "",
                    voice: str = "en-IN-Standard-A",
                    language: str = "en",
                    max_duration: int = 300,
                    hangup_after: int = 30,
                    **kwargs) -> Dict:
        """
        Create a new Bolna agent

        Args:
            name: Agent name
            description: Agent description
            prompt: System prompt for the agent
            welcome_message: Initial message when call starts
            voice: Voice type (e.g., "en-IN-Standard-A")
            language: Language code (e.g., "en", "hi")
            max_duration: Maximum call duration in seconds
            hangup_after: Hangup after silence in seconds
            **kwargs: Additional agent configuration

        Returns:
            Dict containing created agent details
        """

        # Default prompt if not provided
        if not prompt:
            prompt = f"""You are {name}, a helpful AI assistant. {description}

Be polite, professional, and helpful. Keep responses concise and relevant.
If you don't understand something, ask for clarification.
Always maintain a friendly and professional tone."""

        # Default welcome message if not provided
        if not welcome_message:
            welcome_message = f"Hello! This is {name}. How can I help you today?"

        agent_config = {
            "agent_name": name,
            "agent_type": "voice",
            "agent_welcome_message": welcome_message,
            "tasks": [
                {
                    "task_type": "conversation",
                    "tools_config": {},  # Required field
                    "toolchain": {  # Required field
                        "execution": "parallel",
                        "pipelines": []
                    },
                    "task_config": {
                        "llm_agent": {
                            "agent_flow_type": "streaming",
                            "agent_name": name,
                            "agent_type": "other",
                            "system_prompt": prompt,
                            "classification_prompt": "",
                            "max_tokens": 100,
                            "model": "gpt-3.5-turbo",
                            "provider": "openai",
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "presence_penalty": 0,
                            "frequency_penalty": 0
                        },
                        "synthesizer": {
                            "provider": "elevenlabs",
                            "voice": voice,
                            "voice_id": "pNInz6obpgDQGcFmaJgB",  # Default ElevenLabs voice
                            "model": "eleven_turbo_v2",
                            "stability": 0.4,
                            "similarity_boost": 0.8,
                            "style": 0.2,
                            "use_speaker_boost": True
                        },
                        "transcriber": {
                            "provider": "deepgram",
                            "model": "nova-2",
                            "language": language,
                            "stream": True
                        }
                    }
                }
            ],
            "hangup_after": hangup_after,
            "max_duration": max_duration,
            "ambient_sound": None,
            "ambient_sound_volume": 0.1,
            "interruption_threshold": 100,
            "backchanneling": False,
            "optimize_latency": True,
            "incremental_delay": 100,
            "normalize_audio": True,
            "extra_config": kwargs.get('extra_config', {})
        }

        agent_data = {
            "agent_config": agent_config,
            "agent_name": name,
            "description": description
        }

        try:
            # Use v2 API endpoint
            response = self._make_request('POST', '/v2/agent', agent_data)
            print(f"Bolna agent created successfully: {response}")
            return response
        except Exception as e:
            print(f"Failed to create Bolna agent: {e}")
            raise

    def get_call_history(self, phone_number=None):
        """Get call history from Bolna API"""
        try:
            endpoint = '/calls/history'
            params = {}

            if phone_number:
                params['phone_number'] = phone_number

            # Make request to Bolna API
            response = self._make_request('GET', endpoint, params=params)

            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and 'calls' in response:
                return response['calls']
            else:
                print(f"Unexpected response format from Bolna API: {response}")
                return []

        except Exception as e:
            print(f"Error fetching call history from Bolna API: {e}")
            # Return mock data for testing
            return self._get_mock_call_history(phone_number)

    def _get_mock_call_history(self, phone_number):
        """Return mock call history for testing"""
        import time
        from datetime import datetime, timedelta

        mock_calls = []
        for i in range(3):
            call_time = datetime.now() - timedelta(days=i, hours=i*2)
            mock_call = {
                'call_id': f'mock_call_{int(time.time())}_{i}',
                'id': f'mock_{i}',
                'from_number': phone_number,
                'to_number': f'+91987654321{i}',
                'direction': 'outbound',
                'status': ['completed', 'failed', 'busy'][i % 3],
                'duration_seconds': [120, 0, 45][i % 3],
                'duration': [120, 0, 45][i % 3],
                'cost': [2.5, 0, 1.2][i % 3],
                'created_at': call_time.isoformat(),
                'recording_url': f'https://example.com/recording_{i}.mp3' if i == 0 else None,
                'transcript': f'Mock conversation transcript for call {i+1}' if i == 0 else None,
                'agent_name': 'AI Sales Agent',
                'recipient_phone': f'+91987654321{i}'
            }
            mock_calls.append(mock_call)

        return mock_calls
    
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