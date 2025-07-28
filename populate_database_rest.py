#!/usr/bin/env python3
"""
Populate Database with Test Data using Supabase REST API
This script creates test data for all tables using direct REST API calls.
"""

import os
import requests
import json
import uuid
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

HEADERS = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def make_request(method, endpoint, data=None):
    """Make API request to Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=HEADERS)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=HEADERS, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, headers=HEADERS, json=data)
        
        if response.status_code in [200, 201, 204]:
            return True, response.json() if response.text else None
        else:
            return False, f"Status: {response.status_code}, Response: {response.text}"
            
    except Exception as e:
        return False, str(e)

def get_existing_data():
    """Get existing data from key tables"""
    print("📊 Fetching existing data...")
    
    data = {}
    
    # Get enterprises
    success, enterprises = make_request('GET', 'enterprises')
    if success:
        data['enterprises'] = enterprises or []
        print(f"   Enterprises: {len(data['enterprises'])}")
    
    # Get organizations  
    success, organizations = make_request('GET', 'organizations')
    if success:
        data['organizations'] = organizations or []
        print(f"   Organizations: {len(data['organizations'])}")
    
    # Get channels
    success, channels = make_request('GET', 'channels')
    if success:
        data['channels'] = channels or []
        print(f"   Channels: {len(data['channels'])}")
    
    # Get voice agents
    success, voice_agents = make_request('GET', 'voice_agents')
    if success:
        data['voice_agents'] = voice_agents or []
        print(f"   Voice Agents: {len(data['voice_agents'])}")
    
    # Get contacts
    success, contacts = make_request('GET', 'contacts')
    if success:
        data['contacts'] = contacts or []
        print(f"   Contacts: {len(data['contacts'])}")
    
    # Get phone number providers
    success, providers = make_request('GET', 'phone_number_providers')
    if success:
        data['phone_providers'] = providers or []
        print(f"   Phone Providers: {len(data['phone_providers'])}")
    
    # Get voice providers
    success, voice_providers = make_request('GET', 'voice_providers')
    if success:
        data['voice_providers'] = voice_providers or []
        print(f"   Voice Providers: {len(data['voice_providers'])}")
    
    # Get available voices
    success, voices = make_request('GET', 'available_voices')
    if success:
        data['available_voices'] = voices or []
        print(f"   Available Voices: {len(data['available_voices'])}")
    
    return data

def populate_channels(data):
    """Populate channels for each organization"""
    print("\n🔄 Populating channels...")
    
    organizations = data.get('organizations', [])
    existing_channels = data.get('channels', [])
    
    # Get existing channel combinations
    existing_combos = set()
    for channel in existing_channels:
        combo = (channel['organization_id'], channel['name'])
        existing_combos.add(combo)
    
    channel_types = ['Inbound Calls', 'Outbound Calls', 'WhatsApp Messages']
    
    created_count = 0
    for org in organizations:
        for channel_type in channel_types:
            combo = (org['id'], channel_type)
            if combo not in existing_combos:
                channel_data = {
                    'name': channel_type,
                    'description': f'{channel_type} for {org["name"]}',
                    'status': 'active',
                    'organization_id': org['id'],
                    'configuration': {
                        'max_wait_time': 30 if channel_type == 'Inbound Calls' else None,
                        'max_attempts': 3 if channel_type == 'Outbound Calls' else None,
                        'api_key': 'demo_key' if channel_type == 'WhatsApp Messages' else None
                    }
                }
                
                success, result = make_request('POST', 'channels', channel_data)
                if success:
                    created_count += 1
                else:
                    print(f"   ❌ Failed to create channel: {result}")
    
    print(f"   ✅ Created {created_count} channels")

def populate_call_logs(data):
    """Populate call logs"""
    print("\n📞 Populating call logs...")
    
    voice_agents = data.get('voice_agents', [])
    contacts = data.get('contacts', [])
    
    if not voice_agents or not contacts:
        print("   ⚠️  No voice agents or contacts found")
        return
    
    # Check existing call logs
    success, existing_logs = make_request('GET', 'call_logs?select=count')
    existing_count = 0
    if success and existing_logs:
        existing_count = len(existing_logs)
    
    if existing_count > 0:
        print(f"   ⚠️  {existing_count} call logs already exist, skipping...")
        return
    
    created_count = 0
    for _ in range(min(50, len(contacts) * 3)):  # Max 50 call logs
        contact = random.choice(contacts)
        voice_agent = next((va for va in voice_agents if va['id'] == contact['voice_agent_id']), None)
        
        if not voice_agent:
            continue
        
        duration = random.randint(30, 600)
        started_at = datetime.now() - timedelta(days=random.randint(1, 30))
        ended_at = started_at + timedelta(seconds=duration)
        
        call_data = {
            'voice_agent_id': voice_agent['id'],
            'contact_id': contact['id'],
            'phone_number': contact['phone'],
            'call_type': random.choice(['inbound', 'outbound']),
            'status': random.choice(['completed', 'completed', 'completed', 'failed', 'no_answer']),
            'duration': duration,
            'ai_score': random.randint(60, 100),
            'resolution': random.choice(['Issue resolved', 'Follow-up required', 'Transferred to agent']),
            'transcript_url': f'https://storage.example.com/transcripts/{uuid.uuid4()}.txt',
            'call_cost': round(random.uniform(0.5, 5.0), 2),
            'metadata': {
                'sentiment': random.choice(['positive', 'neutral', 'negative']),
                'language': 'en-US',
                'keywords': ['support', 'help', 'question']
            },
            'started_at': started_at.isoformat(),
            'ended_at': ended_at.isoformat()
        }
        
        success, result = make_request('POST', 'call_logs', call_data)
        if success:
            created_count += 1
        else:
            print(f"   ❌ Failed to create call log: {result}")
    
    print(f"   ✅ Created {created_count} call logs")

def populate_activity_logs(data):
    """Populate activity logs"""
    print("\n📝 Populating activity logs...")
    
    # Check for users table first
    success, users = make_request('GET', 'users')
    if not success or not users:
        print("   ⚠️  No users found")
        return
    
    voice_agents = data.get('voice_agents', [])
    if not voice_agents:
        print("   ⚠️  No voice agents found")
        return
    
    # Check existing activity logs
    success, existing_logs = make_request('GET', 'activity_logs?select=count')
    existing_count = 0
    if success and existing_logs:
        existing_count = len(existing_logs)
    
    if existing_count > 0:
        print(f"   ⚠️  {existing_count} activity logs already exist, skipping...")
        return
    
    created_count = 0
    actions = ['create', 'update', 'view', 'delete']
    
    for _ in range(min(30, len(users) * 5)):  # Max 30 activity logs
        user = random.choice(users)
        voice_agent = random.choice(voice_agents)
        action = random.choice(actions)
        
        activity_data = {
            'user_id': user['id'],
            'action': action,
            'entity_type': 'voice_agent',
            'entity_id': voice_agent['id'],
            'description': f'{action.title()}d voice agent: {voice_agent["title"]}',
            'metadata': {
                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                'user_agent': 'Mozilla/5.0',
                'session_id': str(uuid.uuid4())
            },
            'created_at': (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()
        }
        
        success, result = make_request('POST', 'activity_logs', activity_data)
        if success:
            created_count += 1
        else:
            print(f"   ❌ Failed to create activity log: {result}")
    
    print(f"   ✅ Created {created_count} activity logs")

def populate_purchased_phone_numbers(data):
    """Populate purchased phone numbers"""
    print("\n📱 Populating purchased phone numbers...")
    
    enterprises = data.get('enterprises', [])
    phone_providers = data.get('phone_providers', [])
    
    if not enterprises or not phone_providers:
        print("   ⚠️  No enterprises or phone providers found")
        return
    
    # Check existing phone numbers
    success, existing_numbers = make_request('GET', 'purchased_phone_numbers?select=count')
    existing_count = 0
    if success and existing_numbers:
        existing_count = len(existing_numbers)
    
    if existing_count > 0:
        print(f"   ⚠️  {existing_count} phone numbers already exist, skipping...")
        return
    
    created_count = 0
    for enterprise in enterprises:
        for _ in range(2):  # 2 phone numbers per enterprise
            provider = random.choice(phone_providers)
            
            phone_data = {
                'enterprise_id': enterprise['id'],
                'phone_number': f'+1{random.randint(2000000000, 9999999999)}',
                'country_code': 'US',
                'country_name': 'United States',
                'provider_id': provider['id'],
                'provider_phone_id': f'PN{uuid.uuid4().hex[:16]}',
                'monthly_cost': 5.00 if provider['name'] == 'Plivo' else 1.00,
                'setup_cost': 0.00,
                'status': 'active',
                'capabilities': {
                    'voice': True,
                    'sms': True,
                    'mms': False
                },
                'expires_at': (datetime.now() + timedelta(days=365)).isoformat()
            }
            
            success, result = make_request('POST', 'purchased_phone_numbers', phone_data)
            if success:
                created_count += 1
            else:
                print(f"   ❌ Failed to create phone number: {result}")
    
    print(f"   ✅ Created {created_count} phone numbers")

def populate_voice_preferences(data):
    """Populate enterprise voice preferences"""
    print("\n🎤 Populating voice preferences...")
    
    enterprises = data.get('enterprises', [])
    voice_agents = data.get('voice_agents', [])
    available_voices = data.get('available_voices', [])
    
    if not enterprises or not voice_agents or not available_voices:
        print("   ⚠️  Missing required data for voice preferences")
        return
    
    # Check existing preferences
    success, existing_prefs = make_request('GET', 'enterprise_voice_preferences?select=count')
    existing_count = 0
    if success and existing_prefs:
        existing_count = len(existing_prefs)
    
    if existing_count > 0:
        print(f"   ⚠️  {existing_count} voice preferences already exist, skipping...")
        return
    
    created_count = 0
    for voice_agent in voice_agents:
        if available_voices:
            preferred_voice = random.choice(available_voices)
            backup_voice = random.choice(available_voices)
            
            pref_data = {
                'enterprise_id': voice_agent['enterprise_id'],
                'voice_agent_id': voice_agent['id'],
                'preferred_voice_id': preferred_voice['id'],
                'backup_voice_id': backup_voice['id'],
                'voice_settings': {
                    'speed': round(random.uniform(0.8, 1.2), 2),
                    'pitch': round(random.uniform(0.9, 1.1), 2),
                    'volume': round(random.uniform(0.8, 1.0), 2),
                    'emphasis': random.choice(['moderate', 'strong'])
                }
            }
            
            success, result = make_request('POST', 'enterprise_voice_preferences', pref_data)
            if success:
                created_count += 1
            else:
                print(f"   ❌ Failed to create voice preference: {result}")
    
    print(f"   ✅ Created {created_count} voice preferences")

def populate_financial_tables(data):
    """Populate financial tables"""
    print("\n💰 Populating financial tables...")
    
    enterprises = data.get('enterprises', [])
    if not enterprises:
        print("   ⚠️  No enterprises found")
        return
    
    # Account balances
    success, existing_balances = make_request('GET', 'account_balances?select=count')
    balance_count = 0
    if success and existing_balances:
        balance_count = len(existing_balances)
    
    if balance_count == 0:
        created_balances = 0
        for enterprise in enterprises:
            balance_data = {
                'enterprise_id': enterprise['id'],
                'credits_balance': round(random.uniform(100, 5000), 2),
                'currency': 'USD',
                'auto_recharge_enabled': random.choice([True, False]),
                'auto_recharge_amount': random.choice([25.00, 50.00, 100.00]),
                'auto_recharge_trigger': random.choice([25.00, 50.00]),
                'last_recharge_date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            }
            
            success, result = make_request('POST', 'account_balances', balance_data)
            if success:
                created_balances += 1
            else:
                print(f"   ❌ Failed to create account balance: {result}")
        
        print(f"   ✅ Created {created_balances} account balances")
    else:
        print(f"   ⚠️  {balance_count} account balances already exist, skipping...")
    
    # Payment transactions
    success, existing_transactions = make_request('GET', 'payment_transactions?select=count')
    transaction_count = 0
    if success and existing_transactions:
        transaction_count = len(existing_transactions)
    
    if transaction_count == 0:
        created_transactions = 0
        for enterprise in enterprises:
            for _ in range(3):  # 3 transactions per enterprise
                transaction_data = {
                    'enterprise_id': enterprise['id'],
                    'razorpay_payment_id': f'pay_{uuid.uuid4().hex[:14]}',
                    'razorpay_order_id': f'order_{uuid.uuid4().hex[:14]}',
                    'amount': random.choice([25.00, 50.00, 100.00]),
                    'currency': 'INR',
                    'credits_purchased': random.choice([2500.00, 5000.00, 10000.00]),
                    'status': random.choice(['completed', 'completed', 'completed', 'failed', 'pending']),
                    'payment_method': random.choice(['card', 'upi', 'netbanking', 'wallet']),
                    'transaction_type': random.choice(['manual', 'auto_recharge']),
                    'metadata': {
                        'customer_email': f'customer{random.randint(1, 1000)}@example.com',
                        'customer_phone': f'+91{random.randint(9000000000, 9999999999)}',
                        'notes': 'Credit purchase for voice services'
                    },
                    'created_at': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
                }
                
                success, result = make_request('POST', 'payment_transactions', transaction_data)
                if success:
                    created_transactions += 1
                else:
                    print(f"   ❌ Failed to create payment transaction: {result}")
        
        print(f"   ✅ Created {created_transactions} payment transactions")
    else:
        print(f"   ⚠️  {transaction_count} payment transactions already exist, skipping...")

def populate_usage_logs(data):
    """Populate phone usage and credit usage logs"""
    print("\n📊 Populating usage logs...")
    
    # Phone number usage logs
    success, phone_numbers = make_request('GET', 'purchased_phone_numbers')
    voice_agents = data.get('voice_agents', [])
    
    if phone_numbers and voice_agents:
        success, existing_usage = make_request('GET', 'phone_number_usage_logs?select=count')
        usage_count = 0
        if success and existing_usage:
            usage_count = len(existing_usage)
        
        if usage_count == 0:
            created_usage = 0
            for phone_number in phone_numbers:
                for _ in range(5):  # 5 usage logs per phone number
                    usage_data = {
                        'enterprise_id': phone_number['enterprise_id'],
                        'phone_number_id': phone_number['id'],
                        'voice_agent_id': random.choice(voice_agents)['id'],
                        'usage_type': random.choice(['inbound_call', 'outbound_call', 'sms', 'mms']),
                        'duration_seconds': random.randint(30, 600) if random.random() > 0.3 else None,
                        'cost': round(random.uniform(0.01, 2.0), 4),
                        'metadata': {
                            'destination': f'+1{random.randint(5000000000, 9999999999)}',
                            'status': 'completed',
                            'direction': random.choice(['inbound', 'outbound'])
                        },
                        'created_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                    
                    success, result = make_request('POST', 'phone_number_usage_logs', usage_data)
                    if success:
                        created_usage += 1
            
            print(f"   ✅ Created {created_usage} phone usage logs")
        else:
            print(f"   ⚠️  {usage_count} phone usage logs already exist, skipping...")
    
    # Credit usage logs
    contacts = data.get('contacts', [])
    if voice_agents and contacts:
        success, existing_credit_usage = make_request('GET', 'credit_usage_logs?select=count')
        credit_usage_count = 0
        if success and existing_credit_usage:
            credit_usage_count = len(existing_credit_usage)
        
        if credit_usage_count == 0:
            created_credit_usage = 0
            for _ in range(min(100, len(contacts) * 2)):  # Max 100 credit usage logs
                contact = random.choice(contacts)
                voice_agent = next((va for va in voice_agents if va['id'] == contact['voice_agent_id']), None)
                
                if voice_agent:
                    credit_data = {
                        'enterprise_id': voice_agent['enterprise_id'],
                        'voice_agent_id': voice_agent['id'],
                        'contact_id': contact['id'],
                        'credits_used': round(random.uniform(0.1, 10.0), 4),
                        'cost_per_credit': 0.01,
                        'service_type': random.choice(['voice_call', 'sms', 'whatsapp']),
                        'duration_seconds': random.randint(30, 600) if random.random() > 0.2 else None,
                        'call_id': f'call_{uuid.uuid4().hex[:16]}',
                        'metadata': {
                            'provider': random.choice(['twilio', 'plivo']),
                            'destination_country': 'US',
                            'quality_score': random.randint(60, 100)
                        },
                        'created_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                    
                    success, result = make_request('POST', 'credit_usage_logs', credit_data)
                    if success:
                        created_credit_usage += 1
            
            print(f"   ✅ Created {created_credit_usage} credit usage logs")
        else:
            print(f"   ⚠️  {credit_usage_count} credit usage logs already exist, skipping...")

def get_final_counts():
    """Get final record counts for all tables"""
    print("\n📊 Final Database Status:")
    print("-" * 50)
    
    tables = [
        'enterprises', 'organizations', 'channels', 'voice_agents', 'contacts',
        'call_logs', 'activity_logs', 'purchased_phone_numbers', 
        'enterprise_voice_preferences', 'phone_number_usage_logs',
        'account_balances', 'payment_transactions', 'credit_usage_logs'
    ]
    
    for table in tables:
        success, data = make_request('GET', f'{table}?select=count')
        if success:
            count = len(data) if data else 0
            print(f"{table:<30}: {count:>8} records")
        else:
            print(f"{table:<30}: {'ERROR':>8}")

def main():
    """Main execution function"""
    print("🚀 DrM Hope Platform - Database Population")
    print("=" * 60)
    
    # Check Supabase connection
    success, _ = make_request('GET', 'enterprises?select=count')
    if not success:
        print("❌ Cannot connect to Supabase")
        return
    
    print("✅ Supabase connection successful")
    
    # Get existing data
    data = get_existing_data()
    
    # Populate tables
    populate_channels(data)
    populate_call_logs(data)
    populate_activity_logs(data)
    populate_purchased_phone_numbers(data)
    populate_voice_preferences(data)
    populate_financial_tables(data)
    populate_usage_logs(data)
    
    # Show final counts
    get_final_counts()
    
    print("\n" + "=" * 60)
    print("✅ Database population completed successfully!")
    print("💡 Your DrM Hope Platform database is now ready with test data.")
    print("=" * 60)

if __name__ == "__main__":
    main()