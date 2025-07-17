#!/usr/bin/env python3
"""
Create admin user for testing admin dashboard redirect
"""

import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

def create_admin_user():
    """Create admin user in Supabase"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Supabase credentials not found")
        return
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Admin user data
    admin_email = "admin@bhashai.com"
    admin_password = "admin123456"
    
    try:
        print("👑 Creating admin user...")
        
        # Check if admin user already exists
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'email': f'eq.{admin_email}'}
        )
        
        if check_response.status_code == 200:
            existing = check_response.json()
            if existing:
                print(f"⚠️ Admin user '{admin_email}' already exists")
                
                # Update role to admin if not already
                user_id = existing[0]['id']
                if existing[0]['role'] != 'admin':
                    update_response = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/users",
                        headers=headers,
                        params={'id': f'eq.{user_id}'},
                        json={'role': 'admin'}
                    )
                    
                    if update_response.status_code == 204:
                        print(f"✅ Updated user role to admin")
                    else:
                        print(f"❌ Failed to update role: {update_response.text}")
                
                print(f"📧 Admin Email: {admin_email}")
                print(f"🔑 Admin Password: {admin_password}")
                return
        
        # Hash password using bcrypt
        import bcrypt
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create admin user
        admin_user = {
            'id': str(uuid.uuid4()),
            'email': admin_email,
            'name': 'Admin User',
            'organization': 'BhashAI Admin',
            'role': 'admin',
            'status': 'active',
            'password': password_hash,
            'enterprise_id': None
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            json=admin_user
        )
        
        if response.status_code == 201:
            print(f"✅ Admin user created successfully!")
            print(f"📧 Admin Email: {admin_email}")
            print(f"🔑 Admin Password: {admin_password}")
            print(f"👑 Role: admin")
            print(f"🎯 Login URL: http://127.0.0.1:3000/login")
            print(f"🏠 Admin Dashboard: http://127.0.0.1:3000/admin-dashboard.html")
        else:
            print(f"❌ Failed to create admin user: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_admin_user()
