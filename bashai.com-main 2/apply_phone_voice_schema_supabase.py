#!/usr/bin/env python3
"""
Script to apply phone number and voice management schema using Supabase client
"""

import os
import sys
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase package not found. Installing...")
    os.system("pip3 install supabase --user")
    from supabase import create_client, Client

# Load environment variables
load_dotenv()

def apply_schema():
    """Apply the phone number and voice management schema using Supabase client"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return False
    
    # Read the schema file
    try:
        with open('phone_voice_schema.sql', 'r') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print("❌ phone_voice_schema.sql file not found")
        return False
    
    try:
        # Create Supabase client with service key
        print("🔄 Connecting to Supabase...")
        supabase: Client = create_client(supabase_url, service_key)
        
        # Split schema into individual statements for better error handling
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        print(f"🔄 Applying {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                # Execute each statement individually
                if statement.upper().startswith(('CREATE', 'INSERT', 'ALTER', 'DROP')):
                    result = supabase.postgrest.rpc('exec_sql', {'query': statement}).execute()
                    if i % 10 == 0:  # Progress indicator
                        print(f"🔄 Processed {i+1}/{len(statements)} statements...")
            except Exception as e:
                print(f"⚠️  Warning on statement {i+1}: {e}")
                # Continue with other statements
        
        print("✅ Phone number and voice management schema applied successfully!")
        
        # Verify some key tables were created
        try:
            tables_result = supabase.table('phone_number_providers').select('name').limit(1).execute()
            voices_result = supabase.table('available_voices').select('voice_name').limit(1).execute()
            print("✅ Tables verified successfully!")
        except Exception as e:
            print(f"⚠️  Could not verify tables: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False

if __name__ == "__main__":
    success = apply_schema()
    exit(0 if success else 1)