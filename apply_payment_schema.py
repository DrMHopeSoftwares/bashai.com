#!/usr/bin/env python3
"""
Apply payment schema to Supabase database
"""

import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🔧 Payment Schema Setup Required")
    print("=" * 40)
    print()
    print("📝 Please run the following SQL commands in your Supabase SQL Editor:")
    print()
    
    # Read the schema file
    try:
        with open('payment_schema.sql', 'r') as f:
            schema_content = f.read()
        
        print("--- COPY THE SQL BELOW ---")
        print()
        print(schema_content)
        print()
        print("--- END OF SQL ---")
        print()
        print("🔗 Supabase SQL Editor: https://supabase.com/dashboard/project/[your-project-id]/sql")
        print("💡 After running the SQL, test the payment system again")
        
    except FileNotFoundError:
        print("❌ payment_schema.sql file not found")
        return False
    
    return True

if __name__ == "__main__":
    main()