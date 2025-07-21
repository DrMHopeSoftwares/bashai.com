#!/usr/bin/env python3
"""
Sales Agent Configuration for Bolna AI
Complete configuration for creating a Hindi/English sales voice agent
"""

import os
import json
from bolna_integration import BolnaAPI
from dotenv import load_dotenv

load_dotenv()

# Sales Agent Configuration
SALES_AGENT_CONFIG = {
    "agent_name": "Sales Expert - राज",
    "agent_welcome_message": "नमस्ते! मैं राज हूं, आपका sales assistant। आज मैं आपकी कैसे मदद कर सकता हूं?",
    "webhook_url": None,  # Add your webhook URL if needed
    "agent_type": "sales",
    "tasks": [
        {
            "task_type": "conversation",
            "tools_config": {
                "llm_agent": {
                    "agent_type": "simple_llm_agent",
                    "agent_flow_type": "streaming",
                    "routes": {
                        "embedding_model": "snowflake/snowflake-arctic-embed-m",
                        "routes": [
                            {
                                "route_name": "price_objection",
                                "utterances": [
                                    "यह बहुत महंगा है",
                                    "This is too expensive",
                                    "Price is high",
                                    "कीमत ज्यादा है"
                                ],
                                "response": "मैं समझ सकता हूं कि price एक concern है। लेकिन हमारे product की quality और value को देखते हुए, यह actually बहुत reasonable है। क्या मैं आपको कुछ special offers बता सकूं?",
                                "score_threshold": 0.8
                            },
                            {
                                "route_name": "competitor_comparison",
                                "utterances": [
                                    "Other companies are cheaper",
                                    "दूसरी कंपनी सस्ती है",
                                    "Competition में better options हैं"
                                ],
                                "response": "बिल्कुल सही कह रहे हैं! Market में options हैं। लेकिन हमारी USP है quality, after-sales service और guarantee। क्या मैं आपको हमारे unique benefits explain कर सकूं?",
                                "score_threshold": 0.8
                            },
                            {
                                "route_name": "not_interested",
                                "utterances": [
                                    "मुझे interest नहीं है",
                                    "Not interested",
                                    "Don't need this",
                                    "अभी नहीं चाहिए"
                                ],
                                "response": "कोई बात नहीं! मैं समझ सकता हूं। लेकिन क्या मैं सिर्फ 2 मिनट में आपको बता सकूं कि यह आपके लिए कैसे beneficial हो सकता है? फिर आप decide कर सकते हैं।",
                                "score_threshold": 0.8
                            }
                        ]
                    },
                    "llm_config": {
                        "agent_flow_type": "streaming",
                        "provider": "openai",
                        "family": "openai",
                        "model": "gpt-4",
                        "summarization_details": None,
                        "extraction_details": None,
                        "max_tokens": 200,
                        "presence_penalty": 0.1,
                        "frequency_penalty": 0.1,
                        "base_url": "https://api.openai.com/v1",
                        "top_p": 0.9,
                        "min_p": 0.1,
                        "top_k": 0,
                        "temperature": 0.7,
                        "request_json": True
                    }
                },
                "synthesizer": {
                    "provider": "polly",
                    "provider_config": {
                        "voice": "Aditi",  # Hindi female voice
                        "engine": "neural",
                        "sampling_rate": "8000",
                        "language": "hi-IN"
                    },
                    "stream": True,
                    "buffer_size": 150,
                    "audio_format": "wav"
                },
                "transcriber": {
                    "provider": "deepgram",
                    "model": "nova-2",
                    "language": "hi",  # Hindi language
                    "stream": True,
                    "sampling_rate": 16000,
                    "encoding": "linear16",
                    "endpointing": 100
                },
                "input": {
                    "provider": "twilio",
                    "format": "wav"
                },
                "output": {
                    "provider": "twilio",
                    "format": "wav"
                },
                "api_tools": None
            },
            "toolchain": {
                "execution": "parallel",
                "pipelines": [
                    [
                        "transcriber",
                        "llm",
                        "synthesizer"
                    ]
                ]
            },
            "task_config": {
                "hangup_after_silence": 15,  # 15 seconds silence
                "incremental_delay": 300,
                "number_of_words_for_interruption": 3,
                "hangup_after_LLMCall": False,
                "call_cancellation_prompt": "धन्यवाद! आपका दिन शुभ हो। नमस्ते!",
                "backchanneling": True,
                "backchanneling_message_gap": 4,
                "backchanneling_start_delay": 3,
                "ambient_noise": False,
                "ambient_noise_track": "office-ambience",
                "call_terminate": 180,  # 3 minutes max call
                "voicemail": True,
                "inbound_limit": -1,
                "whitelist_phone_numbers": [
                    "<any>"
                ],
                "disallow_unknown_numbers": False
            }
        }
    ]
}

