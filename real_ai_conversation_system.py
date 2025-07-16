#!/usr/bin/env python3
"""
Real AI Conversation System
Integrates OpenAI API for dynamic, intelligent responses during phone calls
Uses Flask webhook to process speech and generate real AI responses
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class RealAIConversation:
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"
        
        # OpenAI API
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.conversations = {}  # Store conversation history per call
        
        print(f"🤖 Real AI Conversation System Ready")
        print(f"📞 Twilio: {self.from_number}")
        print(f"🧠 OpenAI: {'✅ Connected' if self.openai_api_key else '❌ No API Key'}")

    def generate_ai_response(self, user_speech: str, call_sid: str) -> str:
        """Generate real AI response using OpenAI API"""
        
        if not self.openai_api_key:
            return "I'm sorry, my AI brain isn't connected right now. But I'm still here to talk with you!"
        
        try:
            # Get conversation history
            conversation_history = self.conversations.get(call_sid, [])
            
            # Build conversation context for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """You are BhashAI, a friendly and intelligent AI voice assistant. You're having a real phone conversation with someone who called you. 

Key guidelines:
- Keep responses conversational and under 50 words
- You can speak Hindi and English naturally  
- Be warm, engaging, and curious about the person
- Ask follow-up questions to keep conversation flowing
- Remember you're on a phone call, so be natural and spontaneous
- Show genuine interest in what they say
- Be helpful and informative when appropriate"""
                }
            ]
            
            # Add conversation history
            for turn in conversation_history[-6:]:  # Last 6 turns for context
                messages.append(turn)
            
            # Add current user input
            messages.append({"role": "user", "content": user_speech})
            
            # Call OpenAI API for intelligent response
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4',
                    'messages': messages,
                    'max_tokens': 100,  # Keep responses concise for phone calls
                    'temperature': 0.8,  # More creative responses
                    'presence_penalty': 0.3,  # Encourage variety
                    'frequency_penalty': 0.3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Update conversation history
                if call_sid not in self.conversations:
                    self.conversations[call_sid] = []
                
                self.conversations[call_sid].append({"role": "user", "content": user_speech})
                self.conversations[call_sid].append({"role": "assistant", "content": ai_response})
                
                print(f"🧠 AI Generated: {ai_response}")
                return ai_response
            else:
                print(f"❌ OpenAI API Error: {response.status_code}")
                return self._fallback_response(user_speech)
                
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            return self._fallback_response(user_speech)
    
    def _fallback_response(self, user_speech: str) -> str:
        """Fallback when OpenAI is unavailable"""
        return f"I heard you mention '{user_speech[:30]}...' - that's interesting! Tell me more about that."

    def make_ai_conversation_call(self, phone_number: str) -> dict:
        """Initiate a call with real AI conversation"""
        
        try:
            call_id = f"ai_conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create initial TwiML that starts conversation
            initial_twiml = self._create_conversation_starter()
            
            print(f"🎯 Making real AI conversation call to {phone_number}")
            print(f"🎵 TwiML length: {len(initial_twiml)} characters")
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=initial_twiml,
                timeout=60
            )
            
            print(f"✅ AI conversation call initiated!")
            print(f"📞 Twilio SID: {call.sid}")
            
            return {
                'success': True,
                'call_id': call_id,
                'twilio_sid': call.sid,
                'phone_number': phone_number,
                'message': 'Real AI conversation call started'
            }
            
        except Exception as e:
            print(f"❌ Error making AI call: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_conversation_starter(self) -> str:
        """Create TwiML that starts the AI conversation"""
        
        response = VoiceResponse()
        
        # Initial AI greeting
        response.say(
            "Hello! This is BhashAI, your intelligent AI assistant. I'm excited to have a real conversation with you using advanced artificial intelligence!",
            voice='alice',
            language='en-IN'
        )
        
        # Start the conversation by listening
        gather = Gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action=f'http://localhost:8001/ai-webhook/process-speech',  # This will need ngrok
            method='POST',
            language='en-IN'
        )
        
        gather.say(
            "How are you doing today? Please tell me about yourself - I'm genuinely curious to learn about you!",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback if no speech detected
        response.say(
            "I didn't hear you there. Thank you for calling BhashAI! Have a wonderful day!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return str(response)


# Global AI conversation system
ai_conversation = RealAIConversation()


# Flask webhook endpoints for real-time AI conversation
@app.route('/ai-webhook/process-speech', methods=['POST'])
def process_speech():
    """Process user speech and generate real AI response"""
    
    try:
        # Get speech data from Twilio
        speech_result = request.form.get('SpeechResult', '')
        confidence = request.form.get('Confidence', '0')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  User said: '{speech_result}' (confidence: {confidence})")
        print(f"📞 Call SID: {call_sid}")
        
        if not speech_result.strip():
            speech_result = "I didn't hear anything clearly"
        
        # Generate real AI response using OpenAI
        ai_response = ai_conversation.generate_ai_response(speech_result, call_sid)
        
        # Create TwiML response with AI-generated content
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(
            ai_response,
            voice='alice',
            language='en-IN'
        )
        
        # Continue conversation - listen for next response
        gather = Gather(
            input='speech',
            timeout=8,
            speech_timeout='auto',
            action='/ai-webhook/process-speech',
            method='POST',
            language='en-IN'
        )
        
        # Check if conversation should continue
        if len(ai_conversation.conversations.get(call_sid, [])) < 10:  # Max 5 conversation turns
            gather.say(
                "What would you like to talk about next?",
                voice='alice',
                language='en-IN'
            )
            response.append(gather)
        
        # End conversation after several turns
        response.say(
            "It's been absolutely wonderful having this intelligent conversation with you! Thank you for experiencing BhashAI's real AI technology. Have a fantastic day! Goodbye!",
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
            "I encountered a technical issue, but thank you for calling BhashAI! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        return Response(str(response), mimetype='text/xml')


@app.route('/start-ai-call/<phone_number>')
def start_ai_call(phone_number):
    """Endpoint to start an AI conversation call"""
    
    result = ai_conversation.make_ai_conversation_call(f"+{phone_number}")
    return result


@app.route('/status')
def status():
    """System status"""
    return {
        'status': 'running',
        'active_conversations': len(ai_conversation.conversations),
        'openai_connected': bool(ai_conversation.openai_api_key)
    }


if __name__ == '__main__':
    print("🤖 Starting Real AI Conversation System")
    print("🔗 Endpoints:")
    print("   - /ai-webhook/process-speech - Process user speech with AI")
    print("   - /start-ai-call/<phone_number> - Start AI conversation")
    print("   - /status - System status")
    print("")
    print("⚠️  NOTE: This requires ngrok to expose webhooks to Twilio")
    print("   Run: ngrok http 8000")
    print("")
    
    # For testing, make a direct call
    if len(os.sys.argv) > 1 and os.sys.argv[1] == 'test':
        result = ai_conversation.make_ai_conversation_call("+919373111709")
        print(f"\n📋 RESULT: {json.dumps(result, indent=2)}")
    else:
        port = int(os.environ.get('PORT', 8001))
        app.run(host='0.0.0.0', port=port, debug=True)