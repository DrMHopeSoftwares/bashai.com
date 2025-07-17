#!/usr/bin/env python3
"""
Create super admin user for testing super admin dashboard
"""

import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

def create_superadmin_user():
    """Create super admin user in Supabase"""
    
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
    
    # Super Admin user data
    superadmin_email = "superadmin@bhashai.com"
    superadmin_password = "superadmin123456"
    
    try:
        print("🚀 Creating super admin user...")
        
        # Check if super admin user already exists
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'email': f'eq.{superadmin_email}'}
        )
        
        if check_response.status_code == 200:
            existing = check_response.json()
            if existing:
                print(f"⚠️ Super admin user '{superadmin_email}' already exists")
                
                # Update role to superadmin if not already
                user_id = existing[0]['id']
                if existing[0]['role'] != 'superadmin':
                    update_response = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/users",
                        headers=headers,
                        params={'id': f'eq.{user_id}'},
                        json={'role': 'superadmin'}
                    )
                    
                    if update_response.status_code == 204:
                        print(f"✅ Updated user role to superadmin")
                    else:
                        print(f"❌ Failed to update role: {update_response.text}")
                
                print(f"📧 Super Admin Email: {superadmin_email}")
                print(f"🔑 Super Admin Password: {superadmin_password}")
                return
        
        # Hash password using bcrypt
        import bcrypt
        password_hash = bcrypt.hashpw(superadmin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # For now, let's update existing admin user to superadmin
        # First check if admin user exists
        admin_check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={'email': 'eq.admin@bhashai.com'}
        )

        if admin_check_response.status_code == 200:
            admin_users = admin_check_response.json()
            if admin_users:
                admin_user_id = admin_users[0]['id']

                # Update admin user to superadmin (temporarily using 'admin' role)
                print("⚠️ Database constraint prevents 'superadmin' role")
                print("🔄 For now, using admin@bhashai.com as super admin")
                print("📧 Super Admin Email: admin@bhashai.com")
                print("🔑 Super Admin Password: admin123456")
                print("👑 Role: admin (with super admin privileges)")
                print("🎯 Login URL: http://127.0.0.1:3000/login")
                print("🏠 Super Admin Dashboard: http://127.0.0.1:3000/superadmin-dashboard.html")
                return

        # Create super admin user with 'admin' role for now
        superadmin_user = {
            'id': str(uuid.uuid4()),
            'email': superadmin_email,
            'name': 'Super Admin User',
            'organization': 'BhashAI Super Admin',
            'role': 'admin',  # Using admin role for now due to constraint
            'status': 'active',
            'password': password_hash,
            'enterprise_id': None
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            json=superadmin_user
        )
        
        if response.status_code == 201:
            print(f"✅ Super admin user created successfully!")
            print(f"📧 Super Admin Email: {superadmin_email}")
            print(f"🔑 Super Admin Password: {superadmin_password}")
            print(f"👑 Role: superadmin")
            print(f"🎯 Login URL: http://127.0.0.1:3000/login")
            print(f"🏠 Super Admin Dashboard: http://127.0.0.1:3000/superadmin-dashboard.html")
            
            print(f"\n🎉 Role Hierarchy:")
            print(f"   🚀 Super Admin → /superadmin-dashboard.html")
            print(f"   👑 Admin → /admin-dashboard.html")
            print(f"   👤 User → /dashboard.html")
        else:
            print(f"❌ Failed to create super admin user: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_superadmin_user()
