#!/usr/bin/env python3
"""
Apply RelevanceAI Schema Updates to Supabase Database
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def apply_schema_updates():
    """Apply RelevanceAI schema updates to the database"""
    
    # Get Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase configuration. Please check your .env file.")
        return False
    
    # Read the schema update SQL file
    try:
        with open('relevance_ai_schema_update.sql', 'r') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("❌ Schema update file 'relevance_ai_schema_update.sql' not found.")
        return False
    
    # Split SQL into individual statements
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    print("🚀 Starting RelevanceAI schema update...")
    print(f"📊 Found {len(statements)} SQL statements to execute")
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        if not statement or statement.startswith('--'):
            continue
            
        try:
            # Execute SQL statement via Supabase REST API
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"sql": statement}
            )
            
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Statement {i}/{len(statements)} executed successfully")
            else:
                error_count += 1
                print(f"❌ Statement {i}/{len(statements)} failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ Statement {i}/{len(statements)} failed with exception: {e}")
    
    print(f"\n📊 Schema update completed:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {error_count}")
    
    if error_count == 0:
        print("🎉 All schema updates applied successfully!")
        return True
    else:
        print("⚠️  Some schema updates failed. Please check the errors above.")
        return False

def verify_schema_updates():
    """Verify that the schema updates were applied correctly"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔍 Verifying schema updates...")
    
    # Check if new tables exist
    tables_to_check = [
        'relevance_ai_sessions',
        'relevance_ai_messages', 
        'relevance_ai_tools',
        'relevance_ai_workflows',
        'relevance_ai_integrations'
    ]
    
    for table in tables_to_check:
        try:
            response = requests.get(
                f"{supabase_url}/rest/v1/{table}?limit=1",
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ Table '{table}' exists and accessible")
            else:
                print(f"❌ Table '{table}' not accessible: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking table '{table}': {e}")
    
    # Check if voice_agents table has new columns
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/voice_agents?select=provider_type,relevance_ai_agent_id&limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Voice agents table updated with new columns")
        else:
            print(f"❌ Voice agents table update verification failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying voice_agents table: {e}")

def test_relevance_ai_integration():
    """Test the RelevanceAI integration"""
    
    print("\n🧪 Testing RelevanceAI integration...")
    
    try:
        # Import and test the integration module
        sys.path.append('.')
        from relevance_ai_integration import test_relevance_ai_integration
        
        success = test_relevance_ai_integration()
        
        if success:
            print("✅ RelevanceAI integration test passed!")
        else:
            print("❌ RelevanceAI integration test failed!")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing RelevanceAI integration: {e}")
        return False

def main():
    """Main function to run the schema update process"""
    
    print("🔧 RelevanceAI Integration Setup")
    print("=" * 50)
    
    # Step 1: Apply schema updates
    schema_success = apply_schema_updates()
    
    if not schema_success:
        print("\n❌ Schema update failed. Exiting.")
        return False
    
    # Step 2: Verify schema updates
    verify_schema_updates()
    
    # Step 3: Test RelevanceAI integration
    integration_success = test_relevance_ai_integration()
    
    print("\n" + "=" * 50)
    if schema_success and integration_success:
        print("🎉 RelevanceAI integration setup completed successfully!")
        print("\nNext steps:")
        print("1. Update your main.py to import the new RelevanceAI integration")
        print("2. Add new API endpoints for RelevanceAI agents")
        print("3. Test the enhanced UI at /create-agent-enhanced.html")
        return True
    else:
        print("⚠️  Setup completed with some issues. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)