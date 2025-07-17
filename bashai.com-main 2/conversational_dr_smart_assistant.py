#!/usr/bin/env python3
"""
Real Conversational Dr. Smart Assistant
Creates interactive voice conversations using Twilio + OpenAI
"""

import os
import asyncio
import json
import requests
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say, Gather, Record, Pause
from dotenv import load_dotenv
from openai import OpenAI
from threading import Thread
import time

load_dotenv()

class ConversationalDrSmartAssistant:
    """Dr. Smart Assistant with real conversation capabilities"""
    
    def __init__(self):
        # Twilio setup
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"
        self.twilio_client = Client(self.account_sid, self.auth_token)
        
        # OpenAI setup
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Conversation state
        self.active_conversations = {}
        
        # Dr. Smart Assistant personality
        self.assistant_prompt = """
        You are Dr. Smart Assistant, a professional healthcare AI assistant from BhashAI.
        
        Personality:
        - Warm, caring, and empathetic
        - Professional medical knowledge
        - Bilingual (Hindi/English mix - Hinglish)
        - Patient and understanding
        - Always prioritizes patient safety
        
        Capabilities:
        - Book medical appointments
        - Provide health guidance
        - Answer medical questions
        - Emergency assistance
        - Prescription reminders
        
        Communication Style:
        - Mix Hindi and English naturally (Hinglish)
        - Use medical terms appropriately
        - Always be reassuring but honest
        - Keep responses concise for phone calls (2-3 sentences max)
        
        Remember: You're on a phone call, so keep responses brief and clear.
        Always ask if the patient needs anything else before ending.
        """
        
        print("🩺 Conversational Dr. Smart Assistant Ready")
        
    def create_flask_app(self):
        """Create Flask app for handling Twilio webhooks"""
        app = Flask(__name__)
        
        @app.route('/webhook/voice', methods=['POST'])
        def handle_voice_webhook():
            """Handle incoming voice calls"""
            return self.handle_voice_call()
        
        @app.route('/webhook/gather', methods=['POST'])
        def handle_gather_webhook():
            """Handle user speech/DTMF input"""
            return self.handle_user_input()
        
        @app.route('/webhook/recording', methods=['POST'])
        def handle_recording_webhook():
            """Handle completed recordings"""
            return self.handle_voice_recording()
        
        return app
    
    def handle_voice_call(self):
        """Handle initial incoming voice call"""
        response = VoiceResponse()
        
        # Get caller info
        from_number = request.values.get('From', 'Unknown')
        call_sid = request.values.get('CallSid')
        
        # Initialize conversation
        self.active_conversations[call_sid] = {
            'from_number': from_number,
            'conversation_history': [],
            'start_time': datetime.now()
        }
        
        # Dr. Smart Assistant greeting
        greeting = """
        नमस्ते! Hello! I am Dr. Smart Assistant from BhashAI Healthcare.
        मैं आपकी स्वास्थ्य संबंधी सहायता के लिए यहाँ हूँ।
        How can I help you today? आप क्या सहायता चाहते हैं?
        """
        
        response.say(greeting, voice='alice', language='en-IN')
        
        # Gather user input
        gather = Gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/webhook/gather',
            method='POST'
        )
        
        gather.say(
            "Please tell me your health concern or what you need help with. "
            "आप अपनी समस्या बताइए।",
            voice='alice',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback if no input
        response.say(
            "I didn't hear anything. Please call back if you need assistance. "
            "धन्यवाद!",
            voice='alice',
            language='en-IN'
        )
        
        return Response(str(response), mimetype='application/xml')
    
    def handle_user_input(self):
        """Process user speech input and generate AI response"""
        response = VoiceResponse()
        
        call_sid = request.values.get('CallSid')
        user_speech = request.values.get('SpeechResult', '')
        
        print(f"🎤 User said: {user_speech}")
        
        if call_sid not in self.active_conversations:
            response.say("Sorry, there was an error. Please call back.", voice='alice')
            return Response(str(response), mimetype='application/xml')
        
        conversation = self.active_conversations[call_sid]
        
        if user_speech:
            # Add user input to conversation history
            conversation['conversation_history'].append({
                'role': 'user',
                'content': user_speech
            })
            
            # Generate AI response
            ai_response = self.generate_ai_response(conversation['conversation_history'])
            
            # Add AI response to history
            conversation['conversation_history'].append({
                'role': 'assistant',
                'content': ai_response
            })
            
            print(f"🩺 Dr. Smart Assistant: {ai_response}")
            
            # Speak the AI response
            response.say(ai_response, voice='alice', language='en-IN')
            
            # Continue conversation
            gather = Gather(
                input='speech',
                timeout=5,
                speech_timeout='auto',
                action='/webhook/gather',
                method='POST'
            )
            
            gather.say(
                "Is there anything else I can help you with? "
                "और कोई मदद चाहिए?",
                voice='alice',
                language='en-IN'
            )
            
            response.append(gather)
            
            # End conversation gracefully
            response.say(
                "Thank you for calling Dr. Smart Assistant. Take care! "
                "स्वस्थ रहें!",
                voice='alice',
                language='en-IN'
            )
        
        else:
            response.say(
                "I didn't understand. Could you please repeat? "
                "कृपया दोबारा बोलिए।",
                voice='alice',
                language='en-IN'
            )
        
        return Response(str(response), mimetype='application/xml')
    
    def generate_ai_response(self, conversation_history):
        """Generate AI response using OpenAI"""
        try:
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.assistant_prompt}
            ] + conversation_history
            
            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Ensure response is phone-appropriate (brief)
            if len(ai_response.split()) > 50:
                ai_response = ' '.join(ai_response.split()[:50]) + "..."
            
            return ai_response
            
        except Exception as e:
            print(f"❌ OpenAI Error: {e}")
            return (
                "I'm having trouble processing right now. "
                "Please call back in a moment. "
                "माफ करें, कुछ तकनीकी समस्या है।"
            )
    
    def handle_voice_recording(self):
        """Handle completed voice recordings if needed"""
        response = VoiceResponse()
        recording_url = request.values.get('RecordingUrl')
        call_sid = request.values.get('CallSid')
        
        print(f"📹 Recording completed: {recording_url}")
        
        response.say("Thank you for your message.", voice='alice')
        return Response(str(response), mimetype='application/xml')
    
    async def make_conversational_call(self, to_number: str, webhook_base_url: str):
        """Make a conversational call with proper webhook URLs"""
        
        print(f"🩺 Dr. Smart Assistant making conversational call...")
        print(f"📱 To: {to_number}")
        print(f"🌐 Webhook URL: {webhook_base_url}/webhook/voice")
        
        try:
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=f"{webhook_base_url}/webhook/voice",
                timeout=30,
                record=False,
                machine_detection='Enable'
            )
            
            print(f"✅ CONVERSATIONAL CALL INITIATED!")
            print(f"📋 Call SID: {call.sid}")
            print(f"🩺 Dr. Smart Assistant will have a real conversation!")
            print(f"📱 Answer your phone to talk with the AI assistant")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'message': 'Conversational Dr. Smart Assistant call initiated!',
                'webhook_url': f"{webhook_base_url}/webhook/voice"
            }
            
        except Exception as e:
            print(f"❌ Error making conversational call: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Standalone webhook server for testing
def run_webhook_server(port=5001):
    """Run the webhook server for testing"""
    assistant = ConversationalDrSmartAssistant()
    app = assistant.create_flask_app()
    
    print(f"🌐 Starting webhook server on port {port}")
    print(f"📡 Webhook URL will be: http://localhost:{port}/webhook/voice")
    print("🚨 For production, use ngrok to expose this to the internet")
    
    app.run(host='0.0.0.0', port=port, debug=True)

# Main execution
async def make_conversational_dr_smart_call():
    """Make a conversational call with Dr. Smart Assistant"""
    
    print("🩺 Conversational Dr. Smart Assistant Call System")
    print("=" * 60)
    
    # For this demo, you'll need to expose your webhook URL
    # Use ngrok: ngrok http 5001
    # Then use the ngrok URL as webhook_base_url
    
    webhook_base_url = "https://your-ngrok-url.ngrok.io"  # Replace with your ngrok URL
    
    assistant = ConversationalDrSmartAssistant()
    
    # Make conversational call
    result = await assistant.make_conversational_call(
        to_number="+919373111709",
        webhook_base_url=webhook_base_url
    )
    
    if result['success']:
        print(f"\n🎊 SUCCESS! Conversational call initiated!")
        print(f"📱 Answer your phone to have a real conversation with Dr. Smart Assistant")
        print(f"💬 You can ask questions, book appointments, get health advice")
        print(f"🩺 Call ID: {result['call_sid']}")
    else:
        print(f"\n❌ Failed: {result['error']}")
    
    return result

if __name__ == "__main__":
    print("🩺 Conversational Dr. Smart Assistant")
    print("\nChoose an option:")
    print("1. Run webhook server (for testing)")
    print("2. Make conversational call (requires ngrok)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n🌐 Starting webhook server...")
        print("💡 In another terminal, run: ngrok http 5001")
        print("💡 Then use option 2 with the ngrok URL")
        run_webhook_server(5001)
    
    elif choice == "2":
        ngrok_url = input("Enter your ngrok URL (e.g., https://abc123.ngrok.io): ").strip()
        if ngrok_url:
            # Update the webhook URL
            async def run_call():
                assistant = ConversationalDrSmartAssistant()
                result = await assistant.make_conversational_call(
                    to_number="+919373111709",
                    webhook_base_url=ngrok_url
                )
                return result
            
            result = asyncio.run(run_call())
        else:
            print("❌ ngrok URL required for conversational calls")
    
    else:
        print("❌ Invalid choice")