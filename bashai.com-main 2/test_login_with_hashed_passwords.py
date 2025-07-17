#!/usr/bin/env python3
"""
Test login with hashed passwords
"""

import requests
import json

def test_login_scenarios():
    """Test various login scenarios"""
    
    print("🔐 Testing Login with Hashed Passwords")
    print("=" * 50)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Test User (original password: bhupendra)",
            "email": "test@example.com",
            "password": "bhupendra"
        },
        {
            "name": "New Hash Test User",
            "email": "hashtest@example.com", 
            "password": "hashtest123"
        },
        {
            "name": "Murali (original password: bhupendra)",
            "email": "b@gmail.com",
            "password": "bhupendra"
        },
        {
            "name": "Wrong Password Test",
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📧 Email: {test_case['email']}")
        print(f"🔑 Password: {test_case['password']}")
        
        try:
            response = requests.post(
                'http://localhost:3000/api/auth/login',
                headers={'Content-Type': 'application/json'},
                json={
                    "email": test_case['email'],
                    "password": test_case['password']
                }
            )
            
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Login successful!")
                    print(f"👤 User: {data['user']['name']}")
                    print(f"🏢 Organization: {data['user']['organization']}")
                    print(f"🎭 Role: {data['user']['role']}")
                    success_count += 1
                else:
                    print(f"❌ Login failed: {data.get('error')}")
            elif response.status_code == 401:
                data = response.json()
                print(f"❌ Authentication failed: {data.get('error')}")
                if test_case['password'] == "wrongpassword":
                    print("✅ (This was expected for wrong password test)")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Successful logins: {success_count}/{len(test_cases)-1} (excluding wrong password test)")
    
    return success_count >= 2  # At least 2 successful logins expected

def test_new_registration():
    """Test new user registration with hashed password"""
    
    print("\n👤 Testing New User Registration")
    print("=" * 40)
    
    new_user = {
        "name": "Security Test Enterprise",
        "owner_name": "Security Test User",
        "contact_email": "security@test.com",
        "contact_phone": "+91 9876543210",
        "password": "securepass123",
        "type": "healthcare"
    }
    
    try:
        # Register new user
        response = requests.post(
            'http://localhost:3000/api/public/signup',
            headers={'Content-Type': 'application/json'},
            json=new_user
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Registration successful!")
                print(f"👤 User: {data['user']['name']}")
                
                # Test login immediately
                print(f"\n🔐 Testing immediate login...")
                login_response = requests.post(
                    'http://localhost:3000/api/auth/login',
                    headers={'Content-Type': 'application/json'},
                    json={
                        "email": new_user['contact_email'],
                        "password": new_user['password']
                    }
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    if login_data.get('success'):
                        print(f"✅ Login after registration successful!")
                        return True
                    else:
                        print(f"❌ Login failed: {login_data.get('error')}")
                else:
                    print(f"❌ Login HTTP Error: {login_response.status_code}")
            else:
                print(f"❌ Registration failed: {data.get('message')}")
        else:
            print(f"❌ Registration HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def check_database_passwords():
    """Check current state of passwords in database"""
    
    print("\n🗄️  Checking Database Password Status")
    print("=" * 45)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'select': 'id,email,name,password', 'order': 'created_at.desc'}
        )
        
        if response.status_code == 200:
            users = response.json()
            
            hashed_count = 0
            plain_count = 0
            null_count = 0
            
            print(f"📊 Password Status for {len(users)} users:")
            
            for user in users:
                password = user.get('password')
                email = user['email']
                name = user['name']
                
                if not password:
                    status = "NULL"
                    null_count += 1
                elif password.startswith('$2b$'):
                    status = "HASHED ✅"
                    hashed_count += 1
                else:
                    status = "PLAIN TEXT ❌"
                    plain_count += 1
                
                print(f"  👤 {name} ({email}): {status}")
            
            print(f"\n📈 Summary:")
            print(f"  🔒 Hashed passwords: {hashed_count}")
            print(f"  📝 Plain text passwords: {plain_count}")
            print(f"  ❌ NULL passwords: {null_count}")
            
            return plain_count == 0  # All should be hashed
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Password Security Implementation")
    print("=" * 60)
    
    # Check database status
    db_secure = check_database_passwords()
    
    # Test login scenarios
    login_success = test_login_scenarios()
    
    # Test new registration
    reg_success = test_new_registration()
    
    print("\n" + "=" * 60)
    print("🎯 Final Results:")
    print(f"🗄️  Database Security: {'✅ SECURE' if db_secure else '❌ NEEDS FIXING'}")
    print(f"🔐 Login System: {'✅ WORKING' if login_success else '❌ NEEDS FIXING'}")
    print(f"👤 Registration: {'✅ WORKING' if reg_success else '❌ NEEDS FIXING'}")
    
    if db_secure and login_success and reg_success:
        print("\n🎉 Password security is fully implemented!")
        print("\n📋 What's working:")
        print("✅ All passwords are hashed with bcrypt")
        print("✅ Login verification works correctly")
        print("✅ New registrations use hashed passwords")
        print("✅ Authentication system is secure")
    else:
        print("\n⚠️  Some issues need to be addressed")
        print("Please check the test results above")
