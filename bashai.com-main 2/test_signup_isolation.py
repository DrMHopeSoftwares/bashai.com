#!/usr/bin/env python3

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5001"

def test_signup_isolation():
    """Test that different email signups through Clerk create separate enterprises"""
    
    print("🧪 Testing Signup Enterprise Isolation")
    print("=" * 50)
    
    print("\n📝 Manual Test Instructions:")
    print("1. Open two different browsers (or incognito windows)")
    print("2. Go to: http://localhost:5001")
    print("3. Sign up with different Gmail accounts:")
    print("   - Browser 1: Sign up with gmail1@gmail.com")
    print("   - Browser 2: Sign up with gmail2@gmail.com")
    print("4. After signup, check if they see different instances")
    
    print("\n🔍 What to verify:")
    print("- Each user should only see their own voice agents")
    print("- Each user should only see their own contacts")
    print("- Voice agents created by one user should not be visible to another")
    
    print("\n🚀 Testing the API endpoints...")
    
    # Test if the server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Flask server is running on port 5001")
        else:
            print(f"❌ Server responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on port 5001")
        return
    
    print("\n🔗 Test URLs:")
    print(f"   Landing Page: {BASE_URL}/")
    print(f"   Dashboard: {BASE_URL}/dashboard.html")
    
    print("\n📋 Test Checklist:")
    print("□ Sign up with first Gmail account")
    print("□ Create a voice agent")
    print("□ Add some contacts")
    print("□ Sign up with second Gmail account (different browser)")
    print("□ Verify second user cannot see first user's data")
    print("□ Create voice agent with second user")
    print("□ Verify first user cannot see second user's data")
    
    print("\n💡 Expected Behavior:")
    print("- Each Gmail signup should create a separate enterprise")
    print("- Users should only see their own enterprise's data")
    print("- No data leakage between different Gmail accounts")
    
    print("\n🏁 Test completed. Please follow the manual steps above.")

if __name__ == "__main__":
    test_signup_isolation() 