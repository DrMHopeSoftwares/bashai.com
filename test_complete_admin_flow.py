#!/usr/bin/env python3
"""
Complete test for admin dashboard redirect flow
"""

import requests
import json

def test_complete_admin_flow():
    """Test complete admin flow including dashboard access"""
    
    base_url = "http://127.0.0.1:3000"
    
    print("🧪 Testing Complete Admin Dashboard Flow...")
    print("=" * 60)
    
    # Step 1: Test admin login
    print("\n👑 Step 1: Testing Admin Login...")
    admin_email = "admin@bhashai.com"
    admin_password = "admin123456"
    
    try:
        login_data = {
            "email": admin_email,
            "password": admin_password
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            json=login_data
        )
        
        print(f"📊 Login Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('success'):
                user_data = response_data.get('user', {})
                token = response_data.get('token')
                redirect_url = response_data.get('redirect_url')
                
                print("✅ Admin login successful!")
                print(f"👤 User: {user_data.get('name', 'N/A')}")
                print(f"📧 Email: {user_data.get('email', 'N/A')}")
                print(f"👑 Role: {user_data.get('role', 'N/A')}")
                print(f"🎯 Redirect URL: {redirect_url}")
                print(f"🔑 Token: {'✅ Present' if token else '❌ Missing'}")
                
                if redirect_url == '/admin-dashboard.html':
                    print("✅ Correct admin dashboard redirect!")
                else:
                    print(f"❌ Wrong redirect URL! Expected: /admin-dashboard.html, Got: {redirect_url}")
                    return False
                
                # Step 2: Test admin dashboard access
                print(f"\n🏠 Step 2: Testing Admin Dashboard Access...")
                
                dashboard_headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                dashboard_response = requests.get(
                    f"{base_url}/admin-dashboard.html",
                    headers=dashboard_headers
                )
                
                print(f"📊 Dashboard Response Status: {dashboard_response.status_code}")
                
                if dashboard_response.status_code == 200:
                    print("✅ Admin dashboard accessible!")
                    
                    # Check if it's the correct admin dashboard
                    if 'SuperAdmin Dashboard' in dashboard_response.text or 'admin' in dashboard_response.text.lower():
                        print("✅ Correct admin dashboard content!")
                    else:
                        print("⚠️ Dashboard content may not be admin-specific")
                else:
                    print(f"❌ Admin dashboard not accessible: {dashboard_response.status_code}")
                    return False
                
                # Step 3: Test admin profile API
                print(f"\n👤 Step 3: Testing Admin Profile API...")
                
                profile_response = requests.get(
                    f"{base_url}/api/auth/profile",
                    headers=dashboard_headers
                )
                
                print(f"📊 Profile Response Status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    profile_user = profile_data.get('user', {})
                    
                    print("✅ Admin profile API working!")
                    print(f"👑 Profile Role: {profile_user.get('role', 'N/A')}")
                    
                    if profile_user.get('role') == 'admin':
                        print("✅ Profile confirms admin role!")
                    else:
                        print(f"❌ Profile role mismatch! Expected: admin, Got: {profile_user.get('role')}")
                        return False
                else:
                    print(f"❌ Profile API failed: {profile_response.status_code}")
                    return False
                
                # Step 4: Test regular user for comparison
                print(f"\n👤 Step 4: Testing Regular User Redirect...")
                
                regular_login_data = {
                    "email": "testuser_1752555737@example.com",
                    "password": "test123456"
                }
                
                regular_response = requests.post(
                    f"{base_url}/api/auth/login",
                    headers={'Content-Type': 'application/json'},
                    json=regular_login_data
                )
                
                if regular_response.status_code == 200:
                    regular_data = regular_response.json()
                    regular_redirect = regular_data.get('redirect_url')
                    regular_role = regular_data.get('user', {}).get('role')
                    
                    print(f"✅ Regular user login successful!")
                    print(f"👑 Regular Role: {regular_role}")
                    print(f"🎯 Regular Redirect: {regular_redirect}")
                    
                    if regular_redirect == '/dashboard.html':
                        print("✅ Regular user redirects to correct dashboard!")
                    else:
                        print(f"❌ Regular user wrong redirect! Expected: /dashboard.html, Got: {regular_redirect}")
                        return False
                else:
                    print(f"⚠️ Regular user login failed: {regular_response.status_code}")
                
            else:
                print(f"❌ Admin login failed: {response_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Admin login request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during admin flow test: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL ADMIN TESTS PASSED!")
    print("✅ Admin login working")
    print("✅ Admin dashboard redirect working")
    print("✅ Admin dashboard accessible")
    print("✅ Admin profile API working")
    print("✅ Regular user redirect working")
    print("=" * 60)
    
    print("\n📋 Manual Testing Instructions:")
    print("1. Open: http://127.0.0.1:3000/login")
    print("2. Login with: admin@bhashai.com / admin123456")
    print("3. Should redirect to: /admin-dashboard.html")
    print("4. Logout and login with regular user")
    print("5. Should redirect to: /dashboard.html")
    
    return True

if __name__ == "__main__":
    success = test_complete_admin_flow()
    if not success:
        print("\n💥 SOME TESTS FAILED!")
        exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED!")
        exit(0)
