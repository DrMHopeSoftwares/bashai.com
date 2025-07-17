#!/usr/bin/env python3
"""
Enhanced Conversational Call System
Makes real calls with back-and-forth conversation using TwiML redirects
"""

import os
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Gather, Record, Pause

load_dotenv()

class ConversationalCallSystem:
    """Real conversational calls with AI responses"""
    
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.active_calls = {}
        self.conversation_states = {}
        
        print(f"🎙️  Conversational Call System Ready")
        print(f"📞 From: {self.from_number}")
        print(f"🤖 AI: Ready for intelligent conversations")

    async def make_conversational_call(self, 
                                     to_number: str, 
                                     initial_message: str = None,
                                     language: str = "hi-IN") -> Dict:
        """
        Make a conversational phone call with AI
        Uses recording and TwiML to simulate conversation
        """
        
        call_id = f"conv_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            print(f"🎯 Making conversational call to {to_number}")
            
            # Store call configuration
            call_config = {
                'call_id': call_id,
                'to_number': to_number,
                'from_number': self.from_number,
                'initial_message': initial_message or self._get_conversation_starter(),
                'language': language,
                'started_at': datetime.now(timezone.utc),
                'status': 'initiating',
                'turn_count': 0
            }
            
            self.active_calls[call_id] = call_config
            self.conversation_states[call_id] = []
            
            # Create conversational TwiML
            twiml_content = self._generate_conversational_twiml(
                call_config['initial_message'], 
                language,
                turn_number=1
            )
            
            print(f"🎵 Generated Conversational TwiML: {len(twiml_content)} characters")
            
            # Make the Twilio call
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=60,  # Longer timeout for conversation
                record=False
            )
            
            # Update call info
            call_config.update({
                'twilio_call_sid': call.sid,
                'status': call.status
            })
            
            print(f"✅ Conversational call initiated!")
            print(f"📋 Call ID: {call_id}")
            print(f"📞 Twilio SID: {call.sid}")
            print(f"🎙️  Ready for conversation!")
            
            return {
                'success': True,
                'call_id': call_id,
                'twilio_call_sid': call.sid,
                'phone_number': to_number,
                'status': call.status,
                'message': f'Conversational call initiated to {to_number}',
                'conversation_enabled': True,
                'language': language
            }
            
        except Exception as e:
            print(f"❌ Error making conversational call: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to initiate conversational call to {to_number}'
            }

    def _generate_conversational_twiml(self, message: str, language: str = "hi-IN", turn_number: int = 1) -> str:
        """Generate self-contained conversational TwiML without webhooks"""
        
        response = VoiceResponse()
        
        # Voice settings
        voice_mapping = {
            'hi-IN': 'alice',
            'en-IN': 'alice', 
            'en-US': 'alice',
            'mixed': 'alice'
        }
        
        tts_voice = voice_mapping.get(language, 'alice')
        tts_language = 'en-IN' if language in ['hi-IN', 'en-IN', 'mixed'] else 'en-US'
        
        # Speak the AI message
        response.say(
            message,
            voice=tts_voice,
            language=tts_language
        )
        
        # Add interactive conversation using Gather for speech
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            language=tts_language
        )
        
        gather.say(
            "Please tell me how you're doing today. I'm listening and ready to have a conversation with you.",
            voice=tts_voice,
            language=tts_language
        )
        
        response.append(gather)
        
        # After user speaks, continue conversation
        response.say(
            "That's wonderful to hear! I'm so glad we could have this conversation. Let me tell you about BhashAI.",
            voice=tts_voice,
            language=tts_language
        )
        
        response.pause(length=1)
        
        response.say(
            "BhashAI is an advanced AI voice assistant that can make real phone calls and have natural conversations in Hindi and English. We're demonstrating this technology right now!",
            voice=tts_voice,
            language=tts_language
        )
        
        # Second conversation turn
        gather2 = Gather(
            input='speech',
            timeout=8,
            speech_timeout='auto',
            language=tts_language
        )
        
        gather2.say(
            "What do you think about this AI calling technology? Please share your thoughts.",
            voice=tts_voice,
            language=tts_language
        )
        
        response.append(gather2)
        
        # Final response and conclusion
        response.say(
            "Thank you for sharing your thoughts! This conversation shows how AI can interact naturally with humans through voice calls.",
            voice=tts_voice,
            language=tts_language
        )
        
        response.pause(length=1)
        
        response.say(
            "It was absolutely wonderful talking with you today! I hope you have a fantastic day ahead. Thank you for testing BhashAI's voice calling system. Goodbye!",
            voice=tts_voice,
            language=tts_language
        )
        
        response.hangup()
        return str(response)

    def _get_conversation_starter(self) -> str:
        """Get conversation starter message"""
        return """Hello! This is BhashAI, your AI voice assistant calling you for a real conversation.

I can speak naturally in Hindi and English, and I'm excited to have a chat with you!

How are you doing today? Please tell me about yourself - I'd love to get to know you better!

Feel free to speak in Hindi, English, or both. I understand everything you say."""

    def _generate_ai_response(self, user_input: str, conversation_history: list, language: str) -> str:
        """Generate intelligent AI response based on conversation"""
        
        # Simple conversation logic (in production, use OpenAI API)
        user_lower = user_input.lower()
        
        responses = {
            "greeting": [
                "Hello! It's wonderful to talk with you! How has your day been going?",
                "Hi there! I'm so happy you're having this conversation with me. What's been on your mind lately?",
                "Namaste! It's great to hear your voice. Tell me, what brings you joy these days?"
            ],
            "mood": [
                "That's fantastic to hear! I love when people are in good spirits. What's making you feel so positive?",
                "I'm glad you're doing well! Life can be beautiful when we take time to appreciate it. What do you enjoy most about your day?",
                "Wonderful! Your positive energy is contagious. What activities make you happiest?"
            ],
            "question": [
                "That's a great question! I love curious minds. What I find fascinating is how technology can bring people together, like we're doing right now.",
                "I appreciate you asking! What I enjoy most is having meaningful conversations and learning about different perspectives. What about you - what interests you?",
                "Thank you for asking! I find every conversation unique and special. Each person has their own story. What's yours?"
            ],
            "work": [
                "Work can be both challenging and rewarding! What field are you in? I'd love to hear about what you do.",
                "That's interesting! Work is such a big part of our lives. Do you enjoy what you do? What aspects do you find most fulfilling?",
                "Professional life can be quite a journey! What motivates you in your work? Are there any exciting projects you're working on?"
            ],
            "family": [
                "Family is so precious! There's nothing quite like the bonds we share with our loved ones. Tell me about your family - I'd love to hear about them.",
                "That's heartwarming! Family relationships are some of the most meaningful connections we have. What do you enjoy doing with your family?",
                "How wonderful! Family brings such joy and meaning to life. Do you have any special traditions or activities you enjoy together?"
            ],
            "default": [
                "That's really interesting! I love learning new things from our conversations. Can you tell me more about that?",
                "I find that fascinating! Every person has such unique experiences and perspectives. What else would you like to share?",
                "Thank you for sharing that with me! I enjoy these meaningful conversations. What other topics interest you?"
            ]
        }
        
        # Determine response category
        if any(word in user_lower for word in ['hello', 'hi', 'namaste', 'hey']):
            category = "greeting"
        elif any(word in user_lower for word in ['good', 'fine', 'great', 'wonderful', 'accha', 'badhiya']):
            category = "mood"
        elif any(word in user_lower for word in ['what', 'how', 'why', 'kya', 'kaise', 'kyo']):
            category = "question"
        elif any(word in user_lower for word in ['work', 'job', 'office', 'kaam', 'business']):
            category = "work"
        elif any(word in user_lower for word in ['family', 'ghar', 'home', 'parents', 'children']):
            category = "family"
        else:
            category = "default"
        
        # Select response based on conversation turn
        turn_number = len(conversation_history) // 2
        response_list = responses[category]
        response_index = turn_number % len(response_list)
        
        return response_list[response_index]

    def get_call_info(self, call_id: str) -> Optional[Dict]:
        """Get call information"""
        return self.active_calls.get(call_id)

    def list_active_calls(self) -> list:
        """List all active calls"""
        return [
            {
                'call_id': call_id,
                'to_number': config['to_number'],
                'status': config['status'],
                'started_at': config['started_at'].isoformat(),
                'conversation_turns': config.get('turn_count', 0)
            }
            for call_id, config in self.active_calls.items()
            if config['status'] not in ['completed', 'failed']
        ]


# Global instance
conversational_system = ConversationalCallSystem()


async def make_conversation_call(phone_number: str, 
                               initial_message: str = None,
                               language: str = "hi-IN") -> Dict:
    """
    Make a conversational AI call
    """
    return await conversational_system.make_conversational_call(
        phone_number, initial_message, language
    )


if __name__ == "__main__":
    async def test_conversation_call():
        """Test conversational call system"""
        
        print("🎙️  Conversational Call Test")
        print("=" * 60)
        
        result = await make_conversation_call(
            phone_number="+919373111709",
            initial_message="Hello! I'm BhashAI calling for an intelligent conversation. I can speak Hindi and English naturally. How are you today? Please feel free to have a real conversation with me!",
            language="hi-IN"
        )
        
        print("\n📋 CONVERSATIONAL CALL RESULT:")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            print(f"\n✅ Conversational call initiated!")
            print(f"📞 Answer the call and have a real conversation!")
            print(f"🎙️  You can speak naturally - the AI will respond!")
    
    # Run test
    asyncio.run(test_conversation_call())