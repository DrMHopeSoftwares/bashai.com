"""
WebSocket Handler for OpenAI Realtime API Integration
Provides Flask-SocketIO endpoints for real-time voice conversations
"""

import os
import json
import base64
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from flask import request, g
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from openai_realtime_integration import session_manager, OpenAIRealtimeAPI
from auth import auth_manager, login_required
from trial_middleware import check_trial_limits, log_trial_activity

class RealtimeWebSocketHandler:
    """Handles WebSocket connections for real-time voice conversations"""
    
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.user_sessions = {}  # Maps socket_id to session info
        
        # Register event handlers
        self.socketio.on_event('connect', self.handle_connect)
        self.socketio.on_event('disconnect', self.handle_disconnect)
        self.socketio.on_event('start_voice_session', self.handle_start_voice_session)
        self.socketio.on_event('send_audio', self.handle_send_audio)
        self.socketio.on_event('send_text', self.handle_send_text)
        self.socketio.on_event('commit_audio', self.handle_commit_audio)
        self.socketio.on_event('interrupt_response', self.handle_interrupt_response)
        self.socketio.on_event('end_voice_session', self.handle_end_voice_session)
        
        self.logger = logging.getLogger(__name__)

    def handle_connect(self):
        """Handle client connection"""
        self.logger.info(f"Client connected: {request.sid}")
        emit('status', {'message': 'Connected to bhashai.com Realtime Voice API'})

    def handle_disconnect(self):
        """Handle client disconnection"""
        socket_id = request.sid
        self.logger.info(f"Client disconnected: {socket_id}")
        
        # Cleanup user session if exists
        if socket_id in self.user_sessions:
            asyncio.create_task(self._cleanup_user_session(socket_id))

    async def _cleanup_user_session(self, socket_id: str):
        """Cleanup user session on disconnect"""
        if socket_id in self.user_sessions:
            session_info = self.user_sessions[socket_id]
            session_id = session_info.get('session_id')
            
            if session_id:
                await session_manager.close_session(session_id)
            
            del self.user_sessions[socket_id]

    def handle_start_voice_session(self, data):
        """Start a new voice session"""
        try:
            # Validate authentication
            token = data.get('auth_token')
            if not token:
                emit('error', {'message': 'Authentication token required'})
                return
            
            # Verify user authentication
            user_info = auth_manager.verify_token(token)
            if not user_info:
                emit('error', {'message': 'Invalid authentication token'})
                return
            
            user_id = user_info.get('user_id')
            user_email = user_info.get('email')
            
            # Check trial limits for realtime API usage
            if not check_trial_limits(user_id, 'realtime_minutes', 1):
                emit('error', {'message': 'Trial limit exceeded for realtime voice sessions'})
                return
            
            # Get voice agent configuration
            voice_agent_id = data.get('voice_agent_id')
            if not voice_agent_id:
                emit('error', {'message': 'Voice agent ID required'})
                return
            
            # Fetch voice agent config from database
            voice_agent_config = self._get_voice_agent_config(voice_agent_id, user_id)
            if not voice_agent_config:
                emit('error', {'message': 'Voice agent not found or access denied'})
                return
            
            # Create async task to start session
            asyncio.create_task(self._start_realtime_session(
                request.sid, user_id, user_email, voice_agent_config
            ))
            
        except Exception as e:
            self.logger.error(f"Error starting voice session: {e}")
            emit('error', {'message': f'Failed to start voice session: {str(e)}'})

    async def _start_realtime_session(self, socket_id: str, user_id: str, user_email: str, voice_agent_config: Dict):
        """Start realtime session (async)"""
        try:
            # Create realtime session
            session_id = await session_manager.create_session(user_id, voice_agent_config)
            realtime_api = await session_manager.get_session(session_id)
            
            if not realtime_api:
                self.socketio.emit('error', {'message': 'Failed to create realtime session'}, room=socket_id)
                return
            
            # Store session info
            self.user_sessions[socket_id] = {
                'session_id': session_id,
                'user_id': user_id,
                'user_email': user_email,
                'voice_agent_config': voice_agent_config,
                'started_at': datetime.now(timezone.utc)
            }
            
            # Set up event handlers for this session
            await self._setup_session_handlers(realtime_api, socket_id)
            
            # Join user to their session room
            join_room(session_id, sid=socket_id)
            
            # Notify client of successful session start
            self.socketio.emit('voice_session_started', {
                'session_id': session_id,
                'voice_agent': voice_agent_config.get('name'),
                'status': 'ready'
            }, room=socket_id)
            
            # Log trial activity
            log_trial_activity(user_id, 'realtime_session_started', {
                'session_id': session_id,
                'voice_agent_id': voice_agent_config.get('id')
            })
            
        except Exception as e:
            self.logger.error(f"Error in _start_realtime_session: {e}")
            self.socketio.emit('error', {'message': f'Session creation failed: {str(e)}'}, room=socket_id)

    async def _setup_session_handlers(self, realtime_api: OpenAIRealtimeAPI, socket_id: str):
        """Setup event handlers for the realtime session"""
        
        async def on_audio_output(audio_bytes: bytes):
            """Handle audio output from OpenAI"""
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            self.socketio.emit('audio_output', {
                'audio_data': audio_base64,
                'format': 'pcm16',
                'sample_rate': 24000
            }, room=socket_id)
        
        async def on_transcript(text: str, role: str):
            """Handle transcript updates"""
            self.socketio.emit('transcript', {
                'text': text,
                'role': role,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=socket_id)
        
        async def on_session_update(session_data: Dict):
            """Handle session updates"""
            self.socketio.emit('session_update', session_data, room=socket_id)
        
        async def on_error(error_message: str):
            """Handle errors from OpenAI"""
            self.socketio.emit('realtime_error', {
                'message': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=socket_id)
        
        # Set handlers
        realtime_api.set_audio_output_handler(on_audio_output)
        realtime_api.set_transcript_handler(on_transcript)
        realtime_api.set_session_update_handler(on_session_update)
        realtime_api.set_error_handler(on_error)

    def handle_send_audio(self, data):
        """Handle audio data from client"""
        try:
            socket_id = request.sid
            if socket_id not in self.user_sessions:
                emit('error', {'message': 'No active voice session'})
                return
            
            session_info = self.user_sessions[socket_id]
            session_id = session_info['session_id']
            
            # Get audio data
            audio_base64 = data.get('audio_data')
            if not audio_base64:
                emit('error', {'message': 'Audio data required'})
                return
            
            # Decode audio data
            audio_bytes = base64.b64decode(audio_base64)
            
            # Send to OpenAI (async)
            asyncio.create_task(self._send_audio_to_openai(session_id, audio_bytes))
            
        except Exception as e:
            self.logger.error(f"Error handling audio: {e}")
            emit('error', {'message': f'Audio processing failed: {str(e)}'})

    async def _send_audio_to_openai(self, session_id: str, audio_bytes: bytes):
        """Send audio to OpenAI realtime API"""
        try:
            realtime_api = await session_manager.get_session(session_id)
            if realtime_api:
                await realtime_api.send_audio(audio_bytes)
        except Exception as e:
            self.logger.error(f"Error sending audio to OpenAI: {e}")

    def handle_send_text(self, data):
        """Handle text message from client"""
        try:
            socket_id = request.sid
            if socket_id not in self.user_sessions:
                emit('error', {'message': 'No active voice session'})
                return
            
            session_info = self.user_sessions[socket_id]
            session_id = session_info['session_id']
            
            text = data.get('text')
            if not text:
                emit('error', {'message': 'Text message required'})
                return
            
            # Send to OpenAI (async)
            asyncio.create_task(self._send_text_to_openai(session_id, text))
            
        except Exception as e:
            self.logger.error(f"Error handling text: {e}")
            emit('error', {'message': f'Text processing failed: {str(e)}'})

    async def _send_text_to_openai(self, session_id: str, text: str):
        """Send text to OpenAI realtime API"""
        try:
            realtime_api = await session_manager.get_session(session_id)
            if realtime_api:
                await realtime_api.send_text(text)
        except Exception as e:
            self.logger.error(f"Error sending text to OpenAI: {e}")

    def handle_commit_audio(self, data):
        """Commit audio buffer and trigger response"""
        try:
            socket_id = request.sid
            if socket_id not in self.user_sessions:
                emit('error', {'message': 'No active voice session'})
                return
            
            session_info = self.user_sessions[socket_id]
            session_id = session_info['session_id']
            
            # Commit audio (async)
            asyncio.create_task(self._commit_audio_to_openai(session_id))
            
        except Exception as e:
            self.logger.error(f"Error committing audio: {e}")
            emit('error', {'message': f'Audio commit failed: {str(e)}'})

    async def _commit_audio_to_openai(self, session_id: str):
        """Commit audio buffer to OpenAI"""
        try:
            realtime_api = await session_manager.get_session(session_id)
            if realtime_api:
                await realtime_api.commit_audio()
        except Exception as e:
            self.logger.error(f"Error committing audio to OpenAI: {e}")

    def handle_interrupt_response(self, data):
        """Interrupt current response generation"""
        try:
            socket_id = request.sid
            if socket_id not in self.user_sessions:
                emit('error', {'message': 'No active voice session'})
                return
            
            session_info = self.user_sessions[socket_id]
            session_id = session_info['session_id']
            
            # Interrupt response (async)
            asyncio.create_task(self._interrupt_openai_response(session_id))
            
        except Exception as e:
            self.logger.error(f"Error interrupting response: {e}")
            emit('error', {'message': f'Response interruption failed: {str(e)}'})

    async def _interrupt_openai_response(self, session_id: str):
        """Interrupt OpenAI response"""
        try:
            realtime_api = await session_manager.get_session(session_id)
            if realtime_api:
                await realtime_api.interrupt_response()
        except Exception as e:
            self.logger.error(f"Error interrupting OpenAI response: {e}")

    def handle_end_voice_session(self, data):
        """End the current voice session"""
        try:
            socket_id = request.sid
            if socket_id not in self.user_sessions:
                emit('error', {'message': 'No active voice session'})
                return
            
            # End session (async)
            asyncio.create_task(self._end_voice_session(socket_id))
            
        except Exception as e:
            self.logger.error(f"Error ending session: {e}")
            emit('error', {'message': f'Session end failed: {str(e)}'})

    async def _end_voice_session(self, socket_id: str):
        """End voice session and cleanup"""
        try:
            if socket_id in self.user_sessions:
                session_info = self.user_sessions[socket_id]
                session_id = session_info['session_id']
                user_id = session_info['user_id']
                
                # Calculate session duration for billing
                duration = datetime.now(timezone.utc) - session_info['started_at']
                duration_minutes = duration.total_seconds() / 60
                
                # Close OpenAI session
                await session_manager.close_session(session_id)
                
                # Leave room
                leave_room(session_id, sid=socket_id)
                
                # Log trial activity
                log_trial_activity(user_id, 'realtime_session_ended', {
                    'session_id': session_id,
                    'duration_minutes': duration_minutes
                })
                
                # Remove from user sessions
                del self.user_sessions[socket_id]
                
                # Notify client
                self.socketio.emit('voice_session_ended', {
                    'session_id': session_id,
                    'duration_minutes': round(duration_minutes, 2)
                }, room=socket_id)
                
        except Exception as e:
            self.logger.error(f"Error ending voice session: {e}")

    def _get_voice_agent_config(self, voice_agent_id: str, user_id: str) -> Optional[Dict]:
        """Fetch voice agent configuration from database"""
        try:
            # Import here to avoid circular imports
            from main import SUPABASE_HEADERS, SUPABASE_URL
            import requests
            
            if not SUPABASE_URL or not SUPABASE_HEADERS:
                # Fallback configuration for development
                return {
                    'id': voice_agent_id,
                    'name': 'Development Voice Agent',
                    'instructions': 'You are a helpful AI assistant that can speak in Hindi and English.',
                    'voice': 'alloy',
                    'language': 'hi-IN'
                }
            
            # Query voice agent from database
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/voice_agents",
                headers=SUPABASE_HEADERS,
                params={
                    'id': f'eq.{voice_agent_id}',
                    'select': '*'
                }
            )
            
            if response.status_code == 200:
                agents = response.json()
                if agents:
                    agent = agents[0]
                    
                    # Verify user has access to this agent
                    if agent.get('user_id') != user_id:
                        return None
                    
                    # Convert to realtime config format
                    config = agent.get('configuration', {})
                    return {
                        'id': agent['id'],
                        'name': agent.get('name', 'Voice Agent'),
                        'instructions': config.get('instructions', 'You are a helpful AI assistant.'),
                        'voice': config.get('voice', 'alloy'),
                        'language': config.get('language', 'en-US')
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching voice agent config: {e}")
            return None

def init_realtime_websocket(app, socketio):
    """Initialize realtime WebSocket handler"""
    return RealtimeWebSocketHandler(app, socketio)