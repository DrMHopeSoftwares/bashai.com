#!/usr/bin/env python3
"""
Test script to verify signup creates user with 'user' role
"""

import requests
import json
import time

def test_signup_user_role():
    """Test that signup form creates user with 'user' role"""
    
    # Test data
    test_email = f"testuser_{int(time.time())}@example.com"
    signup_data = {
        "name": "Test Enterprise",
        "owner_name": "Test User",
        "contact_email": test_email,
        "contact_phone": "+91 9876543210",
        "password": "testpass123",
        "type": "healthcare",
        "status": "trial"
    }
    
    print("🧪 Testing Signup User Role Creation...")
    print(f"📧 Test Email: {test_email}")
    
    try:
        # Test signup
        response = requests.post(
            'http://localhost:3000/api/public/signup',
            headers={'Content-Type': 'application/json'},
            json=signup_data
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Signup Response:")
            print(json.dumps(data, indent=2))
            
            # Check if user role is 'user'
            if data.get('success') and data.get('user'):
                user_role = data['user'].get('role')
                print(f"\n🎯 User Role: {user_role}")
                
                if user_role == 'user':
                    print("✅ SUCCESS: User created with 'user' role!")
                    return True
                else:
                    print(f"❌ FAILED: Expected 'user' role, got '{user_role}'")
                    return False
            else:
                print("❌ FAILED: No user data in response")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_signup_user_role()
    if success:
        print("\n🎉 Test PASSED: Signup creates user with 'user' role")
    else:
        print("\n💥 Test FAILED: Signup not creating user with 'user' role")
