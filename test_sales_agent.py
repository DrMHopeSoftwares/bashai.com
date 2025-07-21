#!/usr/bin/env python3
"""
Test Sales Agent Creation and Assignment
Complete workflow test for creating and using sales agents
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_sales_agent_creation():
    """Test creating a sales agent via the web API"""
    
    print("🎯 Testing Sales Agent Creation")
    print("="*50)
    
    # Test data for sales agent
    sales_agent_data = {
        "name": "Sales Expert - राज",
        "type": "sales",
        "welcome_message": "नमस्ते! मैं राज हूं, आपका sales assistant। आज मैं आपकी कैसे मदद कर सकता हूं?",
        "description": "Expert Hindi/English sales agent for lead conversion",
        "voice": "Aditi",
        "language": "hi",
        "max_duration": 180,
        "silence_timeout": 15,
        "sales_approach": "consultative"
    }
    
    # Test local API endpoint
    api_url = "http://127.0.0.1:5001/api/bolna/create-sales-agent"
    
    try:
        print(f"🔄 Sending request to: {api_url}")
        print(f"📋 Agent Data: {json.dumps(sales_agent_data, indent=2)}")
        
        response = requests.post(
            api_url,
            json=sales_agent_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sales Agent Created Successfully!")
            print(f"🎉 Agent ID: {result.get('agent_id')}")
            print(f"📝 Agent Name: {result.get('agent_name')}")
            print(f"🏷️ Agent Type: {result.get('agent_type')}")
            print(f"📊 Status: {result.get('status')}")
            
            return result.get('agent_id')
            
        else:
            print(f"❌ Failed to create agent: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the Flask server is running:")
        print("   python main.py")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_direct_bolna_api():
    """Test creating agent directly via Bolna API"""
    
    print("\n🔗 Testing Direct Bolna API")
    print("="*40)
    
    try:
        from sales_agent_config import create_sales_agent
        
        print("🔄 Creating sales agent via direct API...")
        result = create_sales_agent()
        
        if result:
            print("✅ Direct API creation successful!")
            return result.get('agent_id')
        else:
            print("❌ Direct API creation failed")
            return None
            
    except ImportError:
        print("❌ sales_agent_config module not found")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_agent_assignment(agent_id):
    """Test assigning agent to phone number"""
    
    print(f"\n📞 Testing Agent Assignment")
    print("="*40)
    
    if not agent_id:
        print("❌ No agent ID provided")
        return False
    
    print(f"🎯 Agent ID to assign: {agent_id}")
    print("📋 Steps to assign agent to phone number:")
    print("1. Go to dashboard: http://127.0.0.1:5001/static/dashboard.html")
    print("2. Navigate to 'My Phone Numbers' section")
    print("3. Click on a phone number to edit")
    print("4. In 'Agent ID' field, enter:", agent_id)
    print("5. Save the configuration")
    
    return True

def test_web_interface():
    """Test the web interface for sales agent creation"""
    
    print(f"\n🌐 Testing Web Interface")
    print("="*40)
    
    web_url = "http://127.0.0.1:5001/create-sales-agent.html"
    
    try:
        response = requests.get(web_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Web interface accessible!")
            print(f"🌐 URL: {web_url}")
            print("📋 Features available:")
            print("   - Step-by-step agent creation")
            print("   - Voice and language selection")
            print("   - Sales configuration options")
            print("   - Real-time preview")
            return True
        else:
            print(f"❌ Web interface not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing web interface: {e}")
        return False

def show_usage_instructions(agent_id=None):
    """Show complete usage instructions"""
    
    print(f"\n📚 Complete Usage Instructions")
    print("="*50)
    
    print("🎯 Sales Agent Creation Methods:")
    print("1. Web Interface:")
    print("   - Open: http://127.0.0.1:5001/create-sales-agent.html")
    print("   - Fill the 4-step form")
    print("   - Click 'Create Sales Agent'")
    
    print("\n2. Direct API Call:")
    print("   - Run: python sales_agent_config.py")
    print("   - Or use: python test_sales_agent.py")
    
    print("\n3. API Endpoint:")
    print("   - POST /api/bolna/create-sales-agent")
    print("   - Send JSON with agent configuration")
    
    if agent_id:
        print(f"\n📞 Using Your Created Agent:")
        print(f"   Agent ID: {agent_id}")
        print("   1. Go to dashboard phone numbers section")
        print("   2. Assign this agent ID to a phone number")
        print("   3. Start making sales calls!")
    
    print(f"\n🔧 Configuration Options:")
    print("   - Voice: Aditi (Hindi), Kendra (English), etc.")
    print("   - Language: Hindi, English, or Hinglish")
    print("   - Sales Approach: Consultative, Direct, Educational")
    print("   - Call Duration: 60-600 seconds")
    print("   - Objection Handling: Price, Competition, Interest")
    
    print(f"\n🎯 Sales Features:")
    print("   - Automatic objection handling")
    print("   - Hindi/English bilingual support")
    print("   - Customizable sales approach")
    print("   - Real-time conversation routing")
    print("   - Professional closing techniques")

def main():
    """Main test function"""
    
    print("🚀 Sales Agent Creation & Testing Suite")
    print("="*60)
    
    # Check if Flask server is running
    try:
        response = requests.get("http://127.0.0.1:5001/", timeout=5)
        print("✅ Flask server is running")
    except:
        print("❌ Flask server not running. Please start it first:")
        print("   python main.py")
        return
    
    # Test 1: Web Interface
    web_success = test_web_interface()
    
    # Test 2: API Endpoint
    agent_id = test_sales_agent_creation()
    
    # Test 3: Direct API (if available)
    if not agent_id:
        agent_id = test_direct_bolna_api()
    
    # Test 4: Assignment Instructions
    test_agent_assignment(agent_id)
    
    # Show complete instructions
    show_usage_instructions(agent_id)
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Web Interface: {'✅ PASS' if web_success else '❌ FAIL'}")
    print(f"   Agent Creation: {'✅ PASS' if agent_id else '❌ FAIL'}")
    print(f"   Agent ID: {agent_id or 'Not created'}")
    
    if agent_id:
        print(f"\n🎉 Success! Your sales agent is ready!")
        print(f"🔗 Next: Assign agent {agent_id} to a phone number")
    else:
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check Bolna API key in .env file")
        print(f"   2. Ensure Flask server is running")
        print(f"   3. Check network connectivity")

if __name__ == "__main__":
    main()
