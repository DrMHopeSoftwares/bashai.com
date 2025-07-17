#!/usr/bin/env python3
"""
Real AI Conversation with ngrok
Uses ngrok to expose webhooks publicly so AI can actually process speech
"""

import os
import subprocess
import requests
import json
import time
import threading
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class RealAIWithNgrok:
    def __init__(self):
        # Load credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.ngrok_token = os.getenv('NGROK_AUTH_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.ngrok_url = None
        self.conversations = {}
        
        print(f"🎙️  Real AI Conversation with ngrok")
        print(f"📞 Twilio: {self.from_number}")
        print(f"🌐 ngrok: {'✅' if self.ngrok_token else '❌'}")
        print(f"🧠 OpenAI: {'✅' if self.openai_api_key else '❌'}")

    def setup_ngrok(self, port: int = 8001) -> str:
        """Set up ngrok tunnel for public webhook access"""
        
        try:
            print(f"🌐 Setting up ngrok tunnel for port {port}...")
            
            # Configure ngrok with auth token
            if self.ngrok_token:
                subprocess.run(['ngrok', 'config', 'add-authtoken', self.ngrok_token], 
                             capture_output=True, timeout=10)
            
            # Start ngrok tunnel
            self.ngrok_process = subprocess.Popen([
                'ngrok', 'http', str(port), '--log', 'stdout'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for tunnel to start
            time.sleep(5)
            
            # Get public URL from ngrok API
            try:
                response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        self.ngrok_url = tunnels[0]['public_url']
                        print(f"✅ ngrok tunnel active: {self.ngrok_url}")
                        return self.ngrok_url
            except:
                pass
            
            print("❌ Failed to get ngrok URL")
            return None
            
        except Exception as e:
            print(f"❌ Error setting up ngrok: {e}")
            return None

    def generate_intelligent_response(self, user_speech: str, call_sid: str) -> str:
        """Generate intelligent AI response using OpenAI"""
        
        if not self.openai_api_key:
            return self._generate_contextual_fallback(user_speech)
        
        try:
            # Get conversation history
            conversation_history = self.conversations.get(call_sid, {}).get('history', [])
            
            # Build OpenAI messages
            messages = [
                {
                    "role": "system",
                    "content": """You are BhashAI, an intelligent AI voice assistant having a real phone conversation.

You are actually listening to and understanding what the user says. Key guidelines:
- Respond directly to their specific words and topics
- Keep responses under 50 words for natural phone conversation
- Ask relevant follow-up questions based on what they said
- Show that you understood their specific message by referencing it
- Be warm, engaging, and genuinely interested
- You can speak Hindi and English naturally
- Remember previous parts of the conversation"""
                }
            ]
            
            # Add conversation history
            messages.extend(conversation_history[-6:])  # Last 6 turns
            
            # Add current user input
            messages.append({"role": "user", "content": user_speech})
            
            print(f"🧠 Generating AI response for: '{user_speech}'")
            
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
                    'presence_penalty': 0.4
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Update conversation history
                if call_sid not in self.conversations:
                    self.conversations[call_sid] = {'history': []}
                
                self.conversations[call_sid]['history'].extend([
                    {"role": "user", "content": user_speech},
                    {"role": "assistant", "content": ai_response}
                ])
                
                print(f"🤖 AI Response: {ai_response}")
                return ai_response
                
            else:
                print(f"❌ OpenAI API Error: {response.status_code}")
                return self._generate_contextual_fallback(user_speech)
                
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            return self._generate_contextual_fallback(user_speech)

    def _generate_contextual_fallback(self, user_speech: str) -> str:
        """Generate contextual fallback response"""
        
        user_lower = user_speech.lower()
        
        # Respond based on actual speech content
        if any(word in user_lower for word in ['good', 'great', 'fine', 'excellent']):
            return f"That's wonderful! You said you're doing {[w for w in user_speech.split() if w.lower() in ['good', 'great', 'fine', 'excellent']][0]}. What's making your day so positive?"
        
        elif any(word in user_lower for word in ['work', 'job', 'business']):
            return f"Interesting! You mentioned something about work. What kind of work do you do?"
        
        elif any(word in user_lower for word in ['family', 'home', 'kids']):
            return f"Family is important! You talked about family. Tell me more about that."
        
        elif any(word in user_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello! Nice to hear from you. How are you doing today?"
        
        else:
            return f"I heard you say '{user_speech[:30]}...' - that's interesting! Can you tell me more about that?"

    def make_real_ai_call(self, phone_number: str) -> dict:
        """Make a call with real AI speech processing"""
        
        if not self.ngrok_url:
            return {
                'success': False,
                'error': 'ngrok tunnel not available'
            }
        
        try:
            call_id = f"real_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🎯 Making real AI call to {phone_number}")
            print(f"🌐 Using webhook: {self.ngrok_url}")
            
            # Create TwiML with real webhook
            twiml_content = self._create_real_ai_twiml()
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=90
            )
            
            print(f"✅ Real AI call initiated!")
            print(f"📞 Call SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'phone_number': phone_number,
                'message': 'Real AI call with speech processing started'
            }
            
        except Exception as e:
            print(f"❌ Error making real AI call: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_real_ai_twiml(self) -> str:
        """Create TwiML with real webhook for AI processing"""
        
        response = VoiceResponse()
        
        # Introduction
        response.say(
            "Hello! This is BhashAI with real AI speech processing. I can actually understand and respond to what you say.",
            voice='alice',
            language='en-IN'
        )
        
        # Start conversation with webhook
        gather = Gather(
            input='speech',
            timeout=12,
            speech_timeout='auto',
            action=f'{self.ngrok_url}/process-speech',
            method='POST',
            language='en-IN'
        )
        
        gather.say(
            "How are you doing today? Please tell me about yourself - I'm genuinely listening and will understand what you say.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback
        response.say(
            "Thank you for calling BhashAI! Have a great day!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return str(response)


# Global instance
real_ai_system = RealAIWithNgrok()


# Flask webhook routes
@app.route('/process-speech', methods=['POST'])
def process_speech():
    """Process speech from Twilio and generate real AI response"""
    
    try:
        # Get speech data from Twilio
        speech_result = request.form.get('SpeechResult', '')
        confidence = request.form.get('Confidence', '0')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  REAL SPEECH RECEIVED: '{speech_result}' (confidence: {confidence})")
        print(f"📞 Call SID: {call_sid}")
        
        if not speech_result.strip():
            speech_result = "I didn't hear you clearly"
        
        # Generate real AI response
        ai_response = real_ai_system.generate_intelligent_response(speech_result, call_sid)
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(
            ai_response,
            voice='alice',
            language='en-IN'
        )
        
        # Continue conversation
        conversation_length = len(real_ai_system.conversations.get(call_sid, {}).get('history', []))
        
        if conversation_length < 8:  # Allow multiple turns
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
        
        # End conversation
        response.say(
            "This has been a wonderful conversation! Thank you for talking with BhashAI. Have a great day! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error in speech processing: {e}")
        
        # Error fallback
        response = VoiceResponse()
        response.say(
            "Sorry, I had trouble understanding. Thank you for calling BhashAI!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        return Response(str(response), mimetype='text/xml')


@app.route('/status')
def status():
    """Check system status"""
    return {
        'status': 'running',
        'ngrok_url': real_ai_system.ngrok_url,
        'active_conversations': len(real_ai_system.conversations)
    }


def run_real_ai_system():
    """Run the complete real AI system with ngrok"""
    
    print("🎙️  Starting Real AI Conversation System with ngrok")
    print("=" * 70)
    
    # Start ngrok tunnel
    port = 8001
    if real_ai_system.setup_ngrok(port):
        print(f"✅ System ready with public webhooks!")
        
        # Start Flask app in background
        def start_flask():
            app.run(host='0.0.0.0', port=port, debug=False)
        
        flask_thread = threading.Thread(target=start_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        time.sleep(2)
        
        # Make real AI call
        result = real_ai_system.make_real_ai_call("+919373111709")
        
        print(f"\n📋 CALL RESULT:")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            print(f"\n🎉 REAL AI CONVERSATION ACTIVE!")
            print(f"📞 Answer your phone - the AI will ACTUALLY understand what you say!")
            print(f"🧠 Your speech will be processed with real AI responses")
            print(f"💬 The AI will respond specifically to your words")
            
            # Keep system running
            input("\nPress Enter to stop the system...")
        
    else:
        print("❌ Failed to start ngrok tunnel")


if __name__ == "__main__":
    run_real_ai_system()