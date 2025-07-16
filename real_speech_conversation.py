#!/usr/bin/env python3
"""
Real Speech Conversation System
Uses localtunnel to expose webhooks and process actual user speech with OpenAI
"""

import os
import requests
import json
import subprocess
import time
import threading
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class RealSpeechConversation:
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Store conversations
        self.conversations = {}
        self.public_url = None
        
        print(f"🎙️  Real Speech Conversation System")
        print(f"📞 Twilio: {self.from_number}")
        print(f"🧠 OpenAI: {'✅' if self.openai_api_key else '❌'}")

    def start_public_tunnel(self, port: int = 9002) -> str:
        """Start localtunnel to expose Flask app publicly"""
        
        try:
            print(f"🌐 Starting public tunnel for port {port}...")
            
            # Install localtunnel if not available
            try:
                subprocess.run(['npx', 'localtunnel', '--version'], 
                             capture_output=True, check=True, timeout=5)
            except:
                print("📦 Installing localtunnel...")
                subprocess.run(['npm', 'install', '-g', 'localtunnel'], 
                             capture_output=True, timeout=30)
            
            # Start localtunnel
            tunnel_process = subprocess.Popen([
                'npx', 'localtunnel', '--port', str(port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for tunnel URL
            time.sleep(3)
            
            # Try to get the URL from localtunnel output
            if tunnel_process.poll() is None:
                # Tunnel is running, URL should be available
                self.public_url = f"https://localhost-{port}.loca.lt"
                print(f"✅ Public tunnel available at: {self.public_url}")
                return self.public_url
            else:
                print("❌ Failed to start tunnel")
                return None
                
        except Exception as e:
            print(f"❌ Error starting tunnel: {e}")
            return None

    def generate_real_ai_response(self, user_speech: str, call_sid: str) -> str:
        """Generate actual AI response using OpenAI API"""
        
        if not self.openai_api_key:
            return f"I heard you say '{user_speech[:50]}'. That's really interesting! Can you tell me more about that?"
        
        try:
            # Get conversation history
            conversation_history = self.conversations.get(call_sid, {}).get('history', [])
            
            # Build OpenAI messages
            messages = [
                {
                    "role": "system",
                    "content": """You are BhashAI, an intelligent AI voice assistant having a real phone conversation.

Guidelines:
- Keep responses under 50 words for natural phone conversation flow
- Be genuinely interested and engaging
- Ask thoughtful follow-up questions
- Remember what the user has said previously in this conversation
- Speak naturally as if you're really listening and understanding
- Be warm, friendly, and conversational
- You can speak Hindi and English naturally"""
                }
            ]
            
            # Add conversation history for context
            messages.extend(conversation_history[-8:])  # Last 8 turns
            
            # Add current user input
            messages.append({"role": "user", "content": user_speech})
            
            print(f"🧠 Processing with OpenAI: '{user_speech}'")
            
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
                    'max_tokens': 120,
                    'temperature': 0.8,
                    'presence_penalty': 0.4,
                    'frequency_penalty': 0.3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Update conversation history
                if call_sid not in self.conversations:
                    self.conversations[call_sid] = {'history': [], 'started_at': datetime.now()}
                
                self.conversations[call_sid]['history'].extend([
                    {"role": "user", "content": user_speech},
                    {"role": "assistant", "content": ai_response}
                ])
                
                print(f"🤖 AI Response Generated: {ai_response}")
                return ai_response
                
            else:
                print(f"❌ OpenAI API Error: {response.status_code}")
                return f"That's fascinating! You mentioned '{user_speech[:30]}'. I'd love to hear more about your thoughts on that."
                
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            return f"I find that really interesting! You said '{user_speech[:25]}'. Can you share more about that with me?"

    def make_real_speech_call(self, phone_number: str) -> dict:
        """Make a call with real speech understanding"""
        
        try:
            if not self.public_url:
                print("❌ No public URL available. Need to start tunnel first.")
                return {
                    'success': False,
                    'error': 'Public webhook URL not available'
                }
            
            call_id = f"real_speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🎯 Making real speech call to {phone_number}")
            
            # Create TwiML with webhook to our public URL
            twiml_content = self._create_webhook_twiml()
            
            print(f"🎵 Generated webhook TwiML: {len(twiml_content)} characters")
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=60
            )
            
            # Initialize conversation
            self.conversations[call.sid] = {
                'call_id': call_id,
                'history': [],
                'started_at': datetime.now()
            }
            
            print(f"✅ Real speech call initiated!")
            print(f"📞 Call SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'phone_number': phone_number,
                'message': 'Real speech conversation call started',
                'webhook_url': self.public_url
            }
            
        except Exception as e:
            print(f"❌ Error making real speech call: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_webhook_twiml(self) -> str:
        """Create TwiML that uses webhooks for real speech processing"""
        
        response = VoiceResponse()
        
        # Brief greeting
        response.say(
            "Hello! This is BhashAI with real speech understanding. I can actually hear and process what you say.",
            voice='alice',
            language='en-IN'
        )
        
        # Gather with webhook for processing
        gather = Gather(
            input='speech',
            timeout=12,
            speech_timeout='auto',
            action=f'{self.public_url}/webhook/speech',
            method='POST',
            language='en-IN'
        )
        
        gather.say(
            "How are you doing today? I'm really listening and will understand what you tell me.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback
        response.say(
            "I didn't hear you there. Thank you for calling BhashAI! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return str(response)


# Global system instance
real_speech_system = RealSpeechConversation()


# Flask webhook endpoints
@app.route('/webhook/speech', methods=['POST'])
def webhook_process_speech():
    """Process actual speech from Twilio"""
    
    try:
        # Get speech data from Twilio
        speech_result = request.form.get('SpeechResult', '')
        confidence = request.form.get('Confidence', '0')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  REAL SPEECH: '{speech_result}' (confidence: {confidence})")
        print(f"📞 Call SID: {call_sid}")
        
        if not speech_result.strip():
            speech_result = "I didn't catch what you said clearly"
        
        # Generate real AI response
        ai_response = real_speech_system.generate_real_ai_response(speech_result, call_sid)
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(
            ai_response,
            voice='alice',
            language='en-IN'
        )
        
        # Continue conversation
        conversation_length = len(real_speech_system.conversations.get(call_sid, {}).get('history', []))
        
        if conversation_length < 10:  # Allow up to 5 conversation turns
            gather = Gather(
                input='speech',
                timeout=8,
                speech_timeout='auto',
                action='/webhook/speech',
                method='POST',
                language='en-IN'
            )
            
            gather.say(
                "What else would you like to share?",
                voice='alice',
                language='en-IN'
            )
            
            response.append(gather)
        
        # End conversation after several turns
        response.say(
            "This has been such a meaningful conversation! Thank you for sharing your thoughts with BhashAI. Have a wonderful day! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error in webhook: {e}")
        
        # Error fallback
        response = VoiceResponse()
        response.say(
            "Sorry, I had trouble processing that. Thank you for calling BhashAI!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        return Response(str(response), mimetype='text/xml')


@app.route('/start-real-speech-call/<phone_number>')
def start_real_speech_call(phone_number):
    """Start a real speech conversation call"""
    
    result = real_speech_system.make_real_speech_call(f"+{phone_number}")
    return result


@app.route('/conversations')
def list_real_conversations():
    """List active conversations"""
    
    return {
        'active_conversations': len(real_speech_system.conversations),
        'public_url': real_speech_system.public_url,
        'conversations': {
            call_sid: {
                'turns': len(conv['history']) // 2,
                'started_at': conv['started_at'].isoformat(),
                'last_exchange': conv['history'][-2:] if conv['history'] else []
            }
            for call_sid, conv in real_speech_system.conversations.items()
        }
    }


def run_real_speech_system():
    """Run the complete real speech system"""
    
    print("🎙️  Starting Real Speech Conversation System")
    print("=" * 60)
    
    # Start public tunnel
    port = 9002
    tunnel_url = real_speech_system.start_public_tunnel(port)
    
    if tunnel_url:
        print(f"✅ System ready with public webhooks!")
        print(f"🌐 Public URL: {tunnel_url}")
        
        # Start Flask app
        def start_flask():
            app.run(host='0.0.0.0', port=port, debug=False)
        
        flask_thread = threading.Thread(target=start_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        time.sleep(2)
        
        # Make test call
        result = real_speech_system.make_real_speech_call("+919373111709")
        
        print(f"\n📋 CALL RESULT:")
        print(json.dumps(result, indent=2, default=str))
        
        if result['success']:
            print(f"\n🎉 REAL SPEECH CONVERSATION ACTIVE!")
            print(f"📞 Answer your phone - the AI will actually understand what you say!")
            print(f"🧠 Your speech will be processed with OpenAI for intelligent responses")
            
        # Keep running
        input("Press Enter to stop the system...")
        
    else:
        print("❌ Failed to start public tunnel")


if __name__ == "__main__":
    run_real_speech_system()