#!/usr/bin/env python3
"""
Create bolna_agents table in Supabase database
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_bolna_agents_table():
    """Create the bolna_agents table using Supabase REST API"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials in .env file")
            return False
        
        print("🔄 Creating bolna_agents table...")
        
        # SQL to create table
        sql_commands = [
            # Create table
            """
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
            """,
            
            # Create indexes
            """
            CREATE INDEX IF NOT EXISTS idx_bolna_agents_bolna_agent_id ON bolna_agents(bolna_agent_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_bolna_agents_phone_number ON bolna_agents(phone_number);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_bolna_agents_user_id ON bolna_agents(user_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_bolna_agents_status ON bolna_agents(status);
            """,
            
            # Create trigger function
            """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            """,
            
            # Create trigger
            """
            CREATE TRIGGER update_bolna_agents_updated_at 
                BEFORE UPDATE ON bolna_agents
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
        ]
        
        # Execute each SQL command
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        for i, sql in enumerate(sql_commands, 1):
            print(f"🔄 Executing SQL command {i}/{len(sql_commands)}...")
            
            # Use Supabase REST API to execute SQL
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={'sql': sql.strip()},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Command {i} executed successfully")
            else:
                print(f"⚠️ Command {i} failed: {response.status_code} - {response.text}")
        
        print("✅ Bolna agents table creation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def test_table_creation():
    """Test if table was created successfully"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        # Try to query the table
        result = supabase.table('bolna_agents').select('*').limit(1).execute()
        
        print("✅ Table exists and is accessible!")
        print(f"📊 Current records: {len(result.data)}")
        return True
        
    except Exception as e:
        print(f"⚠️ Table test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating Bolna Agents Table")
    print("="*40)
    
    success = create_bolna_agents_table()
    
    if success:
        print("\n🧪 Testing table creation...")
        test_success = test_table_creation()
        
        if test_success:
            print("\n🎉 Setup completed successfully!")
            print("📋 You can now create agents and they will be stored in bolna_agents table")
        else:
            print("\n⚠️ Table created but testing failed")
    else:
        print("\n❌ Failed to create table")
    
    sys.exit(0 if success else 1)
