"""
Authentication Routes for BhashAI Platform
Login, Logout, Register, Profile management
"""

from flask import Blueprint, request, jsonify, make_response, render_template_string
from auth import auth_manager, login_required, admin_required, role_required
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        user_data, error = auth_manager.authenticate_user(email, password)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Generate token
        token = auth_manager.generate_token(user_data)

        # Determine redirect URL based on user role
        redirect_url = '/dashboard.html'  # Default for user role
        if user_data['role'] == 'superadmin':
            redirect_url = '/superadmin-dashboard.html'
        elif user_data['role'] == 'admin':
            redirect_url = '/admin-dashboard.html'
        elif user_data['role'] == 'manager':
            redirect_url = '/dashboard.html'  # Managers use regular dashboard

        # Create response
        response = make_response(jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'role': user_data['role'],
                'status': user_data['status'],
                'organization': user_data['organization']
            },
            'token': token,
            'redirect_url': redirect_url
        }))
        
        # Set HTTP-only cookie for web clients
        response.set_cookie('auth_token', token, httponly=True, secure=False, max_age=86400)
        
        return response
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint"""
    response = make_response(jsonify({'success': True, 'message': 'Logged out successfully'}))
    response.set_cookie('auth_token', '', expires=0)
    return response

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')
        organization = data.get('organization')
        password = data.get('password')
        role = data.get('role', 'user')

        if not all([email, name, organization, password]):
            return jsonify({'error': 'All fields required'}), 400

        # Only admin can create admin/manager users
        if role in ['admin', 'manager']:
            token = request.headers.get('Authorization') or request.cookies.get('auth_token')
            if token and token.startswith('Bearer '):
                token = token[7:]

            if not token:
                return jsonify({'error': 'Admin access required to create admin/manager users'}), 403

            user_data = auth_manager.verify_token(token)
            if not user_data or user_data['role'] != 'admin':
                return jsonify({'error': 'Admin access required'}), 403

        user_id, error = auth_manager.create_user(email, name, organization, password, role)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user_id': user_id
        }), 201

    except Exception as e:
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/api/public/enterprises', methods=['GET'])
def get_public_enterprises():
    """Get all enterprises for signup dropdown"""
    try:
        import requests
        import os

        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            # Fallback to hardcoded enterprise types
            return jsonify({
                'success': True,
                'enterprises': [
                    {'id': 'healthcare', 'name': 'Healthcare / Hospital', 'type': 'healthcare'},
                    {'id': 'clinic', 'name': 'Clinic / Medical Center', 'type': 'clinic'},
                    {'id': 'diagnostic', 'name': 'Diagnostic Center', 'type': 'diagnostic'},
                    {'id': 'pharmacy', 'name': 'Pharmacy', 'type': 'pharmacy'},
                    {'id': 'other', 'name': 'Other', 'type': 'other'}
                ]
            })

        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json'
        }

        # Get enterprises from Supabase
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/enterprises",
            headers=headers,
            params={'select': 'id,name,type', 'status': 'eq.active'}
        )

        if response.status_code == 200:
            enterprises = response.json()
            return jsonify({
                'success': True,
                'enterprises': enterprises
            })
        else:
            # Fallback to hardcoded types
            return jsonify({
                'success': True,
                'enterprises': [
                    {'id': 'healthcare', 'name': 'Healthcare / Hospital', 'type': 'healthcare'},
                    {'id': 'clinic', 'name': 'Clinic / Medical Center', 'type': 'clinic'},
                    {'id': 'diagnostic', 'name': 'Diagnostic Center', 'type': 'diagnostic'},
                    {'id': 'pharmacy', 'name': 'Pharmacy', 'type': 'pharmacy'},
                    {'id': 'other', 'name': 'Other', 'type': 'other'}
                ]
            })

    except Exception as e:
        print(f"Get enterprises error: {e}")
        # Fallback to hardcoded types
        return jsonify({
            'success': True,
            'enterprises': [
                {'id': 'healthcare', 'name': 'Healthcare / Hospital', 'type': 'healthcare'},
                {'id': 'clinic', 'name': 'Clinic / Medical Center', 'type': 'clinic'},
                {'id': 'diagnostic', 'name': 'Diagnostic Center', 'type': 'diagnostic'},
                {'id': 'pharmacy', 'name': 'Pharmacy', 'type': 'pharmacy'},
                {'id': 'other', 'name': 'Other', 'type': 'other'}
            ]
        })

@auth_bp.route('/api/public/signup', methods=['POST'])
def public_signup():
    """Public signup endpoint for enterprise registration"""
    try:
        data = request.get_json()

        # Extract data from signup form
        enterprise_name = data.get('name')  # Enterprise name
        owner_name = data.get('owner_name')  # Owner's name
        email = data.get('contact_email')
        phone = data.get('contact_phone')
        password = data.get('password')
        enterprise_type = data.get('type')
        enterprise_id = data.get('enterprise_id')  # Selected enterprise ID

        if not all([enterprise_name, owner_name, email, password]):
            return jsonify({'error': 'Enterprise name, owner name, email, and password are required'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        # Create user with user role for new registrations
        user_data, error = auth_manager.register_user(
            email=email,
            password=password,
            name=owner_name,
            organization=enterprise_name,
            role='user',  # New registrations get user role
            status='active',
            enterprise_id=enterprise_id  # Pass enterprise_id to register_user
        )

        if error:
            return jsonify({'success': False, 'message': error}), 400

        # Generate token for immediate login
        token = auth_manager.generate_token(user_data)

        # Create response
        response = make_response(jsonify({
            'success': True,
            'message': f'Enterprise "{enterprise_name}" created successfully!',
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'name': user_data['name'],
                'role': user_data['role'],
                'organization': user_data['organization'],
                'enterprise_id': user_data.get('enterprise_id')
            },
            'token': token
        }))

        # Set HTTP-only cookie for web clients
        response.set_cookie('auth_token', token, httponly=True, secure=False, max_age=86400)

        return response

    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        user_data = request.current_user

        # Return the JWT payload directly (it already has all needed fields)
        profile_response = {
            'success': True,
            'user': {
                'id': user_data.get('user_id'),
                'email': user_data.get('email'),
                'name': user_data.get('name', ''),
                'role': user_data.get('role'),
                'status': user_data.get('status'),
                'organization': user_data.get('organization', ''),
                'enterprise_id': user_data.get('enterprise_id')
            }
        }

        # Also add enterprise_id at root level for easier access
        profile_response['enterprise_id'] = user_data.get('enterprise_id')

        return jsonify(profile_response)

    except Exception as e:
        print(f"Profile error: {e}")
        print(f"User data keys: {list(user_data.keys()) if 'user_data' in locals() else 'No user_data'}")
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500



@auth_bp.route('/api/auth/users', methods=['GET'])
@role_required('admin', 'manager')
def list_users():
    """List all users (admin/manager only)"""
    import sqlite3
    
    conn = sqlite3.connect(auth_manager.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Managers can only see users in their organization
    if request.current_user['role'] == 'manager':
        cursor.execute('''
            SELECT id, email, name, organization, role, status, created_at, last_login
            FROM users WHERE organization = ?
            ORDER BY created_at DESC
        ''', (request.current_user.get('organization'),))
    else:
        cursor.execute('''
            SELECT id, email, name, organization, role, status, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'users': users
    })

@auth_bp.route('/api/auth/users/<user_id>/status', methods=['PUT'])
@role_required('admin', 'manager')
def update_user_status(user_id):
    """Update user status (admin/manager only)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['active', 'inactive', 'pending']:
            return jsonify({'error': 'Invalid status'}), 400
        
        import sqlite3
        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()
        
        # Check if user exists and get current data
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Managers can only update users in their organization
        if request.current_user['role'] == 'manager':
            cursor.execute('SELECT organization FROM users WHERE id = ?', (user_id,))
            user_org = cursor.fetchone()[0]
            if user_org != request.current_user.get('organization'):
                conn.close()
                return jsonify({'error': 'Cannot update user from different organization'}), 403
        
        # Update status
        cursor.execute('UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                      (new_status, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'User status updated to {new_status}'
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to update status', 'details': str(e)}), 500

@auth_bp.route('/login')
def login_page():
    """Enhanced login page with register option"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>BhashAI - Login</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #ff6b9d 0%, #c44569 50%, #6c5ce7 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 420px;
            width: 100%;
            background: white;
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }
        .logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            border-radius: 20px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            color: white;
            font-weight: bold;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #6c5ce7;
            margin: 0 0 8px 0;
            font-size: 28px;
            font-weight: 700;
        }
        .header p {
            color: #74b9ff;
            margin: 0;
            font-size: 16px;
            font-weight: 500;
        }

        .form-container {
            position: relative;
            overflow: hidden;
            border-radius: 16px;
        }
        .form-group {
            margin-bottom: 24px;
        }
        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #2d3436;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        input {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid #e8ecff;
            border-radius: 16px;
            box-sizing: border-box;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #f8f9ff;
            color: #2d3436;
        }
        input:focus {
            outline: none;
            border-color: #6c5ce7;
            background: white;
            box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.1);
            transform: translateY(-2px);
        }
        input::placeholder {
            color: #b2bec3;
        }
        .btn-primary {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            color: white;
            border: none;
            border-radius: 16px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 700;
            transition: all 0.3s ease;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(108, 92, 231, 0.4);
        }
        .btn-secondary {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            border: none;
            border-radius: 16px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 700;
            transition: all 0.3s ease;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn-secondary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(116, 185, 255, 0.4);
        }
        .error {
            color: #dc2626;
            margin-top: 15px;
            padding: 12px;
            background: #fef2f2;
            border-radius: 6px;
            border-left: 4px solid #dc2626;
        }
        .success {
            color: #059669;
            margin-top: 15px;
            padding: 12px;
            background: #f0fdf4;
            border-radius: 6px;
            border-left: 4px solid #059669;
        }

        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #059669;
            text-decoration: none;
            font-weight: 500;
        }
        .back-link a:hover {
            text-decoration: underline;
        }

    </style>
</head>
<body>
    <div class="container">
        <div class="logo">B</div>
        <div class="header">
            <h1>BhashAI</h1>
            <p>Start Your Free Trial</p>
        </div>



        <div class="form-container">
            <!-- Login Form -->
            <div class="login-form form-slide">
                <form id="loginForm">
                    <div class="form-group">
                        <label for="email">Email Address:</label>
                        <input type="email" id="email" name="email" required placeholder="Enter your email">
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required placeholder="Enter your password">
                    </div>
                    <button type="submit" class="btn-primary">Login to Dashboard</button>
                </form>

                <!-- New Registration Link -->
                <div class="register-link" style="text-align: center; margin-top: 20px;">
                    <p style="color: #636e72; margin: 0;">Don't have an account?
                        <a href="/signup.html" style="color: #6c5ce7; text-decoration: none; font-weight: 600;">Create New Account</a>
                    </p>
                </div>

            </div>


        </div>

        <div id="message"></div>



        <div class="back-link">
            <a href="/">← Back to Home</a>
        </div>
    </div>

    <script>






        // Login Form Handler
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');

            messageDiv.innerHTML = '<div class="success">Logging in...</div>';

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (data.success) {
                    messageDiv.innerHTML = '<div class="success">✅ Login successful! Redirecting...</div>';

                    // Store token in localStorage
                    if (data.token) {
                        localStorage.setItem('auth_token', data.token);

                        // Use redirect_url from response or default to dashboard
                        const redirectUrl = data.redirect_url || '/dashboard.html';

                        // Show appropriate message based on redirect
                        if (redirectUrl.includes('admin-dashboard')) {
                            messageDiv.innerHTML = '<div class="success">✅ Admin login successful! Redirecting to admin dashboard...</div>';
                        } else {
                            messageDiv.innerHTML = '<div class="success">✅ Login successful! Redirecting to dashboard...</div>';
                        }

                        // Immediate redirect after token storage
                        setTimeout(() => {
                            window.location.href = redirectUrl;
                        }, 2000);
                    } else {
                        messageDiv.innerHTML = '<div class="error">❌ Login failed: No token received</div>';
                    }
                } else {
                    messageDiv.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                }
            } catch (error) {
                console.error('Login error:', error);
                messageDiv.innerHTML = '<div class="error">❌ Login failed: ' + error.message + '</div>';
            }
        });


    </script>
</body>
</html>
    ''')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Simple dashboard page"""
    user = request.current_user
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>BhashAI - Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .user-info { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .role-badge { padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .role-admin { background: #dc3545; color: white; }
        .role-manager { background: #ffc107; color: black; }
        .role-user { background: #28a745; color: white; }
        .status-badge { padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .status-active { background: #28a745; color: white; }
        .status-pending { background: #ffc107; color: black; }
        .status-inactive { background: #6c757d; color: white; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .logout-btn { background: #dc3545; }
        .logout-btn:hover { background: #c82333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BhashAI Dashboard</h1>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        
        <div class="user-info">
            <h3>Welcome, {{ user.email }}!</h3>
            <p><strong>Name:</strong> {{ user.name }}</p>
            <p><strong>Organization:</strong> {{ user.organization }}</p>
            <p><strong>Role:</strong> <span class="role-badge role-{{ user.role }}">{{ user.role.upper() }}</span></p>
            <p><strong>Status:</strong> <span class="status-badge status-{{ user.status }}">{{ user.status.upper() }}</span></p>
        </div>
        
        <div class="actions">
            <button onclick="window.location.href='/'">Go to Main Site</button>
            {% if user.role in ['admin', 'manager'] %}
            <button onclick="window.location.href='/admin/users'">Manage Users</button>
            {% endif %}
        </div>
    </div>

    <script>
        async function logout() {
            try {
                const response = await fetch('/api/auth/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = '/login';
                }
            } catch (error) {
                alert('Logout failed');
            }
        }
    </script>
</body>
</html>
    ''', user=user)

@auth_bp.route('/admin/users')
@role_required('admin', 'manager')
def admin_users():
    """Admin users management page"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>BhashAI - User Management</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
        .role-badge, .status-badge { padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .role-admin { background: #dc3545; color: white; }
        .role-manager { background: #ffc107; color: black; }
        .role-user { background: #28a745; color: white; }
        .status-active { background: #28a745; color: white; }
        .status-pending { background: #ffc107; color: black; }
        .status-inactive { background: #6c757d; color: white; }
        button { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 2px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        button:hover { opacity: 0.8; }
        .loading { text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>User Management</h1>
            <div>
                <button class="btn-primary" onclick="window.location.href='/dashboard'">Back to Dashboard</button>
                <button class="btn-success" onclick="showCreateUserForm()">Create User</button>
            </div>
        </div>

        <div id="usersList" class="loading">Loading users...</div>

        <!-- Create User Modal -->
        <div id="createUserModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 10px; width: 400px;">
                <h3>Create New User</h3>
                <form id="createUserForm">
                    <div style="margin-bottom: 15px;">
                        <label>Email:</label>
                        <input type="email" id="newEmail" required style="width: 100%; padding: 8px; margin-top: 5px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Name:</label>
                        <input type="text" id="newName" required style="width: 100%; padding: 8px; margin-top: 5px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Organization:</label>
                        <input type="text" id="newOrganization" required style="width: 100%; padding: 8px; margin-top: 5px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Password:</label>
                        <input type="password" id="newPassword" required style="width: 100%; padding: 8px; margin-top: 5px;">
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label>Role:</label>
                        <select id="newRole" style="width: 100%; padding: 8px; margin-top: 5px;">
                            <option value="user">User</option>
                            <option value="manager">Manager</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>
                    <div style="text-align: right;">
                        <button type="button" class="btn-secondary" onclick="hideCreateUserForm()">Cancel</button>
                        <button type="submit" class="btn-primary">Create User</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        let users = [];

        async function loadUsers() {
            try {
                const response = await fetch('/api/auth/users');
                const data = await response.json();

                if (data.success) {
                    users = data.users;
                    renderUsers();
                } else {
                    document.getElementById('usersList').innerHTML = '<div class="error">Failed to load users</div>';
                }
            } catch (error) {
                document.getElementById('usersList').innerHTML = '<div class="error">Error loading users: ' + error.message + '</div>';
            }
        }

        function renderUsers() {
            const html = `
                <table>
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Name</th>
                            <th>Organization</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Last Login</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td>${user.email}</td>
                                <td>${user.name}</td>
                                <td>${user.organization}</td>
                                <td><span class="role-badge role-${user.role}">${user.role.toUpperCase()}</span></td>
                                <td><span class="status-badge status-${user.status}">${user.status.toUpperCase()}</span></td>
                                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                                <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                                <td>
                                    ${user.status === 'active' ?
                                        `<button class="btn-warning" onclick="updateUserStatus('${user.id}', 'inactive')">Deactivate</button>` :
                                        `<button class="btn-success" onclick="updateUserStatus('${user.id}', 'active')">Activate</button>`
                                    }
                                    ${user.status === 'pending' ?
                                        `<button class="btn-success" onclick="updateUserStatus('${user.id}', 'active')">Approve</button>` : ''
                                    }
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;

            document.getElementById('usersList').innerHTML = html;
        }

        async function updateUserStatus(userId, newStatus) {
            try {
                const response = await fetch(`/api/auth/users/${userId}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });

                const data = await response.json();

                if (data.success) {
                    alert('User status updated successfully');
                    loadUsers(); // Reload users
                } else {
                    alert('Failed to update user status: ' + data.error);
                }
            } catch (error) {
                alert('Error updating user status: ' + error.message);
            }
        }

        function showCreateUserForm() {
            document.getElementById('createUserModal').style.display = 'block';
        }

        function hideCreateUserForm() {
            document.getElementById('createUserModal').style.display = 'none';
            document.getElementById('createUserForm').reset();
        }

        document.getElementById('createUserForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const userData = {
                email: document.getElementById('newEmail').value,
                name: document.getElementById('newName').value,
                organization: document.getElementById('newOrganization').value,
                password: document.getElementById('newPassword').value,
                role: document.getElementById('newRole').value
            };

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                const data = await response.json();

                if (data.success) {
                    alert('User created successfully');
                    hideCreateUserForm();
                    loadUsers(); // Reload users
                } else {
                    alert('Failed to create user: ' + data.error);
                }
            } catch (error) {
                alert('Error creating user: ' + error.message);
            }
        });

        // Load users on page load
        loadUsers();
    </script>
</body>
</html>
    ''')
