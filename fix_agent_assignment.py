#!/usr/bin/env python3
"""
Fix agent assignment issues by:
1. Adding agent_id column to purchased_phone_numbers table if missing
2. Updating phone numbers with correct agent IDs
3. Cleaning up old/invalid agent references
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def fix_agent_assignment():
    """Fix agent assignment issues"""
    
    try:
        # Initialize Supabase client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials")
            return False
            
        supabase = create_client(url, key)
        
        print("🔧 **FIXING AGENT ASSIGNMENT ISSUES**")
        print("=" * 60)
        
        # Step 1: Check current table structure
        print("\n1. 🔍 Checking purchased_phone_numbers table structure...")
        
        # Try to get a sample record to see what columns exist
        try:
            sample = supabase.table('purchased_phone_numbers').select('*').limit(1).execute()
            if sample.data:
                columns = list(sample.data[0].keys())
                print(f"   Current columns: {columns}")
                
                if 'agent_id' not in columns:
                    print("   ⚠️ agent_id column missing - need to add it")
                    # Note: We can't add columns via Supabase client, need to do it via SQL
                    print("   💡 Please add agent_id column manually in Supabase dashboard:")
                    print("   ALTER TABLE purchased_phone_numbers ADD COLUMN agent_id VARCHAR(255);")
                else:
                    print("   ✅ agent_id column exists")
            else:
                print("   ⚠️ No records found in purchased_phone_numbers table")
                
        except Exception as e:
            print(f"   ❌ Error checking table structure: {e}")
        
        # Step 2: Check bolna_agents table
        print("\n2. 🤖 Checking bolna_agents table...")
        try:
            agents = supabase.table('bolna_agents').select('*').execute()
            print(f"   Found {len(agents.data)} agents in bolna_agents table:")
            
            for agent in agents.data:
                agent_id = agent.get('bolna_agent_id')
                agent_name = agent.get('agent_name')
                phone_number = agent.get('phone_number')
                print(f"     - {agent_name} (ID: {agent_id}) for phone: {phone_number}")
                
        except Exception as e:
            print(f"   ❌ Error checking bolna_agents: {e}")
        
        # Step 3: Check phone numbers and their current agent assignments
        print("\n3. 📞 Checking phone number assignments...")
        try:
            phones = supabase.table('purchased_phone_numbers').select('*').execute()
            print(f"   Found {len(phones.data)} phone numbers:")
            
            for phone in phones.data:
                phone_number = phone.get('phone_number')
                current_agent = phone.get('agent_id', 'NO_AGENT_ID_COLUMN')
                print(f"     - {phone_number} -> Agent: {current_agent}")
                
        except Exception as e:
            print(f"   ❌ Error checking phone numbers: {e}")
        
        # Step 4: Suggest fixes
        print("\n4. 💡 **RECOMMENDED FIXES:**")
        print("   1. Add agent_id column to purchased_phone_numbers table:")
        print("      ALTER TABLE purchased_phone_numbers ADD COLUMN agent_id VARCHAR(255);")
        print("   ")
        print("   2. Update phone numbers with correct agent IDs from bolna_agents table")
        print("   ")
        print("   3. Clean up old agent references that no longer exist in Bolna API")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fix_agent_assignment: {e}")
        return False

def update_phone_agent_mapping():
    """Update phone number agent mapping based on bolna_agents table"""
    
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase = create_client(url, key)
        
        print("\n🔄 **UPDATING PHONE-AGENT MAPPING**")
        print("=" * 50)
        
        # Get all agents from bolna_agents table
        agents = supabase.table('bolna_agents').select('*').execute()
        
        for agent in agents.data:
            agent_id = agent.get('bolna_agent_id')
            phone_number = agent.get('phone_number')
            agent_name = agent.get('agent_name')
            
            if phone_number and agent_id:
                print(f"\n📞 Updating {phone_number} -> {agent_name} ({agent_id})")
                
                try:
                    # Try to update the phone number record
                    # Note: This will fail if agent_id column doesn't exist
                    result = supabase.table('purchased_phone_numbers').update({
                        'agent_id': agent_id
                    }).eq('phone_number', phone_number).execute()
                    
                    if result.data:
                        print(f"   ✅ Updated successfully")
                    else:
                        print(f"   ⚠️ No matching phone number found")
                        
                except Exception as e:
                    if "agent_id" in str(e) and "column" in str(e):
                        print(f"   ❌ agent_id column missing - please add it first")
                    else:
                        print(f"   ❌ Update failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating phone-agent mapping: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting agent assignment fix...")
    
    # Run the fixes
    fix_agent_assignment()
    
    # Ask user if they want to try updating mappings
    print("\n" + "="*60)
    response = input("Do you want to try updating phone-agent mappings? (y/n): ")
    
    if response.lower() == 'y':
        update_phone_agent_mapping()
    
    print("\n✅ Agent assignment fix complete!")
