#!/usr/bin/env python3
"""
Manual enterprise isolation migration using Supabase REST API.
This script works around SQL execution limitations by using direct table operations.
"""

import os
import requests
import sys
import uuid
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

def run_manual_migration():
    """Run manual migration using REST API operations"""
    
    print("🚀 Starting Manual Enterprise Isolation Migration")
    print("=" * 60)
    
    # Step 1: Check current state
    print("\n1. Analyzing current database state...")
    
    try:
        # Get all users
        users_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=SUPABASE_HEADERS
        )
        
        # Get all enterprises
        enterprises_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/enterprises",
            headers=SUPABASE_HEADERS
        )
        
        if users_response.status_code != 200:
            print(f"   ❌ Failed to get users: {users_response.status_code}")
            return
        
        if enterprises_response.status_code != 200:
            print(f"   ❌ Failed to get enterprises: {enterprises_response.status_code}")
            return
        
        users = users_response.json()
        enterprises = enterprises_response.json()
        
        print(f"   📊 Found {len(users)} users and {len(enterprises)} enterprises")
        
        # Check if enterprise_id column exists
        has_enterprise_id = len(users) > 0 and 'enterprise_id' in users[0]
        print(f"   🔍 Users table has enterprise_id: {'✅ Yes' if has_enterprise_id else '❌ No'}")
        
        if has_enterprise_id:
            users_with_enterprise = sum(1 for u in users if u.get('enterprise_id'))
            print(f"   📈 Users with enterprise_id: {users_with_enterprise}/{len(users)}")
            
            if users_with_enterprise == len(users):
                print("   ✅ All users already have enterprise_id - migration not needed")
                return
        
    except Exception as e:
        print(f"   ❌ Error analyzing database: {e}")
        return
    
    # Step 2: Create enterprises for unique organizations
    print("\n2. Creating enterprises for unique organizations...")
    
    try:
        # Get unique organizations from users
        organizations = set()
        for user in users:
            org = user.get('organization', '').strip()
            if org:
                organizations.add(org)
        
        print(f"   🏢 Found {len(organizations)} unique organizations: {list(organizations)}")
        
        # Create enterprise map
        enterprise_map = {e['name']: e['id'] for e in enterprises}
        
        # Create missing enterprises
        created_count = 0
        for org in organizations:
            if org not in enterprise_map:
                # Create new enterprise
                enterprise_data = {
                    'id': str(uuid.uuid4()),
                    'name': org,
                    'type': 'trial',
                    'contact_email': f'contact@{org.lower().replace(" ", "")}.com',
                    'status': 'active'
                }
                
                create_response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/enterprises",
                    headers=SUPABASE_HEADERS,
                    json=enterprise_data
                )
                
                if create_response.status_code in [200, 201]:
                    enterprise_map[org] = enterprise_data['id']
                    created_count += 1
                    print(f"   ✅ Created enterprise: {org}")
                else:
                    print(f"   ⚠️  Failed to create enterprise for {org}: {create_response.status_code}")
        
        print(f"   📈 Created {created_count} new enterprises")
        
    except Exception as e:
        print(f"   ❌ Error creating enterprises: {e}")
        return
    
    # Step 3: Update users with enterprise_id (if column exists)
    print("\n3. Linking users to enterprises...")
    
    if not has_enterprise_id:
        print("   ⚠️  enterprise_id column doesn't exist in users table")
        print("   📝 Please run this SQL manually in Supabase SQL Editor:")
        print("      ALTER TABLE users ADD COLUMN enterprise_id UUID;")
        print("      CREATE INDEX idx_users_enterprise_id ON users(enterprise_id);")
        print("   🔄 Then run this script again")
        return
    
    try:
        updated_count = 0
        
        for user in users:
            # Skip if user already has enterprise_id
            if user.get('enterprise_id'):
                continue
            
            organization = user.get('organization', '').strip()
            if organization and organization in enterprise_map:
                enterprise_id = enterprise_map[organization]
                
                # Update user with enterprise_id
                update_response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/users?id=eq.{user['id']}",
                    headers=SUPABASE_HEADERS,
                    json={'enterprise_id': enterprise_id}
                )
                
                if update_response.status_code in [200, 204]:
                    updated_count += 1
                    print(f"   ✅ Linked {user['email']} to {organization}")
                else:
                    print(f"   ⚠️  Failed to update {user['email']}: {update_response.status_code}")
            else:
                print(f"   ⚠️  No enterprise found for user {user['email']} (org: {organization})")
        
        print(f"   📈 Updated {updated_count} users with enterprise_id")
        
    except Exception as e:
        print(f"   ❌ Error updating users: {e}")
        return
    
    # Step 4: Verify migration
    print("\n4. Verifying migration results...")
    
    try:
        # Get updated users
        users_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=SUPABASE_HEADERS
        )
        
        if users_response.status_code == 200:
            updated_users = users_response.json()
            users_with_enterprise = sum(1 for u in updated_users if u.get('enterprise_id'))
            
            print(f"   📊 Final stats: {users_with_enterprise}/{len(updated_users)} users have enterprise_id")
            
            if users_with_enterprise == len(updated_users):
                print("   ✅ Migration completed successfully!")
            else:
                print("   ⚠️  Some users still missing enterprise_id")
                
                # Show users without enterprise_id
                missing_users = [u for u in updated_users if not u.get('enterprise_id')]
                for user in missing_users[:3]:  # Show first 3
                    print(f"      - {user['email']} (org: {user.get('organization', 'None')})")
        
        else:
            print(f"   ❌ Failed to verify migration: {users_response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error verifying migration: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Migration Summary:")
    print("   - Created enterprises for all unique organizations")
    print("   - Linked users to their respective enterprises")
    print("   - Your multi-tenant SaaS should now have proper data isolation")
    
    print("\n💡 Next Steps:")
    print("   1. If enterprise_id column was missing, add it manually in Supabase SQL Editor")
    print("   2. Run this script again after adding the column")
    print("   3. Test the application: python3 test_enterprise_isolation.py")
    print("   4. Restart your Flask app to use the new enterprise middleware")

if __name__ == "__main__":
    run_manual_migration() 