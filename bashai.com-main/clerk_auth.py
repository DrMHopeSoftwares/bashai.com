#!/usr/bin/env python3
"""
Clerk Authentication Middleware Stub
This is a simplified version for development/testing
"""

from functools import wraps
from flask import g, request, jsonify
import os

class ClerkAuth:
    def __init__(self):
        self.secret_key = os.getenv('CLERK_SECRET_KEY', 'dev-key')
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app

# Create clerk_auth instance
clerk_auth = ClerkAuth()

def require_auth(f):
    """Decorator to require authentication - simplified for development"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For development, set a default user
        g.user_id = 'dev-user-123'
        g.enterprise_id = 'dev-enterprise-123'
        return f(*args, **kwargs)
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication - simplified for development"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For development, set a default user
        g.user_id = 'dev-user-123'
        g.enterprise_id = 'dev-enterprise-123'
        return f(*args, **kwargs)
    return decorated_function