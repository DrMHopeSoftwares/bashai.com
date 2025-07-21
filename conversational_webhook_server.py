#!/usr/bin/env python3
"""
Simple webhook server for conversational Twilio calls
Handles speech-to-text and generates AI responses
"""

from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Say, Gather
import os
import json
from datetime import datetime
import requests

app = Flask(__name__)

# Store conversation state
conversations = {}

class ConversationalAI:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
    def generate_response(self, user_speech: str, conversation_context: list = None) -> str:
        """Generate AI response using OpenAI API"""
        
        if not self.openai_api_key:
            return self._fallback_response(user_speech)
        
        try:
            # Create conversation context
            messages = [
                {
                    "role": "system", 
                    "content": "You are BhashAI, a friendly AI voice assistant. You can speak Hindi and English naturally. Keep responses conversational, under 50 words, and engaging. You're on a phone call."
                }
            ]
            
            # Add conversation history
            if conversation_context:
                messages.extend(conversation_context)
            
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
                    'max_tokens': 150,
                    'temperature': 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                return ai_response
            else:
                print(f"OpenAI API error: {response.status_code}")
                return self._fallback_response(user_speech)
                
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._fallback_response(user_speech)
    
    def _fallback_response(self, user_speech: str) -> str:
        """Generate fallback response when OpenAI is not available"""
        
        user_lower = user_speech.lower()
        
        if any(word in user_lower for word in ['hello', 'hi', 'namaste', 'hey']):
            return "Hello! I'm BhashAI. How can I help you today?"
        
        elif any(word in user_lower for word in ['how', 'kaise', 'kaisa']):
            return "I'm doing great, thank you for asking! How are you?"
        
        elif any(word in user_lower for word in ['fine', 'good', 'accha', 'theek']):
            return "That's wonderful to hear! What would you like to talk about?"
        
        elif any(word in user_lower for word in ['bye', 'goodbye', 'alvida']):
            return "It was lovely talking with you! Have a wonderful day ahead. Goodbye!"
        
        elif any(word in user_lower for word in ['name', 'naam', 'who']):
            return "I'm BhashAI, an AI voice assistant. I can speak Hindi and English. What's your name?"
        
        else:
            return f"That's interesting! You mentioned '{user_speech}'. I'd love to hear more about that. What else would you like to discuss?"

# Initialize AI
ai = ConversationalAI()

@app.route('/webhook/twilio/speech', methods=['POST'])
def handle_speech():
    """Handle speech input from Twilio"""
    
    # Get speech data from Twilio
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    call_sid = request.form.get('CallSid', '')
    
    print(f"🗣️  User said: '{speech_result}' (confidence: {confidence})")
    print(f"📞 Call SID: {call_sid}")
    
    # Get or create conversation context
    if call_sid not in conversations:
        conversations[call_sid] = []
    
    conversation_context = conversations[call_sid]
    
    # Generate AI response
    ai_response = ai.generate_response(speech_result, conversation_context)
    
    # Update conversation context
    conversation_context.append({"role": "user", "content": speech_result})
    conversation_context.append({"role": "assistant", "content": ai_response})
    
    # Keep only last 10 exchanges
    if len(conversation_context) > 20:
        conversation_context = conversation_context[-20:]
    
    conversations[call_sid] = conversation_context
    
    print(f"🤖 AI Response: {ai_response}")
    
    # Create TwiML response
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
        action='/webhook/twilio/speech',
        method='POST',
        language='en-IN'
    )
    
    # Check if this seems like an ending
    if any(word in ai_response.lower() for word in ['goodbye', 'bye', 'alvida', 'take care']):
        # End the conversation
        response.say(
            "Thank you for the wonderful conversation! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
    else:
        # Continue conversation
        gather.say(
            "Please continue speaking, I'm listening.",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # If no response, end gracefully
        response.say(
            "Thank you for the conversation! Have a great day! Goodbye!",
            voice='alice',
            language='en-IN'
        )
        response.hangup()
    
    return Response(str(response), mimetype='text/xml')

@app.route('/webhook/twilio/start/<call_id>', methods=['GET', 'POST'])
def start_conversation(call_id):
    """Start a conversational call"""
    
    print(f"🎯 Starting conversation for call: {call_id}")
    
    response = VoiceResponse()
    
    # Initial greeting
    response.say(
        "Hello! This is BhashAI, your AI voice assistant. I can have natural conversations with you in Hindi and English. How are you doing today?",
        voice='alice',
        language='en-IN'
    )
    
    # Listen for user response
    gather = Gather(
        input='speech',
        timeout=10,
        speech_timeout='auto',
        action='/webhook/twilio/speech',
        method='POST',
        language='en-IN'
    )
    
    gather.say(
        "Please speak now, I'm listening and ready to have a conversation with you.",
        voice='alice',
        language='en-IN'
    )
    
    response.append(gather)
    
    # If no response
    response.say(
        "I didn't hear you. Thank you for calling BhashAI! Have a great day!",
        voice='alice',
        language='en-IN'
    )
    response.hangup()
    
    return Response(str(response), mimetype='text/xml')

@app.route('/status')
def status():
    """Check server status"""
    return {
        'status': 'running',
        'active_conversations': len(conversations),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    print("🎙️  Starting Conversational Webhook Server")
    print("🔗 Endpoints:")
    print("   - /webhook/twilio/start/<call_id> - Start conversation")
    print("   - /webhook/twilio/speech - Handle speech input")
    print("   - /status - Server status")
    print("")
    
    port = int(os.environ.get('PORT', 9000))
    app.run(host='0.0.0.0', port=port, debug=True)