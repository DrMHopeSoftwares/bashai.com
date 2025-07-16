"""
OpenAI Realtime API Integration Module
Handles speech-to-speech real-time conversations using OpenAI's Realtime API
"""

import os
import json
import uuid
import asyncio
import websockets
import base64
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dotenv import load_dotenv

load_dotenv()

class OpenAIRealtimeAPI:
    """OpenAI Realtime API client for speech-to-speech conversations"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
        self.base_url = "wss://api.openai.com/v1/realtime"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.websocket = None
        self.session_id = None
        self.conversation_id = None
        self.connected = False
        
        # Event handlers
        self.event_handlers = {
            'session.created': self._handle_session_created,
            'conversation.item.created': self._handle_conversation_item,
            'response.audio.delta': self._handle_audio_delta,
            'response.audio.done': self._handle_audio_done,
            'response.done': self._handle_response_done,
            'error': self._handle_error
        }
        
        # Audio settings
        self.input_audio_format = "pcm16"
        self.output_audio_format = "pcm16"
        self.sample_rate = 24000
        
        # Callback functions (to be set by application)
        self.on_audio_output = None
        self.on_transcript = None
        self.on_session_update = None
        self.on_error_callback = None
        
        # Session state
        self.conversation_items = []
        self.audio_buffer = b""
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def connect(self, voice_instructions: str = None, voice: str = "alloy") -> bool:
        """
        Establish WebSocket connection to OpenAI Realtime API
        
        Args:
            voice_instructions: Custom instructions for the voice agent
            voice: Voice model to use (alloy, echo, fable, onyx, nova, shimmer)
        
        Returns:
            bool: Connection success status
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            url = f"{self.base_url}?model={self.model}"
            
            self.websocket = await websockets.connect(url, additional_headers=headers)
            self.connected = True
            self.session_id = str(uuid.uuid4())
            self.conversation_id = str(uuid.uuid4())
            
            # Configure session
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": voice_instructions or "You are a helpful AI voice assistant. Respond naturally and conversationally in Hindi and English (Hinglish) as appropriate.",
                    "voice": voice,
                    "input_audio_format": self.input_audio_format,
                    "output_audio_format": self.output_audio_format,
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200
                    },
                    "tools": [],
                    "tool_choice": "auto",
                    "temperature": 0.8,
                    "max_response_output_tokens": 4096
                }
            }
            
            await self.websocket.send(json.dumps(session_config))
            self.logger.info(f"Connected to OpenAI Realtime API - Session: {self.session_id}")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OpenAI Realtime API: {e}")
            self.connected = False
            return False

    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages and handle events"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                event_type = data.get('type')
                
                if event_type in self.event_handlers:
                    await self.event_handlers[event_type](data)
                else:
                    self.logger.debug(f"Unhandled event type: {event_type}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
            self.connected = False
        except Exception as e:
            self.logger.error(f"Error in message listener: {e}")
            if self.on_error_callback:
                await self.on_error_callback(f"Message listener error: {e}")

    async def send_audio(self, audio_data: bytes, append: bool = True):
        """
        Send audio data to the Realtime API
        
        Args:
            audio_data: Raw audio bytes in PCM16 format
            append: Whether to append to existing audio or start new input
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to OpenAI Realtime API")
        
        # Encode audio data to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        
        await self.websocket.send(json.dumps(event))

    async def commit_audio(self):
        """Commit the audio buffer and trigger response generation"""
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to OpenAI Realtime API")
        
        event = {
            "type": "input_audio_buffer.commit"
        }
        
        await self.websocket.send(json.dumps(event))

    async def send_text(self, text: str):
        """
        Send text message to the conversation
        
        Args:
            text: Text message to send
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to OpenAI Realtime API")
        
        item_id = str(uuid.uuid4())
        
        event = {
            "type": "conversation.item.create",
            "item": {
                "id": item_id,
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        
        await self.websocket.send(json.dumps(event))
        
        # Trigger response
        response_event = {
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": "Please respond naturally in the user's preferred language (Hindi/English/Hinglish)."
            }
        }
        
        await self.websocket.send(json.dumps(response_event))

    async def interrupt_response(self):
        """Cancel the current response generation"""
        if not self.connected or not self.websocket:
            return
        
        event = {
            "type": "response.cancel"
        }
        
        await self.websocket.send(json.dumps(event))

    async def disconnect(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info("Disconnected from OpenAI Realtime API")

    # Event Handlers
    async def _handle_session_created(self, data: Dict):
        """Handle session.created event"""
        self.logger.info(f"Session created: {data.get('session', {}).get('id')}")
        if self.on_session_update:
            await self.on_session_update(data)

    async def _handle_conversation_item(self, data: Dict):
        """Handle conversation.item.created event"""
        item = data.get('item', {})
        self.conversation_items.append(item)
        
        if item.get('type') == 'message' and item.get('role') == 'assistant':
            content = item.get('content', [])
            for content_part in content:
                if content_part.get('type') == 'text':
                    transcript = content_part.get('text', '')
                    if self.on_transcript:
                        await self.on_transcript(transcript, 'assistant')

    async def _handle_audio_delta(self, data: Dict):
        """Handle response.audio.delta event"""
        audio_delta = data.get('delta')
        if audio_delta and self.on_audio_output:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_delta)
            await self.on_audio_output(audio_bytes)

    async def _handle_audio_done(self, data: Dict):
        """Handle response.audio.done event"""
        self.logger.info("Audio response completed")

    async def _handle_response_done(self, data: Dict):
        """Handle response.done event"""
        response = data.get('response', {})
        self.logger.info(f"Response completed: {response.get('id')}")

    async def _handle_error(self, data: Dict):
        """Handle error events"""
        error = data.get('error', {})
        error_message = f"OpenAI Realtime API Error: {error.get('message', 'Unknown error')}"
        self.logger.error(error_message)
        
        if self.on_error_callback:
            await self.on_error_callback(error_message)

    def set_audio_output_handler(self, handler: Callable):
        """Set callback for audio output"""
        self.on_audio_output = handler

    def set_transcript_handler(self, handler: Callable):
        """Set callback for transcript updates"""
        self.on_transcript = handler

    def set_session_update_handler(self, handler: Callable):
        """Set callback for session updates"""
        self.on_session_update = handler

    def set_error_handler(self, handler: Callable):
        """Set callback for error handling"""
        self.on_error_callback = handler

    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history"""
        return self.conversation_items.copy()

    def get_session_info(self) -> Dict:
        """Get current session information"""
        return {
            'session_id': self.session_id,
            'conversation_id': self.conversation_id,
            'connected': self.connected,
            'model': self.model,
            'conversation_length': len(self.conversation_items)
        }


class RealtimeSessionManager:
    """Manages multiple realtime sessions for different users/conversations"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_metadata = {}
        
    async def create_session(self, user_id: str, voice_agent_config: Dict) -> str:
        """
        Create a new realtime session for a user
        
        Args:
            user_id: User identifier
            voice_agent_config: Voice agent configuration
            
        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Create realtime API instance
        realtime_api = OpenAIRealtimeAPI()
        
        # Extract configuration
        instructions = voice_agent_config.get('instructions', '')
        voice = voice_agent_config.get('voice', 'alloy')
        
        # Connect to OpenAI
        success = await realtime_api.connect(
            voice_instructions=instructions,
            voice=voice
        )
        
        if success:
            self.active_sessions[session_id] = realtime_api
            self.session_metadata[session_id] = {
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc),
                'voice_agent_config': voice_agent_config,
                'status': 'active'
            }
            return session_id
        else:
            raise ConnectionError("Failed to establish realtime connection")
    
    async def get_session(self, session_id: str) -> Optional[OpenAIRealtimeAPI]:
        """Get an active session"""
        return self.active_sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """Close and cleanup a session"""
        if session_id in self.active_sessions:
            await self.active_sessions[session_id].disconnect()
            del self.active_sessions[session_id]
            
        if session_id in self.session_metadata:
            self.session_metadata[session_id]['status'] = 'closed'
            self.session_metadata[session_id]['closed_at'] = datetime.now(timezone.utc)
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user"""
        return [
            session_id for session_id, metadata in self.session_metadata.items()
            if metadata['user_id'] == user_id and metadata['status'] == 'active'
        ]
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 2):
        """Cleanup sessions older than specified hours"""
        current_time = datetime.now(timezone.utc)
        sessions_to_close = []
        
        for session_id, metadata in self.session_metadata.items():
            if metadata['status'] == 'active':
                age = current_time - metadata['created_at']
                if age.total_seconds() > max_age_hours * 3600:
                    sessions_to_close.append(session_id)
        
        for session_id in sessions_to_close:
            await self.close_session(session_id)


# Global session manager instance
session_manager = RealtimeSessionManager()