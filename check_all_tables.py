#!/usr/bin/env python3
"""
Check what tables exist and their structures
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_existing_tables():
    """Check what tables exist in the database"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("🔍 Checking Existing Tables...")
        
        # List of tables to check
        tables_to_check = [
            'users',
            'voice_agents', 
            'bolna_agents',
            'purchased_phone_numbers',
            'enterprises',
            'organizations'
        ]
        
        accessible_tables = []
        
        for table_name in tables_to_check:
            try:
                print(f"\n📋 Checking table: {table_name}")
                result = supabase.table(table_name).select('*').limit(1).execute()
                
                print(f"✅ {table_name} is accessible")
                print(f"📊 Records: {len(result.data)}")
                
                if result.data:
                    print(f"📋 Sample structure:")
                    sample = result.data[0]
                    for key, value in sample.items():
                        print(f"  {key}: {type(value).__name__}")
                else:
                    print(f"📋 Table is empty")
                
                accessible_tables.append(table_name)
                
            except Exception as table_error:
                print(f"❌ {table_name} error: {table_error}")
        
        return accessible_tables
        
    except Exception as e:
        print(f"❌ Table check error: {e}")
        return []

def test_purchased_phone_numbers():
    """Test using purchased_phone_numbers table for agent storage"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🧪 Testing purchased_phone_numbers table...")
        
        # Get existing phone numbers
        result = supabase.table('purchased_phone_numbers').select('*').limit(3).execute()
        
        print(f"📊 Phone numbers found: {len(result.data)}")
        
        if result.data:
            print(f"\n📋 Sample phone number structure:")
            sample = result.data[0]
            for key, value in sample.items():
                print(f"  {key}: {value} ({type(value).__name__})")
            
            # Check if we can update with agent info
            phone_id = sample.get('id')
            phone_number = sample.get('phone_number')
            
            print(f"\n🔄 Testing update with agent info...")
            print(f"📞 Phone: {phone_number} (ID: {phone_id})")
            
            # Try to update with agent info
            update_data = {
                'agent_id': f"test-agent-{phone_id}",
                'agent_name': 'Test Agent राज'
            }
            
            update_result = supabase.table('purchased_phone_numbers').update(update_data).eq('id', phone_id).execute()
            
            if update_result.data:
                print(f"✅ Phone number updated with agent info!")
                updated_phone = update_result.data[0]
                print(f"📊 Updated phone:")
                print(f"  Agent ID: {updated_phone.get('agent_id')}")
                print(f"  Agent Name: {updated_phone.get('agent_name')}")
                return True
            else:
                print(f"❌ Failed to update phone number")
                return False
        else:
            print(f"📋 No phone numbers found")
            return False
            
    except Exception as e:
        print(f"❌ Phone numbers test error: {e}")
        return False

def create_simple_agents_table():
    """Create a simple agents table without RLS"""
    try:
        # Import supabase client
        from supabase import create_client, Client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        print("\n🔧 Creating simple agents table...")
        
        # Test if we can create a simple table
        test_data = {
            'agent_id': 'test-simple-agent',
            'agent_name': 'Test Simple Agent',
            'phone_number': '+918035315404',
            'created_at': '2025-07-21T17:00:00Z'
        }
        
        # Try to insert into a simple_agents table (might not exist)
        try:
            result = supabase.table('simple_agents').insert(test_data).execute()
            if result.data:
                print(f"✅ Simple agents table works!")
                return True
        except Exception as simple_error:
            print(f"⚠️ Simple agents table doesn't exist: {simple_error}")
        
        return False
        
    except Exception as e:
        print(f"❌ Simple table creation error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Database Tables Analysis")
    print("="*30)
    
    # Test 1: Check existing tables
    accessible_tables = check_existing_tables()
    
    # Test 2: Test phone numbers table
    phone_success = test_purchased_phone_numbers()
    
    # Test 3: Try simple table
    simple_success = create_simple_agents_table()
    
    # Summary
    print("\n📊 Analysis Results:")
    print("="*30)
    print(f"Accessible Tables: {len(accessible_tables)}")
    for table in accessible_tables:
        print(f"  ✅ {table}")
    
    print(f"\nPhone Numbers Update: {'✅ PASS' if phone_success else '❌ FAIL'}")
    print(f"Simple Table Test: {'✅ PASS' if simple_success else '❌ FAIL'}")
    
    if phone_success:
        print(f"\n🎉 SOLUTION FOUND!")
        print(f"💡 Use purchased_phone_numbers table to store agent mapping")
        print(f"📋 Strategy: Update phone records with agent_id and agent_name")
    else:
        print(f"\n⚠️ Need alternative approach for agent storage")

if __name__ == "__main__":
    main()
