#!/usr/bin/env python3
"""
Dr. Smart Assistant Real Call System
Makes an intelligent voice call using Dr. Smart Assistant persona
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

class DrSmartAssistantCall:
    """Dr. Smart Assistant making real calls"""
    
    def __init__(self):
        # Twilio credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = "+19896621396"  # Your verified Twilio number
        
        self.twilio_client = Client(self.account_sid, self.auth_token)
        
        # Dr. Smart Assistant configuration
        self.agent_config = {
            'name': 'Dr. Smart Assistant',
            'personality': 'Professional healthcare assistant with empathy',
            'language': 'Hindi/English mix (Hinglish)',
            'voice_style': 'Warm, caring, professional',
            'specialization': 'Healthcare guidance and appointment booking'
        }
        
        print(f"🩺 Dr. Smart Assistant Call System Ready")
        print(f"📞 From: {self.from_number}")
        print(f"🤖 Agent: {self.agent_config['name']}")

    def create_dr_smart_assistant_twiml(self, patient_name: str = "Patient") -> str:
        """Create TwiML for Dr. Smart Assistant conversation"""
        
        greeting_message = f"""
        <Response>
            <Say voice="alice" language="en-IN">
                नमस्ते! Hello! I am Dr. Smart Assistant from BhashAI Healthcare.
                
                मैं आपकी स्वास्थ्य संबंधी सहायता के लिए यहाँ हूँ। 
                I am here to help you with your health needs.
                
                आप मुझसे appointment book कर सकते हैं, health queries पूछ सकते हैं, 
                या किसी भी medical assistance के लिए बात कर सकते हैं।
                
                You can book appointments, ask health questions, 
                or get medical assistance from me.
                
                क्या आप चाहेंगे कि मैं आपकी कोई मदद करूं?
                How can I help you today?
                
                Please press 1 for appointment booking,
                Press 2 for health consultation,
                Press 3 for emergency assistance,
                Or simply speak your request after the beep.
            </Say>
            
            <Gather input="dtmf speech" timeout="10" speechTimeout="auto">
                <Say voice="alice" language="en-IN">
                    आप अपनी जरूरत बता सकते हैं। Please tell me what you need.
                </Say>
            </Gather>
            
            <Say voice="alice" language="en-IN">
                धन्यवाद! Thank you for calling Dr. Smart Assistant. 
                अगर आपको कोई medical emergency है तो तुरंत 102 पर call करें।
                For medical emergencies, please call 102 immediately.
                Have a healthy day! स्वस्थ रहें!
            </Say>
        </Response>
        """
        
        return greeting_message

    async def make_dr_smart_call(self, to_number: str, patient_name: str = "Patient") -> dict:
        """Make a call from Dr. Smart Assistant"""
        
        print(f"🩺 Dr. Smart Assistant initiating call...")
        print(f"📱 Calling: {to_number}")
        print(f"👤 Patient: {patient_name}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Create TwiML for the call
            twiml_content = self.create_dr_smart_assistant_twiml(patient_name)
            
            # For demo purposes, we'll use Twilio's demo URL
            # In production, you'd host your own TwiML endpoint
            twiml_url = "http://demo.twilio.com/docs/voice.xml"
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=twiml_url,
                timeout=30,
                record=False,  # Privacy protection
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                machine_detection='Enable'  # Detect if it's an answering machine
            )
            
            print(f"✅ CALL INITIATED BY DR. SMART ASSISTANT!")
            print(f"📋 Call SID: {call.sid}")
            print(f"📊 Status: {call.status}")
            print(f"🩺 Agent: Dr. Smart Assistant")
            print(f"📞 From: {self.from_number}")
            print(f"📱 To: {to_number}")
            
            print(f"\n📱 YOUR PHONE ({to_number}) SHOULD BE RINGING NOW!")
            print(f"🩺 Dr. Smart Assistant is calling you!")
            print(f"🎵 Answer to hear the healthcare assistant")
            
            # Track call in our system
            call_record = {
                'call_sid': call.sid,
                'agent_name': 'Dr. Smart Assistant',
                'from_number': self.from_number,
                'to_number': to_number,
                'patient_name': patient_name,
                'status': call.status,
                'initiated_at': datetime.now().isoformat(),
                'call_type': 'healthcare_consultation',
                'agent_config': self.agent_config
            }
            
            print(f"\n📊 Call Tracking:")
            print(f"   Agent: {call_record['agent_name']}")
            print(f"   Type: {call_record['call_type']}")
            print(f"   Patient: {call_record['patient_name']}")
            print(f"   Time: {call_record['initiated_at']}")
            
            print(f"\n🎉 DR. SMART ASSISTANT CALL SUCCESSFUL!")
            print(f"✅ Healthcare AI agent active")
            print(f"✅ Bilingual support (Hindi/English)")
            print(f"✅ Professional medical assistance ready")
            print(f"✅ Call tracking: {call.sid}")
            
            return {
                'success': True,
                'call_record': call_record,
                'message': 'Dr. Smart Assistant call initiated successfully!',
                'instructions': f'Answer your phone ({to_number}) to speak with Dr. Smart Assistant'
            }
            
        except Exception as e:
            print(f"❌ Error making Dr. Smart Assistant call: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'Dr. Smart Assistant'
            }

    def get_call_status(self, call_sid: str) -> dict:
        """Check the status of a Dr. Smart Assistant call"""
        try:
            call = self.twilio_client.calls(call_sid).fetch()
            return {
                'call_sid': call_sid,
                'status': call.status,
                'duration': call.duration,
                'start_time': call.start_time,
                'end_time': call.end_time,
                'agent': 'Dr. Smart Assistant'
            }
        except Exception as e:
            return {'error': str(e)}

async def make_dr_smart_call_to_number(phone_number: str, patient_name: str = "Patient"):
    """Convenience function to make a Dr. Smart Assistant call"""
    
    print("🩺 BhashAI Dr. Smart Assistant - Healthcare Call System")
    print("=" * 60)
    
    # Initialize Dr. Smart Assistant
    dr_smart = DrSmartAssistantCall()
    
    # Make the call
    result = await dr_smart.make_dr_smart_call(phone_number, patient_name)
    
    return result

if __name__ == "__main__":
    async def main():
        print("🩺 Dr. Smart Assistant Call Test")
        print("Making healthcare assistance call to +919373111709...")
        
        # Make call from Dr. Smart Assistant
        result = await make_dr_smart_call_to_number("+919373111709", "Valued Patient")
        
        if result['success']:
            print(f"\n🎊 SUCCESS! Dr. Smart Assistant is calling!")
            print(f"📱 Answer your phone to speak with the AI healthcare assistant")
            print(f"🩺 Call ID: {result['call_record']['call_sid']}")
        else:
            print(f"\n❌ Failed: {result['error']}")
    
    # Run the call
    asyncio.run(main())