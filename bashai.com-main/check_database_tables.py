#!/usr/bin/env python3
"""
Database Health Check Script
Checks all Supabase tables for proper functioning and data storage
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Headers for API requests
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def check_table(table_name, sample_limit=10):
    """Check a table for data and structure"""
    print(f"\n{'='*60}")
    print(f"Checking table: {table_name}")
    print(f"{'='*60}")
    
    try:
        # First check if table exists
        test_url = f"{SUPABASE_URL}/rest/v1/{table_name}?limit=1"
        test_response = requests.get(test_url, headers=headers)
        
        if test_response.status_code == 404:
            print(f"❌ Table does not exist: {table_name}")
            return
        elif test_response.status_code != 200:
            print(f"Error accessing table: {test_response.status_code} - {test_response.text}")
            return
        
        # Get all records to count them (Supabase count issues)
        all_url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"
        all_response = requests.get(all_url, headers=headers)
        
        if all_response.status_code == 200:
            all_data = all_response.json()
            total_count = len(all_data)
            print(f"Total records: {total_count}")
        else:
            print(f"Error getting data: {all_response.status_code} - {all_response.text}")
            return
        
        # Use the already fetched data
        data = all_data[:sample_limit] if all_data else []
        
        if data:
            print(f"\nSample data ({len(data)} records):")
            
            # Analyze first record structure
            first_record = data[0]
            print(f"\nTable columns: {', '.join(first_record.keys())}")
            
            # Check for required fields
            check_required_fields(table_name, data)
            
            # Display sample records
            for i, record in enumerate(data[:3], 1):
                print(f"\nRecord {i}:")
                for key, value in record.items():
                    if value is not None:
                        print(f"  {key}: {value}")
            
            # Check data integrity
            check_data_integrity(table_name, data)
            
        else:
            print("No data found in table")
            
    except Exception as e:
        print(f"Exception checking table {table_name}: {str(e)}")

def check_required_fields(table_name, data):
    """Check if required fields are populated"""
    print("\nChecking required fields...")
    
    # Define required fields per table
    required_fields = {
        'enterprises': ['id', 'name', 'email'],
        'organizations': ['id', 'name', 'enterprise_id'],
        'channels': ['id', 'name', 'organization_id', 'type'],
        'voice_agents': ['id', 'name', 'channel_id'],
        'contacts': ['id', 'phone_number', 'agent_id'],
        'users': ['id', 'email'],
        'call_logs': ['id', 'agent_id', 'contact_id'],
        'activity_logs': ['id', 'enterprise_id', 'action'],
        'account_balances': ['id', 'enterprise_id', 'balance'],
        'payment_transactions': ['id', 'enterprise_id', 'amount'],
        'credit_usage_logs': ['id', 'enterprise_id', 'credits_used'],
        'phone_number_providers': ['id', 'name', 'api_endpoint'],
        'purchased_phone_numbers': ['id', 'phone_number', 'enterprise_id'],
        'voice_providers': ['id', 'name'],
        'available_voices': ['id', 'name', 'provider_id'],
        'enterprise_voice_preferences': ['id', 'enterprise_id', 'voice_id'],
        'phone_number_usage_logs': ['id', 'phone_number_id']
    }
    
    if table_name in required_fields:
        missing_data = []
        for record in data:
            for field in required_fields[table_name]:
                if field not in record or record[field] is None:
                    missing_data.append(f"Record {record.get('id', 'unknown')} missing {field}")
        
        if missing_data:
            print(f"⚠️  Missing required data:")
            for missing in missing_data[:5]:  # Show first 5 issues
                print(f"   - {missing}")
            if len(missing_data) > 5:
                print(f"   ... and {len(missing_data) - 5} more issues")
        else:
            print("✅ All required fields are populated")

def check_data_integrity(table_name, data):
    """Check data integrity and relationships"""
    print("\nChecking data integrity...")
    
    issues = []
    
    # Table-specific integrity checks
    if table_name == 'organizations' and data:
        # Check enterprise_id references
        enterprise_ids = set(r.get('enterprise_id') for r in data if r.get('enterprise_id'))
        if enterprise_ids:
            print(f"  Referenced enterprise IDs: {list(enterprise_ids)[:3]}...")
    
    elif table_name == 'channels' and data:
        # Check organization_id references
        org_ids = set(r.get('organization_id') for r in data if r.get('organization_id'))
        if org_ids:
            print(f"  Referenced organization IDs: {list(org_ids)[:3]}...")
        
        # Check channel types
        channel_types = set(r.get('type') for r in data if r.get('type'))
        print(f"  Channel types found: {channel_types}")
    
    elif table_name == 'voice_agents' and data:
        # Check channel_id references
        channel_ids = set(r.get('channel_id') for r in data if r.get('channel_id'))
        if channel_ids:
            print(f"  Referenced channel IDs: {list(channel_ids)[:3]}...")
    
    elif table_name == 'contacts' and data:
        # Check phone number format
        for record in data:
            phone = record.get('phone_number')
            if phone and not (phone.startswith('+') or phone.isdigit()):
                issues.append(f"Invalid phone format: {phone}")
    
    elif table_name == 'call_logs' and data:
        # Check duration values
        for record in data:
            duration = record.get('duration')
            if duration is not None and duration < 0:
                issues.append(f"Negative duration: {duration}")
    
    elif table_name == 'account_balances' and data:
        # Check balance values
        for record in data:
            balance = record.get('balance')
            if balance is not None and balance < 0:
                issues.append(f"Negative balance for enterprise {record.get('enterprise_id')}")
    
    if issues:
        print(f"⚠️  Data integrity issues found:")
        for issue in issues[:5]:
            print(f"   - {issue}")
        if len(issues) > 5:
            print(f"   ... and {len(issues) - 5} more issues")
    else:
        print("✅ No data integrity issues found")

def check_relationships():
    """Check foreign key relationships across tables"""
    print(f"\n{'='*60}")
    print("Checking table relationships")
    print(f"{'='*60}")
    
    # Check enterprise -> organization relationship
    print("\nChecking enterprise -> organization relationships...")
    try:
        # Get all organizations with enterprise data
        url = f"{SUPABASE_URL}/rest/v1/organizations?select=id,name,enterprise_id,enterprises(id,name)"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            orphaned = [r for r in data if not r.get('enterprises')]
            if orphaned:
                print(f"⚠️  Found {len(orphaned)} organizations without valid enterprise reference")
            else:
                print("✅ All organizations have valid enterprise references")
    except Exception as e:
        print(f"Error checking relationships: {str(e)}")

def main():
    """Main function to check all tables"""
    print("Database Health Check Report")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Supabase URL: {SUPABASE_URL}")
    
    # Core tables
    core_tables = [
        'enterprises',
        'organizations', 
        'channels',
        'voice_agents',
        'contacts',
        'users'
    ]
    
    # Additional tables
    additional_tables = [
        'call_logs',
        'activity_logs',
        'account_balances',
        'payment_transactions',
        'credit_usage_logs',
        'phone_number_providers',
        'purchased_phone_numbers',
        'voice_providers',
        'available_voices',
        'enterprise_voice_preferences',
        'phone_number_usage_logs'
    ]
    
    print("\n" + "="*60)
    print("CHECKING CORE TABLES")
    print("="*60)
    
    for table in core_tables:
        check_table(table)
    
    print("\n" + "="*60)
    print("CHECKING ADDITIONAL TABLES")
    print("="*60)
    
    for table in additional_tables:
        check_table(table)
    
    # Check relationships
    check_relationships()
    
    print("\n" + "="*60)
    print("Health check complete!")
    print("="*60)

if __name__ == "__main__":
    main()