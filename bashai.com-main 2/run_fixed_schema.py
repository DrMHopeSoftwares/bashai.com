#!/usr/bin/env python3
"""
Manual steps to apply the fixed schema to Supabase
"""

import os
from datetime import datetime

print("="*60)
print("DrM Hope SaaS Platform - Schema Update Guide")
print("="*60)
print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("The fixed schema has been created at: updated_schema_fixed.sql")
print()
print("To apply this schema to your Supabase database:")
print()
print("1. Open your Supabase Dashboard")
print("   URL: https://supabase.com/dashboard")
print()
print("2. Select your project (ymvfueudlippmfeqdqro)")
print()
print("3. Navigate to SQL Editor (in the left sidebar)")
print()
print("4. IMPORTANT: First, drop existing tables to avoid conflicts:")
print("   - Click 'New query'")
print("   - Paste and run this:")
print()
print("-- Drop existing tables (if any)")
print("DROP TABLE IF EXISTS activity_logs CASCADE;")
print("DROP TABLE IF EXISTS call_logs CASCADE;")
print("DROP TABLE IF EXISTS contacts CASCADE;")
print("DROP TABLE IF EXISTS voice_agents CASCADE;")
print("DROP TABLE IF EXISTS channels CASCADE;")
print("DROP TABLE IF EXISTS organizations CASCADE;")
print("DROP TABLE IF EXISTS users CASCADE;")
print("DROP TABLE IF EXISTS enterprises CASCADE;")
print("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
print()
print("5. After dropping tables, create a new query")
print()
print("6. Copy the entire contents of 'updated_schema_fixed.sql'")
print()
print("7. Paste it in the SQL Editor and click 'Run'")
print()
print("8. Check for any errors in the output")
print()
print("Key improvements in the fixed schema:")
print("- ✅ Fixed enterprises INSERT statement")
print("- ✅ Added contact_email to sample data")
print("- ✅ Added automatic updated_at triggers")
print("- ✅ Complete RLS policies (SELECT, INSERT, UPDATE, DELETE)")
print("- ✅ Safer foreign keys (RESTRICT instead of CASCADE for enterprises)")
print("- ✅ Fixed all SQL syntax errors")
print()
print("After applying the schema, test the connection:")
print("  python test_connection.py")
print()
print("Then run the application:")
print("  python main.py")
print()

# Also create a quick test script
with open('test_new_schema.py', 'w') as f:
    f.write("""#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
}

# Test queries
tests = [
    ('Enterprises', '/rest/v1/enterprises'),
    ('Users', '/rest/v1/users'),
    ('Organizations', '/rest/v1/organizations'),
    ('Channels', '/rest/v1/channels'),
    ('Voice Agents', '/rest/v1/voice_agents'),
    ('Contacts', '/rest/v1/contacts'),
]

print("Testing new schema...")
for name, endpoint in tests:
    response = requests.get(f"{SUPABASE_URL}{endpoint}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {name}: {len(data)} records")
    else:
        print(f"❌ {name}: {response.status_code} - {response.text}")
""")

print("Created test_new_schema.py to verify the schema after applying.")