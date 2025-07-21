#!/usr/bin/env python3
"""
Manually create bolna_agents table using raw SQL
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_table_manually():
    """Create table using raw SQL"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("🔄 Creating bolna_agents table manually...")
        
        # Drop table if exists and recreate
        sql_commands = [
            # Drop table if exists
            "DROP TABLE IF EXISTS bolna_agents CASCADE;",
            
            # Create table
            """
            CREATE TABLE bolna_agents (
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
            
            # Disable RLS
            "ALTER TABLE bolna_agents DISABLE ROW LEVEL SECURITY;",
            
            # Create indexes
            "CREATE INDEX IF NOT EXISTS idx_bolna_agents_bolna_agent_id ON bolna_agents(bolna_agent_id);",
            "CREATE INDEX IF NOT EXISTS idx_bolna_agents_phone_number ON bolna_agents(phone_number);",
            "CREATE INDEX IF NOT EXISTS idx_bolna_agents_user_id ON bolna_agents(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_bolna_agents_status ON bolna_agents(status);",
            
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
        
        # Execute each command
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"🔄 Executing command {i}/{len(sql_commands)}...")
                
                # Use raw SQL execution
                result = supabase.postgrest.rpc('exec_sql', {'sql': sql.strip()}).execute()
                print(f"✅ Command {i} executed successfully")
                
            except Exception as cmd_error:
                print(f"⚠️ Command {i} failed: {cmd_error}")
                # Continue with other commands
        
        print("✅ Table creation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def test_table_access():
    """Test if we can access the table"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🧪 Testing table access...")
        
        # Try to query the table
        result = supabase.table('bolna_agents').select('*').limit(1).execute()
        
        print(f"✅ Table is accessible!")
        print(f"📊 Current records: {len(result.data)}")
        
        # Try to insert a test record
        test_data = {
            'bolna_agent_id': 'test-access-check',
            'agent_name': 'Test Access Agent',
            'agent_type': 'test',
            'description': 'Test record for access check'
        }
        
        insert_result = supabase.table('bolna_agents').insert(test_data).execute()
        
        if insert_result.data:
            print(f"✅ Insert test successful!")
            
            # Clean up test record
            supabase.table('bolna_agents').delete().eq('bolna_agent_id', 'test-access-check').execute()
            print(f"🧹 Test record cleaned up")
            
            return True
        else:
            print(f"❌ Insert test failed")
            return False
        
    except Exception as e:
        print(f"❌ Table access test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Manual Table Creation")
    print("="*30)
    
    # Create table
    create_success = create_table_manually()
    
    if create_success:
        # Test access
        access_success = test_table_access()
        
        if access_success:
            print(f"\n🎉 SUCCESS! Table created and accessible!")
            print(f"📋 You can now store agents in bolna_agents table")
        else:
            print(f"\n⚠️ Table created but access test failed")
    else:
        print(f"\n❌ Failed to create table")

if __name__ == "__main__":
    main()
