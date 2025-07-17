"""
Intelligent Conversation Engine for BhashAI Voice Agents
Provides context-aware, intelligent conversations with memory and NLU capabilities
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import openai
from dotenv import load_dotenv
import re

load_dotenv()

class ConversationState(Enum):
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    PROCESSING = "processing"
    CLARIFICATION = "clarification"
    COMPLETION = "completion"
    FAREWELL = "farewell"

class IntentType(Enum):
    APPOINTMENT_BOOKING = "appointment_booking"
    INFORMATION_REQUEST = "information_request"
    COMPLAINT = "complaint"
    PRESCRIPTION_INQUIRY = "prescription_inquiry"
    EMERGENCY = "emergency"
    GENERAL_CHAT = "general_chat"
    APPOINTMENT_CANCEL = "appointment_cancel"
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"

@dataclass
class ConversationContext:
    """Stores conversation context and memory"""
    session_id: str
    user_id: Optional[str] = None
    conversation_history: List[Dict] = None
    current_state: ConversationState = ConversationState.GREETING
    detected_intent: Optional[IntentType] = None
    extracted_entities: Dict[str, Any] = None
    user_profile: Dict[str, Any] = None
    conversation_goals: List[str] = None
    sentiment_score: float = 0.0
    emotion: str = "neutral"
    language_preference: str = "hindi"
    last_interaction: datetime = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.extracted_entities is None:
            self.extracted_entities = {}
        if self.user_profile is None:
            self.user_profile = {}
        if self.conversation_goals is None:
            self.conversation_goals = []
        if self.last_interaction is None:
            self.last_interaction = datetime.now(timezone.utc)

class IntelligentConversationEngine:
    """Core intelligent conversation engine with NLU and context management"""
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.agent_config = agent_config
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Conversation contexts indexed by session_id
        self.active_contexts: Dict[str, ConversationContext] = {}
        
        # Intent recognition patterns (Hindi/Hinglish/English)
        self.intent_patterns = {
            IntentType.APPOINTMENT_BOOKING: [
                r"(?i)(appointment|अपॉइंटमेंट|मुलाकात|मिलना).*?(book|बुक|करना|चाहिए)",
                r"(?i)(doctor|डॉक्टर|चिकित्सक).*?(मिलना|see|देखना)",
                r"(?i)(consultation|परामर्श|सलाह|checkup|जांच)"
            ],
            IntentType.INFORMATION_REQUEST: [
                r"(?i)(timing|समय|hours|घंटे|schedule|शेड्यूल)",
                r"(?i)(fees|फीस|charge|खर्च|cost|लागत)",
                r"(?i)(location|पता|address|कहां|where)"
            ],
            IntentType.COMPLAINT: [
                r"(?i)(problem|समस्या|issue|परेशानी|complaint|शिकायत)",
                r"(?i)(pain|दर्द|hurt|तकलीफ|uncomfortable|बेचैन)"
            ],
            IntentType.PRESCRIPTION_INQUIRY: [
                r"(?i)(medicine|दवा|prescription|नुस्खा|medication|इलाज)",
                r"(?i)(tablet|गोली|syrup|सिरप|injection|इंजेक्शन)"
            ],
            IntentType.EMERGENCY: [
                r"(?i)(emergency|आपातकाल|urgent|तुरंत|help|मदद|serious|गंभीर)",
                r"(?i)(chest pain|सीने में दर्द|breathing|सांस|unconscious|बेहोश)"
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'phone_number': r'(\+91[\s-]?)?[6-9]\d{9}',
            'name': r'(?i)(name|नाम).*?(?:is|है|हूं|हूँ)\s+([A-Za-z\u0900-\u097F\s]+)',
            'age': r'(?i)(age|उम्र|years|साल|वर्ष).*?(\d+)',
            'date': r'(?i)(today|आज|tomorrow|कल|(\d{1,2})[/-](\d{1,2})[/-](\d{2,4}))',
            'time': r'(?i)(\d{1,2}):?(\d{2})?\s*(am|pm|बजे|morning|evening|सुबह|शाम)?'
        }
        
        # Sentiment keywords
        self.sentiment_keywords = {
            'positive': ['good', 'great', 'excellent', 'happy', 'satisfied', 'अच्छा', 'खुश', 'संतुष्ट'],
            'negative': ['bad', 'terrible', 'angry', 'upset', 'disappointed', 'बुरा', 'गुस्सा', 'निराश'],
            'neutral': ['okay', 'fine', 'normal', 'ठीक', 'सामान्य']
        }
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_conversation(self, session_id: str, user_id: Optional[str] = None) -> ConversationContext:
        """Initialize a new conversation context"""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            current_state=ConversationState.GREETING
        )
        
        self.active_contexts[session_id] = context
        
        # Generate personalized greeting
        greeting = await self._generate_greeting(context)
        context.conversation_history.append({
            'role': 'assistant',
            'content': greeting,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'state': context.current_state.value
        })
        
        return context

    async def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Process user input with intelligent understanding and generate response"""
        context = self.active_contexts.get(session_id)
        if not context:
            raise ValueError(f"No active conversation context for session {session_id}")
        
        # Update last interaction time
        context.last_interaction = datetime.now(timezone.utc)
        
        # Add user input to conversation history
        context.conversation_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Analyze user input
        analysis = await self._analyze_user_input(user_input, context)
        
        # Update context with analysis results
        context.detected_intent = analysis['intent']
        context.extracted_entities.update(analysis['entities'])
        context.sentiment_score = analysis['sentiment_score']
        context.emotion = analysis['emotion']
        
        # Determine next conversation state
        next_state = await self._determine_next_state(context, analysis)
        context.current_state = next_state
        
        # Generate intelligent response
        response = await self._generate_intelligent_response(context, analysis)
        
        # Add response to conversation history
        context.conversation_history.append({
            'role': 'assistant',
            'content': response['text'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'state': context.current_state.value,
            'intent': context.detected_intent.value if context.detected_intent else None,
            'confidence': analysis['confidence']
        })
        
        return {
            'response': response,
            'context': {
                'session_id': session_id,
                'current_state': context.current_state.value,
                'detected_intent': context.detected_intent.value if context.detected_intent else None,
                'entities': context.extracted_entities,
                'sentiment': context.emotion,
                'confidence': analysis['confidence']
            },
            'actions': response.get('actions', [])
        }

    async def _analyze_user_input(self, user_input: str, context: ConversationContext) -> Dict[str, Any]:
        """Comprehensive analysis of user input using NLU"""
        
        # Intent recognition
        detected_intent = await self._detect_intent(user_input)
        
        # Entity extraction
        entities = await self._extract_entities(user_input)
        
        # Sentiment analysis
        sentiment_score, emotion = await self._analyze_sentiment(user_input)
        
        # Language detection
        language = await self._detect_language(user_input)
        
        # Confidence calculation
        confidence = await self._calculate_confidence(user_input, detected_intent, entities)
        
        return {
            'intent': detected_intent,
            'entities': entities,
            'sentiment_score': sentiment_score,
            'emotion': emotion,
            'language': language,
            'confidence': confidence
        }

    async def _detect_intent(self, user_input: str) -> Optional[IntentType]:
        """Advanced intent detection using patterns and OpenAI"""
        
        # Pattern-based detection for quick common intents
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input):
                    return intent
        
        # Use OpenAI for complex intent detection
        try:
            response = await self._get_openai_completion(
                f"""Analyze this user input and determine the intent. Return only the intent category.

User input: "{user_input}"

Possible intents:
- appointment_booking: User wants to book an appointment
- information_request: User asking for information
- complaint: User has a health complaint or problem
- prescription_inquiry: User asking about medicines
- emergency: Urgent medical situation
- general_chat: General conversation
- appointment_cancel: Cancel appointment
- appointment_reschedule: Reschedule appointment

Intent:""",
                max_tokens=50
            )
            
            intent_text = response.strip().lower()
            for intent in IntentType:
                if intent.value in intent_text:
                    return intent
        except Exception as e:
            self.logger.error(f"OpenAI intent detection failed: {e}")
        
        return None

    async def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract relevant entities from user input"""
        entities = {}
        
        # Pattern-based entity extraction
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, user_input)
            if matches:
                if entity_type == 'name':
                    entities[entity_type] = matches[0][1].strip() if len(matches[0]) > 1 else matches[0]
                else:
                    entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        # Use OpenAI for advanced entity extraction
        try:
            response = await self._get_openai_completion(
                f"""Extract relevant entities from this text. Return as JSON format.

