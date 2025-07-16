#!/usr/bin/env python3
"""
Working Conversation System
Creates real AI conversations with proper speech processing using public webhooks
"""

import os
import requests
import json
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class WorkingConversationSystem:
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Store conversations
        self.conversations = {}
        
        print(f"🎙️  Working Conversation System Ready")
        print(f"📞 Twilio: {self.from_number}")
        print(f"🧠 OpenAI: {'✅' if self.openai_api_key else '❌'}")

    def generate_intelligent_response(self, user_speech: str, conversation_history: list = None) -> str:
        """Generate real AI response using OpenAI"""
        
        if not self.openai_api_key:
            return f"I heard you say '{user_speech}'. That's interesting! Tell me more."
        
        try:
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": """You are BhashAI, a friendly AI voice assistant having a phone conversation. 

Guidelines:
- Keep responses under 40 words for natural phone conversation
- Be warm, engaging, and show genuine interest
- Ask follow-up questions to keep conversation flowing
- You can speak Hindi and English naturally
- Remember previous parts of the conversation
- Be conversational and spontaneous"""
                }
            ]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Last 6 turns for context
            
            # Add current user input
            messages.append({"role": "user", "content": user_speech})
            
            # Call OpenAI API
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4',
                    'messages': messages,
                    'max_tokens': 100,
                    'temperature': 0.8,
                    'presence_penalty': 0.3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                print(f"🤖 AI Generated: {ai_response}")
                return ai_response
            else:
                print(f"❌ OpenAI API Error: {response.status_code}")
                return f"I find that fascinating! You mentioned '{user_speech[:30]}'. Can you tell me more about that?"
                
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return f"That's really interesting! You said '{user_speech[:25]}'. I'd love to hear more about your thoughts!"

    def make_working_conversation_call(self, phone_number: str) -> dict:
        """Make a call with working conversation processing"""
        
        try:
            call_id = f"working_conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🎯 Making working conversation call to {phone_number}")
            
            # For this demo, we'll use a public webhook service
            # In production, you'd use ngrok or deploy to a public server
            webhook_base = "https://webhook.site/unique-id"  # Replace with actual webhook
            
            # Create initial TwiML with webhook
            twiml_content = self._create_initial_twiml(webhook_base)
            
            print(f"🎵 Generated working TwiML: {len(twiml_content)} characters")
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=60
            )
            
            # Store conversation
            self.conversations[call.sid] = {
                'call_id': call_id,
                'history': [],
                'started_at': datetime.now()
            }
            
            print(f"✅ Working conversation call initiated!")
            print(f"📞 Call SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'phone_number': phone_number,
                'message': 'Working conversation call with real speech processing started'
            }
            
        except Exception as e:
            print(f"❌ Error making working call: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_initial_twiml(self, webhook_base: str) -> str:
        """Create initial TwiML that uses webhooks for speech processing"""
        
        response = VoiceResponse()
        
        # Brief greeting
        response.say(
            "Hi! This is BhashAI ready for a real conversation.",
            voice='alice',
            language='en-IN'
        )
        
        # Gather with webhook for processing
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f'{webhook_base}/process-speech',
            method='POST',
            language='en-IN'
        )
        
        gather.say(
            "How are you today? I'm listening and will understand what you say.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback
        response.say(
            "Thanks for calling BhashAI! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return str(response)


# Global system instance
working_system = WorkingConversationSystem()


# Flask webhook endpoints
@app.route('/process-speech', methods=['POST'])
def process_speech():
    """Process speech from Twilio and generate AI response"""
    
    try:
        # Get speech data from Twilio
        speech_result = request.form.get('SpeechResult', '')
        confidence = request.form.get('Confidence', '0')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  User said: '{speech_result}' (confidence: {confidence})")
        print(f"📞 Call SID: {call_sid}")
        
        if not speech_result.strip():
            speech_result = "I didn't hear you clearly"
        
        # Get conversation history
        conversation_history = []
        if call_sid in working_system.conversations:
            conversation_history = working_system.conversations[call_sid]['history']
        
        # Generate AI response
        ai_response = working_system.generate_intelligent_response(
            speech_result, 
            conversation_history
        )
        
        # Update conversation history
        if call_sid not in working_system.conversations:
            working_system.conversations[call_sid] = {'history': [], 'started_at': datetime.now()}
        
        working_system.conversations[call_sid]['history'].extend([
            {"role": "user", "content": speech_result},
            {"role": "assistant", "content": ai_response}
        ])
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(
            ai_response,
            voice='alice',
            language='en-IN'
        )
        
        # Continue conversation
        gather = Gather(
            input='speech',
            timeout=8,
            speech_timeout='auto',
            action='/process-speech',
            method='POST',
            language='en-IN'
        )
        
        gather.say(
            "What else would you like to talk about?",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # End conversation after several turns
        if len(working_system.conversations[call_sid]['history']) >= 8:
            response.say(
                "This has been a wonderful conversation! Thank you for talking with BhashAI. Have a great day! Goodbye!",
                voice='alice',
                language='en-IN'
            )
            response.hangup()
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error processing speech: {e}")
        
        # Error fallback
        response = VoiceResponse()
        response.say(
            "Sorry, I had trouble understanding. Thank you for calling BhashAI!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        return Response(str(response), mimetype='text/xml')


@app.route('/start-working-call/<phone_number>')
def start_working_call(phone_number):
    """Start a working conversation call"""
    
    result = working_system.make_working_conversation_call(f"+{phone_number}")
    return result


@app.route('/conversations')
def list_conversations():
    """List active conversations"""
    
    return {
        'active_conversations': len(working_system.conversations),
        'conversations': {
            call_sid: {
                'turns': len(conv['history']) // 2,
                'started_at': conv['started_at'].isoformat()
            }
            for call_sid, conv in working_system.conversations.items()
        }
    }


if __name__ == '__main__':
    print("🎙️  Starting Working Conversation System")
    print("📋 Instructions:")
    print("   1. This creates a Flask server for webhook processing")
    print("   2. You need to expose this server publicly (using ngrok or similar)")
    print("   3. Update webhook_base URL to your public server")
    print("   4. Then make calls with real speech understanding")
    print("")
    print("🔗 Endpoints:")
    print("   - /process-speech - Handle speech from Twilio")
    print("   - /start-working-call/<phone> - Start conversation call")
    print("   - /conversations - List active conversations")
    print("")
    
    # Start the server
    port = int(os.environ.get('PORT', 9001))
    app.run(host='0.0.0.0', port=port, debug=True)