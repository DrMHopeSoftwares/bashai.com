#!/usr/bin/env python3
"""
Test Supabase connection and check if password migration was successful
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("🔄 Testing Supabase connection...")
    print(f"📍 Supabase URL: {SUPABASE_URL}")
    
    try:
        # Test basic connection
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'select': 'id,email,name', 'limit': 1}
        )
        
        if response.status_code == 200:
            print("✅ Supabase connection successful!")
            
            # Check if users table exists and has password_hash column
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                params={'select': 'id,email,name,password_hash', 'limit': 1}
            )
            
            if response.status_code == 200:
                print("✅ Users table exists with password_hash column!")
                
                # Test password functions
                test_password_functions(headers, SUPABASE_URL)
                return True
            else:
                print(f"❌ Users table or password_hash column missing: {response.text}")
                return False
        else:
            print(f"❌ Supabase connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_password_functions(headers, supabase_url):
    """Test password hashing and verification functions"""
    
    print("\n🧪 Testing password functions...")
    
    try:
        # Test if hash_password function exists
        test_password = "test123"
        
        # Try to call hash_password function
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/hash_password",
            headers=headers,
            json={'password': test_password}
        )
        
        if response.status_code == 200:
            password_hash = response.json()
            print(f"✅ hash_password function works! Hash: {password_hash[:20]}...")
            
            # Test verify_password function
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/verify_password",
                headers=headers,
                json={'password': test_password, 'hash': password_hash}
            )
            
            if response.status_code == 200 and response.json():
                print("✅ verify_password function works!")
                return True
            else:
                print(f"❌ verify_password function failed: {response.text}")
                return False
        else:
            print(f"❌ hash_password function not found: {response.text}")
            print("\n💡 You need to run the password migration SQL in Supabase Dashboard")
            return False
            
    except Exception as e:
        print(f"❌ Error testing password functions: {e}")
        return False

def create_test_user():
    """Create a test user to verify everything works"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("\n🧪 Creating test user...")
    
    try:
        # First, hash the password
        test_password = "testuser123"
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/hash_password",
            headers=headers,
            json={'password': test_password}
        )
        
        if response.status_code == 200:
            password_hash = response.json()
            
            # Create test user
            test_user = {
                'email': 'test@bhashai.com',
                'name': 'Test User',
                'organization': 'Test Organization',
                'password_hash': password_hash,
                'role': 'user',
                'status': 'active'
            }
            
            # Insert user
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                json=test_user
            )
            
            if response.status_code == 201:
                print("✅ Test user created successfully!")
                print("📧 Email: test@bhashai.com")
                print("🔑 Password: testuser123")
                return True
            else:
                print(f"❌ Failed to create test user: {response.text}")
                return False
        else:
            print(f"❌ Failed to hash password: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Supabase Setup")
    print("=" * 50)
    
    success = test_supabase_connection()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 Supabase setup is working correctly!")
        print("\n📋 Next steps:")
        print("1. Test the signup page: http://localhost:3000/signup.html")
        print("2. Test user registration")
        print("3. Test login functionality")
        
        # Optionally create test user
        create_test = input("\nDo you want to create a test user? (y/n): ").lower().strip()
        if create_test == 'y':
            create_test_user()
    else:
        print("\n❌ Supabase setup failed. Please check the errors above.")
        print("\n💡 Make sure you've run the password migration SQL in Supabase Dashboard")
