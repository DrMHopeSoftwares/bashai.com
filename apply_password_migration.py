#!/usr/bin/env python3
"""
Apply password column migration to Supabase users table
This script adds encrypted password support to the existing users table
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_password_migration():
    """Apply the password column migration to Supabase"""
    
    # Supabase configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
        return False
    
    # Read the SQL migration file
    try:
        with open('add_password_column.sql', 'r') as file:
            sql_content = file.read()
    except FileNotFoundError:
        print("❌ Error: add_password_column.sql file not found")
        return False
    
    # Supabase REST API headers
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Split SQL into individual statements (basic splitting)
    sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--') and not stmt.strip().startswith('/*')]
    
    print(f"🔄 Applying password migration to Supabase...")
    print(f"📍 Supabase URL: {SUPABASE_URL}")
    print(f"📝 Found {len(sql_statements)} SQL statements to execute")
    
    success_count = 0
    
    for i, sql_statement in enumerate(sql_statements, 1):
        if not sql_statement:
            continue
            
        print(f"\n🔄 Executing statement {i}/{len(sql_statements)}...")
        print(f"📝 SQL: {sql_statement[:100]}{'...' if len(sql_statement) > 100 else ''}")
        
        # Execute SQL via Supabase REST API
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"sql": sql_statement}
            )
            
            if response.status_code == 200:
                print(f"✅ Statement {i} executed successfully")
                success_count += 1
            else:
                print(f"❌ Statement {i} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error executing statement {i}: {str(e)}")
    
    print(f"\n📊 Migration Summary:")
    print(f"✅ Successful statements: {success_count}/{len(sql_statements)}")
    
    if success_count == len(sql_statements):
        print("🎉 Password migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your authentication code to use password hashing")
        print("2. Test user registration with encrypted passwords")
        print("3. Test user login with password verification")
        return True
    else:
        print("⚠️  Some statements failed. Please check the errors above.")
        return False

def test_password_functions():
    """Test the password hashing and verification functions"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Error: Supabase configuration not found")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("\n🧪 Testing password functions...")
    
    # Test password hashing
    test_password = "test123"
    hash_sql = f"SELECT hash_password('{test_password}') as password_hash"
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": hash_sql}
        )
        
        if response.status_code == 200:
            print("✅ Password hashing function works!")
        else:
            print(f"❌ Password hashing test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing password functions: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Supabase Password Migration")
    print("=" * 50)
    
    success = apply_password_migration()
    
    if success:
        test_password_functions()
        
        print("\n" + "=" * 50)
        print("🎯 Migration completed!")
        print("\n📖 Usage Examples:")
        print("1. Hash password: SELECT hash_password('plain_password');")
        print("2. Verify password: SELECT verify_password('plain_password', password_hash);")
        print("3. Insert user: INSERT INTO users (email, name, organization, password_hash) VALUES ('user@example.com', 'John', 'Corp', hash_password('password123'));")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
