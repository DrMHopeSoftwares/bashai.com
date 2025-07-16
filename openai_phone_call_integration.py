"""
OpenAI Realtime API Phone Call Integration
Combines phone providers (Twilio/Plivo) with OpenAI Realtime API for outbound calls
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Callable, List
from dotenv import load_dotenv

# Import existing integrations
from phone_provider_integration import phone_provider_manager
from openai_realtime_integration import OpenAIRealtimeAPI, session_manager
from realtime_usage_tracker import usage_tracker

load_dotenv()

class OpenAIPhoneCallManager:
    """Manages phone calls using OpenAI Realtime API"""
    
    def __init__(self):
        self.active_calls = {}
        self.logger = logging.getLogger(__name__)
        
        # Call configuration
        self.default_voice_config = {
            'voice': 'alloy',
            'language': 'hi-IN',
            'instructions': '''You are a helpful AI assistant making a phone call. 
            You can speak in Hindi and English (Hinglish) naturally. 
            Be polite, clear, and conversational. 
            Keep responses concise since this is a phone conversation.
            If the person asks who you are, say you're calling from BhashAI voice assistant.'''
        }

    async def make_outbound_call(self, 
                                phone_number: str, 
                                voice_config: Dict = None,
                                provider: str = 'twilio',
                                user_id: str = None) -> Dict:
        """
        Initiate an outbound call with OpenAI Realtime API
        
        Args:
            phone_number: Target phone number (e.g., '+919373111709')
            voice_config: Voice agent configuration
            provider: Phone provider ('twilio', 'plivo', 'telnyx')
            user_id: User making the call
            
        Returns:
            Dict: Call information and status
        """
        try:
            call_id = f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{phone_number[-4:]}"
            
            # Merge voice configuration
            config = {**self.default_voice_config, **(voice_config or {})}
            
            self.logger.info(f"Initiating call {call_id} to {phone_number}")
            
            # Step 1: Create OpenAI Realtime session
            realtime_session_id = await session_manager.create_session(
                user_id or 'system', 
                config
            )
            
            realtime_api = await session_manager.get_session(realtime_session_id)
            if not realtime_api:
                raise Exception("Failed to create OpenAI Realtime session")
            
            # Step 2: Set up audio handlers
            audio_buffer = []
            
            async def on_audio_output(audio_bytes: bytes):
                """Handle audio from OpenAI and send to phone"""
                audio_buffer.append(audio_bytes)
                # In real implementation, stream to phone provider
                self.logger.debug(f"Received audio chunk: {len(audio_bytes)} bytes")
            
            async def on_transcript(text: str, role: str):
                """Log conversation transcript"""
                self.logger.info(f"[{role.upper()}] {text}")
            
            realtime_api.set_audio_output_handler(on_audio_output)
            realtime_api.set_transcript_handler(on_transcript)
            
            # Step 3: Initiate phone call (mock implementation)
            call_info = await self._initiate_phone_call(
                phone_number, provider, call_id, realtime_session_id
            )
            
            # Step 4: Store call information
            self.active_calls[call_id] = {
                'call_id': call_id,
                'phone_number': phone_number,
                'provider': provider,
                'realtime_session_id': realtime_session_id,
                'user_id': user_id,
                'status': 'calling',
                'started_at': datetime.now(timezone.utc),
                'config': config,
                'call_info': call_info
            }
            
            # Step 5: Start usage tracking
            usage_tracker.start_session_tracking(
                realtime_session_id, 
                user_id or 'system',
                'gpt-4o-realtime-preview'
            )
            
            return {
                'success': True,
                'call_id': call_id,
                'phone_number': phone_number,
                'status': 'initiated',
                'realtime_session_id': realtime_session_id,
                'message': f'Call initiated to {phone_number}'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to make call: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to initiate call to {phone_number}'
            }

    async def _initiate_phone_call(self, phone_number: str, provider: str, 
                                  call_id: str, session_id: str) -> Dict:
        """
        Initiate the actual phone call through provider
        
        NOTE: This is a mock implementation. In production, you would:
        1. Use provider's voice call API (Twilio Voice, Plivo Voice, etc.)
        2. Set up webhooks for call events
        3. Stream audio bidirectionally between phone and OpenAI
        """
        
        self.logger.info(f"MOCK: Initiating call to {phone_number} via {provider}")
        
        # Mock call setup
        mock_call_info = {
            'provider_call_id': f'{provider}_{call_id}',
            'status': 'initiated',
            'webhook_url': f'https://your-domain.com/webhook/call/{call_id}',
            'mock': True
        }
        
        # In real implementation, this would be:
        # if provider == 'twilio':
        #     return await self._twilio_call(phone_number, call_id, session_id)
        # elif provider == 'plivo':
        #     return await self._plivo_call(phone_number, call_id, session_id)
        
        # Simulate call connection after 3 seconds
        await asyncio.sleep(3)
        
        # Mock conversation start
        await self._simulate_conversation_start(session_id)
        
        return mock_call_info

    async def _simulate_conversation_start(self, session_id: str):
        """Simulate starting conversation (for demo purposes)"""
        try:
            realtime_api = await session_manager.get_session(session_id)
            if realtime_api:
                # Send initial greeting
                greeting = "Hello! This is a call from BhashAI. How are you today?"
                await realtime_api.send_text(greeting)
                
                self.logger.info(f"Sent greeting to session {session_id}")
        except Exception as e:
            self.logger.error(f"Error starting conversation: {e}")

    async def handle_incoming_audio(self, call_id: str, audio_data: bytes):
        """Handle incoming audio from phone call"""
        if call_id not in self.active_calls:
            self.logger.error(f"Call {call_id} not found")
            return
        
        call_info = self.active_calls[call_id]
        session_id = call_info['realtime_session_id']
        
        try:
            realtime_api = await session_manager.get_session(session_id)
            if realtime_api:
                await realtime_api.send_audio(audio_data)
                
                # Track usage
                duration_seconds = len(audio_data) // (24000 * 2)  # Approximate
                usage_tracker.track_audio_input(session_id, duration_seconds)
                
        except Exception as e:
            self.logger.error(f"Error handling incoming audio: {e}")

    async def end_call(self, call_id: str) -> Dict:
        """End an active call"""
        if call_id not in self.active_calls:
            return {'success': False, 'error': 'Call not found'}
        
        call_info = self.active_calls[call_id]
        session_id = call_info['realtime_session_id']
        
        try:
            # End OpenAI session
            await session_manager.close_session(session_id)
            
            # End phone call (mock)
            await self._end_phone_call(call_info)
            
            # Finalize usage tracking
            session_costs = usage_tracker.end_session_tracking(session_id)
            usage_tracker.log_usage_to_database(
                session_costs, 
                call_info['user_id'],
                None  # enterprise_id
            )
            
            # Update call status
            call_info['status'] = 'completed'
            call_info['ended_at'] = datetime.now(timezone.utc)
            
            # Clean up
            del self.active_calls[call_id]
            
            return {
                'success': True,
                'call_id': call_id,
                'status': 'ended',
                'duration_seconds': (call_info['ended_at'] - call_info['started_at']).total_seconds(),
                'estimated_cost': session_costs.get('estimated_cost_usd', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error ending call: {e}")
            return {'success': False, 'error': str(e)}

    async def _end_phone_call(self, call_info: Dict):
        """End the phone call with provider"""
        self.logger.info(f"MOCK: Ending call {call_info['call_id']}")
        # In real implementation, call provider's hangup API

    def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get current call status"""
        return self.active_calls.get(call_id)

    def list_active_calls(self) -> List[Dict]:
        """List all active calls"""
        return list(self.active_calls.values())

    async def get_call_analytics(self, call_id: str) -> Dict:
        """Get call analytics and cost information"""
        if call_id not in self.active_calls:
            return {'error': 'Call not found'}
        
        call_info = self.active_calls[call_id]
        session_id = call_info['realtime_session_id']
        
        # Get current session costs
        session_costs = usage_tracker.get_session_cost(session_id)
        
        if call_info['status'] == 'completed':
            duration = (call_info['ended_at'] - call_info['started_at']).total_seconds()
        else:
            duration = (datetime.now(timezone.utc) - call_info['started_at']).total_seconds()
        
        return {
            'call_id': call_id,
            'phone_number': call_info['phone_number'],
            'status': call_info['status'],
            'duration_seconds': duration,
            'estimated_cost_usd': session_costs.get('estimated_cost_usd', 0) if session_costs else 0,
            'audio_input_seconds': session_costs.get('audio_input_seconds', 0) if session_costs else 0,
            'audio_output_seconds': session_costs.get('audio_output_seconds', 0) if session_costs else 0,
            'provider': call_info['provider']
        }


