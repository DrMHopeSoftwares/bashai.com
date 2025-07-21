"""
Simple Authentication System for BhashAI
Role and Status based authentication with JWT tokens
"""

import jwt
import bcrypt
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, current_app
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AuthManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                organization TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'active',
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                enterprise_id TEXT,
                last_login TIMESTAMP,
                CHECK (role IN ('admin', 'user', 'manager')),
                CHECK (status IN ('active', 'inactive', 'pending'))
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        
        # Insert sample users if table is empty
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            sample_users = [
                ('admin-001', 'admin@bhashai.com', 'Admin User', 'BhashAI', 'admin', 'active', self.hash_password('admin123')),
                ('manager-001', 'manager@bhashai.com', 'Manager User', 'BhashAI', 'manager', 'active', self.hash_password('manager123')),
                ('user-001', 'user@bhashai.com', 'Regular User', 'BhashAI', 'user', 'active', self.hash_password('user123')),
                ('user-002', 'pending@bhashai.com', 'Pending User', 'BhashAI', 'user', 'pending', self.hash_password('pending123'))
            ]
            
            cursor.executemany('''
                INSERT INTO users (id, email, name, organization, role, status, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', sample_users)
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, user_data):
        """Generate JWT token for user"""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'name': user_data.get('name', ''),
            'organization': user_data.get('organization', ''),
            'role': user_data['role'],
            'status': user_data['status'],
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
        """Authenticate user with email and password - Updated for Supabase"""
        import requests

        # Supabase configuration
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return None, "Database configuration error"

        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }

        try:
            # Get user from Supabase
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                params={'email': f'eq.{email}', 'select': '*'}
            )

            if response.status_code != 200:
                return None, "Database connection error"

            users = response.json()
            if not users or len(users) == 0:
                return None, "Invalid email or password"

            user = users[0]

            # Check password using bcrypt verification
            stored_password = user.get('password')
            if not stored_password:
                return None, "Password not set for this account"

            # Verify password using bcrypt
            if not self.verify_password(password, stored_password):
                return None, "Invalid email or password"

            # Check status
            if user['status'] != 'active':
                return None, f"Account is {user['status']}"

            # Remove password from returned data
            user.pop('password', None)

            return user, None

        except Exception as e:
            return None, f"Authentication failed: {str(e)}"
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def create_user(self, email, name, organization, password, role='user', status='active'):
        """Create new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return None, "Email already exists"
        
        user_id = f"{role}-{secrets.token_hex(8)}"
        password_hash = self.hash_password(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (id, email, name, organization, role, status, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, email, name, organization, role, status, password_hash))
            
            conn.commit()
            conn.close()
            return user_id, None
        except Exception as e:
            conn.close()
            return None, str(e)

    def register_user(self, email, password, name, organization, role='user', status='active', enterprise_id=None):
        """Register new user and return user data - Updated for Supabase"""
        import requests
        import uuid

        # Supabase configuration
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return None, "Database configuration error"

        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }

        try:
            # Check if user already exists
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                params={'email': f'eq.{email}', 'select': 'id'}
            )

            if response.status_code == 200 and response.json():
                return None, "User with this email already exists"

            # Hash the password before storing
            password_hash = self.hash_password(password)

            # Create user data
            user_data = {
                'id': str(uuid.uuid4()),
                'email': email,
                'name': name,
                'organization': organization,
                'password': password_hash,  # Store hashed password
                'role': role,
                'status': status,
                'enterprise_id': enterprise_id
            }

            # Insert user into Supabase
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                json=user_data
            )

            if response.status_code == 201:
                # Remove password from returned data
                user_data.pop('password', None)
                return user_data, None
            else:
                return None, f"Registration failed: {response.text}"

        except Exception as e:
            return None, str(e)

# Initialize global auth manager
# Use Supabase Auth Manager for production
try:
    # Check if Supabase environment variables are available
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        from auth_supabase import SupabaseAuthManager
        auth_manager = SupabaseAuthManager()
        print("✅ Using Supabase Auth Manager")
    else:
        print("⚠️ Supabase credentials not found, using SQLite Auth Manager")
        auth_manager = AuthManager()
except Exception as e:
    print(f"⚠️ Error loading Supabase Auth Manager: {e}")
    print("⚠️ Falling back to SQLite Auth Manager")
    auth_manager = AuthManager()

# Decorators for route protection
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            token = request.cookies.get('auth_token')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_data = auth_manager.verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        if user_data['status'] != 'active':
            return jsonify({'error': f'Account is {user_data["status"]}'}), 403
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if request.current_user['role'] not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return role_required('admin')(f)

def manager_or_admin_required(f):
    """Decorator to require manager or admin role"""
    return role_required('admin', 'manager')(f)
