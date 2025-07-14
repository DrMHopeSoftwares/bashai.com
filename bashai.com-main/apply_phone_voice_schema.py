#!/usr/bin/env python3
"""
Script to apply phone number and voice management schema to Supabase database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_schema():
    """Apply the phone number and voice management schema"""
    
    # Get database connection details from Supabase URL
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return False
    
    # Extract database connection details
    # Supabase URLs are in format: https://project.supabase.co
    project_id = supabase_url.split('//')[1].split('.')[0]
    
    # Read the schema file
    try:
        with open('phone_voice_schema.sql', 'r') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print("❌ phone_voice_schema.sql file not found")
        return False
    
    # Database connection parameters for Supabase
    conn_params = {
        'host': f'db.{project_id}.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': service_key.split('.')[1] if '.' in service_key else service_key
    }
    
    try:
        # Connect to database
        print("🔄 Connecting to Supabase database...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Execute schema
        print("🔄 Applying phone number and voice management schema...")
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Phone number and voice management schema applied successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('phone_number_providers', 'purchased_phone_numbers', 'voice_providers', 'available_voices', 'enterprise_voice_preferences')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Created {len(tables)} tables: {[t[0] for t in tables]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False

if __name__ == "__main__":
    success = apply_schema()
    exit(0 if success else 1)