# Global call manager instance
call_manager = OpenAIPhoneCallManager()


# Convenience function for making calls
async def make_call(phone_number: str, 
                   message: str = None,
                   provider: str = 'twilio',
                   user_id: str = 'demo-user') -> Dict:
    """
    Convenience function to make a call with OpenAI Realtime API
    
    Args:
        phone_number: Target phone number
        message: Custom message/instructions for the AI
        provider: Phone provider to use
        user_id: User making the call
        
    Returns:
        Dict: Call result
    """
    
    voice_config = {
        'voice': 'alloy',
        'language': 'hi-IN',
        'instructions': message or '''You are calling from BhashAI voice assistant. 
        Be polite and helpful. You can speak in Hindi and English naturally. 
        Keep the conversation friendly and brief unless the person wants to talk longer.'''
    }
    
    return await call_manager.make_outbound_call(
        phone_number=phone_number,
        voice_config=voice_config,
        provider=provider,
        user_id=user_id
    )


if __name__ == "__main__":
    async def test_call():
        """Test function to demonstrate call functionality"""
        
        # Make a test call
        result = await make_call(
            phone_number="+919373111709",
            message="Hello! This is a test call from BhashAI. I'm an AI assistant that can speak in Hindi and English. How are you today?",
            user_id="test-user"
        )
        
        print("Call Result:", json.dumps(result, indent=2))
        
        if result['success']:
            call_id = result['call_id']
            
            # Wait a bit then check status
            await asyncio.sleep(5)
            
            status = call_manager.get_call_status(call_id)
            print("Call Status:", json.dumps(status, default=str, indent=2))
            
            # Get analytics
            analytics = await call_manager.get_call_analytics(call_id)
            print("Call Analytics:", json.dumps(analytics, default=str, indent=2))
            
            # End the call after 30 seconds (for demo)
            await asyncio.sleep(25)
            end_result = await call_manager.end_call(call_id)
            print("Call End Result:", json.dumps(end_result, default=str, indent=2))
    
    # Run the test
    asyncio.run(test_call())