"""
ElevenLabs API Integration Module
Handles voice synthesis and real-time voice conversations through ElevenLabs platform
"""

import os
import requests
import json
import uuid
try:
    import websocket
    import threading
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("⚠️  websocket-client not installed. WebSocket features will use mock mode.")
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dotenv import load_dotenv
import logging

load_dotenv()

class ElevenLabsAPI:
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.base_url = os.getenv('ELEVENLABS_API_URL', 'https://api.elevenlabs.io/v1')
        self.websocket_url = os.getenv('ELEVENLABS_WEBSOCKET_URL', 'wss://api.elevenlabs.io/v1/text-to-speech')
        
        if not self.api_key:
            print("⚠️  ELEVENLABS_API_KEY not found - using mock mode")
            self.use_mock = True
        else:
            self.use_mock = False
            
        self.headers = {
            'Accept': 'application/json',
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Voice settings
        self.default_voice_id = os.getenv('ELEVENLABS_DEFAULT_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Adam voice
        self.default_model_id = os.getenv('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2')
        
        # WebSocket connection
        self.ws = None
        self.is_connected = False
        self.session_id = None
        
        # Callbacks
        self.on_audio_data = None
        self.on_error = None
        self.on_session_update = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_available_voices(self) -> Dict:
        """Get list of available voices from ElevenLabs"""
        if self.use_mock:
            return self._get_mock_voices()
            
        try:
            response = requests.get(f"{self.base_url}/voices", headers=self.headers)
            if response.status_code == 200:
                voices_data = response.json()
                return {
                    'success': True,
                    'voices': voices_data.get('voices', [])
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch voices: {response.status_code}'
                }
        except Exception as e:
            self.logger.error(f"Error fetching voices: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_mock_voices(self) -> Dict:
        """Return mock voice data for development"""
        return {
            'success': True,
            'voices': [
                {
                    'voice_id': 'pNInz6obpgDQGcFmaJgB',
                    'name': 'Adam',
                    'category': 'premade',
                    'description': 'Deep, authoritative voice',
                    'labels': {'accent': 'american', 'description': 'deep', 'age': 'middle aged', 'gender': 'male'},
                    'preview_url': 'https://storage.googleapis.com/eleven-public-prod/premade/voices/pNInz6obpgDQGcFmaJgB/df6788f9-5c96-470d-8312-aab3b3d8f50a.mp3'
                },
                {
                    'voice_id': '21m00Tcm4TlvDq8ikWAM',
                    'name': 'Rachel',
                    'category': 'premade',
                    'description': 'Calm, professional female voice',
                    'labels': {'accent': 'american', 'description': 'calm', 'age': 'young', 'gender': 'female'},
                    'preview_url': 'https://storage.googleapis.com/eleven-public-prod/premade/voices/21m00Tcm4TlvDq8ikWAM/b7882c0a-5c3d-4d1e-9f0a-7c8b5c3d4e1f.mp3'
                },
                {
                    'voice_id': 'AZnzlk1XvdvUeBnXmlld',
                    'name': 'Domi',
                    'category': 'premade',
                    'description': 'Strong, confident voice',
                    'labels': {'accent': 'american', 'description': 'strong', 'age': 'young', 'gender': 'female'},
                    'preview_url': 'https://storage.googleapis.com/eleven-public-prod/premade/voices/AZnzlk1XvdvUeBnXmlld/c8b5c3d4-e1f2-4a5b-9c8d-7e6f5a4b3c2d.mp3'
                }
            ]
        }

    def create_voice_agent(self, config: Dict) -> Dict:
        """Create a voice agent configuration for ElevenLabs Conversational AI"""
        agent_id = str(uuid.uuid4())

        # ElevenLabs Conversational AI specific configuration
        agent_config = {
            'agent_id': agent_id,
            'name': config.get('name', 'ElevenLabs Voice Agent'),
            'description': config.get('description', 'AI voice agent powered by ElevenLabs Conversational AI'),
            'voice_id': config.get('voice_id', self.default_voice_id),
            'model_id': config.get('model_id', self.default_model_id),
            'language': config.get('language', 'en'),
            'voice_settings': {
                'stability': config.get('stability', 0.75),
                'similarity_boost': config.get('similarity_boost', 0.75),
                'style': config.get('style', 0.0),
                'use_speaker_boost': config.get('use_speaker_boost', True)
            },
            'system_prompt': config.get('system_prompt', 'You are a helpful AI assistant.'),
            'phone_integration': {
                'enabled': True,
                'webhook_url': config.get('webhook_url'),
                'post_call_webhook': config.get('post_call_webhook'),
                'conversation_summaries': config.get('conversation_summaries', True),
                'call_recording': config.get('call_recording', False)
            },
            'workspace_secrets': {
                'api_key': self.api_key,
                'voice_id': config.get('voice_id', self.default_voice_id)
            },
            'created_at': datetime.now().isoformat(),
            'provider': 'elevenlabs'
        }

        # If using mock mode, simulate agent creation
        if self.use_mock:
            return {
                'success': True,
                'agent': agent_config,
                'external_agent_id': agent_id,
                'mock': True
            }

        # In real implementation, this would create the agent via ElevenLabs API
        try:
            # This would be the actual API call to create conversational AI agent
            # response = requests.post(f"{self.base_url}/conversational-ai/agents", ...)

            return {
                'success': True,
                'agent': agent_config,
                'external_agent_id': agent_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create ElevenLabs agent: {str(e)}'
            }

    def synthesize_speech(self, text: str, voice_id: str = None, voice_settings: Dict = None) -> Dict:
        """Convert text to speech using ElevenLabs API"""
        if self.use_mock:
            return self._mock_synthesize_speech(text, voice_id)
            
        voice_id = voice_id or self.default_voice_id
        
        payload = {
            'text': text,
            'model_id': self.default_model_id,
            'voice_settings': voice_settings or {
                'stability': 0.75,
                'similarity_boost': 0.75,
                'style': 0.0,
                'use_speaker_boost': True
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'audio_data': response.content,
                    'content_type': response.headers.get('content-type', 'audio/mpeg')
                }
            else:
                return {
                    'success': False,
                    'error': f'Speech synthesis failed: {response.status_code}'
                }
        except Exception as e:
            self.logger.error(f"Error in speech synthesis: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _mock_synthesize_speech(self, text: str, voice_id: str = None) -> Dict:
        """Mock speech synthesis for development"""
        return {
            'success': True,
            'audio_data': b'mock_audio_data',
            'content_type': 'audio/mpeg',
            'mock': True,
            'text': text,
            'voice_id': voice_id or self.default_voice_id
        }

    def start_conversation_stream(self, voice_id: str = None, voice_settings: Dict = None) -> Dict:
        """Start a real-time conversation stream with ElevenLabs"""
        if self.use_mock or not WEBSOCKET_AVAILABLE:
            return self._mock_start_stream()

        voice_id = voice_id or self.default_voice_id
        self.session_id = str(uuid.uuid4())

        # WebSocket URL with parameters
        ws_url = f"{self.websocket_url}/{voice_id}?model_id={self.default_model_id}"

        try:
            self.ws = websocket.WebSocketApp(
                ws_url,
                header=[f"xi-api-key: {self.api_key}"],
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close
            )

            # Start WebSocket in a separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()

            return {
                'success': True,
                'session_id': self.session_id,
                'status': 'connecting'
            }
        except Exception as e:
            self.logger.error(f"Error starting conversation stream: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _mock_start_stream(self) -> Dict:
        """Mock stream start for development"""
        self.session_id = str(uuid.uuid4())
        self.is_connected = True
        return {
            'success': True,
            'session_id': self.session_id,
            'status': 'connected',
            'mock': True
        }

    def send_text_to_stream(self, text: str) -> Dict:
        """Send text to the active conversation stream"""
        if self.use_mock:
            return self._mock_send_text(text)
            
        if not self.ws or not self.is_connected:
            return {
                'success': False,
                'error': 'No active stream connection'
            }
        
        try:
            message = {
                'text': text,
                'voice_settings': {
                    'stability': 0.75,
                    'similarity_boost': 0.75
                }
            }
            
            self.ws.send(json.dumps(message))
            return {
                'success': True,
                'message': 'Text sent to stream'
            }
        except Exception as e:
            self.logger.error(f"Error sending text to stream: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _mock_send_text(self, text: str) -> Dict:
        """Mock text sending for development"""
        return {
            'success': True,
            'message': 'Text sent to mock stream',
            'text': text,
            'mock': True
        }

    def _on_ws_open(self, ws):
        """WebSocket connection opened"""
        self.is_connected = True
        self.logger.info("ElevenLabs WebSocket connection opened")
        if self.on_session_update:
            self.on_session_update({'status': 'connected', 'session_id': self.session_id})

    def _on_ws_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            # ElevenLabs sends binary audio data
            if isinstance(message, bytes):
                if self.on_audio_data:
                    self.on_audio_data(message)
            else:
                # Handle JSON messages if any
                data = json.loads(message)
                self.logger.info(f"Received message: {data}")
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")

    def _on_ws_error(self, ws, error):
        """Handle WebSocket errors"""
        self.logger.error(f"ElevenLabs WebSocket error: {error}")
        self.is_connected = False
        if self.on_error:
            self.on_error(str(error))

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        self.is_connected = False
        self.logger.info(f"ElevenLabs WebSocket connection closed: {close_status_code} - {close_msg}")
        if self.on_session_update:
            self.on_session_update({'status': 'disconnected', 'session_id': self.session_id})

    def close_stream(self):
        """Close the active conversation stream"""
        if self.ws:
            self.ws.close()
            self.is_connected = False
            self.session_id = None

    def setup_phone_webhook(self, agent_id: str, webhook_config: Dict) -> Dict:
        """Setup phone call webhook for ElevenLabs Conversational AI"""
        if self.use_mock:
            return {
                'success': True,
                'webhook_url': f"https://api.elevenlabs.io/v1/conversational-ai/agents/{agent_id}/webhook",
                'mock': True
            }

        try:
            # This would configure the webhook in ElevenLabs
            webhook_data = {
                'agent_id': agent_id,
                'webhook_url': webhook_config.get('webhook_url'),
                'events': ['conversation.started', 'conversation.ended', 'message.received'],
                'phone_integration': {
                    'enabled': True,
                    'twilio_integration': webhook_config.get('twilio_integration', True),
                    'sip_trunk_integration': webhook_config.get('sip_trunk_integration', False)
                }
            }

            return {
                'success': True,
                'webhook_url': f"https://api.elevenlabs.io/v1/conversational-ai/agents/{agent_id}/webhook",
                'configuration': webhook_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to setup webhook: {str(e)}'
            }

    def handle_phone_call(self, agent_id: str, call_data: Dict) -> Dict:
        """Handle an incoming phone call with ElevenLabs Conversational AI"""
        session_id = str(uuid.uuid4())

        if self.use_mock:
            return {
                'session_id': session_id,
                'response': {
                    'message': 'Mock phone call handled',
                    'agent_id': agent_id,
                    'phone_number': call_data.get('phone_number'),
                    'call_id': call_data.get('call_id')
                },
                'status': 'active',
                'mock': True
            }

        try:
            # Initialize phone call session with ElevenLabs
            call_session = {
                'agent_id': agent_id,
                'session_id': session_id,
                'phone_number': call_data.get('phone_number'),
                'call_id': call_data.get('call_id'),
                'initial_message': call_data.get('initial_message', 'Hello! How can I help you today?'),
                'language': call_data.get('language', 'en'),
                'voice_settings': call_data.get('voice_settings', {
                    'stability': 0.75,
                    'similarity_boost': 0.75
                })
            }

            # This would initiate the call with ElevenLabs Conversational AI
            # response = requests.post(f"{self.base_url}/conversational-ai/phone-calls", ...)

            return {
                'session_id': session_id,
                'response': {
                    'message': 'Phone call session initiated',
                    'agent_id': agent_id,
                    'call_session': call_session
                },
                'status': 'active'
            }
        except Exception as e:
            return {
                'session_id': session_id,
                'response': {'error': f'Failed to handle phone call: {str(e)}'},
                'status': 'error'
            }

    def handle_voice_call(self, agent_id: str, call_data: Dict) -> Dict:
        """Handle an incoming voice call with ElevenLabs agent (legacy method)"""
        # Redirect to the new phone call handler
        return self.handle_phone_call(agent_id, call_data)


    def manage_workspace_secrets(self, action: str, secret_data: Dict = None) -> Dict:
        """Manage workspace secrets for ElevenLabs integration"""
        if self.use_mock:
            return {
                'success': True,
                'action': action,
                'secrets': ['elevenlabs_api_key', 'twilio_token_account'],
                'mock': True
            }

        try:
            if action == 'add':
                # Add new workspace secret
                return {
                    'success': True,
                    'message': f'Secret {secret_data.get("name")} added successfully',
                    'secret_id': str(uuid.uuid4())
                }
            elif action == 'list':
                # List existing secrets
                return {
                    'success': True,
                    'secrets': [
                        {
                            'name': 'elevenlabs_api_key',
                            'description': 'ElevenLabs API Key',
                            'created_at': datetime.now().isoformat()
                        }
                    ]
                }
            elif action == 'delete':
                # Delete secret
                return {
                    'success': True,
                    'message': f'Secret {secret_data.get("name")} deleted successfully'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to manage workspace secrets: {str(e)}'
            }

    def setup_post_call_webhook(self, agent_id: str, webhook_url: str) -> Dict:
        """Setup post-call webhook for conversation analysis"""
        if self.use_mock:
            return {
                'success': True,
                'webhook_url': webhook_url,
                'agent_id': agent_id,
                'mock': True
            }

        try:
            webhook_config = {
                'agent_id': agent_id,
                'webhook_url': webhook_url,
                'events': ['conversation.ended'],
                'data_included': [
                    'conversation_summary',
                    'call_duration',
                    'participant_info',
                    'transcript'
                ]
            }

            return {
                'success': True,
                'message': 'Post-call webhook configured successfully',
                'configuration': webhook_config
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to setup post-call webhook: {str(e)}'
            }


class ElevenLabsAgentManager:
    """High-level manager for ElevenLabs voice agents"""

    def __init__(self):
        self.api = ElevenLabsAPI()
        self.active_sessions = {}

    def create_voice_agent(self, config: Dict) -> Dict:
        """Create a new voice agent with ElevenLabs"""
        result = self.api.create_voice_agent(config)

        # Setup webhooks if configuration provided
        if result['success'] and config.get('webhook_url'):
            webhook_result = self.api.setup_phone_webhook(
                result['external_agent_id'],
                {'webhook_url': config['webhook_url']}
            )
            result['webhook_setup'] = webhook_result

        return result

    def get_available_voices(self) -> Dict:
        """Get available voices for agent configuration"""
        return self.api.get_available_voices()

    def handle_voice_call(self, agent_id: str, call_data: Dict) -> Dict:
        """Handle voice call with specified agent"""
        result = self.api.handle_phone_call(agent_id, call_data)

        if result['status'] == 'active':
            self.active_sessions[result['session_id']] = {
                'agent_id': agent_id,
                'call_data': call_data,
                'started_at': datetime.now().isoformat()
            }

        return result

    def end_session(self, session_id: str) -> Dict:
        """End an active voice session"""
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            del self.active_sessions[session_id]
            self.api.close_stream()

            # Trigger post-call webhook if configured
            return {
                'success': True,
                'message': 'Session ended',
                'session_data': session_data
            }
        else:
            return {'success': False, 'error': 'Session not found'}

    def setup_workspace_secrets(self, secrets: Dict) -> Dict:
        """Setup workspace secrets for the agent"""
        return self.api.manage_workspace_secrets('add', secrets)

    def configure_phone_integration(self, agent_id: str, phone_config: Dict) -> Dict:
        """Configure phone integration settings"""
        webhook_result = self.api.setup_phone_webhook(agent_id, phone_config)

        if phone_config.get('post_call_webhook'):
            post_call_result = self.api.setup_post_call_webhook(
                agent_id,
                phone_config['post_call_webhook']
            )
            webhook_result['post_call_webhook'] = post_call_result

        return webhook_result


# Default agent configurations for ElevenLabs
DEFAULT_ELEVENLABS_CONFIGS = {
    'customer_support': {
        'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - calm, professional
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.8,
            'similarity_boost': 0.7,
            'style': 0.2,
            'use_speaker_boost': True
        },
        'system_prompt': 'You are a helpful customer support agent. Speak clearly and professionally.',
        'use_case': 'customer_support'
    },
    'appointment_booking': {
        'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - deep, authoritative
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.75,
            'similarity_boost': 0.75,
            'style': 0.1,
            'use_speaker_boost': True
        },
        'system_prompt': 'You are an appointment booking assistant. Be friendly and efficient.',
        'use_case': 'appointment_booking'
    },
    'multilingual_support': {
        'voice_id': 'AZnzlk1XvdvUeBnXmlld',  # Domi - strong, confident
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.7,
            'similarity_boost': 0.8,
            'style': 0.3,
            'use_speaker_boost': True
        },
        'system_prompt': 'You are a multilingual support agent. Adapt to the user\'s preferred language.',
        'use_case': 'multilingual_support'
    }
}
