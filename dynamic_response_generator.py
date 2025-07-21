"""
Dynamic Response Generation System for BhashAI
Generates contextually appropriate, intelligent responses using OpenAI integration
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from dotenv import load_dotenv
import random
import re

# Import our conversation engine and agent config
from intelligent_conversation_engine import (
    ConversationContext, ConversationState, IntentType, 
    IntelligentConversationEngine
)
from advanced_agent_config import (
    AdvancedAgentConfig, AdvancedAgentConfigManager,
    ResponseStyle, AgentType
)

load_dotenv()

class ResponseType(Enum):
    GREETING = "greeting"
    INFORMATION_PROVIDING = "information_providing"
    QUESTION_ASKING = "question_asking"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    APOLOGY = "apology"
    ESCALATION = "escalation"
    FAREWELL = "farewell"
    EMPATHETIC = "empathetic"
    INSTRUCTION = "instruction"

class LanguageMixLevel(Enum):
    PURE_HINDI = "pure_hindi"
    PURE_ENGLISH = "pure_english"
    LIGHT_HINGLISH = "light_hinglish"
    HEAVY_HINGLISH = "heavy_hinglish"
    CODE_SWITCHING = "code_switching"

@dataclass
class ResponseContext:
    """Context for generating responses"""
    conversation_context: ConversationContext
    agent_config: AdvancedAgentConfig
    user_emotion: str
    urgency_level: float
    language_preference: str
    previous_responses: List[str]
    knowledge_base_results: List[Dict[str, Any]]
    conversation_goals: List[str]

class DynamicResponseGenerator:
    """Advanced response generation with context awareness and intelligence"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Response templates for different scenarios
        self.response_templates = self._initialize_response_templates()
        
        # Language mixing patterns
        self.language_patterns = self._initialize_language_patterns()
        
        # Emotion-based response modifiers
        self.emotion_modifiers = self._initialize_emotion_modifiers()
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _initialize_response_templates(self) -> Dict[ResponseType, Dict[str, List[str]]]:
        """Initialize response templates for different types and languages"""
        return {
            ResponseType.GREETING: {
                'hindi': [
                    "नमस्ते! मैं {agent_name} हूं। आपकी कैसे सहायता कर सकता हूं?",
                    "आपका स्वागत है! मैं {agent_name} हूं। आज आपके लिए क्या कर सकता हूं?",
                    "नमस्कार! मैं आपका सहायक {agent_name} हूं। बताइए कि मैं आपकी कैसे मदद कर सकता हूं?"
                ],
                'english': [
                    "Hello! I'm {agent_name}. How can I help you today?",
                    "Welcome! I'm {agent_name}, your assistant. What can I do for you?",
                    "Good day! I'm {agent_name}. How may I assist you?"
                ],
                'hinglish': [
                    "Hello! मैं {agent_name} हूं। How can I help you आज?",
                    "नमस्ते! I'm {agent_name}, आपका assistant। What can I do for you?",
                    "Hi there! मैं {agent_name} हूं। आपकी कैसे help कर सकता हूं?"
                ]
            },
            
            ResponseType.INFORMATION_PROVIDING: {
                'hindi': [
                    "आपकी जानकारी के अनुसार, {information}। क्या आपको और कुछ जानना है?",
                    "मैं आपको बता सकता हूं कि {information}। क्या यह सहायक है?",
                    "इस बारे में मैं आपको यह बता सकता हूं: {information}। कोई और प्रश्न?"
                ],
                'english': [
                    "Based on the information I have, {information}. Is there anything else you'd like to know?",
                    "I can tell you that {information}. Does this help?",
                    "Here's what I can share: {information}. Any other questions?"
                ],
                'hinglish': [
                    "मैं आपको बता सकता हूं कि {information}। Anything else आप जानना चाहते हैं?",
                    "According to my information, {information}। Is this helpful?",
                    "यहां है आपकी information: {information}। कोई और questions?"
                ]
            },
            
            ResponseType.QUESTION_ASKING: {
                'hindi': [
                    "मुझे आपकी बेहतर सहायता के लिए {required_info} जानना होगा। क्या आप बता सकते हैं?",
                    "कृपया मुझे {required_info} के बारे में बताएं ताकि मैं आपकी सही मदद कर सकूं।",
                    "आपकी सहायता के लिए मुझे {required_info} की जानकारी चाहिए। क्या आप साझा कर सकते हैं?"
                ],
                'english': [
                    "To better assist you, I need to know {required_info}. Could you please share that?",
                    "I'll need some information about {required_info} to help you properly.",
                    "Could you please tell me about {required_info} so I can assist you better?"
                ],
                'hinglish': [
                    "मुझे आपकी better help के लिए {required_info} जानना होगा। Can you share that?",
                    "Please मुझे {required_info} के बारे में बताएं so I can help properly।",
                    "आपकी assistance के लिए मुझे {required_info} चाहिए। Could you tell me?"
                ]
            },
            
            ResponseType.EMPATHETIC: {
                'hindi': [
                    "मैं समझ सकता हूं कि यह आपके लिए {emotion_context} है। मैं आपकी पूरी सहायता करूंगा।",
                    "आपकी परेशानी समझ में आती है। आइए मिलकर इसका समाधान निकालते हैं।",
                    "मुझे लगता है कि आप {emotion_context} महसूस कर रहे हैं। मैं यहां आपकी मदद के लिए हूं।"
                ],
                'english': [
                    "I understand this must be {emotion_context} for you. I'm here to help in every way I can.",
                    "I can see why you might feel {emotion_context}. Let's work together to resolve this.",
                    "That sounds {emotion_context}. Please know that I'm here to support you."
                ],
                'hinglish': [
                    "मैं समझ सकता हूं कि this is {emotion_context} for you। I'm here to help।",
                    "यह definitely {emotion_context} है। Let's solve this together।",
                    "I understand आप {emotion_context} feel कर रहे हैं। मैं आपकी help करूंगा।"
                ]
            },
            
            ResponseType.ESCALATION: {
                'hindi': [
                    "मैं इस मामले को तुरंत senior team member के पास भेज रहा हूं। कृपया थोड़ा इंतजार करें।",
                    "यह एक महत्वपूर्ण मामला लगता है। मैं इसे अभी specialist को transfer कर रहा हूं।",
                    "मुझे लगता है कि इसके लिए expert help की जरूरत है। मैं आपको connect कर रहा हूं।"
                ],
                'english': [
                    "I'm escalating this to a senior team member right away. Please hold on for a moment.",
                    "This seems to require specialized attention. I'm transferring you to an expert now.",
                    "Let me connect you with someone who can better assist with this specific matter."
                ],
                'hinglish': [
                    "मैं इसे immediately senior person को भेज रहा हूं। Please wait थोड़ा।",
                    "This needs expert attention। मैं आपको specialist से connect कर रहा हूं।",
                    "Let me escalate this तुरंत। Someone will help you better।"
                ]
            }
        }

    def _initialize_language_patterns(self) -> Dict[LanguageMixLevel, Dict[str, Any]]:
        """Initialize language mixing patterns for natural code-switching"""
        return {
            LanguageMixLevel.PURE_HINDI: {
                'ratio': {'hindi': 1.0, 'english': 0.0},
                'switch_probability': 0.0,
                'common_switches': []
            },
            LanguageMixLevel.PURE_ENGLISH: {
                'ratio': {'hindi': 0.0, 'english': 1.0},
                'switch_probability': 0.0,
                'common_switches': []
            },
            LanguageMixLevel.LIGHT_HINGLISH: {
                'ratio': {'hindi': 0.7, 'english': 0.3},
                'switch_probability': 0.2,
                'common_switches': ['okay', 'please', 'thank you', 'sorry', 'help']
            },
            LanguageMixLevel.HEAVY_HINGLISH: {
                'ratio': {'hindi': 0.5, 'english': 0.5},
                'switch_probability': 0.4,
                'common_switches': ['appointment', 'book', 'time', 'date', 'call', 'message', 'problem', 'solution']
            },
            LanguageMixLevel.CODE_SWITCHING: {
                'ratio': {'hindi': 0.6, 'english': 0.4},
                'switch_probability': 0.6,
                'common_switches': ['doctor', 'hospital', 'medicine', 'prescription', 'emergency', 'urgent']
            }
        }

    def _initialize_emotion_modifiers(self) -> Dict[str, Dict[str, str]]:
        """Initialize emotion-based response modifiers"""
        return {
            'frustrated': {
                'hindi': {
                    'prefix': 'मैं आपकी परेशानी समझ सकता हूं। ',
                    'tone': 'calm and understanding',
                    'pace': 'slower'
                },
                'english': {
                    'prefix': 'I completely understand your frustration. ',
                    'tone': 'calm and empathetic',
                    'pace': 'slower'
                }
            },
            'worried': {
                'hindi': {
                    'prefix': 'आपकी चिंता सही है। ',
                    'tone': 'reassuring',
                    'pace': 'gentle'
                },
                'english': {
                    'prefix': 'Your concern is completely valid. ',
                    'tone': 'reassuring',
                    'pace': 'gentle'
                }
            },
            'happy': {
                'hindi': {
                    'prefix': 'खुशी की बात है! ',
                    'tone': 'upbeat',
                    'pace': 'normal'
                },
                'english': {
                    'prefix': 'That\'s wonderful! ',
                    'tone': 'upbeat',
                    'pace': 'normal'
                }
            },
            'angry': {
                'hindi': {
                    'prefix': 'मैं आपकी नाराजगी समझ सकता हूं। ',
                    'tone': 'very calm',
                    'pace': 'slow'
                },
                'english': {
                    'prefix': 'I sincerely understand your anger. ',
                    'tone': 'very calm',
                    'pace': 'slow'
                }
            }
        }

    async def generate_response(self, response_context: ResponseContext) -> Dict[str, Any]:
        """Generate a dynamic, contextually appropriate response"""
        
        try:
            # Determine response type based on conversation state and context
            response_type = self._determine_response_type(response_context)
            
            # Check if we can use knowledge base
            knowledge_enhanced = await self._enhance_with_knowledge_base(response_context)
            
            # Generate base response using OpenAI
            base_response = await self._generate_base_response(response_context, response_type, knowledge_enhanced)
            
            # Apply personality and style modifications
            styled_response = await self._apply_personality_style(base_response, response_context)
            
            # Apply language mixing and localization
            localized_response = await self._apply_language_mixing(styled_response, response_context)
            
            # Apply emotion-based modifications
            emotion_aware_response = await self._apply_emotion_awareness(localized_response, response_context)
            
            # Generate follow-up suggestions
            follow_ups = await self._generate_follow_up_suggestions(response_context)
            
            # Calculate response confidence
            confidence = self._calculate_response_confidence(response_context, emotion_aware_response)
            
            return {
                'text': emotion_aware_response,
                'type': response_type.value,
                'confidence': confidence,
                'follow_ups': follow_ups,
                'metadata': {
                    'knowledge_used': len(response_context.knowledge_base_results) > 0,
                    'emotion_detected': response_context.user_emotion,
                    'urgency_level': response_context.urgency_level,
                    'response_length': len(emotion_aware_response),
                    'language_mix': self._detect_language_mix(emotion_aware_response)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(response_context)

    def _determine_response_type(self, context: ResponseContext) -> ResponseType:
        """Determine the appropriate response type based on context"""
        
        conv_state = context.conversation_context.current_state
        user_emotion = context.user_emotion
        urgency = context.urgency_level
        
        # Handle urgent situations first
        if urgency > 0.8:
            return ResponseType.ESCALATION
        
        # Handle emotional states
        if user_emotion in ['angry', 'frustrated', 'worried', 'sad']:
            return ResponseType.EMPATHETIC
        
        # Handle conversation states
        if conv_state == ConversationState.GREETING:
            return ResponseType.GREETING
        elif conv_state == ConversationState.INFORMATION_GATHERING:
            return ResponseType.QUESTION_ASKING
        elif conv_state == ConversationState.PROCESSING:
            return ResponseType.INFORMATION_PROVIDING
        elif conv_state == ConversationState.CLARIFICATION:
            return ResponseType.CLARIFICATION
        elif conv_state == ConversationState.COMPLETION:
            return ResponseType.CONFIRMATION
        elif conv_state == ConversationState.FAREWELL:
            return ResponseType.FAREWELL
        
        return ResponseType.INFORMATION_PROVIDING

    async def _enhance_with_knowledge_base(self, context: ResponseContext) -> Dict[str, Any]:
        """Enhance response with knowledge base information"""
        
        enhancement = {
            'has_knowledge': False,
            'relevant_info': [],
            'confidence_boost': 0.0
        }
        
        if context.knowledge_base_results:
            # Process knowledge base results
            relevant_info = []
            for result in context.knowledge_base_results:
                for excerpt in result.get('excerpts', []):
                    relevant_info.append({
                        'source': result['source_name'],
                        'content': excerpt,
                        'relevance': result['relevance_score']
                    })
            
            if relevant_info:
                enhancement['has_knowledge'] = True
                enhancement['relevant_info'] = relevant_info
                enhancement['confidence_boost'] = 0.2
        
        return enhancement

    async def _generate_base_response(self, context: ResponseContext, response_type: ResponseType, knowledge: Dict) -> str:
        """Generate base response using OpenAI"""
        
        # Construct system prompt based on agent configuration
        system_prompt = self._create_dynamic_system_prompt(context, response_type)
        
        # Construct user prompt with context
        user_prompt = self._create_user_prompt(context, knowledge)
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=250,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI generation error: {e}")
            # Fall back to template-based response
            return self._get_template_response(response_type, context)

    def _create_dynamic_system_prompt(self, context: ResponseContext, response_type: ResponseType) -> str:
        """Create dynamic system prompt based on context"""
        
        agent_config = context.agent_config
        personality = agent_config.personality
        
        base_prompt = f"""You are {agent_config.name}, a {agent_config.agent_type.value.replace('_', ' ')} AI assistant.

Personality Traits:
- Response Style: {personality.response_style.value}
- Empathy Level: {personality.empathy_level}/1.0 (very empathetic)
- Formality Level: {personality.formality_level}/1.0
- Humor Level: {personality.humor_level}/1.0
- Patience Level: {personality.patience_level}/1.0
- Detail Level: {personality.detail_level}/1.0

Current Context:
- Response Type Needed: {response_type.value}
- User Emotion: {context.user_emotion}
- Conversation State: {context.conversation_context.current_state.value}
- Urgency Level: {context.urgency_level}/1.0

Guidelines:
1. Respond in a natural mix of {', '.join(context.agent_config.languages)}
2. Match the user's emotional state with appropriate empathy
3. Keep responses concise but complete
4. Use knowledge base information when available
5. Always aim to progress the conversation toward the user's goal
6. Maintain your personality consistently

Capabilities: {', '.join(agent_config.capabilities)}
Limitations: {', '.join(agent_config.limitations)}"""

        return base_prompt

    def _create_user_prompt(self, context: ResponseContext, knowledge: Dict) -> str:
        """Create user prompt with full context"""
        
        # Get recent conversation history
        recent_history = context.conversation_context.conversation_history[-6:]
        history_text = ""
        for msg in recent_history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        
        # Include knowledge base information if available
        knowledge_text = ""
        if knowledge['has_knowledge']:
            knowledge_text = "\nRelevant Knowledge Base Information:\n"
            for info in knowledge['relevant_info'][:3]:  # Top 3 most relevant
                knowledge_text += f"- {info['content']}\n"
        
        # Include extracted entities
        entities_text = ""
        if context.conversation_context.extracted_entities:
            entities_text = f"\nExtracted Information: {json.dumps(context.conversation_context.extracted_entities, ensure_ascii=False)}"
        
        prompt = f"""Recent Conversation:
{history_text}

{knowledge_text}

{entities_text}

Current Task: Generate an appropriate response that:
1. Addresses the user's most recent input
2. Maintains conversation flow
3. Shows appropriate emotional awareness
4. Uses available knowledge base information
5. Progresses toward conversation goals: {', '.join(context.conversation_goals)}

User's preferred language pattern: {context.language_preference}
Current emotional state: {context.user_emotion}

Generate a natural, helpful response:"""

        return prompt

    async def _apply_personality_style(self, base_response: str, context: ResponseContext) -> str:
        """Apply personality-based style modifications"""
        
        personality = context.agent_config.personality
        
        # Apply empathy level adjustments
        if personality.empathy_level > 0.7 and context.user_emotion in ['sad', 'worried', 'frustrated']:
            empathy_boost = await self._add_empathy_markers(base_response, context.user_emotion)
            base_response = empathy_boost
        
        # Apply formality level adjustments
        if personality.formality_level < 0.3:
            base_response = await self._make_more_casual(base_response)
        elif personality.formality_level > 0.8:
            base_response = await self._make_more_formal(base_response)
        
        # Apply humor if appropriate
        if personality.humor_level > 0.6 and context.user_emotion in ['happy', 'neutral']:
            base_response = await self._add_light_humor(base_response)
        
        return base_response

    async def _apply_language_mixing(self, response: str, context: ResponseContext) -> str:
        """Apply natural language mixing based on user preference"""
        
        user_language = context.language_preference
        
        # Determine mixing level based on user's language pattern
        if 'english' in user_language.lower():
            mix_level = LanguageMixLevel.LIGHT_HINGLISH
        elif 'hindi' in user_language.lower():
            mix_level = LanguageMixLevel.LIGHT_HINGLISH
        else:
            mix_level = LanguageMixLevel.HEAVY_HINGLISH
        
        # Apply natural code-switching
        mixed_response = await self._apply_code_switching(response, mix_level)
        
        return mixed_response

    async def _apply_emotion_awareness(self, response: str, context: ResponseContext) -> str:
        """Apply emotion-aware modifications to response"""
        
        emotion = context.user_emotion
        language = context.language_preference
        
        if emotion in self.emotion_modifiers:
            modifier = self.emotion_modifiers[emotion]
            
            # Choose appropriate language modifier
            if 'hindi' in language.lower():
                lang_modifier = modifier.get('hindi', modifier.get('english', {}))
            else:
                lang_modifier = modifier.get('english', {})
            
            # Apply prefix if needed
            prefix = lang_modifier.get('prefix', '')
            if prefix and not response.startswith(prefix):
                response = prefix + response
        
        return response

    async def _generate_follow_up_suggestions(self, context: ResponseContext) -> List[str]:
        """Generate contextually appropriate follow-up suggestions"""
        
        follow_ups = []
        
        # Based on current intent and state
        current_intent = context.conversation_context.detected_intent
        
        if current_intent == IntentType.APPOINTMENT_BOOKING:
            follow_ups = [
                "क्या आपको appointment की confirmation SMS चाहिए?",
                "Would you like to set a reminder?",
                "कोई special instructions हैं doctor के लिए?"
            ]
        elif current_intent == IntentType.INFORMATION_REQUEST:
            follow_ups = [
                "कोई और information चाहिए?",
                "Shall I explain this in more detail?",
                "क्या यह helpful था?"
            ]
        elif current_intent == IntentType.COMPLAINT:
            follow_ups = [
                "क्या मैं कोई और सहायता कर सकता हूं?",
                "Would you like to speak to a specialist?",
                "क्या emergency है?"
            ]
        
        return follow_ups[:3]  # Return top 3 suggestions

    def _calculate_response_confidence(self, context: ResponseContext, response: str) -> float:
        """Calculate confidence score for the generated response"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence for knowledge base usage
        if context.knowledge_base_results:
            confidence += 0.2
        
        # Boost confidence for clear intent
        if context.conversation_context.detected_intent:
            confidence += 0.15
        
        # Boost confidence for extracted entities
        if context.conversation_context.extracted_entities:
            confidence += 0.1
        
        # Adjust for response length (not too short, not too long)
        response_length = len(response)
        if 50 <= response_length <= 300:
            confidence += 0.1
        
        # Adjust for emotion appropriateness
        if context.user_emotion != 'neutral':
            if any(emotion_word in response.lower() for emotion_word in ['समझ', 'understand', 'sorry', 'माफ']):
                confidence += 0.05
        
        return min(1.0, confidence)

    def _get_template_response(self, response_type: ResponseType, context: ResponseContext) -> str:
        """Get template-based response as fallback"""
        
        language = context.language_preference if context.language_preference in ['hindi', 'english', 'hinglish'] else 'hinglish'
        
        templates = self.response_templates.get(response_type, {}).get(language, [])
        
        if templates:
            template = random.choice(templates)
            
            # Fill template placeholders
            return template.format(
                agent_name=context.agent_config.name,
                information="जानकारी उपलब्ध है",
                required_info="आवश्यक जानकारी",
                emotion_context=context.user_emotion
            )
        
        return "मैं आपकी सहायता करने की कोशिश कर रहा हूं। कृपया थोड़ा इंतजार करें।"

    async def _add_empathy_markers(self, response: str, emotion: str) -> str:
        """Add empathy markers to response based on user emotion"""
        
        empathy_markers = {
            'frustrated': ['मैं समझ सकता हूं', 'I understand', 'यह निराशाजनक है'],
            'worried': ['आपकी चिंता सही है', 'Your concern is valid', 'यह चिंता की बात है'],
            'sad': ['मुझे खुशी होगी अगर मैं मदद कर सकूं', 'I wish I could help', 'यह दुखद है']
        }
        
        markers = empathy_markers.get(emotion, [])
        if markers and not any(marker in response for marker in markers):
            marker = random.choice(markers)
            response = f"{marker}। {response}"
        
        return response

    async def _make_more_casual(self, response: str) -> str:
        """Make response more casual and friendly"""
        
        # Replace formal words with casual ones
        casual_replacements = {
            'आपकी सहायता': 'आपकी help',
            'कृपया': 'please',
            'धन्यवाद': 'thanks',
            'माफ करें': 'sorry',
        }
        
        for formal, casual in casual_replacements.items():
            response = response.replace(formal, casual)
        
        return response

    async def _make_more_formal(self, response: str) -> str:
        """Make response more formal and professional"""
        
        # Replace casual words with formal ones
        formal_replacements = {
            'help': 'सहायता',
            'thanks': 'धन्यवाद',
            'sorry': 'क्षमा करें',
            'okay': 'ठीक है',
        }
        
        for casual, formal in formal_replacements.items():
            response = response.replace(casual, formal)
        
        return response

    async def _add_light_humor(self, response: str) -> str:
        """Add light, appropriate humor to response"""
        
        humor_additions = [
            " 😊",
            " (मुस्कुराते हुए)",
            " - sounds good!",
            " - बिल्कुल!"
        ]
        
        if random.random() < 0.3:  # 30% chance to add humor
            humor = random.choice(humor_additions)
            response += humor
        
        return response

    async def _apply_code_switching(self, response: str, mix_level: LanguageMixLevel) -> str:
        """Apply natural code-switching based on mix level"""
        
        pattern = self.language_patterns[mix_level]
        switch_prob = pattern['switch_probability']
        common_switches = pattern['common_switches']
        
        if random.random() < switch_prob:
            # Apply some common switches
            for switch_word in common_switches:
                if switch_word in response.lower():
                    # This is a simplified implementation
                    # In practice, you'd have more sophisticated switching logic
                    pass
        
        return response

    def _detect_language_mix(self, response: str) -> str:
        """Detect the language mix pattern in response"""
        
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', response))
        english_chars = len(re.findall(r'[a-zA-Z]', response))
        total_chars = hindi_chars + english_chars
        
        if total_chars == 0:
            return "unknown"
        
        hindi_ratio = hindi_chars / total_chars
        
        if hindi_ratio > 0.8:
            return "mostly_hindi"
        elif hindi_ratio < 0.2:
            return "mostly_english"
        else:
            return "mixed_hinglish"

    def _get_fallback_response(self, context: ResponseContext) -> Dict[str, Any]:
        """Get fallback response when generation fails"""
        
        fallback_responses = {
            'hindi': "क्षमा करें, मुझे कुछ तकनीकी समस्या हो रही है। कृपया दोबारा कोशिश करें।",
            'english': "I'm sorry, I'm experiencing some technical difficulties. Please try again.",
            'hinglish': "Sorry, मुझे कुछ technical issue हो रहा है। Please try again।"
        }
        
        language = context.language_preference if context.language_preference in fallback_responses else 'hinglish'
        
        return {
            'text': fallback_responses[language],
            'type': 'fallback',
            'confidence': 0.3,
            'follow_ups': [],
            'metadata': {
                'is_fallback': True,
                'original_error': True
            }
        }

# Integration class that combines all components
class IntelligentVoiceAgent:
    """Complete intelligent voice agent combining conversation engine, config, and response generation"""
    
    def __init__(self, agent_config: AdvancedAgentConfig):
        self.agent_config = agent_config
        self.conversation_engine = IntelligentConversationEngine(asdict(agent_config))
        self.response_generator = DynamicResponseGenerator()
        self.config_manager = AdvancedAgentConfigManager({})
        
        self.logger = logging.getLogger(__name__)

    async def start_conversation(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new intelligent conversation"""
        
        context = await self.conversation_engine.start_conversation(session_id, user_id)
        
        return {
            'session_id': session_id,
            'greeting': context.conversation_history[0]['content'],
            'agent_name': self.agent_config.name,
            'capabilities': self.agent_config.capabilities,
            'supported_languages': self.agent_config.languages
        }

    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Process user message and generate intelligent response"""
        
        # Process with conversation engine
        engine_result = await self.conversation_engine.process_user_input(session_id, user_message)
        
        # Get conversation context
        conv_context = self.conversation_engine.get_conversation_context(session_id)
        
        # Search knowledge base if needed
        knowledge_results = []
        if conv_context.detected_intent:
            knowledge_results = await self.config_manager.search_knowledge_base(
                self.agent_config.agent_id, 
                user_message
            )
        
        # Create response context
        response_context = ResponseContext(
            conversation_context=conv_context,
            agent_config=self.agent_config,
            user_emotion=engine_result['context']['sentiment'],
            urgency_level=self._calculate_urgency(user_message),
            language_preference=conv_context.language_preference,
            previous_responses=[msg['content'] for msg in conv_context.conversation_history if msg['role'] == 'assistant'],
            knowledge_base_results=knowledge_results,
            conversation_goals=conv_context.conversation_goals
        )
        
        # Generate intelligent response
        response = await self.response_generator.generate_response(response_context)
        
        return {
            'response': response['text'],
            'confidence': response['confidence'],
            'follow_ups': response['follow_ups'],
            'context': engine_result['context'],
            'actions': engine_result['actions'],
            'metadata': response['metadata']
        }

    def _calculate_urgency(self, user_message: str) -> float:
        """Calculate urgency level from user message"""
        
        urgent_keywords = ['emergency', 'urgent', 'serious', 'help', 'pain', 'immediate', 'now']
        urgency_score = 0.0
        
        for keyword in urgent_keywords:
            if keyword in user_message.lower():
                urgency_score += 0.2
        
        return min(1.0, urgency_score)

# Example usage
if __name__ == "__main__":
    async def test_intelligent_agent():
        # This would normally load from the config system
        from advanced_agent_config import AgentPersonality, ResponseStyle, AgentType
        
        # Create test agent config
        personality = AgentPersonality(
            response_style=ResponseStyle.EMPATHETIC,
            empathy_level=0.9,
            formality_level=0.6,
            humor_level=0.3,
            patience_level=0.8,
            detail_level=0.7
        )
        
        agent_config = AdvancedAgentConfig(
            agent_id="test-agent-123",
            name="Dr. Smart Assistant",
            description="Intelligent healthcare assistant",
            agent_type=AgentType.HEALTHCARE_ASSISTANT,
            personality=personality,
            knowledge_sources=[],
            conversation_templates=[],
            system_prompts={},
            languages=['hindi', 'english', 'hinglish'],
            capabilities=['appointment_booking', 'health_information'],
            limitations=['no_medical_diagnosis'],
            escalation_rules={},
            performance_metrics={}
        )
        
        # Test the intelligent agent
        agent = IntelligentVoiceAgent(agent_config)
        
        # Start conversation
        session_id = "test-session-123"
        start_result = await agent.start_conversation(session_id)
        print(f"Greeting: {start_result['greeting']}")
        
        # Test conversation
        test_messages = [
            "Hello, मुझे appointment book करना है",
            "मैं बहुत परेशान हूं, बहुत pain है",
            "My name is Rajesh और मेरा phone 9876543210 है"
        ]
        
        for message in test_messages:
            result = await agent.process_message(session_id, message)
            print(f"\nUser: {message}")
            print(f"Agent: {result['response']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Follow-ups: {result['follow_ups']}")

    # Run test if API key is available
    if os.getenv('OPENAI_API_KEY'):
        asyncio.run(test_intelligent_agent())
    else:
        print("OpenAI API key not found. Skipping test.")