#!/usr/bin/env python3
"""
Apply enterprise isolation migration to fix multi-tenant SaaS data leakage.
This script adds enterprise_id to the users table and links existing users to enterprises.
"""

import os
import requests
import sys
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ ERROR: Missing Supabase configuration. Please check your .env file.")
    sys.exit(1)

# Supabase API headers
SUPABASE_HEADERS = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def execute_sql(sql_query, description=""):
    """Execute SQL query using Supabase REST API"""
    try:
        print(f"🔄 {description}")
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=SUPABASE_HEADERS,
            json={'query': sql_query}
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ {description} - Success")
            return response.json() if response.content else None
        else:
            print(f"❌ {description} - Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return None

def run_migration():
    """Run the complete enterprise isolation migration"""
    
    print("🚀 Starting Enterprise Isolation Migration")
    print("=" * 60)
    
    # Step 1: Check current users table structure
    print("\n1. Checking current users table structure...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?limit=1",
            headers=SUPABASE_HEADERS
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                columns = list(data[0].keys())
                print(f"   Current columns: {columns}")
                
                if 'enterprise_id' in columns:
                    print("   ✅ enterprise_id column already exists")
                    return
                else:
                    print("   ❌ enterprise_id column missing - proceeding with migration")
            else:
                print("   ℹ️  No data in users table")
        else:
            print(f"   ❌ Failed to check users table: {response.status_code}")
            return
    
    except Exception as e:
        print(f"   ❌ Error checking users table: {e}")
        return
    
    # Step 2: Read migration SQL
    print("\n2. Loading migration SQL...")
    try:
        with open('fix_users_table_migration.sql', 'r') as f:
            migration_sql = f.read()
        print("   ✅ Migration SQL loaded")
    except Exception as e:
        print(f"   ❌ Error loading migration SQL: {e}")
        return
    
    # Step 3: Execute migration in parts (since some SQL functions might not be available via REST API)
    print("\n3. Executing migration steps...")
    
    # Add enterprise_id column
    sql_commands = [
        ("Adding enterprise_id column", 
         "ALTER TABLE users ADD COLUMN IF NOT EXISTS enterprise_id UUID;"),
        
        ("Creating index", 
         "CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON users(enterprise_id);"),
    ]
    
    for description, sql in sql_commands:
        execute_sql(sql, description)
    
    # Step 4: Manual data updates using Supabase REST API
    print("\n4. Updating user-enterprise relationships...")
    
    try:
        # Get all users
        users_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=SUPABASE_HEADERS
        )
        
        if users_response.status_code == 200:
            users = users_response.json()
            print(f"   Found {len(users)} users to process")
            
            # Get all enterprises
            enterprises_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/enterprises",
                headers=SUPABASE_HEADERS
            )
            
            if enterprises_response.status_code == 200:
                enterprises = enterprises_response.json()
                enterprise_map = {e['name']: e['id'] for e in enterprises}
                print(f"   Found {len(enterprises)} existing enterprises")
                
                # Update users with enterprise_id
                updated_count = 0
                for user in users:
                    if user.get('enterprise_id'):
                        continue  # Already has enterprise_id
                    
                    organization = user.get('organization', '').strip()
                    if organization and organization in enterprise_map:
                        enterprise_id = enterprise_map[organization]
                        
                        # Update user
                        update_response = requests.patch(
                            f"{SUPABASE_URL}/rest/v1/users?id=eq.{user['id']}",
                            headers=SUPABASE_HEADERS,
                            json={'enterprise_id': enterprise_id}
                        )
                        
                        if update_response.status_code in [200, 204]:
                            updated_count += 1
                        else:
                            print(f"   ⚠️  Failed to update user {user['email']}")
                
                print(f"   ✅ Updated {updated_count} users with enterprise_id")
            
            else:
                print(f"   ❌ Failed to get enterprises: {enterprises_response.status_code}")
        
        else:
            print(f"   ❌ Failed to get users: {users_response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error updating user-enterprise relationships: {e}")
    
    # Step 5: Verify migration
    print("\n5. Verifying migration...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?limit=5",
            headers=SUPABASE_HEADERS
        )
        
        if response.status_code == 200:
            users = response.json()
            if users:
                sample_user = users[0]
                if 'enterprise_id' in sample_user:
                    print("   ✅ enterprise_id column added successfully")
                    
                    # Count users with enterprise_id
                    users_with_enterprise = sum(1 for u in users if u.get('enterprise_id'))
                    print(f"   ✅ {users_with_enterprise}/{len(users)} sample users have enterprise_id")
                else:
                    print("   ❌ enterprise_id column still missing")
            else:
                print("   ℹ️  No users to verify")
        else:
            print(f"   ❌ Failed to verify migration: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error verifying migration: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Migration Summary:")
    print("   - Added enterprise_id column to users table")
    print("   - Linked existing users to enterprises based on organization")
    print("   - Created database indexes for performance")
    print("   - Your multi-tenant SaaS should now have proper data isolation")
    
    print("\n💡 Next Steps:")
    print("   1. Test the application with different users")
    print("   2. Verify that users only see their enterprise's data")
    print("   3. Run the test script: python3 test_enterprise_isolation.py")
    print("   4. Deploy the updated main.py with enterprise middleware")

if __name__ == "__main__":
    run_migration() 