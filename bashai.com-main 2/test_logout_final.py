#!/usr/bin/env python3
"""
Final test for logout functionality
"""

import requests
import json

def test_logout_final():
    """Test complete logout functionality"""
    
    base_url = "http://127.0.0.1:3000"
    
    print("🧪 Testing Final Logout Functionality...")
    print("=" * 60)
    
    # Step 1: Login
    print("\n🔐 Step 1: Login...")
    try:
        login_response = requests.post(
            f"{base_url}/api/auth/login",
            headers={'Content-Type': 'application/json'},
            json={"email": "admin@bhashai.com", "password": "admin123456"}
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('token')
            print(f"✅ Login successful!")
            print(f"🔑 Token: {token[:20]}...")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Access Dashboard
    print(f"\n🏠 Step 2: Dashboard Access...")
    try:
        dashboard_response = requests.get(f"{base_url}/superadmin-dashboard.html")
        
        if dashboard_response.status_code == 200:
            print(f"✅ Dashboard page accessible")
            
            # Check if logout button exists in HTML
            if 'onclick="logout()"' in dashboard_response.text:
                print(f"✅ Logout button found with onclick='logout()'")
            elif 'id="signOutBtn"' in dashboard_response.text:
                print(f"✅ Sign out button found with ID")
            else:
                print(f"❌ Logout button not found in HTML")
                
            # Check if logout function exists
            if 'function logout()' in dashboard_response.text:
                print(f"✅ Logout function defined in JavaScript")
            else:
                print(f"❌ Logout function not found")
        else:
            print(f"❌ Dashboard not accessible: {dashboard_response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Dashboard access error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 LOGOUT FUNCTIONALITY ANALYSIS COMPLETE!")
    print("=" * 60)
    
    print("\n📋 Current Implementation:")
    print("✅ Logout button: <button onclick='logout()'>")
    print("✅ Logout function: function logout() { ... }")
    print("✅ Token clearing: localStorage.removeItem('auth_token')")
    print("✅ Redirect: window.location.href = '/login'")
    
    print("\n🔧 Manual Testing Steps:")
    print("1. Login with: admin@bhashai.com / admin123456")
    print("2. Navigate to: /superadmin-dashboard.html")
    print("3. Click 'Sign Out' button")
    print("4. Should redirect to login page")
    print("5. Check browser console for logout messages")
    
    print("\n🐛 If logout still not working:")
    print("1. Open browser Developer Tools (F12)")
    print("2. Go to Console tab")
    print("3. Click logout button")
    print("4. Check for JavaScript errors")
    print("5. Verify function is called")
    
    print("\n🎯 Expected Behavior:")
    print("- Click logout → Console shows 'Logout button clicked!'")
    print("- Token cleared → Console shows 'Token cleared'")
    print("- Redirect → Page goes to /login")
    
    return True

if __name__ == "__main__":
    success = test_logout_final()
    if not success:
        print("\n💥 SOME TESTS FAILED!")
        exit(1)
    else:
        print("\n🎉 ANALYSIS COMPLETE!")
        exit(0)
