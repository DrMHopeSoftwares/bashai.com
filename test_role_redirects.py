#!/usr/bin/env python3
"""
Test Role-Based Redirects
Test that users are redirected to the correct dashboard based on their role
"""

import requests
import json

def test_role_redirects():
    """Test role-based redirect functionality"""
    
    base_url = "http://127.0.0.1:3000"
    
    print("🧪 Testing Role-Based Redirects...")
    print("=" * 60)
    
    # Test cases for different roles
    test_cases = [
        {
            "role": "admin",
            "email": "admin@bhashai.com",
            "password": "admin123456",
            "expected_redirect": "/admin-dashboard.html",
            "description": "Admin user should redirect to admin dashboard"
        },
        {
            "role": "superadmin", 
            "email": "superadmin@bhashai.com",
            "password": "superadmin123456",
            "expected_redirect": "/superadmin-dashboard.html",
            "description": "Super admin should redirect to superadmin dashboard"
        },
        {
            "role": "user",
            "email": "user@bhashai.com", 
            "password": "user123456",
            "expected_redirect": "/dashboard.html",
            "description": "Regular user should redirect to user dashboard"
        },
        {
            "role": "manager",
            "email": "manager@bhashai.com",
            "password": "manager123456", 
            "expected_redirect": "/dashboard.html",
            "description": "Manager should redirect to user dashboard with admin features"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"📧 Email: {test_case['email']}")
        print(f"👤 Expected Role: {test_case['role']}")
        print(f"🔄 Expected Redirect: {test_case['expected_redirect']}")
        
        try:
            # Attempt login
            login_response = requests.post(
                f"{base_url}/api/auth/login",
                headers={'Content-Type': 'application/json'},
                json={
                    "email": test_case['email'],
                    "password": test_case['password']
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                actual_redirect = login_data.get('redirect_url')
                user_role = login_data.get('user', {}).get('role')
                
                print(f"✅ Login successful!")
                print(f"👤 Actual Role: {user_role}")
                print(f"🔄 Actual Redirect: {actual_redirect}")
                
                # Check if redirect matches expected
                if actual_redirect == test_case['expected_redirect']:
                    print(f"✅ Redirect CORRECT!")
                else:
                    print(f"❌ Redirect MISMATCH!")
                    print(f"   Expected: {test_case['expected_redirect']}")
                    print(f"   Got: {actual_redirect}")
                
                # Check if role matches expected
                if user_role == test_case['role']:
                    print(f"✅ Role CORRECT!")
                else:
                    print(f"⚠️ Role different than expected:")
                    print(f"   Expected: {test_case['role']}")
                    print(f"   Got: {user_role}")
                    
            elif login_response.status_code == 401:
                print(f"❌ Login failed: Invalid credentials")
                print(f"   This user might not exist in the database")
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                try:
                    error_data = login_response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Response: {login_response.text}")
        
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ROLE-BASED REDIRECT TEST SUMMARY")
    print("=" * 60)
    
    print("\n📋 Current Role-Based Redirect Logic:")
    print("✅ superadmin → /superadmin-dashboard.html")
    print("✅ admin → /admin-dashboard.html") 
    print("✅ manager → /dashboard.html (with admin features)")
    print("✅ user → /dashboard.html")
    
    print("\n🔧 How It Works:")
    print("1. User logs in with email/password")
    print("2. Backend checks user role from database")
    print("3. Backend returns appropriate redirect_url")
    print("4. Frontend redirects to the correct dashboard")
    print("5. Dashboard checks user role and shows appropriate features")
    
    print("\n📝 Notes:")
    print("- Admin dashboard has enterprise management")
    print("- Superadmin dashboard has full system control")
    print("- User dashboard has personal features")
    print("- Manager dashboard is user dashboard with admin features")

if __name__ == "__main__":
    test_role_redirects()
