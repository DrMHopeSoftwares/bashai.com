#!/usr/bin/env python3
"""
Database Setup and Population Script for DrM Hope Platform
This script creates missing financial tables and populates all tables with test data.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def execute_sql_file(file_path, description=""):
    """Execute SQL file using Supabase REST API"""
    print(f"\n{'='*60}")
    print(f"Executing: {description or file_path}")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Split SQL content by statements (rough split by semicolon)
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            # Skip comments and empty statements
            if not statement or statement.startswith('--') or statement.startswith('/*'):
                continue
                
            print(f"Executing statement {i+1}/{len(statements)}...")
            
            # Execute SQL using Supabase REST API
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers={
                    'apikey': SUPABASE_SERVICE_KEY,
                    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                    'Content-Type': 'application/json'
                },
                json={'sql': statement}
            )
            
            if response.status_code not in [200, 201, 204]:
                print(f"Warning: Statement {i+1} returned status {response.status_code}")
                print(f"Response: {response.text}")
        
        print(f"✅ Successfully executed {file_path}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error executing {file_path}: {str(e)}")

def execute_sql_direct(sql, description=""):
    """Execute SQL directly using Supabase REST API"""
    print(f"\n{description}")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers={
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'Content-Type': 'application/json'
            },
            json={'sql': sql}
        )
        
        if response.status_code in [200, 201, 204]:
            print("✅ Query executed successfully")
            if response.text:
                print(f"Response: {response.text}")
        else:
            print(f"❌ Query failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error executing query: {str(e)}")

def check_supabase_connection():
    """Check if Supabase connection is working"""
    print("Checking Supabase connection...")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/enterprises?select=count",
            headers={
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}'
            }
        )
        
        if response.status_code == 200:
            print("✅ Supabase connection successful")
            return True
        else:
            print(f"❌ Supabase connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection error: {str(e)}")
        return False

def get_table_counts():
    """Get count of records in all tables"""
    tables = [
        'enterprises', 'organizations', 'channels', 'voice_agents', 'contacts',
        'call_logs', 'activity_logs', 'purchased_phone_numbers', 
        'enterprise_voice_preferences', 'phone_number_usage_logs',
        'account_balances', 'payment_transactions', 'credit_usage_logs'
    ]
    
    print("\n📊 Table Record Counts:")
    print("-" * 40)
    
    for table in tables:
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/{table}?select=count",
                headers={
                    'apikey': SUPABASE_SERVICE_KEY,
                    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                    'Prefer': 'count=exact'
                }
            )
            
            if response.status_code == 200:
                count = response.headers.get('Content-Range', '0-0/0').split('/')[-1]
                print(f"{table:<30}: {count:>8} records")
            else:
                print(f"{table:<30}: {'ERROR':>8}")
                
        except Exception as e:
            print(f"{table:<30}: {'ERROR':>8} ({str(e)})")

def main():
    """Main execution function"""
    print("🚀 DrM Hope Platform - Database Setup and Population")
    print("=" * 60)
    
    # Check Supabase connection
    if not check_supabase_connection():
        print("❌ Cannot proceed without Supabase connection")
        return
    
    # Step 1: Create financial tables
    execute_sql_file('payment_schema.sql', '💰 Creating Financial Tables')
    
    # Step 2: Create phone and voice tables
    execute_sql_file('phone_voice_schema_fixed.sql', '📞 Creating Phone & Voice Tables')
    
    # Step 3: Populate with test data
    execute_sql_file('populate_test_data.sql', '🔄 Populating Test Data')
    
    # Step 4: Show final counts
    print("\n" + "=" * 60)
    print("📊 FINAL DATABASE STATUS")
    print("=" * 60)
    get_table_counts()
    
    print("\n" + "=" * 60)
    print("✅ Database setup and population completed successfully!")
    print("💡 Your DrM Hope Platform database is now ready with test data.")
    print("=" * 60)

if __name__ == "__main__":
    main()