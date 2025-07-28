#!/usr/bin/env python3
"""
Add sample enterprises to Supabase database
"""

import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

def add_sample_enterprises():
    """Add sample enterprises to Supabase"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase credentials not found")
        return
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Sample enterprises to add
    sample_enterprises = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Healthcare / Hospital',
            'type': 'healthcare',
            'status': 'active',
            'contact_email': 'info@healthcare.com'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Clinic / Medical Center',
            'type': 'clinic',
            'status': 'active',
            'contact_email': 'info@clinic.com'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Diagnostic Center',
            'type': 'diagnostic',
            'status': 'active',
            'contact_email': 'info@diagnostic.com'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Pharmacy',
            'type': 'pharmacy',
            'status': 'active',
            'contact_email': 'info@pharmacy.com'
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Other',
            'type': 'other',
            'status': 'active',
            'contact_email': 'info@other.com'
        }
    ]
    
    try:
        print("🏢 Adding sample enterprises...")
        
        for enterprise in sample_enterprises:
            # Check if enterprise already exists
            check_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/enterprises",
                headers=headers,
                params={'name': f'eq.{enterprise["name"]}'}
            )
            
            if check_response.status_code == 200:
                existing = check_response.json()
                if existing:
                    print(f"⚠️ Enterprise '{enterprise['name']}' already exists")
                    continue
            
            # Add enterprise
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/enterprises",
                headers=headers,
                json=enterprise
            )
            
            if response.status_code == 201:
                print(f"✅ Added enterprise: {enterprise['name']}")
            else:
                print(f"❌ Failed to add enterprise '{enterprise['name']}': {response.text}")
        
        print("\n🎉 Sample enterprises setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_sample_enterprises()
