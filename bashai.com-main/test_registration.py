#!/usr/bin/env python3
"""
Test registration functionality
"""

import requests
import json

def test_registration():
    """Test user registration via API"""
    
    # Test data
    test_user = {
        "name": "Test Enterprise",
        "owner_name": "Test Owner",
        "contact_email": "test@example.com",
        "contact_phone": "+91 9876543210",
        "password": "testpass123",
        "type": "healthcare"
    }
    
    print("🧪 Testing User Registration")
    print("=" * 40)
    print(f"📧 Email: {test_user['contact_email']}")
    print(f"👤 Name: {test_user['owner_name']}")
    print(f"🏢 Organization: {test_user['name']}")
    
    try:
        # Test registration endpoint
        response = requests.post(
            'http://localhost:3000/api/public/signup',
            headers={'Content-Type': 'application/json'},
            json=test_user
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Registration successful!")
                print(f"🎉 User ID: {data['user']['id']}")
                print(f"🔑 Token: {data['token'][:20]}...")
                return True
            else:
                print(f"❌ Registration failed: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test user login"""
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    print("\n🔐 Testing User Login")
    print("=" * 40)
    
    try:
        response = requests.post(
            'http://localhost:3000/api/auth/login',
            headers={'Content-Type': 'application/json'},
            json=login_data
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Login successful!")
                print(f"👤 User: {data['user']['name']}")
                print(f"🏢 Organization: {data['user']['organization']}")
                return True
            else:
                print(f"❌ Login failed: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_supabase_data():
    """Check if data was stored in Supabase"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase configuration not found")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("\n🗄️  Checking Supabase Data")
    print("=" * 40)
    
    try:
        # Get users from Supabase
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'select': 'id,email,name,organization,role,status', 'order': 'created_at.desc', 'limit': 5}
        )
        
        if response.status_code == 200:
            users = response.json()
            print(f"📊 Found {len(users)} users in database:")
            
            for user in users:
                print(f"  👤 {user['name']} ({user['email']}) - {user['role']} - {user['status']}")
            
            return True
        else:
            print(f"❌ Failed to fetch users: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Registration System")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:3000/')
        if response.status_code != 200:
            print("❌ Server not running on localhost:3000")
            print("Please start the server first:")
            print("python3 main.py")
            exit(1)
    except:
        print("❌ Server not running on localhost:3000")
        print("Please start the server first:")
        print("python3 main.py")
        exit(1)
    
    print("✅ Server is running")
    
    # Test registration
    reg_success = test_registration()
    
    # Test login
    if reg_success:
        login_success = test_login()
    
    # Check database
    check_supabase_data()
    
    print("\n" + "=" * 50)
    if reg_success:
        print("🎉 Registration system is working!")
        print("\n📋 Next steps:")
        print("1. Open http://localhost:3000/signup.html in browser")
        print("2. Test manual registration")
        print("3. Check dashboard access")
    else:
        print("❌ Registration system needs fixing")
        print("Check the errors above and fix the issues")
