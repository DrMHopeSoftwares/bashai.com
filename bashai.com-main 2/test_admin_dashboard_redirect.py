#!/usr/bin/env python3
"""
Test admin dashboard redirect functionality
"""

import requests
import json

def test_admin_dashboard_redirect():
    """Test admin login and dashboard redirect"""
    
    base_url = "http://127.0.0.1:3000"
    
    print("🧪 Testing Admin Dashboard Redirect...")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Admin User",
            "email": "admin@bhashai.com",
            "password": "admin123456",
            "expected_role": "admin",
            "expected_redirect": "/admin-dashboard.html"
        },
        {
            "name": "Regular User",
            "email": "testuser_1752555737@example.com",
            "password": "test123456",
            "expected_role": "user",
            "expected_redirect": "/dashboard.html"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📧 Email: {test_case['email']}")
        print(f"👑 Expected Role: {test_case['expected_role']}")
        print(f"🎯 Expected Redirect: {test_case['expected_redirect']}")
        
        try:
            # Login request
            login_data = {
                "email": test_case['email'],
                "password": test_case['password']
            }
            
            response = requests.post(
                f"{base_url}/api/auth/login",
                headers={'Content-Type': 'application/json'},
                json=login_data
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('success'):
                    user_data = response_data.get('user', {})
                    actual_role = user_data.get('role')
                    actual_redirect = response_data.get('redirect_url')
                    
                    print(f"✅ Login successful!")
                    print(f"👤 User: {user_data.get('name', 'N/A')}")
                    print(f"👑 Actual Role: {actual_role}")
                    print(f"🎯 Actual Redirect: {actual_redirect}")
                    
                    # Validate role
                    if actual_role == test_case['expected_role']:
                        print(f"✅ Role matches expected: {actual_role}")
                    else:
                        print(f"❌ Role mismatch! Expected: {test_case['expected_role']}, Got: {actual_role}")
                    
                    # Validate redirect URL
                    if actual_redirect == test_case['expected_redirect']:
                        print(f"✅ Redirect URL matches expected: {actual_redirect}")
                    else:
                        print(f"❌ Redirect URL mismatch! Expected: {test_case['expected_redirect']}, Got: {actual_redirect}")
                    
                    # Overall test result
                    if actual_role == test_case['expected_role'] and actual_redirect == test_case['expected_redirect']:
                        print(f"🎉 Test {i} PASSED!")
                    else:
                        print(f"💥 Test {i} FAILED!")
                        
                else:
                    print(f"❌ Login failed: {response_data.get('error', 'Unknown error')}")
                    print(f"💥 Test {i} FAILED!")
            else:
                print(f"❌ Login request failed: {response.status_code}")
                print(f"💥 Test {i} FAILED!")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
            print(f"💥 Test {i} FAILED!")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("✅ Admin users should redirect to /admin-dashboard.html")
    print("✅ Regular users should redirect to /dashboard.html")
    print("✅ Managers should redirect to /dashboard.html")
    print("\n📋 Manual Testing:")
    print("1. Open: http://127.0.0.1:3000/login")
    print("2. Login with admin@bhashai.com / admin123456")
    print("3. Should redirect to admin dashboard")
    print("4. Login with regular user credentials")
    print("5. Should redirect to regular dashboard")

if __name__ == "__main__":
    test_admin_dashboard_redirect()
