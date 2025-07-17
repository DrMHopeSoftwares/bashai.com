"""
Advanced Agent Configuration System for BhashAI
Provides comprehensive agent setup with knowledge base, custom prompts, and intelligence features
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
from dotenv import load_dotenv
import requests
import hashlib
import PyPDF2
import docx
from pathlib import Path

load_dotenv()

class AgentType(Enum):
    CUSTOMER_SERVICE = "customer_service"
    HEALTHCARE_ASSISTANT = "healthcare_assistant"
    SALES_REPRESENTATIVE = "sales_representative"
    APPOINTMENT_SCHEDULER = "appointment_scheduler"
    TECHNICAL_SUPPORT = "technical_support"
    EDUCATIONAL_TUTOR = "educational_tutor"
    CUSTOM = "custom"

class KnowledgeSourceType(Enum):
    PDF_DOCUMENT = "pdf_document"
    TEXT_FILE = "text_file"
    WEB_URL = "web_url"
    FAQ_DATABASE = "faq_database"
    API_ENDPOINT = "api_endpoint"
    CUSTOM_PROMPTS = "custom_prompts"

class ResponseStyle(Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EMPATHETIC = "empathetic"
    AUTHORITATIVE = "authoritative"
    CASUAL = "casual"
    TECHNICAL = "technical"

@dataclass
class KnowledgeSource:
    """Represents a knowledge source for the agent"""
    id: str
    name: str
    type: KnowledgeSourceType
    source_data: Dict[str, Any]
    processed_content: Optional[str] = None
    metadata: Dict[str, Any] = None
    last_updated: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)

@dataclass
class ConversationTemplate:
    """Predefined conversation flows and responses"""
    id: str
    name: str
    trigger_patterns: List[str]
    response_template: str
    follow_up_questions: List[str]
    required_entities: List[str]
    success_criteria: Dict[str, Any]
    language: str = "hinglish"

@dataclass
class AgentPersonality:
    """Comprehensive personality configuration"""
    response_style: ResponseStyle
    empathy_level: float  # 0.0 to 1.0
    formality_level: float  # 0.0 to 1.0
    humor_level: float  # 0.0 to 1.0
    patience_level: float  # 0.0 to 1.0
    detail_level: float  # 0.0 to 1.0
    custom_traits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_traits is None:
            self.custom_traits = {}

@dataclass
class AdvancedAgentConfig:
    """Comprehensive agent configuration"""
    agent_id: str
    name: str
    description: str
    agent_type: AgentType
    personality: AgentPersonality
    knowledge_sources: List[KnowledgeSource]
    conversation_templates: List[ConversationTemplate]
    system_prompts: Dict[str, str]
    languages: List[str]
    capabilities: List[str]
    limitations: List[str]
    escalation_rules: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

class AdvancedAgentConfigManager:
    """Manages advanced agent configurations with knowledge base support"""
    
    def __init__(self, supabase_config: Dict[str, str]):
        self.supabase_config = supabase_config
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize storage paths
        self.base_path = Path("/Users/murali/bhashai.com 15th Jul/bashai.com")
        self.knowledge_base_path = self.base_path / "knowledge_base"
        self.agent_configs_path = self.base_path / "agent_configs"
        
        # Create directories if they don't exist
        self.knowledge_base_path.mkdir(exist_ok=True)
        self.agent_configs_path.mkdir(exist_ok=True)
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Predefined templates for different agent types
        self.agent_templates = self._initialize_agent_templates()

    def _initialize_agent_templates(self) -> Dict[AgentType, Dict]:
        """Initialize predefined agent templates"""
        return {
            AgentType.HEALTHCARE_ASSISTANT: {
                'system_prompts': {
                    'primary': """You are a professional healthcare assistant AI. You help patients with:
                    - Appointment scheduling and management
                    - General health information (non-diagnostic)
                    - Medication reminders and basic information
                    - Directing patients to appropriate healthcare services
                    
                    Important: You must never provide medical diagnosis or emergency medical advice. 
                    Always direct serious medical concerns to healthcare professionals.""",
                    
                    'greeting': """नमस्ते! मैं आपका healthcare assistant हूं। मैं appointment booking, general health information, और medication reminders में आपकी सहायता कर सकता हूं। आपकी कैसे मदद कर सकता हूं?""",
                    
                    'emergency': """This sounds like a medical emergency. मैं तुरंत आपको doctor से मिलवाता हूं। Please call 102 for emergency services या nearest hospital जाएं।"""
                },
                'capabilities': [
                    'appointment_booking',
                    'health_information',
                    'medication_reminders',
                    'symptom_logging',
                    'doctor_availability'
                ],
                'limitations': [
                    'no_medical_diagnosis',
                    'no_prescription_changes',
                    'no_emergency_treatment'
                ],
                'conversation_templates': [
                    {
                        'name': 'appointment_booking',
                        'trigger_patterns': ['appointment', 'book', 'schedule', 'अपॉइंटमेंट'],
                        'response_template': 'मैं आपका appointment book कर सकता हूं। आपका name, phone number, और preferred date/time बताएं।',
                        'required_entities': ['name', 'phone', 'date', 'time'],
                        'follow_up_questions': [
                            'कौन से department के लिए appointment चाहिए?',
                            'कोई specific doctor का preference है?',
                            'यह first visit है या follow-up?'
                        ]
                    }
                ]
            },
            
            AgentType.CUSTOMER_SERVICE: {
                'system_prompts': {
                    'primary': """You are a professional customer service representative. You help customers with:
                    - Product inquiries and information
                    - Order status and tracking
                    - Returns and refunds
                    - Technical support
                    - Billing inquiries
                    
                    Always maintain a helpful, patient, and solution-oriented approach.""",
                    
                    'greeting': """Hello! मैं आपका customer service assistant हूं। Product information, orders, returns, या कोई भी help के लिए मैं यहां हूं। How can I assist you today?""",
                    
                    'escalation': """I understand your concern. Let me connect you with a senior representative who can better assist you with this matter."""
                },
                'capabilities': [
                    'product_information',
                    'order_tracking',
                    'return_processing',
                    'billing_support',
                    'technical_guidance'
                ],
                'limitations': [
                    'no_refund_authorization',
                    'no_account_security_changes',
                    'no_legal_advice'
                ]
            },
            
            AgentType.SALES_REPRESENTATIVE: {
                'system_prompts': {
                    'primary': """You are an enthusiastic and knowledgeable sales representative. Your role is to:
                    - Understand customer needs and preferences
                    - Present relevant products and services
                    - Handle objections professionally
                    - Guide customers through the purchase process
                    - Build long-term customer relationships
                    
                    Always be honest, helpful, and customer-focused.""",
                    
                    'greeting': """नमस्ते! I'm your sales consultant. आज मैं आपकी कैसे help कर सकता हूं? Looking for something specific या should I show you our latest offers?""",
                    
                    'closing': """Thank you for your interest! Shall we proceed with this, या आपके कोई और questions हैं? I'm here to make sure you get exactly what you need."""
                },
                'capabilities': [
                    'product_recommendation',
                    'price_quotation',
                    'demo_scheduling',
                    'objection_handling',
                    'order_processing'
                ],
                'limitations': [
                    'no_unauthorized_discounts',
                    'no_false_promises',
                    'no_pressure_tactics'
                ]
            }
        }

    async def create_agent_config(self, 
                                config_data: Dict[str, Any],
                                knowledge_files: Optional[List[Dict]] = None) -> AdvancedAgentConfig:
        """Create a new advanced agent configuration"""
        
        agent_id = str(uuid.uuid4())
        
        # Process personality configuration
        personality = AgentPersonality(
            response_style=ResponseStyle(config_data.get('response_style', 'professional')),
            empathy_level=config_data.get('empathy_level', 0.7),
            formality_level=config_data.get('formality_level', 0.6),
            humor_level=config_data.get('humor_level', 0.3),
            patience_level=config_data.get('patience_level', 0.8),
            detail_level=config_data.get('detail_level', 0.7),
            custom_traits=config_data.get('custom_traits', {})
        )
        
        # Process knowledge sources
        knowledge_sources = []
        if knowledge_files:
            for file_info in knowledge_files:
                knowledge_source = await self._process_knowledge_source(agent_id, file_info)
                if knowledge_source:
                    knowledge_sources.append(knowledge_source)
        
        # Get template data for agent type
        agent_type = AgentType(config_data.get('agent_type', 'custom'))
        template_data = self.agent_templates.get(agent_type, {})
        
        # Process conversation templates
        conversation_templates = []
        for template_data_item in template_data.get('conversation_templates', []):
            template = ConversationTemplate(
                id=str(uuid.uuid4()),
                name=template_data_item['name'],
                trigger_patterns=template_data_item['trigger_patterns'],
                response_template=template_data_item['response_template'],
                follow_up_questions=template_data_item.get('follow_up_questions', []),
                required_entities=template_data_item.get('required_entities', []),
                success_criteria=template_data_item.get('success_criteria', {}),
                language=config_data.get('language', 'hinglish')
            )
            conversation_templates.append(template)
        
        # Create the agent configuration
        agent_config = AdvancedAgentConfig(
            agent_id=agent_id,
            name=config_data['name'],
            description=config_data.get('description', ''),
            agent_type=agent_type,
            personality=personality,
            knowledge_sources=knowledge_sources,
            conversation_templates=conversation_templates,
            system_prompts=template_data.get('system_prompts', {}),
            languages=config_data.get('languages', ['hindi', 'english', 'hinglish']),
            capabilities=template_data.get('capabilities', []),
            limitations=template_data.get('limitations', []),
            escalation_rules=config_data.get('escalation_rules', {}),
            performance_metrics={}
        )
        
        # Save configuration
        await self._save_agent_config(agent_config)
        
        return agent_config

    async def _process_knowledge_source(self, agent_id: str, file_info: Dict) -> Optional[KnowledgeSource]:
        """Process and store a knowledge source"""
        
        source_id = str(uuid.uuid4())
        source_type = KnowledgeSourceType(file_info['type'])
        
        try:
            if source_type == KnowledgeSourceType.PDF_DOCUMENT:
                content = await self._process_pdf(file_info['file_path'])
            elif source_type == KnowledgeSourceType.TEXT_FILE:
                content = await self._process_text_file(file_info['file_path'])
            elif source_type == KnowledgeSourceType.WEB_URL:
                content = await self._process_web_url(file_info['url'])
            elif source_type == KnowledgeSourceType.FAQ_DATABASE:
                content = await self._process_faq_data(file_info['faq_data'])
            elif source_type == KnowledgeSourceType.CUSTOM_PROMPTS:
                content = file_info['content']
            else:
                self.logger.warning(f"Unsupported knowledge source type: {source_type}")
                return None
            
            # Create knowledge embeddings for better search
            embeddings = await self._create_knowledge_embeddings(content)
            
            knowledge_source = KnowledgeSource(
                id=source_id,
                name=file_info['name'],
                type=source_type,
                source_data=file_info,
                processed_content=content,
                metadata={
                    'embeddings': embeddings,
                    'content_length': len(content),
                    'processing_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Save knowledge source
            await self._save_knowledge_source(agent_id, knowledge_source)
            
            return knowledge_source
            
        except Exception as e:
            self.logger.error(f"Error processing knowledge source: {e}")
            return None

    async def _process_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
                
                return text_content.strip()
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return ""

    async def _process_text_file(self, file_path: str) -> str:
        """Read text content from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            self.logger.error(f"Error reading text file: {e}")
            return ""

    async def _process_web_url(self, url: str) -> str:
        """Extract content from web URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Basic HTML content extraction (you might want to use BeautifulSoup for better extraction)
            content = response.text
            
            # Use OpenAI to extract meaningful content
            extracted_content = await self._extract_web_content(content)
            return extracted_content
            
        except Exception as e:
            self.logger.error(f"Error processing web URL: {e}")
            return ""

    async def _process_faq_data(self, faq_data: List[Dict]) -> str:
        """Process FAQ data into searchable content"""
        faq_content = "Frequently Asked Questions:\n\n"
        
        for faq in faq_data:
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            faq_content += f"Q: {question}\nA: {answer}\n\n"
        
        return faq_content

    async def _extract_web_content(self, html_content: str) -> str:
        """Use OpenAI to extract meaningful content from HTML"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user",
                    "content": f"Extract the main textual content from this HTML, removing navigation, headers, footers, and formatting. Focus on the core information:\n\n{html_content[:4000]}"
                }],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error extracting web content: {e}")
            return html_content[:2000]  # Fallback to truncated HTML

    async def _create_knowledge_embeddings(self, content: str) -> List[float]:
        """Create embeddings for knowledge content for better search"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model="text-embedding-ada-002",
                input=content[:8000]  # Limit content length for embeddings
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            self.logger.error(f"Error creating embeddings: {e}")
            return []

    async def _save_agent_config(self, agent_config: AdvancedAgentConfig):
        """Save agent configuration to file and database"""
        
        # Save to local file
        config_file = self.agent_configs_path / f"{agent_config.agent_id}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            # Convert to serializable format
            config_dict = asdict(agent_config)
            config_dict['created_at'] = agent_config.created_at.isoformat()
            config_dict['updated_at'] = agent_config.updated_at.isoformat()
            
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        # Save to database (Supabase)
        try:
            config_data = {
                'id': agent_config.agent_id,
                'name': agent_config.name,
                'description': agent_config.description,
                'agent_type': agent_config.agent_type.value,
                'configuration': config_dict,
                'is_active': agent_config.is_active,
                'created_at': agent_config.created_at.isoformat(),
                'updated_at': agent_config.updated_at.isoformat()
            }
            
            # This would integrate with the existing Supabase system
            # For now, we'll store locally
            self.logger.info(f"Agent configuration saved: {agent_config.agent_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")

    async def _save_knowledge_source(self, agent_id: str, knowledge_source: KnowledgeSource):
        """Save knowledge source to file system"""
        
        agent_kb_path = self.knowledge_base_path / agent_id
        agent_kb_path.mkdir(exist_ok=True)
        
        # Save content
        content_file = agent_kb_path / f"{knowledge_source.id}.txt"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(knowledge_source.processed_content or "")
        
        # Save metadata
        metadata_file = agent_kb_path / f"{knowledge_source.id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            metadata = asdict(knowledge_source)
            metadata['last_updated'] = knowledge_source.last_updated.isoformat()
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    async def load_agent_config(self, agent_id: str) -> Optional[AdvancedAgentConfig]:
        """Load agent configuration from storage"""
        
        config_file = self.agent_configs_path / f"{agent_id}.json"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Convert back to proper objects
            config_dict['agent_type'] = AgentType(config_dict['agent_type'])
            
            # Convert personality
            personality_data = config_dict['personality']
            personality_data['response_style'] = ResponseStyle(personality_data['response_style'])
            config_dict['personality'] = AgentPersonality(**personality_data)
            
            # Convert knowledge sources
            knowledge_sources = []
            for ks_data in config_dict['knowledge_sources']:
                ks_data['type'] = KnowledgeSourceType(ks_data['type'])
                ks_data['last_updated'] = datetime.fromisoformat(ks_data['last_updated'])
                knowledge_sources.append(KnowledgeSource(**ks_data))
            config_dict['knowledge_sources'] = knowledge_sources
            
            # Convert conversation templates
            templates = []
            for template_data in config_dict['conversation_templates']:
                templates.append(ConversationTemplate(**template_data))
            config_dict['conversation_templates'] = templates
            
            # Convert datetime fields
            config_dict['created_at'] = datetime.fromisoformat(config_dict['created_at'])
            config_dict['updated_at'] = datetime.fromisoformat(config_dict['updated_at'])
            
            return AdvancedAgentConfig(**config_dict)
            
        except Exception as e:
            self.logger.error(f"Error loading agent config: {e}")
            return None

    async def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing agent configuration"""
        
        agent_config = await self.load_agent_config(agent_id)
        if not agent_config:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(agent_config, key):
                setattr(agent_config, key, value)
        
        agent_config.updated_at = datetime.now(timezone.utc)
        
        # Save updated configuration
        await self._save_agent_config(agent_config)
        return True

    async def search_knowledge_base(self, agent_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search through agent's knowledge base"""
        
        agent_kb_path = self.knowledge_base_path / agent_id
        
        if not agent_kb_path.exists():
            return []
        
        results = []
        
        # Get all knowledge sources for this agent
        for metadata_file in agent_kb_path.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Load content
                content_file = agent_kb_path / f"{metadata['id']}.txt"
                if content_file.exists():
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple text search (you could implement vector search here)
                    if query.lower() in content.lower():
                        # Extract relevant excerpts
                        excerpts = self._extract_relevant_excerpts(content, query)
                        results.append({
                            'source_id': metadata['id'],
                            'source_name': metadata['name'],
                            'excerpts': excerpts,
                            'relevance_score': self._calculate_relevance_score(content, query)
                        })
            
            except Exception as e:
                self.logger.error(f"Error searching knowledge source: {e}")
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:max_results]

    def _extract_relevant_excerpts(self, content: str, query: str, excerpt_length: int = 200) -> List[str]:
        """Extract relevant excerpts from content based on query"""
        
        excerpts = []
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Find all occurrences of query terms
        start_positions = []
        for i in range(len(content_lower) - len(query_lower) + 1):
            if content_lower[i:i+len(query_lower)] == query_lower:
                start_positions.append(i)
        
        # Extract excerpts around each occurrence
        for pos in start_positions[:3]:  # Limit to 3 excerpts
            start = max(0, pos - excerpt_length // 2)
            end = min(len(content), pos + excerpt_length // 2)
            excerpt = content[start:end].strip()
            
            # Add ellipsis if needed
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(content):
                excerpt = excerpt + "..."
            
            excerpts.append(excerpt)
        
        return excerpts

    def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Calculate relevance score for content based on query"""
        
        content_lower = content.lower()
        query_terms = query.lower().split()
        
        score = 0.0
        total_terms = len(query_terms)
        
        for term in query_terms:
            # Count occurrences of each term
            occurrences = content_lower.count(term)
            # Normalize by content length
            term_score = occurrences / max(1, len(content) / 1000)
            score += term_score
        
        return score / max(1, total_terms)

    async def get_agent_intelligence_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get intelligence and capability summary for an agent"""
        
        agent_config = await self.load_agent_config(agent_id)
        if not agent_config:
            return {}
        
        knowledge_base_size = 0
        knowledge_sources_count = len(agent_config.knowledge_sources)
        
        # Calculate knowledge base size
        agent_kb_path = self.knowledge_base_path / agent_id
        if agent_kb_path.exists():
            for content_file in agent_kb_path.glob("*.txt"):
                try:
                    knowledge_base_size += content_file.stat().st_size
                except:
                    pass
        
        return {
            'agent_id': agent_id,
            'agent_name': agent_config.name,
            'agent_type': agent_config.agent_type.value,
            'intelligence_features': {
                'knowledge_sources': knowledge_sources_count,
                'knowledge_base_size_kb': round(knowledge_base_size / 1024, 2),
                'conversation_templates': len(agent_config.conversation_templates),
                'supported_languages': len(agent_config.languages),
                'capabilities': len(agent_config.capabilities),
                'personality_traits': {
                    'empathy_level': agent_config.personality.empathy_level,
                    'formality_level': agent_config.personality.formality_level,
                    'humor_level': agent_config.personality.humor_level,
                    'patience_level': agent_config.personality.patience_level,
                    'detail_level': agent_config.personality.detail_level
                }
            },
            'last_updated': agent_config.updated_at.isoformat(),
            'is_active': agent_config.is_active
        }

# Example usage and testing
if __name__ == "__main__":
    async def test_agent_config():
        # Initialize config manager
        supabase_config = {
            'url': os.getenv('SUPABASE_URL', ''),
            'key': os.getenv('SUPABASE_SERVICE_KEY', '')
        }
        
        manager = AdvancedAgentConfigManager(supabase_config)
        
        # Test agent configuration
        config_data = {
            'name': 'Dr. Smart Assistant',
            'description': 'Intelligent healthcare assistant with comprehensive knowledge',
            'agent_type': 'healthcare_assistant',
            'response_style': 'empathetic',
            'empathy_level': 0.9,
            'formality_level': 0.7,
            'humor_level': 0.3,
            'patience_level': 0.9,
            'detail_level': 0.8,
            'languages': ['hindi', 'english', 'hinglish'],
            'escalation_rules': {
                'emergency_keywords': ['emergency', 'urgent', 'serious', 'help'],
                'escalation_threshold': 0.8
            }
        }
        
        # Test knowledge sources
        knowledge_files = [
            {
                'name': 'Hospital Policies',
                'type': 'custom_prompts',
                'content': 'Hospital visiting hours: 9 AM to 6 PM. Emergency services available 24/7.'
            },
            {
                'name': 'Common FAQs',
                'type': 'faq_database',
                'faq_data': [
                    {
                        'question': 'What are the visiting hours?',
                        'answer': 'Visiting hours are from 9 AM to 6 PM daily.'
                    },
                    {
                        'question': 'How to book an appointment?',
                        'answer': 'You can book appointments by calling us or using our online portal.'
                    }
                ]
            }
        ]
        
        # Create agent configuration
        agent_config = await manager.create_agent_config(config_data, knowledge_files)
        print(f"Created agent: {agent_config.agent_id}")
        
        # Test knowledge base search
        search_results = await manager.search_knowledge_base(
            agent_config.agent_id, 
            "visiting hours"
        )
        print(f"Search results: {search_results}")
        
        # Get intelligence summary
        summary = await manager.get_agent_intelligence_summary(agent_config.agent_id)
        print(f"Intelligence summary: {json.dumps(summary, indent=2)}")

    # Run test if API key is available
    if os.getenv('OPENAI_API_KEY'):
        asyncio.run(test_agent_config())
    else:
        print("OpenAI API key not found. Skipping test.")