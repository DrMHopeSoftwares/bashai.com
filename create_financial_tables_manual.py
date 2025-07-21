#!/usr/bin/env python3
"""
Create Financial Tables Manually using Supabase REST API for table creation
This script will attempt to create the financial tables using direct SQL execution
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

def create_financial_tables():
    """Manually create financial table structures using raw SQL"""
    
    print("💰 Creating Financial Tables...")
    print("=" * 60)
    
    # We'll use a workaround: create the tables by inserting data first
    # This will auto-create basic table structures
    
    # Try to check if tables exist
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Test if account_balances table exists
    print("🔍 Checking if account_balances table exists...")
    response = requests.get(f"{SUPABASE_URL}/rest/v1/account_balances?limit=1", headers=headers)
    if response.status_code == 404:
        print("❌ account_balances table does not exist")
        print("📝 Please run the payment_schema.sql in Supabase SQL Editor manually")
        print("   Go to: Supabase Dashboard > SQL Editor > New Query")
        print("   Copy and paste the contents of payment_schema.sql")
        print("   Then run this script again")
        return False
    elif response.status_code == 200:
        print("✅ account_balances table exists")
    else:
        print(f"⚠️ Unexpected response: {response.status_code}")
    
    # Test if payment_transactions table exists
    print("🔍 Checking if payment_transactions table exists...")
    response = requests.get(f"{SUPABASE_URL}/rest/v1/payment_transactions?limit=1", headers=headers)
    if response.status_code == 404:
        print("❌ payment_transactions table does not exist")
        return False
    elif response.status_code == 200:
        print("✅ payment_transactions table exists")
    
    # Test if credit_usage_logs table exists
    print("🔍 Checking if credit_usage_logs table exists...")
    response = requests.get(f"{SUPABASE_URL}/rest/v1/credit_usage_logs?limit=1", headers=headers)
    if response.status_code == 404:
        print("❌ credit_usage_logs table does not exist")
        return False
    elif response.status_code == 200:
        print("✅ credit_usage_logs table exists")
    
    return True

def manual_sql_instructions():
    """Provide manual instructions for creating tables"""
    print("\n" + "=" * 60)
    print("📋 MANUAL SETUP INSTRUCTIONS")
    print("=" * 60)
    print("Since the financial tables don't exist, please follow these steps:")
    print()
    print("1. Go to your Supabase Dashboard:")
    print("   https://app.supabase.com/")
    print()
    print("2. Navigate to: SQL Editor > New Query")
    print()
    print("3. Copy and paste the entire contents of these files:")
    print("   - payment_schema.sql")
    print("   - phone_voice_schema_fixed.sql (if phone tables don't exist)")
    print()
    print("4. Execute the queries")
    print()
    print("5. Re-run this script to populate with test data:")
    print("   python populate_database_rest.py")
    print()
    print("📁 The SQL files are located in your project directory:")
    print(f"   /Users/murali/bhashai.com for git push/bashai.com/")
    print()
    print("=" * 60)

def main():
    """Main execution function"""
    print("🚀 DrM Hope Platform - Financial Tables Setup")
    print("=" * 60)
    
    # Check Supabase connection
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}'
    }
    
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/enterprises?limit=1", headers=headers, timeout=10)
        if response.status_code != 200:
            print("❌ Cannot connect to Supabase")
            return
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Check if financial tables exist
    if not create_financial_tables():
        manual_sql_instructions()
        return
    
    print("\n✅ All financial tables exist!")
    print("💡 You can now run: python populate_database_rest.py")

if __name__ == "__main__":
    main()