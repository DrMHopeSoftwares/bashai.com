#!/usr/bin/env python3
"""
Apply agent prompts database schema changes
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def apply_schema_changes():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase configuration")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    print("🔧 Applying agent prompts schema changes...")
    
    # First, let's check current voice_agents structure
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/voice_agents?limit=1", headers=headers)
        if response.status_code == 200:
            print("✅ Connected to voice_agents table")
            
            # Check if we have any agents
            agents = response.json()
            if agents:
                existing_agent = agents[0]
                print(f"📋 Found existing agent: {existing_agent.get('title', 'Unknown')}")
                
                # Check if prompt fields already exist
                if 'welcome_message' in existing_agent:
                    print("✅ Agent prompt fields already exist in database")
                    return True
                else:
                    print("⚠️  Agent prompt fields not found - schema needs to be updated")
                    print("📝 Please run the following SQL commands in your Supabase SQL editor:")
                    print()
                    print("ALTER TABLE voice_agents ADD COLUMN IF NOT EXISTS welcome_message TEXT;")
                    print("ALTER TABLE voice_agents ADD COLUMN IF NOT EXISTS agent_prompt TEXT;") 
                    print("ALTER TABLE voice_agents ADD COLUMN IF NOT EXISTS conversation_style VARCHAR(100) DEFAULT 'professional';")
                    print("ALTER TABLE voice_agents ADD COLUMN IF NOT EXISTS language_preference VARCHAR(50) DEFAULT 'hinglish';")
                    print()
                    print("After running these commands, the agent settings feature will work.")
                    return False
            else:
                print("⚠️  No voice agents found")
                return False
                
        else:
            print(f"❌ Failed to connect to voice_agents table: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Agent Prompts Database Schema Update")
    print("=" * 40)
    
    success = apply_schema_changes()
    
    if success:
        print("\n🎉 Database schema is ready!")
        print("✅ You can now use the AI Settings feature in the dashboard")
    else:
        print("\n⚠️  Database schema update needed")
        print("🔗 Go to your Supabase project -> SQL Editor and run the commands shown above")