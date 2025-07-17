#!/usr/bin/env python3
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
