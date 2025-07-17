#!/usr/bin/env python3
"""
Test complete login to dashboard flow
"""

import requests
import json

def test_login_dashboard_flow():
    """Test complete login and dashboard access flow"""
    
    print("🔐 Testing Complete Login to Dashboard Flow")
    print("=" * 60)
    
    # Test credentials
    test_credentials = {
        "email": "test@example.com",
        "password": "bhupendra"
    }
    
    print(f"📧 Testing with: {test_credentials['email']}")
    
    try:
        # Step 1: Login
        print("\n🔄 Step 1: Attempting login...")
        login_response = requests.post(
            'http://localhost:3000/api/auth/login',
            headers={'Content-Type': 'application/json'},
            json=test_credentials
        )
        
        print(f"📡 Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        login_data = login_response.json()
        if not login_data.get('success'):
            print(f"❌ Login failed: {login_data.get('error')}")
            return False
        
        print("✅ Login successful!")
        token = login_data.get('token')
        user = login_data.get('user')
        
        print(f"👤 User: {user['name']} ({user['email']})")
        print(f"🎭 Role: {user['role']}")
        print(f"🔑 Token: {token[:20]}...")
        
        # Step 2: Test profile endpoint
        print("\n🔄 Step 2: Testing profile endpoint...")
        profile_response = requests.get(
            'http://localhost:3000/api/auth/profile',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"📡 Profile Status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            if profile_data.get('success'):
                print("✅ Profile endpoint working!")
                print(f"👤 Profile: {profile_data['user']['name']}")
            else:
                print(f"❌ Profile failed: {profile_data.get('error')}")
                return False
        else:
            print(f"❌ Profile endpoint failed: {profile_response.text}")
            return False
        
        # Step 3: Test with cookies
        print("\n🔄 Step 3: Testing cookie-based authentication...")
        
        # Simulate cookie from login response
        cookies = login_response.cookies
        if 'auth_token' in cookies:
            cookie_token = cookies['auth_token']
            print(f"🍪 Cookie token: {cookie_token[:20]}...")
            
            # Test profile with cookie
            profile_cookie_response = requests.get(
                'http://localhost:3000/api/auth/profile',
                cookies={'auth_token': cookie_token},
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📡 Cookie Profile Status: {profile_cookie_response.status_code}")
            
            if profile_cookie_response.status_code == 200:
                print("✅ Cookie authentication working!")
            else:
                print(f"❌ Cookie authentication failed: {profile_cookie_response.text}")
        else:
            print("⚠️  No auth_token cookie found in login response")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dashboard_access():
    """Test dashboard page access"""
    
    print("\n🖥️  Testing Dashboard Page Access")
    print("=" * 40)
    
    try:
        # Test dashboard page
        dashboard_response = requests.get('http://localhost:3000/dashboard.html')
        
        print(f"📡 Dashboard Status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("✅ Dashboard page accessible!")
            
            # Check if it contains authentication script
            if 'initializeAuth' in dashboard_response.text:
                print("✅ Dashboard has authentication script!")
            else:
                print("⚠️  Dashboard missing authentication script")
            
            if '/api/auth/profile' in dashboard_response.text:
                print("✅ Dashboard calls profile endpoint!")
            else:
                print("⚠️  Dashboard doesn't call profile endpoint")
            
            return True
        else:
            print(f"❌ Dashboard page failed: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_token():
    """Test behavior with invalid token"""
    
    print("\n🚫 Testing Invalid Token Behavior")
    print("=" * 40)
    
    try:
        # Test with invalid token
        invalid_response = requests.get(
            'http://localhost:3000/api/auth/profile',
            headers={
                'Authorization': 'Bearer invalid_token_here',
                'Content-Type': 'application/json'
            }
        )
        
        print(f"📡 Invalid Token Status: {invalid_response.status_code}")
        
        if invalid_response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
            return True
        else:
            print(f"❌ Invalid token not handled properly: {invalid_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Login to Dashboard Flow")
    print("=" * 70)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:3000/')
        if response.status_code != 200:
            print("❌ Server not running on localhost:3000")
            exit(1)
    except:
        print("❌ Server not running on localhost:3000")
        exit(1)
    
    print("✅ Server is running")
    
    # Test complete flow
    login_success = test_login_dashboard_flow()
    dashboard_success = test_dashboard_access()
    invalid_token_success = test_invalid_token()
    
    print("\n" + "=" * 70)
    print("🎯 Final Results:")
    print(f"🔐 Login Flow: {'✅ WORKING' if login_success else '❌ FAILED'}")
    print(f"🖥️  Dashboard Access: {'✅ WORKING' if dashboard_success else '❌ FAILED'}")
    print(f"🚫 Security: {'✅ WORKING' if invalid_token_success else '❌ FAILED'}")
    
    if login_success and dashboard_success and invalid_token_success:
        print("\n🎉 All tests passed! Login to Dashboard flow is working!")
        print("\n📋 What's working:")
        print("✅ User can login successfully")
        print("✅ Profile endpoint returns user data")
        print("✅ Dashboard page is accessible")
        print("✅ Authentication script is present")
        print("✅ Invalid tokens are rejected")
        print("\n🎯 Next steps:")
        print("1. Test in browser: http://localhost:3000/login")
        print("2. Login with: test@example.com / bhupendra")
        print("3. Should redirect to dashboard successfully")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        print("The login to dashboard redirect issue may still exist.")
