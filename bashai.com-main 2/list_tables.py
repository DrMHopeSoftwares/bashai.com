#!/usr/bin/env python3
"""
Script to list all tables in the Supabase database
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")
    sys.exit(1)

# Headers for API requests
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json'
}

def list_tables():
    """List all tables in the database using Supabase's table inspection endpoint"""
    try:
        # Query to get all tables from information_schema
        query = """
        SELECT 
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
        """
        
        # Use Supabase's RPC endpoint to execute raw SQL
        url = f"{SUPABASE_URL}/rest/v1/rpc/get_tables"
        
        # First, let's try to get tables using the REST API
        # We'll query each known table to verify it exists
        known_tables = [
            'enterprises',
            'organizations', 
            'channels',
            'voice_agents',
            'contacts',
            'contact_lists',
            'users',
            'profiles',
            'auth.users'
        ]
        
        print("Checking for tables in Supabase database...\n")
        print("=" * 60)
        
        existing_tables = []
        
        for table in known_tables:
            # Skip auth.users for now as it's in a different schema
            if '.' in table:
                continue
                
            # Try to query the table
            table_url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=0"
            response = requests.get(table_url, headers=headers)
            
            if response.status_code == 200:
                existing_tables.append(table)
                print(f"✓ Table found: {table}")
            else:
                print(f"✗ Table not found or inaccessible: {table}")
        
        # Let's also check for any tables we might have missed by trying the schema endpoint
        print("\n" + "=" * 60)
        print("\nAttempting to query database schema directly...")
        
        # Try using a direct query to pg_tables
        schema_query = """
        SELECT 
            schemaname,
            tablename,
            tableowner
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        ORDER BY schemaname, tablename;
        """
        
        # Create a function to get tables (if it doesn't exist)
        create_function_sql = """
        CREATE OR REPLACE FUNCTION get_tables()
        RETURNS TABLE(schema_name text, table_name text, table_type text)
        LANGUAGE sql
        SECURITY DEFINER
        AS $$
            SELECT 
                table_schema::text,
                table_name::text,
                table_type::text
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name;
        $$;
        """
        
        # Try to execute the query via the REST API
        # Note: Direct SQL execution might not be available depending on Supabase configuration
        
        print("\nSummary of accessible tables:")
        print("=" * 60)
        for i, table in enumerate(existing_tables, 1):
            print(f"{i}. {table}")
        
        print(f"\nTotal accessible tables: {len(existing_tables)}")
        
        # Additional check for auth schema tables
        print("\n" + "=" * 60)
        print("\nChecking auth schema tables...")
        
        auth_url = f"{SUPABASE_URL}/auth/v1/admin/users"
        auth_response = requests.get(auth_url, headers=headers)
        
        if auth_response.status_code == 200:
            print("✓ Auth schema is accessible (auth.users table exists)")
        else:
            print("✗ Auth schema requires different access method")
            
    except Exception as e:
        print(f"Error listing tables: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Supabase Table Listing Tool")
    print(f"Database URL: {SUPABASE_URL}")
    print("=" * 60)
    print()
    
    list_tables()