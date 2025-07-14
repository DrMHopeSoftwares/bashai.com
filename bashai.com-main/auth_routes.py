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
            'token': token
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

@auth_bp.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    user_data = auth_manager.get_user_by_id(request.current_user['user_id'])
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    # Remove sensitive data
    user_data.pop('password_hash', None)
    
    return jsonify({
        'success': True,
        'user': user_data
    })

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
            font-family: 'Inter', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 450px;
            width: 100%;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #1e293b;
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 700;
        }
        .header p {
            color: #64748b;
            margin: 0;
            font-size: 16px;
        }
        .tabs {
            display: flex;
            margin-bottom: 30px;
            background: #f8fafc;
            border-radius: 8px;
            padding: 4px;
        }
        .tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .tab.active {
            background: #059669;
            color: white;
        }
        .tab:not(.active) {
            color: #64748b;
        }
        .tab:not(.active):hover {
            background: #e2e8f0;
        }
        .form-container {
            position: relative;
            overflow: hidden;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #374151;
        }
        input {
            width: 100%;
            padding: 14px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input:focus {
            outline: none;
            border-color: #059669;
        }
        .btn-primary {
            width: 100%;
            padding: 14px;
            background: #059669;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: background 0.3s ease;
        }
        .btn-primary:hover {
            background: #047857;
        }
        .btn-secondary {
            width: 100%;
            padding: 14px;
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: background 0.3s ease;
        }
        .btn-secondary:hover {
            background: #4f46e5;
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
        .demo-users {
            margin-top: 25px;
            padding: 20px;
            background: #f8fafc;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
        }
        .demo-users h4 {
            margin-top: 0;
            margin-bottom: 15px;
            color: #374151;
            font-size: 16px;
        }
        .demo-user {
            margin: 8px 0;
            padding: 10px;
            background: white;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid #e5e7eb;
        }
        .demo-user:hover {
            background: #f3f4f6;
            border-color: #059669;
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
        .form-slide {
            transition: transform 0.3s ease;
        }
        .register-form {
            transform: translateX(100%);
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
        }
        .register-form.active {
            transform: translateX(0);
        }
        .login-form.register-active {
            transform: translateX(-100%);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BhashAI</h1>
            <p>Enterprise AI Voice Platform</p>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showLogin()">Login</div>
            <div class="tab" onclick="showRegister()">Register</div>
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

                <div class="demo-users">
                    <h4>Quick Demo Login:</h4>
                    <div class="demo-user" onclick="fillLoginCredentials('admin@bhashai.com', 'admin123')">
                        <strong>👑 Admin:</strong> admin@bhashai.com / admin123
                    </div>
                    <div class="demo-user" onclick="fillLoginCredentials('manager@bhashai.com', 'manager123')">
                        <strong>👔 Manager:</strong> manager@bhashai.com / manager123
                    </div>
                    <div class="demo-user" onclick="fillLoginCredentials('user@bhashai.com', 'user123')">
                        <strong>👤 User:</strong> user@bhashai.com / user123
                    </div>
                </div>
            </div>

            <!-- Register Form -->
            <div class="register-form form-slide">
                <form id="registerForm">
                    <div class="form-group">
                        <label for="regName">Full Name:</label>
                        <input type="text" id="regName" name="name" required placeholder="Enter your full name">
                    </div>
                    <div class="form-group">
                        <label for="regEmail">Email Address:</label>
                        <input type="email" id="regEmail" name="email" required placeholder="Enter your email">
                    </div>
                    <div class="form-group">
                        <label for="regOrganization">Organization:</label>
                        <input type="text" id="regOrganization" name="organization" required placeholder="Enter your organization">
                    </div>
                    <div class="form-group">
                        <label for="regPassword">Password:</label>
                        <input type="password" id="regPassword" name="password" required placeholder="Create a password">
                    </div>
                    <button type="submit" class="btn-secondary">Create Account</button>
                </form>
            </div>
        </div>

        <div id="message"></div>

        <div class="back-link">
            <a href="/">← Back to Home</a>
        </div>
    </div>

    <script>
        function showLogin() {
            document.querySelector('.tab.active').classList.remove('active');
            document.querySelectorAll('.tab')[0].classList.add('active');
            document.querySelector('.login-form').classList.remove('register-active');
            document.querySelector('.register-form').classList.remove('active');
        }

        function showRegister() {
            document.querySelector('.tab.active').classList.remove('active');
            document.querySelectorAll('.tab')[1].classList.add('active');
            document.querySelector('.login-form').classList.add('register-active');
            document.querySelector('.register-form').classList.add('active');
        }

        function fillLoginCredentials(email, password) {
            document.getElementById('email').value = email;
            document.getElementById('password').value = password;
        }

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
                    messageDiv.innerHTML = '<div class="success">✅ Login successful! Redirecting to dashboard...</div>';
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    messageDiv.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="error">❌ Login failed: ' + error.message + '</div>';
            }
        });

        // Register Form Handler
        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const organization = document.getElementById('regOrganization').value;
            const password = document.getElementById('regPassword').value;
            const messageDiv = document.getElementById('message');

            messageDiv.innerHTML = '<div class="success">Creating account...</div>';

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, organization, password })
                });

                const data = await response.json();

                if (data.success) {
                    messageDiv.innerHTML = '<div class="success">✅ Account created successfully! You can now login.</div>';
                    setTimeout(() => {
                        showLogin();
                        document.getElementById('email').value = email;
                        messageDiv.innerHTML = '';
                    }, 2000);
                } else {
                    messageDiv.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="error">❌ Registration failed: ' + error.message + '</div>';
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
