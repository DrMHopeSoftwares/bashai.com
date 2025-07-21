#!/usr/bin/env python3
"""
Simple script to create the bolna_agents table in Supabase
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_bolna_agents_table():
    """Create the bolna_agents table"""
    try:
        # Import supabase
        from supabase import create_client, Client
        
        # Initialize Supabase client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials in .env file")
            return False
            
        supabase: Client = create_client(url, key)
        
        # Simple SQL to create table
        sql = """
        CREATE TABLE IF NOT EXISTS bolna_agents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            bolna_agent_id VARCHAR(255) NOT NULL UNIQUE,
            agent_name VARCHAR(255) NOT NULL,
            agent_type VARCHAR(100) DEFAULT 'voice',
            description TEXT,
            prompt TEXT,
            welcome_message TEXT,
            voice VARCHAR(100),
            language VARCHAR(10),
            max_duration INTEGER DEFAULT 300,
            hangup_after INTEGER DEFAULT 30,
            status VARCHAR(50) DEFAULT 'active',
            voice_agent_id UUID,
            phone_number VARCHAR(20),
            user_id UUID,
            enterprise_id UUID,
            bolna_response JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        print("🔄 Creating bolna_agents table...")
        
        # Execute SQL using raw SQL
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        
        print("✅ Successfully created bolna_agents table!")
        print(f"Result: {result.data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    success = create_bolna_agents_table()
    sys.exit(0 if success else 1)
