#!/usr/bin/env python3
"""
Advanced Webhook-based AI System
Uses Flask webhooks to process real-time speech and generate AI responses
This demonstrates true conversational AI with actual speech processing
"""

import os
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

class AdvancedWebhookAI:
    def __init__(self):
        # Credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.from_number = "+19896621396"
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        
        # Conversation storage
        self.conversations = {}
        
        # Local server URL (for testing without ngrok)
        self.base_url = "http://localhost:8002"
        
        print(f"🎙️  Advanced Webhook-based AI System")
        print(f"📞 Twilio: {'✅' if self.account_sid else '❌'}")
        print(f"🧠 OpenAI: {'✅' if self.openai_api_key else '❌'}")
        print(f"🌐 Webhook Base: {self.base_url}")

    def generate_contextual_ai_response(self, user_speech: str, call_sid: str, turn_number: int = 1) -> str:
        """Generate contextual AI response based on conversation turn"""
        
        if not self.openai_api_key:
            return self._generate_contextual_fallback(user_speech, turn_number)
        
        try:
            # Get conversation context
            conversation = self.conversations.get(call_sid, {})
            history = conversation.get('history', [])
            
            # Create turn-specific system prompt
            if turn_number == 1:
                context = "This is the introduction turn. The user is sharing their name and current mood/feeling."
            elif turn_number == 2:
                context = "This is the interests turn. The user is sharing what's important to them - work, family, hobbies, etc."
            elif turn_number == 3:
                context = "This is the AI discussion turn. The user is sharing their thoughts about AI technology."
            else:
                context = "This is a follow-up conversation."
            
            system_prompt = f"""You are BhashAI, having a real phone conversation with a user.

{context}

User just said: "{user_speech}"

Guidelines:
- Respond directly to what they actually said
- Reference specific words or phrases they used
- Keep responses under 45 words for natural phone conversation
- Ask a relevant follow-up question based on their response
- Show genuine understanding of their message
- Be warm and engaging
- You can speak Hindi/English naturally

Previous conversation: {history[-4:] if history else 'None'}"""

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4',
                    'messages': [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_speech}
                    ],
                    'max_tokens': 100,
                    'temperature': 0.8,
                    'presence_penalty': 0.3
                },
                timeout=8
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Store in conversation history
                if call_sid not in self.conversations:
                    self.conversations[call_sid] = {'history': []}
                
                self.conversations[call_sid]['history'].extend([
                    {"role": "user", "content": user_speech},
                    {"role": "assistant", "content": ai_response}
                ])
                
                print(f"🤖 AI Response (Turn {turn_number}): {ai_response}")
                return ai_response
                
            else:
                print(f"❌ OpenAI Error: {response.status_code}")
                return self._generate_contextual_fallback(user_speech, turn_number)
                
        except Exception as e:
            print(f"❌ Error generating AI response: {e}")
            return self._generate_contextual_fallback(user_speech, turn_number)

    def _generate_contextual_fallback(self, user_speech: str, turn_number: int) -> str:
        """Generate intelligent fallback responses"""
        
        user_lower = user_speech.lower()
        words = user_speech.split()
        
        if turn_number == 1:  # Introduction turn
            if any(word in user_lower for word in ['good', 'great', 'fine', 'excellent']):
                feeling = next((w for w in words if w.lower() in ['good', 'great', 'fine', 'excellent']), 'positive')
                return f"That's wonderful! You said you're {feeling}. What's been making your day so {feeling}?"
            elif any(word in user_lower for word in ['tired', 'busy', 'stressed']):
                feeling = next((w for w in words if w.lower() in ['tired', 'busy', 'stressed']), 'busy')
                return f"I understand you're {feeling}. What's been keeping you so {feeling} lately?"
            else:
                return f"Thanks for sharing! You mentioned '{user_speech[:25]}...' - tell me more about yourself!"
        
        elif turn_number == 2:  # Interests turn
            if any(word in user_lower for word in ['work', 'job', 'career']):
                return f"Work is important! You mentioned '{user_speech[:30]}...' about work. What field are you in?"
            elif any(word in user_lower for word in ['family', 'home', 'kids']):
                return f"Family is precious! You talked about '{user_speech[:30]}...' - family brings such joy, doesn't it?"
            else:
                return f"That's fascinating! You said '{user_speech[:30]}...' - what draws you to that?"
        
        elif turn_number == 3:  # AI discussion turn
            if any(word in user_lower for word in ['excited', 'amazing', 'great']):
                return f"I'm glad you're excited! You said '{user_speech[:30]}...' - what excites you most about AI?"
            elif any(word in user_lower for word in ['worried', 'concerned', 'scary']):
                return f"Your concerns are valid. You mentioned '{user_speech[:30]}...' - what worries you most?"
            else:
                return f"Interesting perspective! You said '{user_speech[:30]}...' - that's a thoughtful view on AI."
        
        else:
            return f"I heard you say '{user_speech[:35]}...' - that's really interesting! Can you elaborate?"

    def create_advanced_webhook_twiml(self) -> str:
        """Create TwiML that uses webhooks for real-time processing"""
        
        response = VoiceResponse()
        
        # Introduction
        response.say(
            "Hello! This is BhashAI with advanced webhook-based AI conversation. I will process your speech in real-time and generate intelligent responses.",
            voice='alice',
            language='en-IN'
        )
        
        # === TURN 1: Introduction with webhook ===
        gather1 = Gather(
            input='speech',
            timeout=12,
            speech_timeout='auto',
            action=f'{self.base_url}/process-turn-1',
            method='POST',
            language='en-IN'
        )
        
        gather1.say(
            "First, please tell me your name and how you're feeling today. I'm listening and will respond to your specific words.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather1)
        
        # Fallback if no speech
        response.say(
            "I didn't catch that. Thank you for trying the advanced AI system!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
        
        return str(response)

    def create_turn_response_twiml(self, ai_response: str, next_turn: int, call_sid: str) -> str:
        """Create TwiML for continuing the conversation"""
        
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(ai_response, voice='alice', language='en-IN')
        
        if next_turn == 2:
            # Turn 2: Interests
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action=f'{self.base_url}/process-turn-2',
                method='POST',
                language='en-IN'
            )
            
            gather.say(
                "Now tell me about something important to you - your work, family, hobbies, or interests. I'll understand and respond to what you share.",
                voice='alice',
                language='en-IN'
            )
            
            response.append(gather)
            
        elif next_turn == 3:
            # Turn 3: AI Discussion
            gather = Gather(
                input='speech',
                timeout=8,
                speech_timeout='auto',
                action=f'{self.base_url}/process-turn-3',
                method='POST',
                language='en-IN'
            )
            
            gather.say(
                "Finally, what are your thoughts about AI technology like this conversation? I'll process your perspective and respond accordingly.",
                voice='alice',
                language='en-IN'
            )
            
            response.append(gather)
            
        else:
            # Final turn
            response.say(
                "This has been a wonderful demonstration of advanced AI conversation! I've been processing your actual speech and generating intelligent responses in real-time. Thank you for this genuine exchange! Goodbye!",
                voice='alice',
                language='en-IN'
            )
            response.hangup()
        
        return str(response)

    def make_advanced_webhook_call(self, phone_number: str) -> dict:
        """Make a call with advanced webhook processing"""
        
        try:
            call_id = f"webhook_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"🎯 Making advanced webhook AI call to {phone_number}")
            
            # Create TwiML with webhook
            twiml_content = self.create_advanced_webhook_twiml()
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml_content,
                timeout=90
            )
            
            # Initialize conversation
            self.conversations[call.sid] = {
                'call_id': call_id,
                'started_at': datetime.now(),
                'history': []
            }
            
            print(f"✅ Advanced webhook AI call initiated!")
            print(f"📞 Call SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'phone_number': phone_number,
                'message': 'Advanced webhook AI call started'
            }
            
        except Exception as e:
            print(f"❌ Error making advanced webhook call: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
webhook_ai = AdvancedWebhookAI()

# Flask webhook routes
@app.route('/process-turn-1', methods=['POST'])
def process_turn_1():
    """Process turn 1 speech (introduction)"""
    
    try:
        speech_result = request.form.get('SpeechResult', '')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  TURN 1 SPEECH: '{speech_result}' (Call: {call_sid})")
        
        if not speech_result.strip():
            speech_result = "I didn't say anything clear"
        
        # Generate AI response
        ai_response = webhook_ai.generate_contextual_ai_response(speech_result, call_sid, 1)
        
        # Create TwiML for next turn
        twiml = webhook_ai.create_turn_response_twiml(ai_response, 2, call_sid)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error in turn 1: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was an issue processing your speech. Thank you for calling!", voice='alice', language='en-IN')
        response.hangup()
        return Response(str(response), mimetype='text/xml')

@app.route('/process-turn-2', methods=['POST'])
def process_turn_2():
    """Process turn 2 speech (interests)"""
    
    try:
        speech_result = request.form.get('SpeechResult', '')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  TURN 2 SPEECH: '{speech_result}' (Call: {call_sid})")
        
        if not speech_result.strip():
            speech_result = "I didn't share anything specific"
        
        # Generate AI response
        ai_response = webhook_ai.generate_contextual_ai_response(speech_result, call_sid, 2)
        
        # Create TwiML for next turn
        twiml = webhook_ai.create_turn_response_twiml(ai_response, 3, call_sid)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error in turn 2: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was an issue. Thank you for the conversation!", voice='alice', language='en-IN')
        response.hangup()
        return Response(str(response), mimetype='text/xml')

@app.route('/process-turn-3', methods=['POST'])
def process_turn_3():
    """Process turn 3 speech (AI discussion)"""
    
    try:
        speech_result = request.form.get('SpeechResult', '')
        call_sid = request.form.get('CallSid', '')
        
        print(f"🗣️  TURN 3 SPEECH: '{speech_result}' (Call: {call_sid})")
        
        if not speech_result.strip():
            speech_result = "I have mixed thoughts about AI"
        
        # Generate AI response
        ai_response = webhook_ai.generate_contextual_ai_response(speech_result, call_sid, 3)
        
        # Create final TwiML
        twiml = webhook_ai.create_turn_response_twiml(ai_response, 4, call_sid)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error in turn 3: {e}")
        response = VoiceResponse()
        response.say("Thank you for this conversation about AI! Goodbye!", voice='alice', language='en-IN')
        response.hangup()
        return Response(str(response), mimetype='text/xml')

@app.route('/status')
def status():
    """Check system status"""
    return {
        'status': 'running',
        'active_conversations': len(webhook_ai.conversations),
        'openai_available': bool(webhook_ai.openai_api_key)
    }

def run_advanced_webhook_system():
    """Run the advanced webhook system"""
    
    print("🎙️  Starting Advanced Webhook AI System")
    print("=" * 60)
    
    # Note: This would need ngrok or public server for production
    print("⚠️  Note: This system requires public webhooks for full functionality")
    print("💡 For demo purposes, it shows the architecture for real-time processing")
    
    # Start Flask server in background
    def start_flask():
        app.run(host='0.0.0.0', port=8002, debug=False)
    
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    time.sleep(2)
    
    # Make test call (will use fallback responses due to localhost webhooks)
    result = webhook_ai.make_advanced_webhook_call("+919373111709")
    
    print(f"\n📋 RESULT:")
    print(json.dumps(result, indent=2, default=str))
    
    if result['success']:
        print(f"\n🎉 ADVANCED WEBHOOK AI CALL ACTIVE!")
        print(f"📞 Answer your phone for:")
        print(f"   🧠 Advanced AI conversation system")
        print(f"   💬 Real-time speech processing architecture")
        print(f"   🎯 Contextual turn-based responses")
        print(f"   🗣️  Intelligent conversation flow")
        print(f"\n🔧 System Features:")
        print(f"   - Flask webhook endpoints for real-time processing")
        print(f"   - Turn-based conversation management")
        print(f"   - Contextual AI response generation")
        print(f"   - Conversation history tracking")
        print(f"   - Fallback responses when API unavailable")
        
        # Keep system running
        print(f"\n🌐 Flask server running on port 8002...")
        print(f"Press Ctrl+C to stop the system")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping advanced webhook system...")
    else:
        print(f"\n❌ Advanced webhook call failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    run_advanced_webhook_system()