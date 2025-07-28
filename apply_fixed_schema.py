#!/usr/bin/env python3
"""Apply the fixed schema to Supabase database"""

import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: Missing Supabase credentials in .env file")
    sys.exit(1)

# Read the fixed schema
with open('updated_schema_fixed.sql', 'r') as f:
    schema_sql = f.read()

# Split into individual statements (handle multi-line statements properly)
statements = []
current_statement = []
in_function = False

for line in schema_sql.split('\n'):
    # Track if we're inside a function definition
    if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
        in_function = True
    elif line.strip() == '$$ language \'plpgsql\';':
        in_function = False
    
    current_statement.append(line)
    
    # End of statement detection
    if not in_function and line.strip().endswith(';'):
        statement = '\n'.join(current_statement).strip()
        if statement and not statement.startswith('--'):
            statements.append(statement)
        current_statement = []

# Execute each statement
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

print(f"Applying fixed schema to Supabase...")
print(f"Total statements to execute: {len(statements)}")

errors = []
success_count = 0

for i, statement in enumerate(statements):
    print(f"\nExecuting statement {i+1}/{len(statements)}...")
    
    # Show first 100 chars of statement
    preview = statement[:100].replace('\n', ' ')
    if len(statement) > 100:
        preview += "..."
    print(f"  {preview}")
    
    # Execute via Supabase REST API
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
        headers=headers,
        json={"query": statement}
    )
    
    if response.status_code == 404:
        # Try direct SQL execution endpoint
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/",
            headers={
                **headers,
                'Content-Profile': 'public'
            },
            json={"query": statement}
        )
    
    if response.status_code not in [200, 201, 204]:
        error_msg = f"Statement {i+1} failed: {response.status_code} - {response.text}"
        errors.append(error_msg)
        print(f"  ❌ {error_msg}")
        
        # For certain errors, we might want to continue
        if "already exists" in response.text.lower():
            print("  ⚠️  Object already exists, continuing...")
            success_count += 1
        elif "duplicate key" in response.text.lower():
            print("  ⚠️  Duplicate data, continuing...")
            success_count += 1
    else:
        success_count += 1
        print(f"  ✅ Success")

print(f"\n{'='*60}")
print(f"Schema application complete!")
print(f"Successful statements: {success_count}/{len(statements)}")
print(f"Errors: {len(errors)}")

if errors:
    print("\nErrors encountered:")
    for error in errors[:5]:  # Show first 5 errors
        print(f"  - {error}")
    if len(errors) > 5:
        print(f"  ... and {len(errors) - 5} more errors")

print("\nNote: Since Supabase doesn't have a direct SQL execution endpoint,")
print("you'll need to apply the schema manually through the Supabase Dashboard:")
print("1. Go to your Supabase project dashboard")
print("2. Navigate to SQL Editor")
print("3. Copy the contents of 'updated_schema_fixed.sql'")
print("4. Paste and run in the SQL Editor")
print("\nThe fixed schema file is ready at: updated_schema_fixed.sql")