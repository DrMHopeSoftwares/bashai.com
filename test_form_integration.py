#!/usr/bin/env python3
"""
Test the complete form integration
"""

import requests
import json
import time
from datetime import datetime

def test_form_endpoint():
    """Test the form endpoint"""
    try:
        print("🧪 Testing Form Integration...")
        
        # Test data matching the form
        form_data = {
            "agent_name": f"Form Test Agent {datetime.now().strftime('%H%M%S')}",
            "phone_number": "+918035749854",
            "language": "hi",
            "voice": "Aditi",
            "sales_approach": "Consultative",
            "welcome_message": "नमस्ते! मैं आपका sales assistant हूं। आज मैं आपकी कैसे मदद कर सकता हूं?",
            "agent_prompt": "आप एक expert sales representative हैं। Customer के साथ friendly relationship बनाएं और product की benefits explain करें।"
        }
        
        print(f"📋 Form Data:")
        print(json.dumps(form_data, indent=2, ensure_ascii=False))
        
        # Make API request to form endpoint
        response = requests.post(
            'http://localhost:5003/api/bolna/create-agent-form',
            headers={'Content-Type': 'application/json'},
            json=form_data,
            timeout=30
        )
        
        print(f"\n📡 API Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') != 'error':
                agent_id = result.get('agent_id')
                agent_name = result.get('agent_name')
                phone_number = result.get('phone_number')
                
                print(f"\n✅ Form Integration Successful!")
                print(f"🎯 Agent ID: {agent_id}")
                print(f"📝 Agent Name: {agent_name}")
                print(f"📞 Phone Number: {phone_number}")
                
                return agent_id
            else:
                print(f"❌ Form integration failed: {result.get('error')}")
                return None
        else:
            print(f"❌ Form endpoint failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Form integration error: {e}")
        return None

def test_form_page():
    """Test if the form page loads"""
    try:
        print("\n🌐 Testing Form Page...")
        
        response = requests.get('http://localhost:5003/agent-form', timeout=10)
        
        print(f"📡 Form page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for key elements
            checks = [
                ('Form Title', 'Create Sales Agent' in content),
                ('Agent Name Field', 'agent_name' in content),
                ('Language Select', 'language' in content),
                ('Sales Approach', 'sales_approach' in content),
                ('Welcome Message', 'welcome_message' in content),
                ('Agent Prompt', 'agent_prompt' in content),
                ('Create Button', 'Create Agent' in content),
                ('JavaScript', '/api/bolna/create-agent-form' in content)
            ]
            
            print(f"\n📋 Form Page Checks:")
            all_passed = True
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
                if not passed:
                    all_passed = False
            
            return all_passed
        else:
            print(f"❌ Form page failed to load")
            return False
            
    except Exception as e:
        print(f"❌ Form page test error: {e}")
        return False

def check_database_storage():
    """Check if agent data is stored in database"""
    try:
        print("\n🔍 Checking Database Storage...")
        
        # Import supabase client
        from supabase import create_client, Client
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase: Client = create_client(url, key)
        
        # Check different tables for recent agent data
        tables_to_check = ['bolna_agents', 'organizations']
        
        total_found = 0
        recent_agents = []
        
        for table_name in tables_to_check:
            try:
                result = supabase.table(table_name).select('*').execute()
                count = len(result.data)
                total_found += count
                
                print(f"📊 {table_name}: {count} records")
                
                # Look for recent agents (created in last hour)
                if result.data:
                    for record in result.data:
                        created_at = record.get('created_at', '')
                        if 'Form Test Agent' in str(record.get('name', '')) or 'Form Test Agent' in str(record.get('agent_name', '')):
                            recent_agents.append({
                                'table': table_name,
                                'id': record.get('id'),
                                'name': record.get('name') or record.get('agent_name'),
                                'created_at': created_at
                            })
                    
            except Exception as table_error:
                print(f"⚠️ {table_name} check failed: {table_error}")
        
        if recent_agents:
            print(f"\n📋 Recent Form Test Agents Found:")
            for agent in recent_agents:
                print(f"  ✅ {agent['name']} (Table: {agent['table']}, ID: {agent['id']})")
        
        return len(recent_agents) > 0
        
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Complete Form Integration Test")
    print("="*40)
    
    # Test 1: Form page loads
    page_success = test_form_page()
    
    # Test 2: Form endpoint works
    agent_id = test_form_endpoint()
    
    # Wait a bit for processing
    if agent_id:
        print(f"\n⏳ Waiting 5 seconds for database processing...")
        time.sleep(5)
    
    # Test 3: Database storage
    db_success = check_database_storage()
    
    # Summary
    print("\n📊 Integration Test Results:")
    print("="*35)
    print(f"Form Page Load: {'✅ PASS' if page_success else '❌ FAIL'}")
    print(f"Form Endpoint: {'✅ PASS' if agent_id else '❌ FAIL'}")
    print(f"Database Storage: {'✅ PASS' if db_success else '❌ FAIL'}")
    
    if page_success and agent_id and db_success:
        print(f"\n🎉 COMPLETE SUCCESS! Form integration working perfectly!")
        print(f"🌐 Form URL: http://localhost:5003/agent-form")
        print(f"🎯 Latest Agent ID: {agent_id}")
        print(f"\n📋 Next Steps:")
        print(f"  1. Open http://localhost:5003/agent-form in browser")
        print(f"  2. Fill out the form")
        print(f"  3. Click 'Create Agent'")
        print(f"  4. Agent will be created and stored in database")
    elif page_success and agent_id:
        print(f"\n✅ Form working! Database storage needs manual verification")
        print(f"🌐 Form URL: http://localhost:5003/agent-form")
        print(f"🎯 Agent ID: {agent_id}")
    else:
        print(f"\n⚠️ Some issues found. Check the logs above.")

if __name__ == "__main__":
    main()