Text: "{user_input}"

Extract these entities if present:
- name: Person's name
- phone: Phone number
- age: Age in years
- symptoms: Health symptoms mentioned
- date: Any date mentioned
- time: Any time mentioned
- department: Medical department
- doctor_name: Specific doctor mentioned

JSON:""",
                max_tokens=200
            )
            
            try:
                openai_entities = json.loads(response)
                entities.update(openai_entities)
            except json.JSONDecodeError:
                pass
        except Exception as e:
            self.logger.error(f"OpenAI entity extraction failed: {e}")
        
        return entities

    async def _analyze_sentiment(self, user_input: str) -> Tuple[float, str]:
        """Analyze sentiment and emotion from user input"""
        
        # Keyword-based sentiment analysis
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word.lower() in user_input.lower())
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word.lower() in user_input.lower())
        
        if positive_count > negative_count:
            sentiment_score = min(0.8, 0.5 + (positive_count * 0.1))
            emotion = "positive"
        elif negative_count > positive_count:
            sentiment_score = max(-0.8, -0.5 - (negative_count * 0.1))
            emotion = "negative"
        else:
            sentiment_score = 0.0
            emotion = "neutral"
        
        # Use OpenAI for detailed emotion analysis
        try:
            response = await self._get_openai_completion(
                f"""Analyze the emotion and sentiment of this text. Rate sentiment from -1 (very negative) to +1 (very positive).

