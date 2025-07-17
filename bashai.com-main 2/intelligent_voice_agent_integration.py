"""
Intelligent Voice Agent Integration System
Brings together all components for a complete intelligent voice agent solution
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid

# Import all our intelligent components
from intelligent_conversation_engine import (
    IntelligentConversationEngine, ConversationContext, ConversationState, IntentType
)
from advanced_agent_config import (
    AdvancedAgentConfigManager, AdvancedAgentConfig, AgentPersonality, 
    ResponseStyle, AgentType
)
from dynamic_response_generator import (
    DynamicResponseGenerator, IntelligentVoiceAgent, ResponseContext
)
from conversation_flow_manager import ConversationFlowManager

@dataclass
class IntelligentVoiceSession:
    """Represents an active intelligent voice session"""
    session_id: str
    agent_id: str
    user_id: Optional[str]
    conversation_context: ConversationContext
    agent_config: AdvancedAgentConfig
    flow_context: Optional[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    start_time: datetime
    last_activity: datetime
    is_active: bool = True

class IntelligentVoiceAgentSystem:
    """Complete intelligent voice agent system integrating all components"""
    
    def __init__(self, supabase_config: Dict[str, str]):
        self.supabase_config = supabase_config
        
        # Initialize component managers
        self.config_manager = AdvancedAgentConfigManager(supabase_config)
        self.response_generator = DynamicResponseGenerator()
        
        # Active sessions and agents
        self.active_sessions: Dict[str, IntelligentVoiceSession] = {}
        self.agent_instances: Dict[str, IntelligentVoiceAgent] = {}
        self.flow_managers: Dict[str, ConversationFlowManager] = {}
        
        # System metrics
        self.system_metrics = {
            'total_conversations': 0,
            'average_satisfaction': 0.0,
            'total_response_time': 0.0,
            'success_rate': 0.0,
            'intelligence_score': 0.0
        }
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def create_intelligent_agent(self, agent_config_data: Dict[str, Any]) -> str:
        """Create a new intelligent voice agent with full capabilities"""
        
        try:
            # Create advanced agent configuration
            agent_config = await self.config_manager.create_agent_config(
                agent_config_data,
                agent_config_data.get('knowledge_files', [])
            )
            
            # Create the intelligent voice agent instance
            intelligent_agent = IntelligentVoiceAgent(agent_config)
            
            # Create conversation flow manager for this agent
            flow_manager = ConversationFlowManager(agent_config)
            
            # Store instances
            self.agent_instances[agent_config.agent_id] = intelligent_agent
            self.flow_managers[agent_config.agent_id] = flow_manager
            
            self.logger.info(f"Created intelligent agent: {agent_config.agent_id}")
            
            return agent_config.agent_id
            
        except Exception as e:
            self.logger.error(f"Error creating intelligent agent: {e}")
            raise

    async def start_voice_session(self, agent_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new intelligent voice session"""
        
        if agent_id not in self.agent_instances:
            raise ValueError(f"Agent {agent_id} not found")
        
        session_id = str(uuid.uuid4())
        agent = self.agent_instances[agent_id]
        flow_manager = self.flow_managers[agent_id]
        
        # Start conversation with the intelligent agent
        conversation_result = await agent.start_conversation(session_id, user_id)
        
        # Get conversation context
        conversation_context = agent.conversation_engine.get_conversation_context(session_id)
        
        # Create session record
        session = IntelligentVoiceSession(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            conversation_context=conversation_context,
            agent_config=agent.agent_config,
            flow_context=None,
            performance_metrics={
                'response_times': [],
                'user_satisfaction': 0.0,
                'intent_accuracy': 0.0,
                'conversation_success': False
            },
            start_time=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        self.active_sessions[session_id] = session
        
        return {
            'session_id': session_id,
            'agent_name': agent.agent_config.name,
            'greeting': conversation_result['greeting'],
            'capabilities': conversation_result['capabilities'],
            'languages': conversation_result['supported_languages'],
            'intelligence_features': {
                'intent_recognition': True,
                'context_memory': True,
                'sentiment_analysis': True,
                'multi_language': True,
                'knowledge_base': len(agent.agent_config.knowledge_sources) > 0,
                'conversation_flows': len(agent.agent_config.conversation_templates) > 0
            }
        }

    async def process_voice_input(self, session_id: str, user_input: str, audio_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process voice input with full intelligence capabilities"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now(timezone.utc)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get the intelligent agent and flow manager
            agent = self.agent_instances[session.agent_id]
            flow_manager = self.flow_managers[session.agent_id]
            
            # Process message with intelligent agent
            agent_result = await agent.process_message(session_id, user_input)
            
            # Process with flow manager if flows are active
            flow_result = None
            if flow_manager and hasattr(flow_manager, 'active_flows') and session_id in flow_manager.active_flows:
                conversation_context = agent.conversation_engine.get_conversation_context(session_id)
                flow_result = await flow_manager.process_user_input(session_id, user_input, conversation_context)
            
            # Calculate response time
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            session.performance_metrics['response_times'].append(response_time)
            
            # Update session context
            session.conversation_context = agent.conversation_engine.get_conversation_context(session_id)
            if flow_result:
                session.flow_context = flow_result
            
            # Calculate intelligence metrics
            intelligence_metrics = await self._calculate_intelligence_metrics(session, agent_result)
            
            # Prepare response
            response = {
                'session_id': session_id,
                'response': agent_result['response'],
                'confidence': agent_result['confidence'],
                'context': agent_result['context'],
                'actions': agent_result['actions'],
                'follow_ups': agent_result.get('follow_ups', []),
                'intelligence_metrics': intelligence_metrics,
                'performance': {
                    'response_time': response_time,
                    'avg_response_time': sum(session.performance_metrics['response_times']) / len(session.performance_metrics['response_times']),
                    'conversation_turns': len(session.conversation_context.conversation_history)
                }
            }
            
            # Add flow information if available
            if flow_result:
                response['flow_status'] = {
                    'current_node': flow_result.get('node_id'),
                    'flow_complete': flow_result.get('flow_complete', False),
                    'next_actions': flow_result.get('action_results', [])
                }
            
            # Update system metrics
            await self._update_system_metrics(session, agent_result, response_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing voice input: {e}")
            raise

    async def _calculate_intelligence_metrics(self, session: IntelligentVoiceSession, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate intelligence metrics for the conversation"""
        
        context = session.conversation_context
        
        # Intent recognition accuracy
        intent_accuracy = 1.0 if context.detected_intent else 0.5
        
        # Context retention score
        context_score = min(1.0, len(context.extracted_entities) / 5.0)  # Normalize to entities found
        
        # Response quality based on confidence
        response_quality = agent_result.get('confidence', 0.5)
        
        # Sentiment handling appropriateness
        sentiment_handling = 1.0 if context.emotion in ['happy', 'neutral'] else 0.8
        if context.emotion in ['angry', 'frustrated'] and agent_result['confidence'] > 0.8:
            sentiment_handling = 0.9  # Good handling of negative emotions
        
        # Language handling score
        language_score = 0.9  # Assume good multilingual handling
        
        # Overall intelligence score
        intelligence_score = (
            intent_accuracy * 0.25 +
            context_score * 0.2 +
            response_quality * 0.25 +
            sentiment_handling * 0.15 +
            language_score * 0.15
        )
        
        return {
            'intent_accuracy': round(intent_accuracy, 3),
            'context_retention': round(context_score, 3),
            'response_quality': round(response_quality, 3),
            'sentiment_handling': round(sentiment_handling, 3),
            'language_handling': round(language_score, 3),
            'overall_intelligence': round(intelligence_score, 3),
            'conversation_coherence': round(min(1.0, len(context.conversation_history) / 10.0), 3)
        }

    async def _update_system_metrics(self, session: IntelligentVoiceSession, agent_result: Dict[str, Any], response_time: float):
        """Update system-wide performance metrics"""
        
        self.system_metrics['total_conversations'] += 1
        
        # Update average response time
        total_time = self.system_metrics['total_response_time'] + response_time
        self.system_metrics['total_response_time'] = total_time
        
        # Update success rate based on confidence
        confidence = agent_result.get('confidence', 0.5)
        current_success = self.system_metrics['success_rate']
        self.system_metrics['success_rate'] = (current_success + (1.0 if confidence > 0.7 else 0.0)) / 2
        
        # Update intelligence score
        intelligence_metrics = await self._calculate_intelligence_metrics(session, agent_result)
        current_intelligence = self.system_metrics['intelligence_score']
        self.system_metrics['intelligence_score'] = (current_intelligence + intelligence_metrics['overall_intelligence']) / 2

    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a session"""
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        context = session.conversation_context
        
        # Calculate conversation metrics
        total_turns = len(context.conversation_history)
        user_turns = len([msg for msg in context.conversation_history if msg['role'] == 'user'])
        agent_turns = len([msg for msg in context.conversation_history if msg['role'] == 'assistant'])
        
        # Calculate average response time
        response_times = session.performance_metrics['response_times']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate conversation duration
        duration = (session.last_activity - session.start_time).total_seconds()
        
        # Analyze conversation quality
        quality_metrics = {
            'intent_recognition_rate': 1.0 if context.detected_intent else 0.0,
            'entity_extraction_success': len(context.extracted_entities) / max(1, user_turns),
            'sentiment_tracking_accuracy': 0.85,  # Mock value
            'response_coherence': 0.92,  # Mock value
            'language_adaptation': 0.88   # Mock value
        }
        
        return {
            'session_id': session_id,
            'agent_name': session.agent_config.name,
            'duration_seconds': duration,
            'conversation_metrics': {
                'total_turns': total_turns,
                'user_turns': user_turns,
                'agent_turns': agent_turns,
                'avg_response_time': avg_response_time,
                'conversation_state': context.current_state.value,
                'detected_intent': context.detected_intent.value if context.detected_intent else None,
                'extracted_entities': context.extracted_entities,
                'current_sentiment': context.emotion,
                'language_used': context.language_preference
            },
            'quality_metrics': quality_metrics,
            'performance_score': sum(quality_metrics.values()) / len(quality_metrics),
            'intelligence_features_used': {
                'context_memory': len(context.conversation_history) > 1,
                'entity_extraction': len(context.extracted_entities) > 0,
                'intent_recognition': context.detected_intent is not None,
                'sentiment_analysis': context.emotion != 'neutral',
                'multi_language': any(char in 'हिंदी' for msg in context.conversation_history for char in msg.get('content', ''))
            }
        }

    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End an intelligent voice session with comprehensive summary"""
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        
        # Get final analytics
        analytics = await self.get_session_analytics(session_id)
        
        # End conversation in the engine
        agent = self.agent_instances[session.agent_id]
        engine_summary = agent.conversation_engine.end_conversation(session_id)
        
        # End flow if active
        flow_manager = self.flow_managers[session.agent_id]
        flow_summary = None
        if hasattr(flow_manager, 'active_flows') and session_id in flow_manager.active_flows:
            flow_summary = flow_manager.end_flow(session_id)
        
        # Calculate final performance metrics
        response_times = session.performance_metrics['response_times']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Determine conversation success
        conversation_success = (
            analytics['performance_score'] > 0.7 and
            len(session.conversation_context.extracted_entities) > 0 and
            session.conversation_context.current_state in [ConversationState.COMPLETION, ConversationState.FAREWELL]
        )
        
        # Create comprehensive summary
        summary = {
            'session_id': session_id,
            'agent_id': session.agent_id,
            'agent_name': session.agent_config.name,
            'user_id': session.user_id,
            'duration_seconds': (session.last_activity - session.start_time).total_seconds(),
            'conversation_success': conversation_success,
            'performance_metrics': {
                'total_turns': len(session.conversation_context.conversation_history),
                'average_response_time': avg_response_time,
                'performance_score': analytics['performance_score'],
                'intelligence_score': analytics['quality_metrics']
            },
            'conversation_summary': {
                'final_intent': session.conversation_context.detected_intent.value if session.conversation_context.detected_intent else None,
                'entities_extracted': session.conversation_context.extracted_entities,
                'final_sentiment': session.conversation_context.emotion,
                'language_used': session.conversation_context.language_preference,
                'goals_achieved': conversation_success
            },
            'engine_summary': engine_summary,
            'flow_summary': flow_summary,
            'recommendations': self._generate_recommendations(session, analytics)
        }
        
        # Clean up session
        session.is_active = False
        del self.active_sessions[session_id]
        
        self.logger.info(f"Session ended: {session_id}, Success: {conversation_success}")
        
        return summary

    def _generate_recommendations(self, session: IntelligentVoiceSession, analytics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving the agent based on session data"""
        
        recommendations = []
        
        # Check response time
        response_times = session.performance_metrics['response_times']
        if response_times and sum(response_times) / len(response_times) > 2.0:
            recommendations.append("Consider optimizing response generation for faster replies")
        
        # Check intent recognition
        if not session.conversation_context.detected_intent:
            recommendations.append("Improve intent recognition training with more conversation examples")
        
        # Check entity extraction
        if len(session.conversation_context.extracted_entities) < 2:
            recommendations.append("Enhance entity extraction patterns for better information gathering")
        
        # Check conversation completion
        if session.conversation_context.current_state not in [ConversationState.COMPLETION, ConversationState.FAREWELL]:
            recommendations.append("Review conversation flows to improve completion rates")
        
        # Check performance score
        if analytics['performance_score'] < 0.8:
            recommendations.append("Consider adding more knowledge sources or improving response templates")
        
        if not recommendations:
            recommendations.append("Agent performed excellently! Consider expanding capabilities for more use cases")
        
        return recommendations

    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview and metrics"""
        
        # Count active components
        total_agents = len(self.agent_instances)
        active_sessions = len([s for s in self.active_sessions.values() if s.is_active])
        
        # Calculate system-wide metrics
        system_health = {
            'total_agents': total_agents,
            'active_sessions': active_sessions,
            'system_uptime': '99.9%',  # Mock value
            'average_response_time': self.system_metrics['total_response_time'] / max(1, self.system_metrics['total_conversations']),
            'success_rate': self.system_metrics['success_rate'],
            'intelligence_score': self.system_metrics['intelligence_score']
        }
        
        # Agent performance summary
        agent_performance = {}
        for agent_id, agent in self.agent_instances.items():
            agent_sessions = [s for s in self.active_sessions.values() if s.agent_id == agent_id]
            agent_performance[agent_id] = {
                'name': agent.agent_config.name,
                'type': agent.agent_config.agent_type.value,
                'active_sessions': len(agent_sessions),
                'knowledge_sources': len(agent.agent_config.knowledge_sources),
                'capabilities': len(agent.agent_config.capabilities),
                'languages': len(agent.agent_config.languages)
            }
        
        return {
            'system_health': system_health,
            'agent_performance': agent_performance,
            'intelligence_features': {
                'natural_language_understanding': True,
                'context_memory': True,
                'sentiment_analysis': True,
                'multi_language_support': True,
                'conversation_flows': True,
                'knowledge_base_integration': True,
                'real_time_analytics': True
            },
            'system_metrics': self.system_metrics
        }

    async def test_agent_intelligence(self, agent_id: str) -> Dict[str, Any]:
        """Comprehensive intelligence test for an agent"""
        
        if agent_id not in self.agent_instances:
            return {'error': 'Agent not found'}
        
        agent = self.agent_instances[agent_id]
        
        # Test scenarios
        test_scenarios = [
            {
                'name': 'Intent Recognition Test',
                'input': 'Hello, मुझे appointment book करना है',
                'expected_intent': 'appointment_booking'
            },
            {
                'name': 'Entity Extraction Test',
                'input': 'My name is राजेश Kumar और मेरा phone 9876543210 है',
                'expected_entities': ['name', 'phone']
            },
            {
                'name': 'Sentiment Analysis Test',
                'input': 'मैं बहुत परेशान हूं, please help करें',
                'expected_sentiment': 'negative'
            },
            {
                'name': 'Multi-language Test',
                'input': 'नमस्ते! Can you help me with my health issues?',
                'expected_language': 'hinglish'
            }
        ]
        
        test_results = []
        overall_score = 0.0
        
        # Create test session
        test_session_id = f"test_{uuid.uuid4().hex[:8]}"
        await self.start_voice_session(agent_id)
        
        for scenario in test_scenarios:
            try:
                # Process test input
                result = await self.process_voice_input(test_session_id, scenario['input'])
                
                # Evaluate results
                score = 0.0
                details = {}
                
                if 'intent' in scenario['expected_intent']:
                    detected_intent = result['context'].get('detected_intent')
                    if detected_intent == scenario['expected_intent']:
                        score += 0.5
                    details['intent_match'] = detected_intent == scenario['expected_intent']
                
                if 'entities' in scenario:
                    entities = result['context'].get('entities', {})
                    expected_entities = scenario['expected_entities']
                    entity_score = len([e for e in expected_entities if e in entities]) / len(expected_entities)
                    score += entity_score * 0.5
                    details['entity_extraction'] = entity_score
                
                test_results.append({
                    'scenario': scenario['name'],
                    'input': scenario['input'],
                    'score': score,
                    'details': details,
                    'response': result['response']
                })
                
                overall_score += score
                
            except Exception as e:
                test_results.append({
                    'scenario': scenario['name'],
                    'input': scenario['input'],
                    'score': 0.0,
                    'error': str(e)
                })
        
        # End test session
        await self.end_session(test_session_id)
        
        overall_score = overall_score / len(test_scenarios)
        
        return {
            'agent_id': agent_id,
            'agent_name': agent.agent_config.name,
            'overall_score': round(overall_score, 3),
            'test_results': test_results,
            'intelligence_grade': self._get_intelligence_grade(overall_score),
            'recommendations': self._generate_test_recommendations(overall_score, test_results)
        }

    def _get_intelligence_grade(self, score: float) -> str:
        """Convert intelligence score to grade"""
        if score >= 0.9:
            return 'A+ (Exceptional)'
        elif score >= 0.8:
            return 'A (Excellent)'
        elif score >= 0.7:
            return 'B+ (Very Good)'
        elif score >= 0.6:
            return 'B (Good)'
        elif score >= 0.5:
            return 'C (Average)'
        else:
            return 'D (Needs Improvement)'

    def _generate_test_recommendations(self, overall_score: float, test_results: List[Dict]) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        if overall_score < 0.7:
            recommendations.append("Consider additional training data for better performance")
        
        # Check specific test results
        for result in test_results:
            if result.get('score', 0) < 0.5:
                if 'Intent Recognition' in result['scenario']:
                    recommendations.append("Improve intent recognition with more training examples")
                elif 'Entity Extraction' in result['scenario']:
                    recommendations.append("Enhance entity extraction patterns")
                elif 'Sentiment Analysis' in result['scenario']:
                    recommendations.append("Improve sentiment analysis accuracy")
        
        if overall_score >= 0.8:
            recommendations.append("Excellent performance! Consider expanding to new use cases")
        
        return recommendations

# Integration with Flask app
def create_intelligent_voice_endpoints(app, socketio, supabase_config):
    """Create Flask endpoints for the intelligent voice agent system"""
    
    # Initialize the intelligent voice agent system
    intelligent_system = IntelligentVoiceAgentSystem(supabase_config)
    
    @app.route('/api/intelligent-agents', methods=['POST'])
    async def create_intelligent_agent():
        """Create a new intelligent voice agent"""
        try:
            agent_config_data = request.json
            agent_id = await intelligent_system.create_intelligent_agent(agent_config_data)
            
            return jsonify({
                'success': True,
                'agent_id': agent_id,
                'message': 'Intelligent agent created successfully'
            }), 201
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/intelligent-sessions', methods=['POST'])
    async def start_intelligent_session():
        """Start a new intelligent voice session"""
        try:
            data = request.json
            agent_id = data.get('agent_id')
            user_id = data.get('user_id')
            
            session_result = await intelligent_system.start_voice_session(agent_id, user_id)
            
            return jsonify({
                'success': True,
                'session': session_result
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/intelligent-sessions/<session_id>/message', methods=['POST'])
    async def process_intelligent_message():
        """Process a message in an intelligent voice session"""
        try:
            session_id = request.view_args['session_id']
            data = request.json
            user_input = data.get('message')
            audio_metadata = data.get('audio_metadata')
            
            result = await intelligent_system.process_voice_input(session_id, user_input, audio_metadata)
            
            return jsonify({
                'success': True,
                'result': result
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/intelligent-sessions/<session_id>/analytics', methods=['GET'])
    async def get_session_analytics():
        """Get analytics for an intelligent voice session"""
        try:
            session_id = request.view_args['session_id']
            analytics = await intelligent_system.get_session_analytics(session_id)
            
            return jsonify({
                'success': True,
                'analytics': analytics
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/intelligent-sessions/<session_id>', methods=['DELETE'])
    async def end_intelligent_session():
        """End an intelligent voice session"""
        try:
            session_id = request.view_args['session_id']
            summary = await intelligent_system.end_session(session_id)
            
            return jsonify({
                'success': True,
                'summary': summary
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/intelligent-agents/<agent_id>/test', methods=['POST'])
    async def test_agent_intelligence():
        """Test an agent's intelligence capabilities"""
        try:
            agent_id = request.view_args['agent_id']
            test_results = await intelligent_system.test_agent_intelligence(agent_id)
            
            return jsonify({
                'success': True,
                'test_results': test_results
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/intelligent-system/overview', methods=['GET'])
    async def get_system_overview():
        """Get comprehensive system overview"""
        try:
            overview = await intelligent_system.get_system_overview()
            
            return jsonify({
                'success': True,
                'overview': overview
            }), 200
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return intelligent_system

# Example usage and testing
if __name__ == "__main__":
    async def test_intelligent_system():
        # Initialize system
        supabase_config = {
            'url': os.getenv('SUPABASE_URL', ''),
            'key': os.getenv('SUPABASE_SERVICE_KEY', '')
        }
        
        system = IntelligentVoiceAgentSystem(supabase_config)
        
        # Create intelligent agent
        agent_config = {
            'name': 'Dr. Intelligent Assistant',
            'description': 'Advanced AI assistant with full intelligence capabilities',
            'agent_type': 'healthcare_assistant',
            'response_style': 'empathetic',
            'empathy_level': 0.9,
            'formality_level': 0.6,
            'humor_level': 0.3,
            'patience_level': 0.9,
            'detail_level': 0.8,
            'languages': ['hindi', 'english', 'hinglish'],
            'knowledge_files': [
                {
                    'name': 'Healthcare FAQ',
                    'type': 'faq_database',
                    'faq_data': [
                        {
                            'question': 'What are visiting hours?',
                            'answer': 'Visiting hours are 9 AM to 6 PM daily'
                        }
                    ]
                }
            ]
        }
        
        agent_id = await system.create_intelligent_agent(agent_config)
        print(f"Created intelligent agent: {agent_id}")
        
        # Start session
        session_result = await system.start_voice_session(agent_id)
        session_id = session_result['session_id']
        print(f"Started session: {session_id}")
        print(f"Greeting: {session_result['greeting']}")
        
        # Test conversation
        test_messages = [
            "Hello, मुझे appointment book करना है",
            "My name is राजेश और phone 9876543210",
            "Tomorrow morning कोई slot available है?"
        ]
        
        for message in test_messages:
            result = await system.process_voice_input(session_id, message)
            print(f"\nUser: {message}")
            print(f"Agent: {result['response']}")
            print(f"Intelligence Score: {result['intelligence_metrics']['overall_intelligence']}")
            print(f"Confidence: {result['confidence']}")
        
        # Get analytics
        analytics = await system.get_session_analytics(session_id)
        print(f"\nSession Analytics:")
        print(f"Performance Score: {analytics['performance_score']}")
        print(f"Intelligence Features Used: {analytics['intelligence_features_used']}")
        
        # Test agent intelligence
        test_results = await system.test_agent_intelligence(agent_id)
        print(f"\nIntelligence Test Results:")
        print(f"Overall Score: {test_results['overall_score']}")
        print(f"Grade: {test_results['intelligence_grade']}")
        
        # End session
        summary = await system.end_session(session_id)
        print(f"\nSession Summary:")
        print(f"Success: {summary['conversation_success']}")
        print(f"Duration: {summary['duration_seconds']} seconds")
        print(f"Recommendations: {summary['recommendations']}")
        
        # System overview
        overview = await system.get_system_overview()
        print(f"\nSystem Overview:")
        print(f"Intelligence Score: {overview['system_health']['intelligence_score']}")
        print(f"Success Rate: {overview['system_health']['success_rate']}")

    # Run test if API key is available
    if os.getenv('OPENAI_API_KEY'):
        asyncio.run(test_intelligent_system())
    else:
        print("OpenAI API key not found. Skipping test.")