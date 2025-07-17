"""
Conversation Flow Management System for BhashAI
Manages complex conversation flows with intent recognition and dynamic branching
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from intelligent_conversation_engine import (
    ConversationContext, ConversationState, IntentType
)
from advanced_agent_config import AdvancedAgentConfig

class FlowNodeType(Enum):
    START = "start"
    INTENT_RECOGNITION = "intent_recognition"
    INFORMATION_COLLECTION = "information_collection"
    CONDITION_CHECK = "condition_check"
    ACTION_EXECUTION = "action_execution"
    RESPONSE_GENERATION = "response_generation"
    ESCALATION = "escalation"
    END = "end"
    BRANCH = "branch"
    LOOP = "loop"

class FlowConditionType(Enum):
    ENTITY_PRESENT = "entity_present"
    ENTITY_VALUE = "entity_value"
    INTENT_CONFIDENCE = "intent_confidence"
    SENTIMENT_SCORE = "sentiment_score"
    USER_RESPONSE = "user_response"
    TIME_ELAPSED = "time_elapsed"
    ATTEMPT_COUNT = "attempt_count"
    CUSTOM_FUNCTION = "custom_function"

@dataclass
class FlowCondition:
    """Represents a condition for flow branching"""
    type: FlowConditionType
    field: str
    operator: str  # ==, !=, >, <, >=, <=, contains, in
    value: Any
    custom_function: Optional[str] = None

@dataclass
class FlowNode:
    """Represents a node in the conversation flow"""
    id: str
    type: FlowNodeType
    name: str
    description: str
    conditions: List[FlowCondition]
    actions: List[Dict[str, Any]]
    next_nodes: Dict[str, str]  # condition_name -> next_node_id
    default_next: Optional[str] = None
    max_attempts: int = 3
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConversationFlow:
    """Represents a complete conversation flow"""
    id: str
    name: str
    description: str
    start_node: str
    nodes: Dict[str, FlowNode]
    global_conditions: List[FlowCondition]
    variables: Dict[str, Any]
    created_at: datetime
    version: str = "1.0"
    is_active: bool = True
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}

@dataclass
class FlowExecutionContext:
    """Tracks the execution context of a conversation flow"""
    session_id: str
    flow_id: str
    current_node_id: str
    conversation_context: ConversationContext
    flow_variables: Dict[str, Any]
    node_history: List[Dict[str, Any]]
    attempt_counts: Dict[str, int]
    start_time: datetime
    last_update: datetime
    
    def __post_init__(self):
        if self.flow_variables is None:
            self.flow_variables = {}
        if self.node_history is None:
            self.node_history = []
        if self.attempt_counts is None:
            self.attempt_counts = {}

class ConversationFlowManager:
    """Manages conversation flows with intelligent branching and intent recognition"""
    
    def __init__(self, agent_config: AdvancedAgentConfig):
        self.agent_config = agent_config
        
        # Active flow executions indexed by session_id
        self.active_flows: Dict[str, FlowExecutionContext] = {}
        
        # Predefined flows for different agent types and intents
        self.predefined_flows = self._initialize_predefined_flows()
        
        # Custom condition functions
        self.condition_functions = self._initialize_condition_functions()
        
        # Action handlers
        self.action_handlers = self._initialize_action_handlers()
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _initialize_predefined_flows(self) -> Dict[str, ConversationFlow]:
        """Initialize predefined conversation flows"""
        flows = {}
        
        # Healthcare Appointment Booking Flow
        flows['healthcare_appointment'] = self._create_appointment_booking_flow()
        
        # Customer Service Issue Resolution Flow
        flows['customer_service_issue'] = self._create_issue_resolution_flow()
        
        # Information Request Flow
        flows['information_request'] = self._create_information_request_flow()
        
        # Emergency Handling Flow
        flows['emergency_handling'] = self._create_emergency_flow()
        
        return flows

    def _create_appointment_booking_flow(self) -> ConversationFlow:
        """Create appointment booking conversation flow"""
        
        # Create nodes
        nodes = {}
        
        # Start node
        nodes['start'] = FlowNode(
            id='start',
            type=FlowNodeType.START,
            name='Flow Start',
            description='Initialize appointment booking flow',
            conditions=[],
            actions=[{'type': 'set_variable', 'name': 'booking_stage', 'value': 'started'}],
            next_nodes={'default': 'collect_personal_info'},
            default_next='collect_personal_info'
        )
        
        # Collect personal information
        nodes['collect_personal_info'] = FlowNode(
            id='collect_personal_info',
            type=FlowNodeType.INFORMATION_COLLECTION,
            name='Collect Personal Information',
            description='Gather patient name and contact details',
            conditions=[
                FlowCondition(
                    type=FlowConditionType.ENTITY_PRESENT,
                    field='name',
                    operator='!=',
                    value=None
                ),
                FlowCondition(
                    type=FlowConditionType.ENTITY_PRESENT,
                    field='phone',
                    operator='!=',
                    value=None
                )
            ],
            actions=[
                {
                    'type': 'ask_question',
                    'question': 'आपका नाम और phone number क्या है? (What is your name and phone number?)',
                    'required_entities': ['name', 'phone']
                }
            ],
            next_nodes={
                'info_complete': 'collect_appointment_details',
                'info_incomplete': 'collect_personal_info'
            },
            default_next='collect_personal_info',
            max_attempts=3
        )
        
        # Collect appointment details
        nodes['collect_appointment_details'] = FlowNode(
            id='collect_appointment_details',
            type=FlowNodeType.INFORMATION_COLLECTION,
            name='Collect Appointment Details',
            description='Gather preferred date, time, and department',
            conditions=[
                FlowCondition(
                    type=FlowConditionType.ENTITY_PRESENT,
                    field='date',
                    operator='!=',
                    value=None
                ),
                FlowCondition(
                    type=FlowConditionType.ENTITY_PRESENT,
                    field='department',
                    operator='!=',
                    value=None
                )
            ],
            actions=[
                {
                    'type': 'ask_question',
                    'question': 'कौन से department के लिए और कब appointment चाहिए? (Which department and when would you like the appointment?)',
                    'required_entities': ['date', 'department']
                }
            ],
            next_nodes={
                'details_complete': 'check_availability',
                'details_incomplete': 'collect_appointment_details'
            },
            default_next='collect_appointment_details',
            max_attempts=3
        )
        
        # Check availability
        nodes['check_availability'] = FlowNode(
            id='check_availability',
            type=FlowNodeType.ACTION_EXECUTION,
            name='Check Availability',
            description='Check doctor/slot availability',
            conditions=[],
            actions=[
                {
                    'type': 'check_availability',
                    'date': '${date}',
                    'department': '${department}',
                    'time': '${time}'
                }
            ],
            next_nodes={
                'available': 'confirm_booking',
                'not_available': 'suggest_alternatives',
                'error': 'escalate_booking'
            },
            default_next='suggest_alternatives'
        )
        
        # Confirm booking
        nodes['confirm_booking'] = FlowNode(
            id='confirm_booking',
            type=FlowNodeType.ACTION_EXECUTION,
            name='Confirm Booking',
            description='Finalize the appointment booking',
            conditions=[],
            actions=[
                {
                    'type': 'book_appointment',
                    'patient_name': '${name}',
                    'phone': '${phone}',
                    'date': '${date}',
                    'department': '${department}',
                    'time': '${time}'
                },
                {
                    'type': 'send_confirmation',
                    'method': 'sms',
                    'phone': '${phone}'
                }
            ],
            next_nodes={'default': 'booking_success'},
            default_next='booking_success'
        )
        
        # Booking success
        nodes['booking_success'] = FlowNode(
            id='booking_success',
            type=FlowNodeType.RESPONSE_GENERATION,
            name='Booking Success',
            description='Confirm successful booking',
            conditions=[],
            actions=[
                {
                    'type': 'generate_response',
                    'template': 'आपका appointment successfully book हो गया है ${date} को ${time} बजे ${department} में। Confirmation SMS भेजा गया है।'
                }
            ],
            next_nodes={'default': 'end'},
            default_next='end'
        )
        
        # Suggest alternatives
        nodes['suggest_alternatives'] = FlowNode(
            id='suggest_alternatives',
            type=FlowNodeType.RESPONSE_GENERATION,
            name='Suggest Alternatives',
            description='Offer alternative slots',
            conditions=[],
            actions=[
                {
                    'type': 'get_alternative_slots',
                    'department': '${department}',
                    'preferred_date': '${date}'
                },
                {
                    'type': 'generate_response',
                    'template': 'Sorry, ${date} को slot available नहीं है। क्या आप ${alternative_dates} में से कोई date choose करना चाहेंगे?'
                }
            ],
            next_nodes={
                'alternative_selected': 'check_availability',
                'no_alternative': 'end'
            },
            default_next='end'
        )
        
        # End node
        nodes['end'] = FlowNode(
            id='end',
            type=FlowNodeType.END,
            name='Flow End',
            description='End the appointment booking flow',
            conditions=[],
            actions=[{'type': 'log_completion', 'flow': 'appointment_booking'}],
            next_nodes={},
            default_next=None
        )
        
        return ConversationFlow(
            id='healthcare_appointment',
            name='Healthcare Appointment Booking',
            description='Complete flow for booking medical appointments',
            start_node='start',
            nodes=nodes,
            global_conditions=[],
            variables={},
            created_at=datetime.now(timezone.utc)
        )

    def _create_issue_resolution_flow(self) -> ConversationFlow:
        """Create customer service issue resolution flow"""
        
        nodes = {}
        
        # Start node
        nodes['start'] = FlowNode(
            id='start',
            type=FlowNodeType.START,
            name='Issue Resolution Start',
            description='Begin issue resolution process',
            conditions=[],
            actions=[{'type': 'set_variable', 'name': 'resolution_stage', 'value': 'started'}],
            next_nodes={'default': 'understand_issue'},
            default_next='understand_issue'
        )
        
        # Understand the issue
        nodes['understand_issue'] = FlowNode(
            id='understand_issue',
            type=FlowNodeType.INFORMATION_COLLECTION,
            name='Understand Issue',
            description='Gather details about the customer issue',
            conditions=[
                FlowCondition(
                    type=FlowConditionType.ENTITY_PRESENT,
                    field='issue_description',
                    operator='!=',
                    value=None
                )
            ],
            actions=[
                {
                    'type': 'ask_question',
                    'question': 'Please describe your issue in detail. क्या problem है और कब से है?',
                    'required_entities': ['issue_description', 'issue_start_date']
                }
            ],
            next_nodes={
                'issue_understood': 'categorize_issue',
                'need_clarification': 'understand_issue'
            },
            default_next='understand_issue',
            max_attempts=3
        )
        
        # Categorize issue
        nodes['categorize_issue'] = FlowNode(
            id='categorize_issue',
            type=FlowNodeType.CONDITION_CHECK,
            name='Categorize Issue',
            description='Determine issue category and urgency',
            conditions=[
                FlowCondition(
                    type=FlowConditionType.CUSTOM_FUNCTION,
                    field='issue_description',
                    operator='contains',
                    value='high_priority_keywords',
                    custom_function='check_issue_priority'
                )
            ],
            actions=[
                {
                    'type': 'analyze_issue',
                    'description': '${issue_description}'
                }
            ],
            next_nodes={
                'high_priority': 'escalate_immediately',
                'medium_priority': 'attempt_resolution',
                'low_priority': 'provide_self_service'
            },
            default_next='attempt_resolution'
        )
        
        # Attempt resolution
        nodes['attempt_resolution'] = FlowNode(
            id='attempt_resolution',
            type=FlowNodeType.ACTION_EXECUTION,
            name='Attempt Resolution',
            description='Try to resolve the issue',
            conditions=[],
            actions=[
                {
                    'type': 'search_knowledge_base',
                    'query': '${issue_description}'
                },
                {
                    'type': 'provide_solution',
                    'issue_type': '${issue_category}'
                }
            ],
            next_nodes={
                'resolved': 'confirm_resolution',
                'partial_resolution': 'escalate_to_specialist',
                'unresolved': 'escalate_immediately'
            },
            default_next='escalate_to_specialist'
        )
        
        # Confirm resolution
        nodes['confirm_resolution'] = FlowNode(
            id='confirm_resolution',
            type=FlowNodeType.RESPONSE_GENERATION,
            name='Confirm Resolution',
            description='Check if the issue is resolved',
            conditions=[],
            actions=[
                {
                    'type': 'ask_confirmation',
                    'question': 'क्या आपका issue resolve हो गया है? Are you satisfied with the solution?'
                }
            ],
            next_nodes={
                'satisfied': 'resolution_success',
                'not_satisfied': 'escalate_to_specialist'
            },
            default_next='escalate_to_specialist'
        )
        
        # Resolution success
        nodes['resolution_success'] = FlowNode(
            id='resolution_success',
            type=FlowNodeType.END,
            name='Resolution Success',
            description='Issue successfully resolved',
            conditions=[],
            actions=[
                {
                    'type': 'log_resolution',
                    'status': 'resolved',
                    'satisfaction': 'high'
                },
                {
                    'type': 'generate_response',
                    'template': 'Great! आपका issue resolve हो गया। Thank you for contacting us!'
                }
            ],
            next_nodes={},
            default_next=None
        )
        
        return ConversationFlow(
            id='customer_service_issue',
            name='Customer Service Issue Resolution',
            description='Flow for resolving customer service issues',
            start_node='start',
            nodes=nodes,
            global_conditions=[],
            variables={},
            created_at=datetime.now(timezone.utc)
        )

    def _create_information_request_flow(self) -> ConversationFlow:
        """Create information request handling flow"""
        
        nodes = {}
        
        nodes['start'] = FlowNode(
            id='start',
            type=FlowNodeType.START,
            name='Information Request Start',
            description='Begin information request handling',
            conditions=[],
            actions=[],
            next_nodes={'default': 'identify_information_type'},
            default_next='identify_information_type'
        )
        
        nodes['identify_information_type'] = FlowNode(
            id='identify_information_type',
            type=FlowNodeType.INTENT_RECOGNITION,
            name='Identify Information Type',
            description='Determine what type of information is needed',
            conditions=[],
            actions=[
                {
                    'type': 'analyze_information_request',
                    'query': '${user_input}'
                }
            ],
            next_nodes={
                'hours_timings': 'provide_hours',
                'location_address': 'provide_location',
                'services_offered': 'provide_services',
                'pricing_fees': 'provide_pricing',
                'contact_info': 'provide_contact',
                'general_info': 'search_knowledge_base'
            },
            default_next='search_knowledge_base'
        )
        
        nodes['search_knowledge_base'] = FlowNode(
            id='search_knowledge_base',
            type=FlowNodeType.ACTION_EXECUTION,
            name='Search Knowledge Base',
            description='Search for relevant information',
            conditions=[],
            actions=[
                {
                    'type': 'search_knowledge_base',
                    'query': '${user_input}'
                }
            ],
            next_nodes={
                'information_found': 'provide_information',
                'no_information': 'escalate_to_human'
            },
            default_next='provide_information'
        )
        
        nodes['provide_information'] = FlowNode(
            id='provide_information',
            type=FlowNodeType.RESPONSE_GENERATION,
            name='Provide Information',
            description='Deliver the requested information',
            conditions=[],
            actions=[
                {
                    'type': 'format_information',
                    'data': '${search_results}'
                },
                {
                    'type': 'generate_response',
                    'template': 'आपकी जानकारी: ${formatted_information}. क्या आपको कुछ और चाहिए?'
                }
            ],
            next_nodes={
                'more_questions': 'identify_information_type',
                'satisfied': 'end'
            },
            default_next='end'
        )
        
        nodes['end'] = FlowNode(
            id='end',
            type=FlowNodeType.END,
            name='Information Request End',
            description='Complete information request',
            conditions=[],
            actions=[],
            next_nodes={},
            default_next=None
        )
        
        return ConversationFlow(
            id='information_request',
            name='Information Request Handling',
            description='Flow for handling information requests',
            start_node='start',
            nodes=nodes,
            global_conditions=[],
            variables={},
            created_at=datetime.now(timezone.utc)
        )

    def _create_emergency_flow(self) -> ConversationFlow:
        """Create emergency handling flow"""
        
        nodes = {}
        
        nodes['start'] = FlowNode(
            id='start',
            type=FlowNodeType.START,
            name='Emergency Start',
            description='Begin emergency handling',
            conditions=[],
            actions=[
                {
                    'type': 'set_priority',
                    'level': 'emergency'
                }
            ],
            next_nodes={'default': 'assess_emergency'},
            default_next='assess_emergency'
        )
        
        nodes['assess_emergency'] = FlowNode(
            id='assess_emergency',
            type=FlowNodeType.CONDITION_CHECK,
            name='Assess Emergency',
            description='Determine emergency severity',
            conditions=[
                FlowCondition(
                    type=FlowConditionType.CUSTOM_FUNCTION,
                    field='user_input',
                    operator='contains',
                    value='critical_keywords',
                    custom_function='assess_emergency_severity'
                )
            ],
            actions=[],
            next_nodes={
                'life_threatening': 'immediate_escalation',
                'urgent': 'priority_escalation',
                'non_emergency': 'regular_flow'
            },
            default_next='priority_escalation'
        )
        
        nodes['immediate_escalation'] = FlowNode(
            id='immediate_escalation',
            type=FlowNodeType.ESCALATION,
            name='Immediate Escalation',
            description='Escalate life-threatening emergency',
            conditions=[],
            actions=[
                {
                    'type': 'escalate_immediately',
                    'priority': 'critical',
                    'notify': ['emergency_team', 'supervisor']
                },
                {
                    'type': 'generate_response',
                    'template': 'यह emergency है। मैं तुरंत आपको emergency services से connect कर रहा हूं। Please call 102 immediately!'
                }
            ],
            next_nodes={'default': 'end'},
            default_next='end'
        )
        
        nodes['end'] = FlowNode(
            id='end',
            type=FlowNodeType.END,
            name='Emergency End',
            description='Complete emergency handling',
            conditions=[],
            actions=[],
            next_nodes={},
            default_next=None
        )
        
        return ConversationFlow(
            id='emergency_handling',
            name='Emergency Handling',
            description='Flow for handling emergency situations',
            start_node='start',
            nodes=nodes,
            global_conditions=[],
            variables={},
            created_at=datetime.now(timezone.utc)
        )

    def _initialize_condition_functions(self) -> Dict[str, Callable]:
        """Initialize custom condition functions"""
        
        return {
            'check_issue_priority': self._check_issue_priority,
            'assess_emergency_severity': self._assess_emergency_severity,
            'validate_phone_number': self._validate_phone_number,
            'check_business_hours': self._check_business_hours
        }

    def _initialize_action_handlers(self) -> Dict[str, Callable]:
        """Initialize action handler functions"""
        
        return {
            'ask_question': self._handle_ask_question,
            'set_variable': self._handle_set_variable,
            'check_availability': self._handle_check_availability,
            'book_appointment': self._handle_book_appointment,
            'search_knowledge_base': self._handle_search_knowledge_base,
            'escalate_immediately': self._handle_escalate_immediately,
            'generate_response': self._handle_generate_response,
            'log_completion': self._handle_log_completion
        }

    async def start_flow(self, session_id: str, flow_id: str, conversation_context: ConversationContext) -> FlowExecutionContext:
        """Start a new conversation flow"""
        
        if flow_id not in self.predefined_flows:
            raise ValueError(f"Flow {flow_id} not found")
        
        flow = self.predefined_flows[flow_id]
        
        # Create execution context
        execution_context = FlowExecutionContext(
            session_id=session_id,
            flow_id=flow_id,
            current_node_id=flow.start_node,
            conversation_context=conversation_context,
            flow_variables=flow.variables.copy(),
            node_history=[],
            attempt_counts={},
            start_time=datetime.now(timezone.utc),
            last_update=datetime.now(timezone.utc)
        )
        
        # Store active flow
        self.active_flows[session_id] = execution_context
        
        # Execute the start node
        await self._execute_node(execution_context, flow.start_node)
        
        return execution_context

    async def process_user_input(self, session_id: str, user_input: str, conversation_context: ConversationContext) -> Dict[str, Any]:
        """Process user input within the current flow"""
        
        if session_id not in self.active_flows:
            # Auto-select flow based on intent
            flow_id = await self._select_flow_for_intent(conversation_context.detected_intent)
            await self.start_flow(session_id, flow_id, conversation_context)
        
        execution_context = self.active_flows[session_id]
        execution_context.conversation_context = conversation_context
        execution_context.last_update = datetime.now(timezone.utc)
        
        # Add user input to flow variables
        execution_context.flow_variables['user_input'] = user_input
        execution_context.flow_variables['last_user_message'] = user_input
        
        # Process current node
        result = await self._process_current_node(execution_context)
        
        return result

    async def _select_flow_for_intent(self, intent: Optional[IntentType]) -> str:
        """Select appropriate flow based on detected intent"""
        
        if intent == IntentType.APPOINTMENT_BOOKING:
            return 'healthcare_appointment'
        elif intent == IntentType.EMERGENCY:
            return 'emergency_handling'
        elif intent == IntentType.COMPLAINT:
            return 'customer_service_issue'
        elif intent == IntentType.INFORMATION_REQUEST:
            return 'information_request'
        else:
            return 'information_request'  # Default flow

    async def _execute_node(self, execution_context: FlowExecutionContext, node_id: str) -> Dict[str, Any]:
        """Execute a specific node in the flow"""
        
        flow = self.predefined_flows[execution_context.flow_id]
        node = flow.nodes[node_id]
        
        # Add to history
        execution_context.node_history.append({
            'node_id': node_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'variables_snapshot': execution_context.flow_variables.copy()
        })
        
        # Execute node actions
        action_results = []
        for action in node.actions:
            result = await self._execute_action(action, execution_context)
            action_results.append(result)
        
        # Determine next node
        next_node = await self._determine_next_node(node, execution_context)
        
        if next_node:
            execution_context.current_node_id = next_node
        
        return {
            'node_id': node_id,
            'node_type': node.type.value,
            'action_results': action_results,
            'next_node': next_node,
            'flow_complete': node.type == FlowNodeType.END
        }

    async def _process_current_node(self, execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Process the current node based on user input and conditions"""
        
        current_node_id = execution_context.current_node_id
        flow = self.predefined_flows[execution_context.flow_id]
        node = flow.nodes[current_node_id]
        
        # Check node conditions
        conditions_met = await self._check_node_conditions(node, execution_context)
        
        # Update attempt count
        attempt_key = f"{current_node_id}_attempts"
        execution_context.attempt_counts[attempt_key] = execution_context.attempt_counts.get(attempt_key, 0) + 1
        
        # Check if max attempts exceeded
        if execution_context.attempt_counts[attempt_key] > node.max_attempts:
            # Handle max attempts exceeded
            return await self._handle_max_attempts_exceeded(execution_context, node)
        
        # Execute node based on conditions
        if conditions_met:
            # Move to next node
            next_node = await self._determine_next_node(node, execution_context)
            if next_node:
                return await self._execute_node(execution_context, next_node)
        
        # Stay on current node, execute again
        return await self._execute_node(execution_context, current_node_id)

    async def _check_node_conditions(self, node: FlowNode, execution_context: FlowExecutionContext) -> bool:
        """Check if node conditions are satisfied"""
        
        if not node.conditions:
            return True
        
        for condition in node.conditions:
            if not await self._evaluate_condition(condition, execution_context):
                return False
        
        return True

    async def _evaluate_condition(self, condition: FlowCondition, execution_context: FlowExecutionContext) -> bool:
        """Evaluate a single condition"""
        
        try:
            if condition.type == FlowConditionType.ENTITY_PRESENT:
                entities = execution_context.conversation_context.extracted_entities
                return condition.field in entities and entities[condition.field] is not None
            
            elif condition.type == FlowConditionType.ENTITY_VALUE:
                entities = execution_context.conversation_context.extracted_entities
                if condition.field not in entities:
                    return False
                
                value = entities[condition.field]
                return self._compare_values(value, condition.operator, condition.value)
            
            elif condition.type == FlowConditionType.SENTIMENT_SCORE:
                sentiment_score = execution_context.conversation_context.sentiment_score
                return self._compare_values(sentiment_score, condition.operator, condition.value)
            
            elif condition.type == FlowConditionType.CUSTOM_FUNCTION:
                if condition.custom_function in self.condition_functions:
                    func = self.condition_functions[condition.custom_function]
                    return await func(condition, execution_context)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition: {e}")
            return False

    def _compare_values(self, value1: Any, operator: str, value2: Any) -> bool:
        """Compare two values using the specified operator"""
        
        try:
            if operator == '==':
                return value1 == value2
            elif operator == '!=':
                return value1 != value2
            elif operator == '>':
                return value1 > value2
            elif operator == '<':
                return value1 < value2
            elif operator == '>=':
                return value1 >= value2
            elif operator == '<=':
                return value1 <= value2
            elif operator == 'contains':
                return value2 in str(value1).lower()
            elif operator == 'in':
                return value1 in value2
            
            return False
            
        except Exception:
            return False

    async def _determine_next_node(self, node: FlowNode, execution_context: FlowExecutionContext) -> Optional[str]:
        """Determine the next node based on conditions and results"""
        
        # Check condition-based next nodes
        for condition_name, next_node_id in node.next_nodes.items():
            if condition_name == 'default':
                continue
            
            # This is a simplified version - in practice, you'd have more sophisticated condition checking
            if condition_name in execution_context.flow_variables.get('last_result', {}):
                return next_node_id
        
        # Return default next node
        return node.default_next

    async def _execute_action(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Execute a single action"""
        
        action_type = action['type']
        
        if action_type in self.action_handlers:
            handler = self.action_handlers[action_type]
            return await handler(action, execution_context)
        else:
            self.logger.warning(f"Unknown action type: {action_type}")
            return {'status': 'unknown_action', 'action_type': action_type}

    async def _handle_max_attempts_exceeded(self, execution_context: FlowExecutionContext, node: FlowNode) -> Dict[str, Any]:
        """Handle when maximum attempts for a node are exceeded"""
        
        # Escalate or move to fallback
        execution_context.flow_variables['escalation_reason'] = 'max_attempts_exceeded'
        execution_context.flow_variables['failed_node'] = node.id
        
        # Find escalation node or end flow
        escalation_node = self._find_escalation_node(execution_context.flow_id)
        if escalation_node:
            return await self._execute_node(execution_context, escalation_node)
        else:
            # End flow with failure
            return {
                'flow_complete': True,
                'status': 'failed',
                'reason': 'max_attempts_exceeded'
            }

    def _find_escalation_node(self, flow_id: str) -> Optional[str]:
        """Find an escalation node in the flow"""
        
        flow = self.predefined_flows[flow_id]
        for node_id, node in flow.nodes.items():
            if node.type == FlowNodeType.ESCALATION:
                return node_id
        return None

    # Action Handlers
    async def _handle_ask_question(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle ask question action"""
        
        question = action.get('question', '')
        required_entities = action.get('required_entities', [])
        
        # Store question context
        execution_context.flow_variables['current_question'] = question
        execution_context.flow_variables['required_entities'] = required_entities
        
        return {
            'status': 'question_asked',
            'question': question,
            'required_entities': required_entities
        }

    async def _handle_set_variable(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle set variable action"""
        
        var_name = action.get('name')
        var_value = action.get('value')
        
        if var_name:
            execution_context.flow_variables[var_name] = var_value
        
        return {
            'status': 'variable_set',
            'variable': var_name,
            'value': var_value
        }

    async def _handle_check_availability(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle check availability action"""
        
        # This would integrate with actual appointment system
        # For now, return mock availability
        
        date = action.get('date')
        department = action.get('department')
        
        # Mock availability check
        available = True  # In practice, this would check real availability
        
        execution_context.flow_variables['availability_checked'] = True
        execution_context.flow_variables['slot_available'] = available
        
        return {
            'status': 'availability_checked',
            'available': available,
            'date': date,
            'department': department
        }

    async def _handle_book_appointment(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle book appointment action"""
        
        # This would integrate with actual booking system
        
        booking_data = {
            'patient_name': action.get('patient_name'),
            'phone': action.get('phone'),
            'date': action.get('date'),
            'department': action.get('department'),
            'time': action.get('time')
        }
        
        # Mock booking
        booking_id = f"BOOK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution_context.flow_variables['booking_id'] = booking_id
        execution_context.flow_variables['booking_data'] = booking_data
        
        return {
            'status': 'appointment_booked',
            'booking_id': booking_id,
            'booking_data': booking_data
        }

    async def _handle_search_knowledge_base(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle search knowledge base action"""
        
        query = action.get('query', '')
        
        # This would integrate with the knowledge base search
        # For now, return mock results
        
        search_results = [
            {
                'title': 'Hospital Information',
                'content': 'Mock search result for: ' + query,
                'relevance': 0.8
            }
        ]
        
        execution_context.flow_variables['search_results'] = search_results
        
        return {
            'status': 'knowledge_searched',
            'query': query,
            'results': search_results
        }

    async def _handle_escalate_immediately(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle immediate escalation action"""
        
        priority = action.get('priority', 'high')
        notify = action.get('notify', [])
        
        # This would trigger actual escalation
        
        execution_context.flow_variables['escalated'] = True
        execution_context.flow_variables['escalation_priority'] = priority
        
        return {
            'status': 'escalated',
            'priority': priority,
            'notify': notify
        }

    async def _handle_generate_response(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle generate response action"""
        
        template = action.get('template', '')
        
        # Replace variables in template
        response = self._replace_template_variables(template, execution_context.flow_variables)
        
        execution_context.flow_variables['last_response'] = response
        
        return {
            'status': 'response_generated',
            'response': response
        }

    async def _handle_log_completion(self, action: Dict[str, Any], execution_context: FlowExecutionContext) -> Dict[str, Any]:
        """Handle log completion action"""
        
        flow_name = action.get('flow')
        
        self.logger.info(f"Flow completed: {flow_name} for session {execution_context.session_id}")
        
        return {
            'status': 'logged',
            'flow': flow_name
        }

    def _replace_template_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace variables in template string"""
        
        result = template
        for var_name, var_value in variables.items():
            placeholder = f"${{{var_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        
        return result

    # Condition Functions
    async def _check_issue_priority(self, condition: FlowCondition, execution_context: FlowExecutionContext) -> bool:
        """Check issue priority based on keywords"""
        
        issue_description = execution_context.flow_variables.get('issue_description', '').lower()
        
        high_priority_keywords = ['urgent', 'emergency', 'critical', 'broken', 'down', 'not working']
        
        for keyword in high_priority_keywords:
            if keyword in issue_description:
                return True
        
        return False

    async def _assess_emergency_severity(self, condition: FlowCondition, execution_context: FlowExecutionContext) -> bool:
        """Assess emergency severity"""
        
        user_input = execution_context.flow_variables.get('user_input', '').lower()
        
        critical_keywords = ['chest pain', 'can\'t breathe', 'unconscious', 'bleeding', 'accident']
        
        for keyword in critical_keywords:
            if keyword in user_input:
                return True
        
        return False

    async def _validate_phone_number(self, condition: FlowCondition, execution_context: FlowExecutionContext) -> bool:
        """Validate phone number format"""
        
        phone = execution_context.conversation_context.extracted_entities.get('phone', '')
        
        # Simple phone validation (Indian format)
        import re
        pattern = r'^(\+91)?[6-9]\d{9}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

    async def _check_business_hours(self, condition: FlowCondition, execution_context: FlowExecutionContext) -> bool:
        """Check if current time is within business hours"""
        
        current_hour = datetime.now().hour
        return 9 <= current_hour <= 18  # 9 AM to 6 PM

    def get_flow_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current flow status for a session"""
        
        if session_id not in self.active_flows:
            return None
        
        execution_context = self.active_flows[session_id]
        flow = self.predefined_flows[execution_context.flow_id]
        current_node = flow.nodes[execution_context.current_node_id]
        
        return {
            'session_id': session_id,
            'flow_id': execution_context.flow_id,
            'flow_name': flow.name,
            'current_node': execution_context.current_node_id,
            'current_node_name': current_node.name,
            'current_node_type': current_node.type.value,
            'variables': execution_context.flow_variables,
            'start_time': execution_context.start_time.isoformat(),
            'last_update': execution_context.last_update.isoformat(),
            'node_history': execution_context.node_history
        }

    def end_flow(self, session_id: str) -> Optional[Dict[str, Any]]:
        """End the current flow for a session"""
        
        if session_id not in self.active_flows:
            return None
        
        execution_context = self.active_flows[session_id]
        
        # Create summary
        summary = {
            'session_id': session_id,
            'flow_id': execution_context.flow_id,
            'duration_seconds': (datetime.now(timezone.utc) - execution_context.start_time).total_seconds(),
            'nodes_visited': len(execution_context.node_history),
            'final_variables': execution_context.flow_variables,
            'completion_status': 'ended'
        }
        
        # Clean up
        del self.active_flows[session_id]
        
        return summary

# Example usage
if __name__ == "__main__":
    async def test_flow_manager():
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
        
        # Test flow manager
        flow_manager = ConversationFlowManager(agent_config)
        
        # Create mock conversation context
        from intelligent_conversation_engine import ConversationContext, IntentType
        
        conv_context = ConversationContext(
            session_id="test-session-123",
            detected_intent=IntentType.APPOINTMENT_BOOKING
        )
        
        # Start appointment booking flow
        execution_context = await flow_manager.start_flow(
            "test-session-123", 
            "healthcare_appointment", 
            conv_context
        )
        
        print(f"Started flow: {execution_context.flow_id}")
        print(f"Current node: {execution_context.current_node_id}")
        
        # Simulate user inputs
        test_inputs = [
            "Hello, मुझे appointment book करना है",
            "My name is राजेश और phone number 9876543210",
            "Tomorrow cardiology department में appointment चाहिए"
        ]
        
        for user_input in test_inputs:
            # Update context with entities (mock)
            conv_context.extracted_entities = {
                'name': 'राजेश',
                'phone': '9876543210',
                'date': 'tomorrow',
                'department': 'cardiology'
            }
            
            result = await flow_manager.process_user_input("test-session-123", user_input, conv_context)
            print(f"\nUser: {user_input}")
            print(f"Flow result: {result}")
        
        # Get flow status
        status = flow_manager.get_flow_status("test-session-123")
        print(f"\nFlow status: {json.dumps(status, indent=2, default=str)}")

    asyncio.run(test_flow_manager())