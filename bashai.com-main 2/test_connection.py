#!/usr/bin/env python3
"""
Test script to verify Supabase connection and data
"""

import os
import requests
from dotenv import load_dotenv

def test_supabase_connection():
    """Test basic Supabase connection"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    print(f"🔗 Testing connection to: {supabase_url}")
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test enterprises table
        print("\n📊 Testing enterprises table...")
        response = requests.get(f"{supabase_url}/rest/v1/enterprises", headers=headers, timeout=10)
        
        if response.status_code == 200:
            enterprises = response.json()
            print(f"✅ Enterprises table accessible - Found {len(enterprises)} records")
            
            if enterprises:
                print("Sample enterprise:")
                for key, value in enterprises[0].items():
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Enterprises table error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Test users table
        print("\n👥 Testing users table...")
        response = requests.get(f"{supabase_url}/rest/v1/users", headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Users table accessible - Found {len(users)} records")
            
            if users:
                print("Sample user:")
                for key, value in users[0].items():
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Users table error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Test authentication endpoint
        print("\n🔐 Testing authentication endpoint...")
        auth_response = requests.get(f"{supabase_url}/auth/v1/settings", 
                                   headers={'apikey': supabase_key}, timeout=10)
        
        if auth_response.status_code == 200:
            print("✅ Authentication endpoint accessible")
        else:
            print(f"⚠️  Authentication endpoint returned: {auth_response.status_code}")
        
        print("\n🎉 All tests passed! Your Supabase setup is working correctly.")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_admin_user():
    """Test if admin user exists in the database"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        return False
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("\n🔍 Checking for admin user...")
        response = requests.get(
            f"{supabase_url}/rest/v1/users?email=eq.admin@drmhope.com", 
            headers=headers, 
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            if users and len(users) > 0:
                user = users[0]
                print(f"✅ Admin user found: {user['name']} ({user['email']})")
                print(f"   Role: {user['role']}")
                print(f"   Status: {user['status']}")
                return True
            else:
                print("❌ Admin user not found in database")
                print("   Please run the sample_data.sql script")
                return False
        else:
            print(f"❌ Error checking admin user: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")
        return False

def main():
    print("=" * 60)
    print(" DrM Hope SaaS Platform - Connection Test")
    print("=" * 60)
    
    # Test basic connection
    if not test_supabase_connection():
        print("\n❌ Connection test failed. Please check your .env file and Supabase setup.")
        return
    
    # Test admin user
    if not test_admin_user():
        print("\n⚠️  Admin user not found. Please:")
        print("1. Create admin user in Supabase Auth (admin@drmhope.com)")
        print("2. Run the sample_data.sql script")
        return
    
    print("\n🚀 Everything looks good! You can now run the application:")
    print("   python main.py")

if __name__ == "__main__":
    main()
