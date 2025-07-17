#!/usr/bin/env python3
"""
Simple script to view and demonstrate editing Anohra's prompt
"""

import os
from dotenv import load_dotenv

load_dotenv()

def view_anohra_prompt():
    """View Anohra's current system prompt"""
    try:
        from relevanceai import RelevanceAI
        
        client = RelevanceAI(
            api_key=os.getenv('RELEVANCE_AI_API_KEY'),
            region=os.getenv('RELEVANCE_AI_REGION'),
            project=os.getenv('RELEVANCE_AI_PROJECT_ID')
        )
        
        anohra_id = "7a4cfa99-6a96-4a48-941f-d5865e0ba577"
        agent = client.agents.retrieve_agent(agent_id=anohra_id)
        
        current_prompt = getattr(agent.metadata, 'system_prompt', 'No prompt found')
        
        print("🤖 ANOHRA'S CURRENT SYSTEM PROMPT")
        print("=" * 50)
        print(current_prompt)
        print("=" * 50)
        print(f"📊 Prompt length: {len(current_prompt)} characters")
        
        # Show key sections
        print(f"\n📋 KEY SECTIONS IDENTIFIED:")
        sections = {
            "Goal": "Provide warm, polite, and patient experience",
            "Hospital Hours": "9 AM - 1 PM (Ayushman), 3 PM - 6 PM (Hope)",
            "Language": "Hindi/English support",
            "Introduction": "Anohra, nurse and telecaller at Dr. Murali's Orthopaedic Clinic",
            "AI Disclosure": "End call mentioning AI assistant",
            "Tone": "Polite, friendly, and patient"
        }
        
        for section, description in sections.items():
            print(f"  • {section}: {description}")
        
        print(f"\n🔧 TO EDIT THIS PROMPT:")
        print(f"1. Use the interactive editor: python edit_anohra_prompt.py")
        print(f"2. Edit directly in RelevanceAI dashboard")
        print(f"3. Update through your BhashAI interface (coming soon)")
        
        return current_prompt
        
    except Exception as e:
        print(f"❌ Error retrieving prompt: {e}")
        return None

if __name__ == "__main__":
    view_anohra_prompt()