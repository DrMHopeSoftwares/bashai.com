#!/usr/bin/env python3
"""
Twilio + ElevenLabs Integration for Real Phone Calls
This module combines Twilio's phone capabilities with ElevenLabs' AI voice agents
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from twilio.rest import Client
    from twilio.twiml import VoiceResponse
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️  Twilio SDK not installed. Install with: pip install twilio")

from elevenlabs_integration import ElevenLabsAgentManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioElevenLabsIntegration:
    """Integration class for Twilio + ElevenLabs phone calls"""
    
    def __init__(self):
        # Twilio configuration
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        # ElevenLabs configuration
        self.elevenlabs_manager = ElevenLabsAgentManager()
        
        # Webhook URLs
        self.voice_webhook_url = os.getenv('VOICE_WEBHOOK_URL', 'https://your-domain.com/api/elevenlabs/voice-webhook')
        
        # Initialize Twilio client
        self.use_mock = not (TWILIO_AVAILABLE and self.auth_token)
        if not self.use_mock:
            self.twilio_client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio client initialized successfully")
        else:
            self.twilio_client = None
            logger.warning("⚠️  Using mock mode - Twilio credentials not configured")
    
    def create_elevenlabs_agent_for_call(self, call_config: Dict) -> Dict:
        """Create an ElevenLabs agent specifically for a phone call"""
        agent_config = {
            'name': call_config.get('agent_name', 'Phone Call Agent'),
            'description': f"AI agent for calling {call_config.get('phone_number')}",
            'language': call_config.get('language', 'en'),
            'use_case': 'phone_support',
            'voice_id': call_config.get('voice_id', '21m00Tcm4TlvDq8ikWAM'),  # Rachel
            'voice_settings': call_config.get('voice_settings', {
                'stability': 0.8,
                'similarity_boost': 0.75,
                'style': 0.2,
                'use_speaker_boost': True
            }),
            'system_prompt': call_config.get('system_prompt', 
                'You are a helpful AI assistant making a phone call. Be professional and friendly.'),
            'webhook_url': self.voice_webhook_url
        }
        
        return self.elevenlabs_manager.create_voice_agent(agent_config)
    
    def make_outbound_call(self, call_config: Dict) -> Dict:
        """Make an outbound call using Twilio + ElevenLabs"""
        try:
            phone_number = call_config.get('phone_number')
            if not phone_number:
                return {'success': False, 'error': 'Phone number is required'}
            
            # Create ElevenLabs agent for this call
            agent_result = self.create_elevenlabs_agent_for_call(call_config)
            if not agent_result['success']:
                return {'success': False, 'error': f'Failed to create agent: {agent_result.get("error")}'}
            
            agent_id = agent_result['external_agent_id']
            call_id = f'twilio-elevenlabs-{int(datetime.now().timestamp())}'
            
            if self.use_mock:
                return self._mock_outbound_call(phone_number, agent_id, call_id, call_config)
            
            # Create TwiML for the call
            twiml_url = f"{self.voice_webhook_url}?agent_id={agent_id}&call_id={call_id}"
            
            # Make the call using Twilio
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.twilio_phone,
                url=twiml_url,
                method='POST',
                record=call_config.get('record_call', False),
                timeout=30,
                status_callback=f"{self.voice_webhook_url}/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            
            logger.info(f"📞 Twilio call initiated: {call.sid}")
            
            return {
                'success': True,
                'call_id': call_id,
                'twilio_call_sid': call.sid,
                'agent_id': agent_id,
                'phone_number': phone_number,
                'status': 'initiated',
                'message': f'Call initiated to {phone_number} using ElevenLabs agent'
            }
            
        except Exception as e:
            logger.error(f"Error making outbound call: {e}")
            return {'success': False, 'error': str(e)}
    
    def _mock_outbound_call(self, phone_number: str, agent_id: str, call_id: str, call_config: Dict) -> Dict:
        """Mock outbound call for development/testing"""
        return {
            'success': True,
            'call_id': call_id,
            'twilio_call_sid': f'mock-{call_id}',
            'agent_id': agent_id,
            'phone_number': phone_number,
            'status': 'mock_initiated',
            'message': f'Mock call initiated to {phone_number} using ElevenLabs agent',
            'mock': True,
            'call_config': call_config
        }
    
    def generate_voice_twiml(self, agent_id: str, call_id: str, initial_message: str = None) -> str:
        """Generate TwiML for voice interaction with ElevenLabs agent"""
        response = VoiceResponse()
        
        # Initial greeting
        if initial_message:
            response.say(initial_message, voice='Polly.Aditi', language='hi-IN')
        else:
            response.say("Hello! Please hold while I connect you to our AI assistant.", 
                        voice='Polly.Joanna', language='en-US')
        
        # Gather speech input
        gather = response.gather(
            input='speech',
            action=f'/api/elevenlabs/process-speech?agent_id={agent_id}&call_id={call_id}',
            method='POST',
            speech_timeout='auto',
            language='en-US'
        )
        
        # If no input, repeat
        response.say("I didn't hear anything. Please speak now.")
        response.redirect(f'/api/elevenlabs/voice-webhook?agent_id={agent_id}&call_id={call_id}')
        
        return str(response)
    
    def process_speech_input(self, speech_result: str, agent_id: str, call_id: str) -> str:
        """Process speech input and generate AI response using ElevenLabs"""
        try:
            # Here you would integrate with ElevenLabs Conversational AI
            # For now, we'll create a simple response
            
            if not speech_result.strip():
                ai_response = "I didn't hear you clearly. Could you please repeat that?"
            else:
                # This would be replaced with actual ElevenLabs conversation processing
                ai_response = f"Thank you for saying: {speech_result}. How else can I help you today?"
            
            # Generate TwiML response
            response = VoiceResponse()
            response.say(ai_response, voice='Polly.Aditi', language='hi-IN')
            
            # Continue conversation
            gather = response.gather(
                input='speech',
                action=f'/api/elevenlabs/process-speech?agent_id={agent_id}&call_id={call_id}',
                method='POST',
                speech_timeout='auto'
            )
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error processing speech: {e}")
            response = VoiceResponse()
            response.say("I'm sorry, there was an error processing your request. Please try again.")
            return str(response)
    
    def handle_call_status(self, call_status_data: Dict) -> Dict:
        """Handle Twilio call status updates"""
        try:
            call_sid = call_status_data.get('CallSid')
            call_status = call_status_data.get('CallStatus')
            
            logger.info(f"📞 Call {call_sid} status: {call_status}")
            
            # Log call events
            call_log = {
                'call_sid': call_sid,
                'status': call_status,
                'timestamp': datetime.now().isoformat(),
                'duration': call_status_data.get('CallDuration'),
                'from': call_status_data.get('From'),
                'to': call_status_data.get('To')
            }
            
            # Here you would typically save to database
            logger.info(f"📊 Call Log: {json.dumps(call_log, indent=2)}")
            
            return {'success': True, 'call_log': call_log}
            
        except Exception as e:
            logger.error(f"Error handling call status: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
twilio_elevenlabs_integration = TwilioElevenLabsIntegration()

def make_test_call_to_number(phone_number: str, message: str = None, voice_id: str = None) -> Dict:
    """Convenience function to make a test call to a specific number"""
    call_config = {
        'phone_number': phone_number,
        'agent_name': f'Test Agent for {phone_number}',
        'language': 'hi' if phone_number.startswith('+91') else 'en',
        'voice_id': voice_id or '21m00Tcm4TlvDq8ikWAM',  # Rachel
        'system_prompt': f'You are calling {phone_number} for a test. Be friendly and professional.',
        'initial_message': message or 'नमस्ते! यह BhashAI से एक टेस्ट कॉल है। क्या आप मुझे सुन सकते हैं?',
        'record_call': False
    }
    
    return twilio_elevenlabs_integration.make_outbound_call(call_config)

if __name__ == "__main__":
    # Test the integration
    print("🎙️ Testing Twilio + ElevenLabs Integration")
    print("=" * 50)
    
    # Test call to +919373111709
    result = make_test_call_to_number(
        phone_number='+919373111709',
        message='नमस्ते! मैं BhashAI से एक AI असिस्टेंट हूं। यह एक टेस्ट कॉल है। आज मैं आपकी कैसे सहायता कर सकता हूं?',
        voice_id='21m00Tcm4TlvDq8ikWAM'  # Rachel voice
    )
    
    print("📞 Call Result:")
    print(json.dumps(result, indent=2))
    
    if result['success']:
        print(f"\n✅ Call initiated successfully!")
        print(f"📞 Call ID: {result['call_id']}")
        print(f"🎙️ Agent ID: {result['agent_id']}")
        print(f"📱 Phone Number: {result['phone_number']}")
        if result.get('mock'):
            print("⚠️  Running in mock mode - configure Twilio credentials for real calls")
    else:
        print(f"\n❌ Call failed: {result['error']}")
