# BhashAI Authentication System

## Overview
Simple role and status-based authentication system for BhashAI platform using JWT tokens and SQLite database.

## Features
- ✅ Role-based access control (Admin, Manager, User)
- ✅ Status-based user management (Active, Inactive, Pending)
- ✅ JWT token authentication
- ✅ Password hashing with bcrypt
- ✅ Web-based login/admin interface
- ✅ RESTful API endpoints

## User Roles

### Admin
- Full system access
- Can create/manage all users
- Can view all organizations
- Can change user status

### Manager
- Can manage users in their organization
- Can view users in their organization
- Can approve/deactivate users in their organization

### User
- Basic access to platform features
- Can view their own profile
- Limited to their organization's data

## User Status

### Active
- Full access to platform features
- Can login and use all assigned features

### Inactive
- Cannot login
- Account is temporarily disabled

### Pending
- Account created but not yet approved
- Cannot access platform features
- Requires admin/manager approval

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/register` - User registration
- `GET /api/auth/profile` - Get current user profile

### User Management (Admin/Manager only)
- `GET /api/auth/users` - List all users
- `PUT /api/auth/users/{user_id}/status` - Update user status

### Web Interface
- `/login` - Login page
- `/dashboard` - User dashboard
- `/admin/users` - User management (Admin/Manager only)

## Demo Users

### Admin User
- **Email:** admin@bhashai.com
- **Password:** admin123
- **Role:** admin
- **Status:** active

### Manager User
- **Email:** manager@bhashai.com
- **Password:** manager123
- **Role:** manager
- **Status:** active

### Regular User
- **Email:** user@bhashai.com
- **Password:** user123
- **Role:** user
- **Status:** active

### Pending User
- **Email:** pending@bhashai.com
- **Password:** pending123
- **Role:** user
- **Status:** pending

## Usage Examples

### Login via API
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bhashai.com","password":"admin123"}'
```

### Get Users List (Admin/Manager)
```bash
curl -X GET http://localhost:3000/api/auth/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update User Status
```bash
curl -X PUT http://localhost:3000/api/auth/users/user-002/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"active"}'
```

### Create New User
```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"newuser@company.com",
    "name":"New User",
    "organization":"Company Name",
    "password":"password123",
    "role":"user"
  }'
```

## Route Protection

### Using Decorators
```python
from auth import login_required, role_required, admin_required

@app.route('/protected')
@login_required
def protected_route():
    user = request.current_user
    return jsonify({'user': user})

@app.route('/admin-only')
@admin_required
def admin_only():
    return jsonify({'message': 'Admin access granted'})

@app.route('/manager-or-admin')
@role_required('admin', 'manager')
def manager_or_admin():
    return jsonify({'message': 'Manager or Admin access'})
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
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
);
```

## Security Features

1. **Password Hashing:** Uses bcrypt for secure password storage
2. **JWT Tokens:** Stateless authentication with 24-hour expiration
3. **Role Validation:** Server-side role checking on protected routes
4. **Status Checking:** Active status required for login
5. **Organization Isolation:** Managers can only manage their organization's users

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python main.py
```

3. Access the login page:
```
http://localhost:3000/login
```

## Files Structure

- `auth.py` - Core authentication logic and decorators
- `auth_routes.py` - Authentication API endpoints and web pages
- `users.db` - SQLite database (auto-created)
- `main.py` - Flask app with auth integration

## Testing

1. **Web Interface:** Visit `/login` and use demo credentials
2. **API Testing:** Use curl commands above
3. **Admin Panel:** Login as admin and visit `/admin/users`

## Next Steps

1. Add email verification for new registrations
2. Implement password reset functionality
3. Add session management
4. Uses local SQLite authentication (completed)
5. Add audit logging for user actions
