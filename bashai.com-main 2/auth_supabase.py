"""
Supabase Authentication System for BhashAI
Role and Status based authentication with JWT tokens and encrypted passwords
"""

import jwt
import bcrypt
import os
import requests
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, current_app
import secrets

class SupabaseAuthManager:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        
        self.headers = {
            'apikey': self.supabase_service_key,
            'Authorization': f'Bearer {self.supabase_service_key}',
            'Content-Type': 'application/json'
        }
    
    def hash_password(self, password):
        """Hash password using bcrypt (compatible with Supabase function)"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    def verify_password_local(self, password, hashed):
        """Verify password against hash locally"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False
    
    def verify_password_supabase(self, password, email):
        """Verify password using Supabase function"""
        try:
            # Get user's password hash first
            response = requests.get(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'email': f'eq.{email}', 'select': 'password'}
            )

            if response.status_code == 200:
                users = response.json()
                if users and len(users) > 0:
                    password_hash = users[0].get('password')
                    if password_hash:
                        # Use Supabase function to verify password
                        verify_response = requests.post(
                            f"{self.supabase_url}/rest/v1/rpc/verify_password",
                            headers=self.headers,
                            json={'password': password, 'hash': password_hash}
                        )
                        
                        if verify_response.status_code == 200:
                            return verify_response.json()
            
            return False
        except Exception as e:
            print(f"Error verifying password with Supabase: {e}")
            return False
    
    def generate_token(self, user_data):
        """Generate JWT token for user"""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'role': user_data['role'],
            'status': user_data['status'],
            'organization': user_data.get('organization', ''),
            'enterprise_id': user_data.get('enterprise_id'),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate_user(self, email, password):
        """Authenticate user with email and password"""
        try:
            # Get user from Supabase
            response = requests.get(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'email': f'eq.{email}', 'select': '*'}
            )
            
            if response.status_code != 200:
                return None, "Database connection error"
            
            users = response.json()
            if not users or len(users) == 0:
                return None, "Invalid email or password"
            
            user = users[0]
            
            # Check user status
            if user['status'] != 'active':
                return None, f"Account is {user['status']}. Please contact administrator."
            
            # Verify password
            password_hash = user.get('password')
            if not password_hash:
                return None, "Password not set for this account"
            
            # Try local verification first (faster)
            password_valid = self.verify_password_local(password, password_hash)
            
            if not password_valid:
                return None, "Invalid email or password"
            
            # Update last login
            self.update_last_login(user['id'])
            
            return user, None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None, "Authentication failed"
    
    def register_user(self, email, password, name, organization, role='user', status='active', enterprise_id=None):
        """Register a new user"""
        try:
            # Check if user already exists
            response = requests.get(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'email': f'eq.{email}', 'select': 'id'}
            )
            
            if response.status_code == 200 and response.json():
                return None, "User with this email already exists"
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user data
            user_data = {
                'id': str(uuid.uuid4()),
                'email': email,
                'name': name,
                'organization': organization,
                'password': password_hash,  # Column name is 'password' not 'password_hash'
                'role': role,
                'status': status,
                'enterprise_id': enterprise_id
            }
            
            # Insert user into Supabase
            response = requests.post(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                json=user_data
            )
            
            if response.status_code == 201:
                # Remove password from returned data
                user_data.pop('password', None)
                return user_data, None
            else:
                return None, f"Registration failed: {response.text}"
                
        except Exception as e:
            print(f"Registration error: {e}")
            return None, "Registration failed"
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        try:
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'id': f'eq.{user_id}'},
                json={'updated_at': datetime.utcnow().isoformat()}
            )
            return response.status_code == 204
        except:
            return False
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'id': f'eq.{user_id}', 'select': '*'}
            )
            
            if response.status_code == 200:
                users = response.json()
                if users and len(users) > 0:
                    user = users[0]
                    user.pop('password', None)  # Remove password hash
                    return user
            return None
        except:
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'email': f'eq.{email}', 'select': '*'}
            )
            
            if response.status_code == 200:
                users = response.json()
                if users and len(users) > 0:
                    user = users[0]
                    user.pop('password', None)  # Remove password hash
                    return user
            return None
        except:
            return None
    
    def update_user_status(self, user_id, status):
        """Update user status"""
        try:
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'id': f'eq.{user_id}'},
                json={'status': status, 'updated_at': datetime.utcnow().isoformat()}
            )
            return response.status_code == 204
        except:
            return False
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        try:
            password_hash = self.hash_password(new_password)
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/users",
                headers=self.headers,
                params={'id': f'eq.{user_id}'},
                json={'password': password_hash, 'updated_at': datetime.utcnow().isoformat()}
            )
            return response.status_code == 204
        except:
            return False

# Initialize auth manager
auth_manager = SupabaseAuthManager()

# Decorators for route protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
        else:
            token = request.cookies.get('auth_token')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_data = auth_manager.verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        if user_data['status'] != 'active':
            return jsonify({'error': 'Account is not active'}), 403
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if request.current_user['role'] not in required_roles:
                return jsonify({'error': f'Access denied. Required roles: {required_roles}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