# Sales Agent Prompts
SALES_AGENT_PROMPTS = {
    "task_1": {
        "system_prompt": """आप एक expert sales representative हैं जिसका नाम राज है। आप Hindi और English दोनों भाषाओं में fluent हैं।

आपका मुख्य goal है:
1. Customer के साथ friendly relationship बनाना
2. Product/service की benefits explain करना
3. Objections को handle करना
4. Sale close करना या follow-up schedule करना

आपकी personality:
- Confident लेकिन humble
- Customer-focused approach
- Problem solver mindset
- Persistent लेकिन respectful

Sales Techniques:
- AIDA (Attention, Interest, Desire, Action) approach use करें
- Customer की needs को समझें
- Benefits को features से ज्यादा highlight करें
- Social proof और testimonials का use करें
- Urgency create करें लेकिन pressure न डालें

Language Guidelines:
- Hindi-English mix (Hinglish) naturally use करें
- Customer की language preference को follow करें
- Technical terms को simple language में explain करें
- Respectful tone maintain करें

Call Structure:
1. Warm greeting और introduction
2. Customer की current situation जानें
3. Product benefits present करें
4. Objections handle करें
5. Closing attempt करें
6. Next steps decide करें

Remember: हमेशा customer की value को priority दें, sales को नहीं।"""
    }
}

def create_sales_agent():
    """Create a sales agent using Bolna API"""
    
    print("🎯 Creating Sales Agent Configuration")
    print("="*50)
    
    try:
        # Initialize Bolna API
        bolna_api = BolnaAPI()
        
        # Create the agent
        print("🔄 Creating sales agent...")
        
        agent_data = {
            "agent_config": SALES_AGENT_CONFIG,
            "agent_prompts": SALES_AGENT_PROMPTS
        }
        
        response = bolna_api._make_request('POST', '/v2/agent', agent_data)
        
        print("✅ Sales Agent Created Successfully!")
        print(f"🎉 Agent ID: {response.get('agent_id')}")
        print(f"📊 Status: {response.get('status')}")
        
        # Save agent ID for future use
        agent_id = response.get('agent_id')
        if agent_id:
            print(f"\n💾 Saving agent ID to environment...")
            with open('.env', 'a') as f:
                f.write(f"\nSALES_AGENT_ID={agent_id}\n")
            print(f"✅ Agent ID saved to .env file")
        
        return response
        
    except Exception as e:
        print(f"❌ Failed to create sales agent: {e}")
        return None

def test_sales_agent_config():
    """Test the sales agent configuration"""
    
    print("\n🧪 Testing Sales Agent Configuration")
    print("="*40)
    
    # Validate configuration structure
    required_fields = ['agent_name', 'agent_welcome_message', 'tasks']
    
    for field in required_fields:
        if field in SALES_AGENT_CONFIG:
            print(f"✅ {field}: Present")
        else:
            print(f"❌ {field}: Missing")
    
    # Check task configuration
    if SALES_AGENT_CONFIG.get('tasks'):
        task = SALES_AGENT_CONFIG['tasks'][0]
        print(f"✅ Task type: {task.get('task_type')}")
        print(f"✅ Tools configured: {len(task.get('tools_config', {}))}")
        print(f"✅ Routes configured: {len(task.get('tools_config', {}).get('llm_agent', {}).get('routes', {}).get('routes', []))}")
    
    print(f"\n📋 Agent Summary:")
    print(f"   Name: {SALES_AGENT_CONFIG['agent_name']}")
    print(f"   Type: {SALES_AGENT_CONFIG['agent_type']}")
    print(f"   Voice: {SALES_AGENT_CONFIG['tasks'][0]['tools_config']['synthesizer']['provider_config']['voice']}")
    print(f"   Language: {SALES_AGENT_CONFIG['tasks'][0]['tools_config']['transcriber']['language']}")
    print(f"   Max Call Duration: {SALES_AGENT_CONFIG['tasks'][0]['task_config']['call_terminate']} seconds")

if __name__ == "__main__":
    # Test configuration first
    test_sales_agent_config()
    
    # Ask user if they want to create the agent
    create = input("\n🤔 Do you want to create this sales agent? (y/n): ").lower().strip()
    
    if create == 'y':
        result = create_sales_agent()
        if result:
            print(f"\n🚀 Next Steps:")
            print(f"1. Go to your phone numbers dashboard")
            print(f"2. Assign agent ID {result.get('agent_id')} to a phone number")
            print(f"3. Start making sales calls!")
    else:
        print("👍 Configuration ready. Run this script again when you want to create the agent.")