Text: "{user_input}"

Provide:
1. Sentiment score (-1 to +1):
2. Primary emotion (happy, sad, angry, frustrated, worried, calm, excited):
3. Urgency level (low, medium, high):

Response:""",
                max_tokens=100
            )
            
            # Parse OpenAI response for better sentiment analysis
            lines = response.strip().split('\n')
            for line in lines:
                if 'sentiment' in line.lower() and any(char.isdigit() or char in '.-' for char in line):
                    try:
                        score = float(re.search(r'-?\d+\.?\d*', line).group())
                        sentiment_score = max(-1, min(1, score))
                    except:
                        pass
                elif 'emotion' in line.lower():
                    emotions = ['happy', 'sad', 'angry', 'frustrated', 'worried', 'calm', 'excited']
                    for emo in emotions:
                        if emo in line.lower():
                            emotion = emo
                            break
        except Exception as e:
            self.logger.error(f"OpenAI sentiment analysis failed: {e}")
        
        return sentiment_score, emotion

    async def _detect_language(self, user_input: str) -> str:
        """Detect primary language of user input"""
        
        # Simple pattern-based detection
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', user_input))
        english_chars = len(re.findall(r'[a-zA-Z]', user_input))
        
        if hindi_chars > english_chars:
            return "hindi"
        elif english_chars > hindi_chars * 2:
            return "english"
        else:
            return "hinglish"

    async def _calculate_confidence(self, user_input: str, intent: Optional[IntentType], entities: Dict) -> float:
        """Calculate confidence score for the analysis"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on intent detection
        if intent:
            confidence += 0.2
        
        # Boost confidence based on entity extraction
        confidence += min(0.2, len(entities) * 0.05)
        
        # Boost confidence for clear, structured input
        if len(user_input.split()) > 3:
            confidence += 0.1
        
        return min(1.0, confidence)

    async def _determine_next_state(self, context: ConversationContext, analysis: Dict) -> ConversationState:
        """Determine the next conversation state based on context and analysis"""
        
        current_state = context.current_state
        intent = analysis['intent']
        
        # State transition logic
        if current_state == ConversationState.GREETING:
            if intent:
                return ConversationState.INFORMATION_GATHERING
            return ConversationState.GREETING
            
        elif current_state == ConversationState.INFORMATION_GATHERING:
            # Check if we have enough information to proceed
            required_entities = self._get_required_entities_for_intent(intent)
            if self._has_sufficient_entities(context.extracted_entities, required_entities):
                return ConversationState.PROCESSING
            return ConversationState.CLARIFICATION
            
        elif current_state == ConversationState.CLARIFICATION:
            # Check if clarification resolved the missing information
            if analysis['confidence'] > 0.7:
                return ConversationState.PROCESSING
            return ConversationState.CLARIFICATION
            
        elif current_state == ConversationState.PROCESSING:
            return ConversationState.COMPLETION
            
        elif current_state == ConversationState.COMPLETION:
            # Check if user wants to do something else
            if intent and intent != context.detected_intent:
                return ConversationState.INFORMATION_GATHERING
            return ConversationState.FAREWELL
        
        return current_state

    async def _generate_intelligent_response(self, context: ConversationContext, analysis: Dict) -> Dict[str, Any]:
        """Generate contextually appropriate and intelligent response"""
        
        # Prepare context for response generation
        conversation_summary = self._summarize_conversation(context)
        
        # Create system prompt based on agent configuration
        system_prompt = self._create_system_prompt(context, analysis)
        
        # Generate response using OpenAI
        try:
            response_text = await self._get_openai_completion(
                system_prompt + f"""

Current conversation state: {context.current_state.value}
Detected intent: {analysis['intent'].value if analysis['intent'] else 'unclear'}
User emotion: {analysis['emotion']}
Extracted entities: {json.dumps(context.extracted_entities, ensure_ascii=False)}

Conversation history:
{conversation_summary}

Generate an appropriate response that:
1. Acknowledges the user's intent and emotion
2. Progresses the conversation toward the goal
3. Asks for missing information if needed
4. Maintains a {self.agent_config.get('personality', 'professional')} tone
5. Responds in {analysis.get('language', 'hindi')} language primarily

Response:""",
                max_tokens=300
            )
            
            # Determine actions based on state and intent
            actions = self._determine_actions(context, analysis)
            
            return {
                'text': response_text.strip(),
                'actions': actions,
                'confidence': analysis['confidence']
            }
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return {
                'text': self._get_fallback_response(analysis.get('language', 'hindi')),
                'actions': [],
                'confidence': 0.3
            }

    async def _generate_greeting(self, context: ConversationContext) -> str:
        """Generate personalized greeting based on agent configuration"""
        
        agent_name = self.agent_config.get('name', 'AI Assistant')
        use_case = self.agent_config.get('use_case', 'general')
        language = self.agent_config.get('language', 'hindi')
        
        greetings = {
            'hindi': f"नमस्ते! मैं {agent_name} हूं। मैं आपकी कैसे सहायता कर सकता हूं?",
            'english': f"Hello! I'm {agent_name}. How can I help you today?",
            'hinglish': f"नमस्ते! मैं {agent_name} हूं। How can I assist you आज?"
        }
        
        return greetings.get(language, greetings['hindi'])

    def _create_system_prompt(self, context: ConversationContext, analysis: Dict) -> str:
        """Create comprehensive system prompt for response generation"""
        
        return f"""You are {self.agent_config.get('name', 'an AI assistant')}, a helpful and intelligent voice agent for {self.agent_config.get('organization', 'healthcare')}.

Your characteristics:
- Personality: {self.agent_config.get('personality', 'Professional and caring')}
- Expertise: {self.agent_config.get('use_case', 'General assistance')}
- Languages: Hindi, English, and Hinglish
- Response style: Natural, conversational, and contextually appropriate

Your role is to:
1. Understand user needs through natural conversation
2. Provide accurate information and assistance
3. Maintain conversation context and memory
4. Handle multiple languages seamlessly
5. Show empathy and emotional intelligence
6. Guide conversations toward successful outcomes

Guidelines:
- Keep responses concise but complete
- Ask clarifying questions when needed
- Acknowledge emotions and respond appropriately
- Use the user's preferred language
- Maintain professional boundaries
- Escalate emergencies immediately"""

    def _summarize_conversation(self, context: ConversationContext) -> str:
        """Create a summary of the conversation for context"""
        
        recent_history = context.conversation_history[-6:]  # Last 3 exchanges
        summary = ""
        
        for entry in recent_history:
            role = "User" if entry['role'] == 'user' else "Assistant"
            summary += f"{role}: {entry['content']}\n"
        
        return summary

    def _get_required_entities_for_intent(self, intent: Optional[IntentType]) -> List[str]:
        """Get required entities for specific intent"""
        
        requirements = {
            IntentType.APPOINTMENT_BOOKING: ['name', 'phone', 'date'],
            IntentType.PRESCRIPTION_INQUIRY: ['name', 'symptoms'],
            IntentType.COMPLAINT: ['symptoms'],
            IntentType.INFORMATION_REQUEST: [],
            IntentType.EMERGENCY: ['name', 'symptoms'],
        }
        
        return requirements.get(intent, [])

    def _has_sufficient_entities(self, entities: Dict, required: List[str]) -> bool:
        """Check if we have sufficient entities to proceed"""
        return all(entity in entities and entities[entity] for entity in required)

    def _determine_actions(self, context: ConversationContext, analysis: Dict) -> List[Dict]:
        """Determine actions to take based on conversation state"""
        
        actions = []
        
        if context.current_state == ConversationState.PROCESSING:
            if context.detected_intent == IntentType.APPOINTMENT_BOOKING:
                actions.append({
                    'type': 'book_appointment',
                    'data': context.extracted_entities
                })
            elif context.detected_intent == IntentType.EMERGENCY:
                actions.append({
                    'type': 'escalate_emergency',
                    'urgency': 'high'
                })
        
        # Always log conversation for analytics
        actions.append({
            'type': 'log_interaction',
            'data': {
                'intent': context.detected_intent.value if context.detected_intent else None,
                'sentiment': analysis['emotion'],
                'entities': context.extracted_entities
            }
        })
        
        return actions

    def _get_fallback_response(self, language: str = 'hindi') -> str:
        """Get fallback response when generation fails"""
        
        fallbacks = {
            'hindi': "क्षमा करें, मुझे आपकी बात समझने में कुछ कठिनाई हो रही है। कृपया अपनी बात को दोबारा कहें।",
            'english': "I'm sorry, I'm having trouble understanding. Could you please rephrase that?",
            'hinglish': "Sorry, मुझे समझने में problem हो रही है। Please repeat करें?"
        }
        
        return fallbacks.get(language, fallbacks['hindi'])

    async def _get_openai_completion(self, prompt: str, max_tokens: int = 200) -> str:
        """Get completion from OpenAI with error handling"""
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise

    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session"""
        return self.active_contexts.get(session_id)

    def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End conversation and return summary"""
        
        context = self.active_contexts.get(session_id)
        if not context:
            return {'error': 'No active conversation found'}
        
        # Generate conversation summary
        summary = {
            'session_id': session_id,
            'duration': (datetime.now(timezone.utc) - context.conversation_history[0]['timestamp']).total_seconds() if context.conversation_history else 0,
            'message_count': len(context.conversation_history),
            'final_intent': context.detected_intent.value if context.detected_intent else None,
            'extracted_entities': context.extracted_entities,
            'final_sentiment': context.emotion,
            'conversation_successful': context.current_state in [ConversationState.COMPLETION, ConversationState.FAREWELL]
        }
        
        # Clean up context
        del self.active_contexts[session_id]
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    async def test_conversation_engine():
        # Test configuration
        agent_config = {
            'name': 'Dr. AI Assistant',
            'organization': 'City Hospital',
            'use_case': 'appointment_booking',
            'personality': 'Professional and caring',
            'language': 'hinglish'
        }
        
        # Initialize engine
        engine = IntelligentConversationEngine(agent_config)
        
        # Start conversation
        session_id = str(uuid.uuid4())
        context = await engine.start_conversation(session_id)
        print(f"Greeting: {context.conversation_history[0]['content']}")
        
        # Test conversation flow
        test_inputs = [
            "Hello, मुझे appointment book करना है",
            "My name is राजेश Kumar and मेरा phone number है 9876543210",
            "Tomorrow morning कोई time available है?",
            "Thank you, बहुत अच्छा लगा"
        ]
        
        for user_input in test_inputs:
            result = await engine.process_user_input(session_id, user_input)
            print(f"\nUser: {user_input}")
            print(f"Assistant: {result['response']['text']}")
            print(f"Intent: {result['context']['detected_intent']}")
            print(f"Entities: {result['context']['entities']}")
        
        # End conversation
        summary = engine.end_conversation(session_id)
        print(f"\nConversation Summary: {json.dumps(summary, indent=2)}")

    # Run test if API key is available
    if os.getenv('OPENAI_API_KEY'):
        asyncio.run(test_conversation_engine())
    else:
        print("OpenAI API key not found. Skipping test.")