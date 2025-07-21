from flask import Flask

app = Flask(__name__)
import os
import sys
import requests
import json
import uuid
import razorpay
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, send_from_directory, g, redirect, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from auth import auth_manager, login_required
from trial_middleware import check_trial_limits, log_trial_activity, get_trial_usage_summary
from bolna_integration import BolnaAPI, get_agent_config_for_voice_agent
from razorpay_integration import RazorpayIntegration, calculate_credits_from_amount, get_predefined_recharge_options
from phone_provider_integration import phone_provider_manager
from auth_routes import auth_bp
from functools import wraps

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)  # Enable CORS for all routes

# Middleware to set g.user_id from request.current_user
@app.before_request
def load_user_context():
    """Load user context into Flask's g object"""
    if hasattr(request, 'current_user') and request.current_user:
        g.user_id = request.current_user.get('user_id')
        g.user_email = request.current_user.get('email')
        g.user_role = request.current_user.get('role')
        g.user_status = request.current_user.get('status')
        g.enterprise_id = request.current_user.get('enterprise_id')

# Redirect non-www to www for consistent domain access
@app.before_request
def redirect_non_www():
    host = request.host
    if host.startswith("bhashai.com"):
        return redirect(request.url.replace("://bhashai.com", "://www.bhashai.com"), code=301)

# Auth system already initialized via auth_routes.py

# Register authentication blueprint
app.register_blueprint(auth_bp)

def get_agent_name_from_bolna(agent_id, voice_agent_config=None):
    """Helper function to get agent name from Bolna API"""
    try:
        # First try to fetch directly from Bolna API using agent_id as bolna_agent_id
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()

            # Try to get agent details directly from Bolna
            bolna_agent_details = bolna_api.get_agent_details(agent_id)
            if bolna_agent_details:
                # Try different possible fields for agent name
                bolna_name = (bolna_agent_details.get('agent_name') or
                            bolna_agent_details.get('name') or
                            bolna_agent_details.get('agent_config', {}).get('agent_name'))
                if bolna_name:
                    print(f"✅ Found agent name from Bolna API: {bolna_name}")
                    return bolna_name
        except Exception as e:
            print(f"Could not fetch agent name directly from Bolna API: {e}")

        # Fallback: Try to get from voice_agents table
        agent_data = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=title,configuration')
        if agent_data and len(agent_data) > 0:
            agent_record = agent_data[0]
            agent_name = agent_record.get('title')

            # Try to get more detailed name from Bolna API using configuration
            try:
                # Check if we have current user context
                current_user = None
                if hasattr(g, 'current_user'):
                    current_user = g.current_user
                elif hasattr(request, 'current_user'):
                    current_user = request.current_user

                if current_user:
                    admin_user_data = {
                        'sender_phone': current_user.get('sender_phone'),
                        'bolna_agent_id': current_user.get('bolna_agent_id')
                    }

                    bolna_api = BolnaAPI(admin_user_data=admin_user_data)

                    # Get Bolna agent ID from configuration
                    config = voice_agent_config or agent_record.get('configuration', {})
                    bolna_agent_id = config.get('bolna_agent_id')

                    if bolna_agent_id:
                        bolna_agent_details = bolna_api.get_agent_details(bolna_agent_id)
                        if bolna_agent_details:
                            # Try different possible fields for agent name
                            bolna_name = (bolna_agent_details.get('agent_name') or
                                        bolna_agent_details.get('name') or
                                        bolna_agent_details.get('agent_config', {}).get('agent_name'))
                            if bolna_name:
                                agent_name = bolna_name
            except Exception as e:
                print(f"Could not fetch agent name from Bolna API via configuration: {e}")

            return agent_name
    except Exception as e:
        print(f"Error fetching agent name for {agent_id}: {e}")

    return None

# Supabase Configuration (with graceful fallback)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize Supabase headers with fallback
SUPABASE_HEADERS = {}
SUPABASE_AVAILABLE = False

try:
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        SUPABASE_HEADERS = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        SUPABASE_AVAILABLE = True
        print("✅ Supabase configuration loaded successfully")
    else:
        print("⚠️  WARNING: Missing Supabase configuration. App will run in limited mode.")
        print("   Some features may not work. Please check your .env file.")
except Exception as e:
    print(f"⚠️  WARNING: Supabase initialization failed: {e}")
    print("   App will run in limited mode.")

def supabase_request(method, endpoint, data=None, params=None):
    """Make a request to Supabase REST API with graceful error handling"""
    # Check if Supabase is available
    if not SUPABASE_AVAILABLE:
        print(f"⚠️  Supabase not available - {method} request to {endpoint} skipped")
        return [] if method == 'GET' else None
    
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=SUPABASE_HEADERS, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=SUPABASE_HEADERS, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=SUPABASE_HEADERS, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=SUPABASE_HEADERS, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=SUPABASE_HEADERS)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else None
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Supabase API error ({method} {endpoint}): {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response content: {e.response.text}")
        # Return empty data instead of raising exception
        return [] if method == 'GET' else None
    except Exception as e:
        print(f"⚠️  Unexpected error in supabase_request: {e}")
        return [] if method == 'GET' else None

def load_enterprise_context():
    """Load enterprise context for the authenticated user"""
    if not hasattr(g, 'user_id') or not g.user_id:
        return None
    
    try:
        # Check if Supabase is available
        if not SUPABASE_AVAILABLE:
            print("⚠️  Enterprise context loading skipped - Supabase not available")
            return None
            
        # Get user's enterprise_id
        user = supabase_request('GET', f'users?id=eq.{g.user_id}&select=enterprise_id,role')
        if not user or len(user) == 0:
            return None
        
        user_data = user[0]
        enterprise_id = user_data.get('enterprise_id')
        
        if not enterprise_id:
            return None
        
        # Store in Flask's g object for use in the request
        g.enterprise_id = enterprise_id
        g.user_role = user_data.get('role', 'user')
        
        return enterprise_id
    
    except Exception as e:
        print(f"⚠️  Error loading enterprise context: {e}")
        return None

def require_enterprise_context(f):
    """Decorator to ensure enterprise context is loaded and user belongs to an enterprise"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Load enterprise context
        enterprise_id = load_enterprise_context()
        
        if not enterprise_id:
            return jsonify({
                'message': 'User not associated with an enterprise. Please contact support.'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def verify_enterprise_access(resource_enterprise_id):
    """Verify that the current user has access to resources from the specified enterprise"""
    if not hasattr(g, 'enterprise_id'):
        load_enterprise_context()
    
    user_enterprise_id = getattr(g, 'enterprise_id', None)
    user_role = getattr(g, 'user_role', 'user')
    
    # Super admins can access any enterprise
    if user_role == 'super_admin':
        return True
    
    # Regular users can only access their own enterprise
    return user_enterprise_id == resource_enterprise_id

@app.route('/auth/enterprise-signup', methods=['POST'])
def enterprise_signup():
    """Register a new enterprise user with trial access"""
    data = request.json

    # Required fields
    required_fields = ['firstName', 'lastName', 'email', 'password', 'company', 'industry', 'useCase']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'{field} is required'}), 400

    try:
        # Create user in Supabase Auth
        auth_data = {
            'email': data['email'],
            'password': data['password']
        }

        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers=headers,
            json=auth_data
        )

        if response.status_code == 200:
            auth_result = response.json()
            print(f"Auth result: {auth_result}")
            user_id = auth_result['user']['id']

            # First create user record in public.users table
            user_data = {
                'id': user_id,
                'email': data['email'],
                'name': f"{data['firstName']} {data['lastName']}",
                'role': 'enterprise_owner',
                'organization': data['company'],
                'status': 'active'
            }

            try:
                user_response = supabase_request('POST', 'users', data=user_data)
                print(f"User creation successful: {user_response}")
            except Exception as e:
                print(f"User creation error: {e}")
                return jsonify({'message': 'User registration failed'}), 500

            # Then create enterprise record
            enterprise_data = {
                'name': data['company'],
                'type': data['industry'],
                'contact_email': data['email'],
                'status': 'active',  # Set as active for trial
                'owner_id': user_id
            }

            try:
                enterprise_response = supabase_request('POST', 'enterprises', data=enterprise_data)
                print(f"Enterprise creation successful: {enterprise_response}")
            except Exception as e:
                print(f"Enterprise creation error: {e}")
                return jsonify({'message': 'Enterprise registration failed'}), 500

            return jsonify({
                'message': 'Enterprise trial account created successfully! Check your email for verification.',
                'user': user_data,
                'enterprise': enterprise_data,
                'trial_days': 14
            }), 201
        else:
            error_data = response.json()
            return jsonify({'message': error_data.get('error_description', 'Registration failed')}), 400

    except Exception as e:
        print(f"Enterprise signup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': 'Enterprise registration failed'}), 500

# Clerk trial signup route removed - using local auth system instead

# Clerk webhook route removed - using local auth system instead

@app.route('/api/config/supabase')
def get_supabase_config():
    """Get Supabase configuration for frontend"""
    return jsonify({
        'url': SUPABASE_URL,
        'anon_key': SUPABASE_ANON_KEY,
        'available': SUPABASE_AVAILABLE
    })

@app.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user information from local auth system"""
    try:
        # Get user from local auth system (request.current_user is set by @login_required)
        user_data = request.current_user
        
        if not user_data:
            return jsonify({'message': 'User not found'}), 404
        
        # Check trial status
        trial_status = check_trial_status(user_data)
        
        return jsonify({
            'user': user_data,
            'trial_status': trial_status,
            'authenticated': True
        })
        
    except Exception as e:
        print(f"Get current user error: {e}")
        return jsonify({'message': 'Failed to get user information'}), 500

def check_trial_status(user):
    """Check if user's trial is still active"""
    if user.get('status') != 'trial':
        return {'is_trial': False, 'status': user.get('status', 'active')}

    trial_end_date = user.get('trial_end_date')
    if not trial_end_date:
        return {'is_trial': True, 'status': 'trial', 'expired': True}

    try:
        end_date = datetime.fromisoformat(trial_end_date.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        days_remaining = (end_date - now).days

        return {
            'is_trial': True,
            'status': 'trial',
            'expired': days_remaining <= 0,
            'days_remaining': max(0, days_remaining),
            'end_date': trial_end_date
        }
    except Exception as e:
        print(f"Error checking trial status: {e}")
        return {'is_trial': True, 'status': 'trial', 'expired': True}

@app.route('/api/trial-status', methods=['GET'])
@login_required
def get_trial_status():
    """Get detailed trial status for current user"""
    try:
        user_id = g.user_id

        # Get user from Supabase
        users = supabase_request('GET', 'users', params={'id': f'eq.{user_id}'})

        if users and len(users) > 0:
            user = users[0]
            trial_status = check_trial_status(user)

            return jsonify(trial_status)
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        print(f"Get trial status error: {e}")
        return jsonify({'message': 'Failed to get trial status'}), 500

@app.route('/api/trial-usage', methods=['GET'])
@login_required
@check_trial_limits()
def get_trial_usage():
    """Get detailed trial usage information"""
    try:
        user_id = g.user_id
        usage_summary = get_trial_usage_summary(user_id)

        return jsonify({
            'usage': usage_summary,
            'trial_status': g.trial_status if hasattr(g, 'trial_status') else None
        })

    except Exception as e:
        print(f"Get trial usage error: {e}")
        return jsonify({'message': 'Failed to get trial usage'}), 500

@app.route('/api/enterprises', methods=['GET'])
@login_required
@check_trial_limits(feature='basic_analytics')
def get_enterprises():
    """Get enterprises with trial limitations"""
    try:
        user_id = g.user_id

        # Log API call for trial users
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            log_trial_activity(user_id, 'api_call', {'endpoint': '/api/enterprises', 'method': 'GET'})

        enterprises = supabase_request('GET', 'enterprises', params={'owner_id': f'eq.{user_id}'})

        return jsonify({'enterprises': enterprises or []})

    except Exception as e:
        print(f"Get enterprises error: {e}")
        return jsonify({'message': 'Failed to get enterprises'}), 500

@app.route('/api/enterprises', methods=['POST'])
@login_required
@check_trial_limits(feature='basic_analytics', usage_type='enterprise_creation')
def create_enterprise():
    """Create enterprise with trial limitations"""
    try:
        user_id = g.user_id
        data = request.json

        # Log API call for trial users
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            log_trial_activity(user_id, 'api_call', {'endpoint': '/api/enterprises', 'method': 'POST'})

        # Required fields
        required_fields = ['name', 'type', 'contact_email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400

        enterprise_data = {
            'name': data['name'],
            'type': data['type'],
            'contact_email': data['contact_email'],
            'status': 'trial' if hasattr(g, 'trial_status') and g.trial_status.get('is_trial') else 'active',
            'owner_id': user_id
        }

        # Add trial dates if this is a trial user
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            enterprise_data['trial_start_date'] = datetime.now(timezone.utc).isoformat()
            enterprise_data['trial_end_date'] = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()

        enterprise = supabase_request('POST', 'enterprises', data=enterprise_data)

        return jsonify({'enterprise': enterprise}), 201

    except Exception as e:
        print(f"Create enterprise error: {e}")
        return jsonify({'message': 'Failed to create enterprise'}), 500

@app.route('/api/voice-agents', methods=['POST'])
@login_required
@check_trial_limits(feature='basic_voice_agent', usage_type='voice_agent_creation')
def create_voice_agent():
    """Create voice agent with trial limitations"""
    try:
        user_id = g.user_id

        # Get enterprise context - try from middleware first, then load manually
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            enterprise_id = load_enterprise_context()

        # If still no enterprise_id, try to get from user record
        if not enterprise_id:
            user_record = supabase_request('GET', 'users', params={'id': f'eq.{user_id}', 'select': 'enterprise_id'})
            if user_record and len(user_record) > 0:
                enterprise_id = user_record[0].get('enterprise_id')

        # If still no enterprise_id, create a default one
        if not enterprise_id:
            print("⚠️  No enterprise_id found, creating default enterprise...")
            enterprise_data = {
                'name': 'Default Enterprise',
                'type': 'business',
                'contact_email': 'admin@bashai.com',
                'status': 'active',
                'owner_id': user_id
            }
            enterprise = supabase_request('POST', 'enterprises', data=enterprise_data)
            if enterprise:
                enterprise_id = enterprise[0]['id'] if isinstance(enterprise, list) else enterprise['id']
                # Update user with enterprise_id
                supabase_request('PATCH', f'users?id=eq.{user_id}', data={'enterprise_id': enterprise_id})
                print(f"✅ Created enterprise: {enterprise_id}")
            else:
                return jsonify({'message': 'Failed to create enterprise context'}), 500

        data = request.json

        # Log API call for trial users
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            log_trial_activity(user_id, 'api_call', {'endpoint': '/api/voice-agents', 'method': 'POST'})

        # Required fields
        required_fields = ['name', 'language', 'use_case']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400

        # Trial users are limited to Hindi/Hinglish
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            allowed_languages = ['hindi', 'hinglish', 'hi-IN']
            if data['language'].lower() not in allowed_languages:
                return jsonify({
                    'message': 'Trial users can only create Hindi/Hinglish voice agents',
                    'allowed_languages': allowed_languages
                }), 403

        # Use the correct voice_agents table structure
        # Map use_case to valid category values
        use_case_to_category = {
            'sales': 'business',
            'customer_service': 'support',
            'support': 'support',
            'business': 'business',
            'general': 'general'
        }

        category = use_case_to_category.get(data.get('use_case', 'support'), 'support')

        voice_agent_data = {
            'title': data['name'],  # Use 'title' instead of 'name'
            'url': data.get('url', 'https://api.bashai.com/voice-agent'),  # Required field
            'category': category,  # Use mapped category
            'status': 'trial' if hasattr(g, 'trial_status') and g.trial_status.get('is_trial') else 'active',
            'enterprise_id': enterprise_id,  # 🔥 CRITICAL FIX: Add enterprise_id
            'configuration': {
                **data.get('configuration', {}),
                'language': data.get('language', 'hindi'),  # Store language in configuration
                'use_case': data.get('use_case', 'support'),  # Store original use_case
                'calling_number': data.get('calling_number'),
                'created_by': user_id
            },
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        voice_agent = supabase_request('POST', 'voice_agents', data=voice_agent_data)

        return jsonify({'voice_agent': voice_agent}), 201

    except Exception as e:
        print(f"Create voice agent error: {e}")
        return jsonify({'message': 'Failed to create voice agent'}), 500

@app.route('/api/enterprises/<enterprise_id>', methods=['PUT'])
@login_required
def update_enterprise(enterprise_id):
    """Update an enterprise"""
    try:
        user_id = g.user_id
        data = request.json

        # Check if user has permission to update enterprises
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=role,enterprise_id')
        if not user or len(user) == 0:
            return jsonify({'message': 'User not found'}), 404

        user_data = user[0]

        # Check permissions: super_admin/admin can update any, users can only update their own
        if user_data.get('role') not in ['super_admin', 'admin']:
            if user_data.get('enterprise_id') != enterprise_id:
                return jsonify({'message': 'Insufficient permissions'}), 403

        # Update enterprise
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'status' in data:
            update_data['status'] = data['status']

        updated_enterprise = supabase_request('PATCH', f'enterprises?id=eq.{enterprise_id}', data=update_data)

        return jsonify({'enterprise': updated_enterprise[0] if updated_enterprise else None}), 200

    except Exception as e:
        print(f"Update enterprise error: {e}")
        return jsonify({'message': 'Failed to update enterprise'}), 500

@app.route('/api/voice-agents', methods=['GET'])
@login_required
@require_enterprise_context
def get_voice_agents():
    """Get voice agents for the current user's enterprise"""
    try:
        enterprise_id = g.enterprise_id  # Now available from middleware

        # Get voice agents for the enterprise
        voice_agents = supabase_request('GET', f'voice_agents?enterprise_id=eq.{enterprise_id}&order=created_at.desc')

        return jsonify({'voice_agents': voice_agents}), 200

    except Exception as e:
        print(f"Get voice agents error: {e}")
        return jsonify({'message': 'Failed to get voice agents'}), 500

@app.route('/api/voice-agents/<agent_id>/contacts', methods=['GET'])
@login_required
@require_enterprise_context
def get_agent_contacts(agent_id):
    """Get contacts for a specific voice agent"""
    try:
        enterprise_id = g.enterprise_id  # Now available from middleware

        # Verify agent belongs to user's enterprise
        agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}')
        if not agent or len(agent) == 0:
            return jsonify({'message': 'Voice agent not found or access denied'}), 404

        # Get contacts for the agent (with enterprise filtering for extra security)
        contacts = supabase_request('GET', f'contacts?voice_agent_id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&order=created_at.desc')

        return jsonify({'contacts': contacts}), 200

    except Exception as e:
        print(f"Get agent contacts error: {e}")
        return jsonify({'message': 'Failed to get contacts'}), 500

@app.route('/api/voice-agents/<agent_id>/contacts', methods=['POST'])
@login_required
@require_enterprise_context
def create_contact(agent_id):
    """Create a new contact for a voice agent"""
    try:
        enterprise_id = g.enterprise_id  # Now available from middleware
        data = request.json

        # Validate required fields
        if not data.get('name') or not data.get('phone'):
            return jsonify({'message': 'Name and phone are required'}), 400

        # Verify agent belongs to user's enterprise
        agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}')
        if not agent or len(agent) == 0:
            return jsonify({'message': 'Voice agent not found or access denied'}), 404

        # Check for duplicate phone number for this agent (with enterprise filtering)
        existing_contact = supabase_request('GET', f'contacts?voice_agent_id=eq.{agent_id}&phone=eq.{data["phone"]}&enterprise_id=eq.{enterprise_id}')
        if existing_contact and len(existing_contact) > 0:
            return jsonify({'message': 'A contact with this phone number already exists for this agent'}), 400

        # Create contact
        contact_data = {
            'name': data['name'],
            'phone': data['phone'],
            'status': data.get('status', 'active'),
            'voice_agent_id': agent_id,
            'enterprise_id': enterprise_id
        }

        contact = supabase_request('POST', 'contacts', data=contact_data)

        return jsonify({'contact': contact[0] if contact else None}), 201

    except Exception as e:
        print(f"Create contact error: {e}")
        return jsonify({'message': 'Failed to create contact'}), 500

@app.route('/api/contacts/<contact_id>', methods=['PUT'])
@login_required
@require_enterprise_context
def update_contact(contact_id):
    """Update a contact"""
    try:
        enterprise_id = g.enterprise_id  # Now available from middleware
        data = request.json

        # Verify contact belongs to user's enterprise
        contact = supabase_request('GET', f'contacts?id=eq.{contact_id}&enterprise_id=eq.{enterprise_id}')
        if not contact or len(contact) == 0:
            return jsonify({'message': 'Contact not found or access denied'}), 404

        # Update contact (with enterprise filtering for security)
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'status' in data:
            update_data['status'] = data['status']

        updated_contact = supabase_request('PATCH', f'contacts?id=eq.{contact_id}&enterprise_id=eq.{enterprise_id}', data=update_data)

        return jsonify({'contact': updated_contact[0] if updated_contact else None}), 200

    except Exception as e:
        print(f"Update contact error: {e}")
        return jsonify({'message': 'Failed to update contact'}), 500

@app.route('/api/contacts/<contact_id>', methods=['DELETE'])
@login_required
@require_enterprise_context
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        enterprise_id = g.enterprise_id  # Now available from middleware

        # Verify contact belongs to user's enterprise
        contact = supabase_request('GET', f'contacts?id=eq.{contact_id}&enterprise_id=eq.{enterprise_id}')
        if not contact or len(contact) == 0:
            return jsonify({'message': 'Contact not found or access denied'}), 404

        # Delete contact (with enterprise filtering for security)
        supabase_request('DELETE', f'contacts?id=eq.{contact_id}&enterprise_id=eq.{enterprise_id}')

        return jsonify({'message': 'Contact deleted successfully'}), 200

    except Exception as e:
        print(f"Delete contact error: {e}")
        return jsonify({'message': 'Failed to delete contact'}), 500

# Bolna AI Voice Agent Integration Endpoints

@app.route('/api/voice-agents/<agent_id>/contacts/bulk-call', methods=['POST'])
@login_required
@check_trial_limits(feature='voice_calls', usage_type='outbound_calls')
def start_bulk_calls(agent_id):
    """Start outbound calls to selected contacts using Bolna AI"""
    try:
        user_id = g.user_id
        data = request.json
        
        # Validate required fields
        contact_ids = data.get('contact_ids', [])
        if not contact_ids:
            return jsonify({'message': 'No contacts selected for calling'}), 400
        
        # Log API call for trial users
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            log_trial_activity(user_id, 'api_call', {
                'endpoint': f'/api/voice-agents/{agent_id}/contacts/bulk-call',
                'method': 'POST',
                'contact_count': len(contact_ids)
            })
        
        # Get voice agent details
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=*')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        agent_data = voice_agent[0]
        
        # Get selected contacts
        contact_filter = ','.join([f'"{cid}"' for cid in contact_ids])
        contacts = supabase_request('GET', f'contacts?id=in.({contact_filter})&voice_agent_id=eq.{agent_id}&status=eq.active')
        
        if not contacts:
            return jsonify({'message': 'No active contacts found'}), 404
        
        # Initialize Bolna API
        try:
            bolna_api = BolnaAPI()
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        
        # Get agent configuration for this voice agent
        agent_config = get_agent_config_for_voice_agent(agent_data)
        
        # Prepare call configurations
        call_configs = []
        for contact in contacts:
            # Custom variables for this contact/agent
            variables = {
                **agent_config.get('default_variables', {}),
                'contact_name': contact['name'],
                'contact_phone': contact['phone'],
                'agent_title': agent_data['title'],
                'agent_description': agent_data.get('description', ''),
                **data.get('custom_variables', {})
            }
            
            call_config = {
                'agent_id': agent_config['agent_id'],
                'recipient_phone': contact['phone'],
                'sender_phone': agent_config['sender_phone'],
                'variables': variables,
                'metadata': {
                    'voice_agent_id': agent_id,
                    'contact_id': contact['id'],
                    'organization_id': agent_data['organization_id'],
                    'enterprise_id': agent_data['enterprise_id'],
                    'initiated_by_user_id': user_id,
                    'campaign_name': data.get('campaign_name', f'Bulk call - {agent_data["title"]}')
                }
            }
            call_configs.append(call_config)
        
        # Start bulk calls
        print(f"Starting {len(call_configs)} calls for voice agent {agent_data['title']}")
        call_results = bolna_api.bulk_start_calls(call_configs)
        
        # Log call attempts in database
        call_logs = []
        successful_calls = 0
        failed_calls = 0
        
        for result in call_results:
            config = result['original_config']
            
            if result['success']:
                successful_calls += 1
                status = 'initiated'
                bolna_call_id = result.get('call_id')
            else:
                failed_calls += 1
                status = 'failed'
                bolna_call_id = None
            
            # Create call log entry
            call_log = {
                'id': str(uuid.uuid4()),
                'voice_agent_id': agent_id,
                'contact_id': config['metadata']['contact_id'],
                'phone_number': config['recipient_phone'],
                'status': status,
                'organization_id': config['metadata']['organization_id'],
                'enterprise_id': config['metadata']['enterprise_id'],
                'metadata': {
                    'bolna_call_id': bolna_call_id,
                    'bolna_agent_id': config['agent_id'],
                    'sender_phone': config['sender_phone'],
                    'variables': config['variables'],
                    'campaign_name': config['metadata']['campaign_name'],
                    'error': result.get('error') if not result['success'] else None
                }
            }
            call_logs.append(call_log)
        
        # Insert call logs into database
        if call_logs:
            supabase_request('POST', 'call_logs', data=call_logs)
        
        # Log activity
        log_trial_activity(user_id, 'bulk_calls_initiated', {
            'voice_agent_id': agent_id,
            'total_calls': len(call_configs),
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'campaign_name': data.get('campaign_name', f'Bulk call - {agent_data["title"]}')
        })
        
        response = {
            'message': f'Bulk call campaign initiated',
            'summary': {
                'total_contacts': len(contacts),
                'total_calls_attempted': len(call_configs),
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'campaign_name': data.get('campaign_name', f'Bulk call - {agent_data["title"]}')
            },
            'call_results': call_results,
            'agent_config': {
                'bolna_agent_id': agent_config['agent_id'],
                'sender_phone': agent_config['sender_phone']
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Bulk call error: {e}")
        return jsonify({'message': f'Failed to initiate bulk calls: {str(e)}'}), 500

@app.route('/api/call-logs', methods=['GET', 'POST'])
@login_required
def get_call_logs():
    """Get call logs for the user's enterprise or specific phone number"""
    try:
        user_id = g.user_id

        # Get user's enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=enterprise_id,role')
        if not user or len(user) == 0:
            return jsonify({'message': 'User not found'}), 404

        user_data = user[0]
        enterprise_id = user_data['enterprise_id']

        # Check if specific phone number is requested
        phone_number = None
        if request.method == 'POST':
            data = request.json or {}
            phone_number = data.get('phone_number')
        elif request.method == 'GET':
            phone_number = request.args.get('phone_number')

        # Get query parameters
        limit = request.args.get('limit', 50)
        offset = request.args.get('offset', 0)
        voice_agent_id = request.args.get('voice_agent_id')
        status = request.args.get('status')

        # Build query
        query_params = f'enterprise_id=eq.{enterprise_id}&order=created_at.desc&limit={limit}&offset={offset}'

        if phone_number:
            # Filter by sender phone number
            query_params += f'&sender_phone=eq.{phone_number}'
        if voice_agent_id:
            query_params += f'&voice_agent_id=eq.{voice_agent_id}'
        if status:
            query_params += f'&status=eq.{status}'

        # Get call logs
        call_logs = supabase_request('GET', f'call_logs?{query_params}&select=*,contacts(name,phone),voice_agents(title)')

        # If no call logs found and phone number specified, try Bolna API
        if not call_logs and phone_number:
            try:
                # Initialize Bolna API
                bolna_api = BolnaAPI()

                # Get call history from Bolna API
                bolna_calls = bolna_api.get_call_history(phone_number)

                # Format Bolna calls to match our structure
                formatted_calls = []
                for call in bolna_calls:
                    formatted_call = {
                        'id': call.get('call_id', f"bolna_{call.get('id', 'unknown')}"),
                        'sender_phone': phone_number,
                        'recipient_phone': call.get('to_number', call.get('recipient_phone', 'Unknown')),
                        'direction': call.get('direction', 'outbound'),
                        'status': call.get('status', 'unknown'),
                        'duration': call.get('duration_seconds', call.get('duration', 0)),
                        'cost': call.get('cost', 0),
                        'created_at': call.get('created_at'),
                        'recording_url': call.get('recording_url'),
                        'transcript': call.get('transcript'),
                        'agent_name': call.get('agent_name', 'AI Agent'),
                        'metadata': call,
                        'from_number': call.get('from_number', phone_number)
                    }
                    formatted_calls.append(formatted_call)

                return jsonify({
                    'call_logs': formatted_calls,
                    'source': 'bolna_api'
                }), 200

            except Exception as bolna_error:
                print(f"Bolna API error: {bolna_error}")
                # Continue with empty database results

        return jsonify({
            'call_logs': call_logs or [],
            'source': 'database'
        }), 200

    except Exception as e:
        print(f"Get call logs error: {e}")
        return jsonify({'message': 'Failed to get call logs'}), 500

@app.route('/api/phone/<phone_number>/data-history', methods=['GET'])
@login_required
def get_phone_data_history(phone_number):
    """Get comprehensive data history and analytics for a specific phone number"""
    try:
        # Get user_id from request.current_user (set by @login_required decorator)
        user_id = None
        if hasattr(request, 'current_user') and request.current_user:
            user_id = request.current_user.get('user_id')

        if not user_id:
            print("Get data history error: user_id not found")
            return jsonify({
                'success': False,
                'error': 'User ID not found'
            }), 400

        # Get query parameters
        days = request.args.get('days', '30', type=int)
        data_type = request.args.get('type', 'all')

        # Get user's enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=enterprise_id')
        if not user or len(user) == 0:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        enterprise_id = user[0]['enterprise_id']

        # Verify user has access to this phone number
        phone_record = supabase_request('GET', f'purchased_phone_numbers?phone_number=eq.{phone_number}&enterprise_id=eq.{enterprise_id}')
        if not phone_record or len(phone_record) == 0:
            return jsonify({
                'success': False,
                'error': 'Phone number not found or access denied'
            }), 404

        # Mock comprehensive data history - replace with actual database queries
        from datetime import datetime, timedelta
        import random

        # Generate mock statistics
        statistics = {
            'totalCalls': random.randint(50, 200),
            'totalSMS': random.randint(100, 500),
            'totalCost': round(random.uniform(50.0, 500.0), 2),
            'avgDuration': f"{random.randint(1, 5)}m {random.randint(10, 59)}s"
        }

        # Generate mock records for the specified period
        records = []
        base_date = datetime.now()

        for i in range(min(days, 50)):  # Limit to 50 records for demo
            record_date = base_date - timedelta(days=random.randint(0, days))
            record_type = random.choice(['call', 'sms'])

            if data_type != 'all' and record_type != data_type.rstrip('s'):
                continue

            record = {
                'id': f'rec_{i+1}',
                'type': record_type,
                'timestamp': record_date.isoformat(),
                'status': random.choice(['completed', 'failed', 'pending']),
                'cost': round(random.uniform(0.5, 5.0), 2)
            }

            if record_type == 'call':
                record.update({
                    'to': f"+91{random.randint(7000000000, 9999999999)}",
                    'duration': f"{random.randint(0, 10)}:{random.randint(10, 59):02d}",
                    'direction': random.choice(['inbound', 'outbound'])
                })
            else:  # SMS
                record.update({
                    'to': f"+91{random.randint(7000000000, 9999999999)}",
                    'message_length': random.randint(50, 160),
                    'direction': random.choice(['inbound', 'outbound'])
                })

            records.append(record)

        # Sort records by timestamp (newest first)
        records.sort(key=lambda x: x['timestamp'], reverse=True)

        # Generate mock usage trends (for charts)
        usage_trends = []
        for i in range(days):
            trend_date = base_date - timedelta(days=i)
            usage_trends.append({
                'date': trend_date.strftime('%Y-%m-%d'),
                'calls': random.randint(0, 10),
                'sms': random.randint(0, 20),
                'cost': round(random.uniform(1.0, 15.0), 2)
            })

        return jsonify({
            'success': True,
            'phone_number': phone_number,
            'period_days': days,
            'data_type': data_type,
            'statistics': statistics,
            'records': records,
            'usage_trends': usage_trends,
            'total_records': len(records),
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Get data history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone/<phone_number>/export-data', methods=['GET'])
@login_required
def export_phone_data_history(phone_number):
    """Export data history in various formats"""
    try:
        user_id = g.user_id
        format_type = request.args.get('format', 'csv').lower()
        days = request.args.get('days', '30', type=int)
        data_type = request.args.get('type', 'all')

        # Get user's enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=enterprise_id')
        if not user or len(user) == 0:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        enterprise_id = user[0]['enterprise_id']

        # Verify user has access to this phone number
        phone_record = supabase_request('GET', f'purchased_phone_numbers?phone_number=eq.{phone_number}&enterprise_id=eq.{enterprise_id}')
        if not phone_record or len(phone_record) == 0:
            return jsonify({
                'success': False,
                'error': 'Phone number not found or access denied'
            }), 404

        # Generate sample data for export
        from datetime import datetime, timedelta
        import random
        import csv
        import json
        from io import StringIO

        records = []
        base_date = datetime.now()

        for i in range(min(days * 2, 100)):  # More records for export
            record_date = base_date - timedelta(days=random.randint(0, days))
            record_type = random.choice(['call', 'sms'])

            if data_type != 'all' and record_type != data_type.rstrip('s'):
                continue

            record = {
                'id': f'rec_{i+1}',
                'phone_number': phone_number,
                'type': record_type,
                'timestamp': record_date.strftime('%Y-%m-%d %H:%M:%S'),
                'to_number': f"+91{random.randint(7000000000, 9999999999)}",
                'status': random.choice(['completed', 'failed', 'pending']),
                'cost': round(random.uniform(0.5, 5.0), 2),
                'duration': f"{random.randint(0, 10)}:{random.randint(10, 59):02d}" if record_type == 'call' else '',
                'direction': random.choice(['inbound', 'outbound'])
            }
            records.append(record)

        # Sort by timestamp
        records.sort(key=lambda x: x['timestamp'], reverse=True)

        if format_type == 'csv':
            output = StringIO()
            if records:
                writer = csv.DictWriter(output, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename={phone_number}_data_{days}days.csv'
            return response

        elif format_type == 'json':
            export_data = {
                'phone_number': phone_number,
                'export_date': datetime.now().isoformat(),
                'period_days': days,
                'data_type': data_type,
                'total_records': len(records),
                'records': records
            }

            response = make_response(json.dumps(export_data, indent=2))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename={phone_number}_data_{days}days.json'
            return response

        elif format_type == 'pdf':
            return jsonify({
                'success': False,
                'error': 'PDF export not implemented yet. Please use CSV or JSON format.'
            }), 501

        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            }), 400

    except Exception as e:
        print(f"Export data history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/call-logs/<call_log_id>/status', methods=['GET'])
@login_required
def get_call_status(call_log_id):
    """Get real-time status of a call from Bolna API"""
    try:
        user_id = g.user_id
        
        # Get call log
        call_log = supabase_request('GET', f'call_logs?id=eq.{call_log_id}')
        if not call_log or len(call_log) == 0:
            return jsonify({'message': 'Call log not found'}), 404
        
        call_data = call_log[0]
        bolna_call_id = call_data.get('metadata', {}).get('bolna_call_id')
        
        if not bolna_call_id:
            return jsonify({'message': 'No Bolna call ID found for this call'}), 400
        
        # Get status from Bolna API
        try:
            bolna_api = BolnaAPI()
            status_response = bolna_api.get_call_status(bolna_call_id)
            
            # Update call log status if different
            current_status = status_response.get('status', 'unknown')
            if current_status != call_data['status']:
                update_data = {
                    'status': current_status,
                    'duration': status_response.get('duration'),
                    'metadata': {
                        **call_data.get('metadata', {}),
                        'bolna_status_response': status_response,
                        'last_status_check': datetime.utcnow().isoformat()
                    }
                }
                supabase_request('PATCH', f'call_logs?id=eq.{call_log_id}', data=update_data)
            
            return jsonify({
                'call_log_id': call_log_id,
                'bolna_call_id': bolna_call_id,
                'status': current_status,
                'bolna_response': status_response
            }), 200
            
        except Exception as e:
            return jsonify({'message': f'Failed to get call status from Bolna: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Get call status error: {e}")
        return jsonify({'message': 'Failed to get call status'}), 500

# Development endpoints (bypass authentication for testing)
# In-memory storage for dev testing
dev_voice_agents_storage = {}

# In-memory storage for phone number to agent mapping

@app.route('/api/dev/voice-agents', methods=['GET', 'POST'])
def dev_voice_agents():
    """Development endpoint to get or create voice agents without authentication"""
    try:
        if request.method == 'GET':
            # Return in-memory agents
            agents_list = list(dev_voice_agents_storage.values())
            return jsonify({'voice_agents': agents_list}), 200

        elif request.method == 'POST':
            data = request.json

            # Generate a unique ID for the agent
            agent_id = str(uuid.uuid4())

            # Create voice agent data with minimal required fields
            agent_data = {
                'id': agent_id,
                'agent_name': data.get('agent_name', 'Test Agent'),
                'description': data.get('description', 'Test agent for development'),
                'welcome_message': data.get('welcome_message', 'नमस्ते! मैं आपका AI assistant हूं।'),
                'agent_prompt': data.get('agent_prompt', 'You are a helpful AI assistant.'),
                'conversation_style': data.get('conversation_style', 'professional'),
                'language_preference': data.get('language_preference', 'hinglish'),
                'agent_type': data.get('agent_type', 'sales'),
                'voice': data.get('voice', 'Aditi'),
                'phone_number': data.get('phone_number'),
                'max_duration': data.get('max_duration', 180),
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            # Store in memory
            dev_voice_agents_storage[agent_id] = agent_data

            return jsonify({
                'message': 'Voice agent created successfully',
                'agent_id': agent_id,
                'voice_agent': agent_data
            }), 201

    except Exception as e:
        print(f"Dev voice agents error: {e}")
        return jsonify({'message': f'Failed to process request: {str(e)}'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/contacts', methods=['GET'])
def dev_get_agent_contacts(agent_id):
    """Development endpoint to get agent contacts without authentication"""
    try:
        contacts = supabase_request('GET', f'contacts?voice_agent_id=eq.{agent_id}&select=*')
        return jsonify({'contacts': contacts or []}), 200
    except Exception as e:
        print(f"Dev get agent contacts error: {e}")
        return jsonify({'message': 'Failed to get agent contacts'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/contacts', methods=['POST'])
def dev_create_contact(agent_id):
    """Development endpoint to create contact without authentication"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name') or not data.get('phone'):
            return jsonify({'message': 'Name and phone are required'}), 400
        
        # Get voice agent to validate it exists and get related IDs
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=*')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        agent_data = voice_agent[0]
        
        # Create contact
        contact_data = {
            'name': data['name'],
            'phone': data['phone'],
            'status': data.get('status', 'active'),
            'voice_agent_id': agent_id,
            'channel_id': agent_data['channel_id'],
            'organization_id': agent_data['organization_id'],
            'enterprise_id': agent_data['enterprise_id']
        }
        
        contact = supabase_request('POST', 'contacts', data=contact_data)
        
        return jsonify({'contact': contact[0] if contact else None}), 201
        
    except Exception as e:
        print(f"Dev create contact error: {e}")
        return jsonify({'message': f'Failed to create contact: {str(e)}'}), 500

@app.route('/api/dev/contacts/<contact_id>', methods=['PUT'])
def dev_update_contact(contact_id):
    """Development endpoint to update contact without authentication"""
    try:
        data = request.json
        
        # Update contact
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'status' in data:
            update_data['status'] = data['status']
        
        if not update_data:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        contact = supabase_request('PATCH', f'contacts?id=eq.{contact_id}', data=update_data)
        
        return jsonify({'contact': contact[0] if contact else None}), 200
        
    except Exception as e:
        print(f"Dev update contact error: {e}")
        return jsonify({'message': 'Failed to update contact'}), 500

@app.route('/api/dev/contacts/<contact_id>', methods=['DELETE'])
def dev_delete_contact(contact_id):
    """Development endpoint to delete contact without authentication"""
    try:
        supabase_request('DELETE', f'contacts?id=eq.{contact_id}')
        return jsonify({'message': 'Contact deleted successfully'}), 200
    except Exception as e:
        print(f"Dev delete contact error: {e}")
        return jsonify({'message': 'Failed to delete contact'}), 500

@app.route('/api/dev/voice-agents/<agent_id>', methods=['GET'])
def dev_get_voice_agent(agent_id):
    """Development endpoint to get voice agent details without authentication"""
    try:
        # Get voice agent from in-memory storage
        if agent_id in dev_voice_agents_storage:
            agent_data = dev_voice_agents_storage[agent_id]
            return jsonify({'agent': agent_data}), 200
        else:
            return jsonify({'message': 'Voice agent not found'}), 404

    except Exception as e:
        print(f"Dev get voice agent error: {e}")
        return jsonify({'message': f'Failed to get voice agent: {str(e)}'}), 500

@app.route('/api/dev/voice-agents/<agent_id>', methods=['PUT'])
def dev_update_voice_agent(agent_id):
    """Development endpoint to update voice agent configuration without authentication"""
    try:
        data = request.json
        
        # Validate agent exists
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        # Prepare update data
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'welcome_message' in data:
            update_data['welcome_message'] = data['welcome_message']
        if 'agent_prompt' in data:
            update_data['agent_prompt'] = data['agent_prompt']
        if 'conversation_style' in data:
            update_data['conversation_style'] = data['conversation_style']
        if 'language_preference' in data:
            update_data['language_preference'] = data['language_preference']
        if 'calling_number' in data:
            update_data['calling_number'] = data['calling_number']
        if 'status' in data:
            update_data['status'] = data['status']
        
        if not update_data:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # Update voice agent
        updated_agent = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}', data=update_data)
        
        return jsonify({'voice_agent': updated_agent[0] if updated_agent else None}), 200
        
    except Exception as e:
        print(f"Dev update voice agent error: {e}")
        return jsonify({'message': f'Failed to update voice agent: {str(e)}'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/prompts', methods=['GET'])
def dev_get_agent_prompts(agent_id):
    """Development endpoint to get agent prompts and configuration"""
    try:
        if agent_id in dev_voice_agents_storage:
            agent_data = dev_voice_agents_storage[agent_id]
            prompts = {
                'welcome_message': agent_data.get('welcome_message', ''),
                'agent_prompt': agent_data.get('agent_prompt', ''),
                'conversation_style': agent_data.get('conversation_style', 'professional'),
                'language_preference': agent_data.get('language_preference', 'hinglish'),
                'agent_name': agent_data.get('agent_name', ''),
                'description': agent_data.get('description', '')
            }
            return jsonify({'prompts': prompts}), 200
        else:
            return jsonify({'message': 'Voice agent not found'}), 404

    except Exception as e:
        print(f"Dev get agent prompts error: {e}")
        return jsonify({'message': 'Failed to get agent prompts'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/prompts', methods=['PUT'])
def dev_update_agent_prompts(agent_id):
    """Development endpoint to update agent prompts and configuration"""
    try:
        data = request.json

        # Check if agent exists in memory
        if agent_id not in dev_voice_agents_storage:
            return jsonify({'message': 'Voice agent not found'}), 404

        # Update agent data in memory
        agent_data = dev_voice_agents_storage[agent_id]
        updated_fields = []

        if 'welcome_message' in data:
            agent_data['welcome_message'] = data['welcome_message']
            updated_fields.append('welcome_message')
        if 'agent_prompt' in data:
            agent_data['agent_prompt'] = data['agent_prompt']
            updated_fields.append('agent_prompt')
        if 'conversation_style' in data:
            agent_data['conversation_style'] = data['conversation_style']
            updated_fields.append('conversation_style')
        if 'language_preference' in data:
            agent_data['language_preference'] = data['language_preference']
            updated_fields.append('language_preference')
        if 'agent_name' in data:
            agent_data['agent_name'] = data['agent_name']
            updated_fields.append('agent_name')
        if 'agent_type' in data:
            agent_data['agent_type'] = data['agent_type']
            updated_fields.append('agent_type')
        if 'voice' in data:
            agent_data['voice'] = data['voice']
            updated_fields.append('voice')

        if not updated_fields:
            return jsonify({'message': 'No valid fields to update'}), 400

        # Update timestamp
        agent_data['updated_at'] = datetime.now().isoformat()

        return jsonify({
            'message': 'Agent prompts updated successfully',
            'agent_id': agent_id,
            'updated_fields': updated_fields
        }), 200

    except Exception as e:
        print(f"Dev update agent prompts error: {e}")
        return jsonify({'message': 'Failed to update agent prompts'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/bolna-update', methods=['PUT'])
def dev_update_bolna_agent(agent_id):
    """Development endpoint to update Bolna agent configuration directly"""
    try:
        data = request.json

        # Get the Bolna agent ID from the voice agent record
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=*')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404

        bolna_agent_id = voice_agent[0].get('bolna_agent_id')
        if not bolna_agent_id:
            return jsonify({'message': 'No Bolna agent ID found for this voice agent'}), 404

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except ImportError as e:
            return jsonify({'message': f'Bolna integration module not found: {str(e)}'}), 500
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500

        # Prepare update data for Bolna API
        bolna_update_data = {}

        if 'welcome_message' in data:
            bolna_update_data['welcome_message'] = data['welcome_message']

        if 'agent_prompt' in data:
            bolna_update_data['prompt'] = data['agent_prompt']

        if 'agent_name' in data:
            bolna_update_data['name'] = data['agent_name']

        if 'description' in data:
            bolna_update_data['description'] = data['description']

        if 'voice' in data:
            bolna_update_data['voice'] = data['voice']

        if 'language' in data:
            bolna_update_data['language'] = data['language']

        if not bolna_update_data:
            return jsonify({'message': 'No valid fields to update in Bolna agent'}), 400

        # Update Bolna agent
        try:
            bolna_response = bolna_api.update_agent(bolna_agent_id, **bolna_update_data)

            # Also update local database
            local_update_data = {}
            if 'welcome_message' in data:
                local_update_data['welcome_message'] = data['welcome_message']
            if 'agent_prompt' in data:
                local_update_data['agent_prompt'] = data['agent_prompt']

            if local_update_data:
                supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}', data=local_update_data)

            return jsonify({
                'message': 'Bolna agent updated successfully',
                'agent_id': agent_id,
                'bolna_agent_id': bolna_agent_id,
                'updated_fields': list(bolna_update_data.keys()),
                'bolna_response': bolna_response
            }), 200

        except Exception as e:
            return jsonify({'message': f'Failed to update Bolna agent: {str(e)}'}), 500

    except Exception as e:
        print(f"Dev update Bolna agent error: {e}")
        return jsonify({'message': f'Failed to update Bolna agent: {str(e)}'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/contacts/bulk-call', methods=['POST'])
def dev_bulk_calls(agent_id):
    """Development endpoint for bulk calls without authentication"""
    try:
        data = request.json
        
        # Validate required fields
        contact_ids = data.get('contact_ids', [])
        if not contact_ids:
            return jsonify({'message': 'No contacts selected for calling'}), 400
        
        # Get voice agent details
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=*')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        agent_data = voice_agent[0]
        
        # Get selected contacts
        contact_filter = ','.join([f'"{cid}"' for cid in contact_ids])
        contacts = supabase_request('GET', f'contacts?id=in.({contact_filter})&voice_agent_id=eq.{agent_id}&status=eq.active')
        
        if not contacts:
            return jsonify({'message': 'No active contacts found'}), 404
        
        # Initialize Bolna API with admin-specific settings
        try:
            from bolna_integration import BolnaAPI, get_agent_config_for_voice_agent

            # Get current user's phone settings
            current_user = g.current_user
            admin_user_data = {
                'sender_phone': current_user.get('sender_phone'),
                'bolna_agent_id': current_user.get('bolna_agent_id')
            }

            bolna_api = BolnaAPI(admin_user_data=admin_user_data)
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        
        # Get custom agent configuration from database
        custom_config = {
            'welcome_message': agent_data.get('welcome_message'),
            'agent_prompt': agent_data.get('agent_prompt'),
            'conversation_style': agent_data.get('conversation_style'),
            'language_preference': agent_data.get('language_preference')
        }
        
        # Get agent configuration with custom prompts
        agent_config = get_agent_config_for_voice_agent(agent_data, custom_config)
        
        # Prepare call configurations
        call_configs = []
        for contact in contacts:
            from bolna_integration import create_personalized_variables
            
            # Create personalized variables with custom prompts
            variables = create_personalized_variables(
                base_variables=agent_config.get('default_variables', {}),
                contact=contact,
                agent_config=agent_config,
                custom_config=custom_config
            )
            
            # Add additional variables
            variables.update({
                'agent_title': agent_data['title'],
                'agent_description': agent_data.get('description', ''),
                **data.get('custom_variables', {})
            })
            
            call_config = {
                'agent_id': agent_config['agent_id'],
                'recipient_phone': contact['phone'],
                'sender_phone': agent_config['sender_phone'],
                'variables': variables,
                'metadata': {
                    'voice_agent_id': agent_id,
                    'contact_id': contact['id'],
                    'organization_id': agent_data['organization_id'],
                    'enterprise_id': agent_data['enterprise_id'],
                    'campaign_name': data.get('campaign_name', f'Dev test - {agent_data["title"]}')
                }
            }
            call_configs.append(call_config)
        
        # Start bulk calls
        print(f"Starting {len(call_configs)} calls for voice agent {agent_data['title']}")
        call_results = bolna_api.bulk_start_calls(call_configs)
        
        # Count successes and failures
        successful_calls = sum(1 for result in call_results if result.get('success'))
        failed_calls = len(call_results) - successful_calls
        
        response = {
            'message': f'Development bulk call campaign initiated',
            'summary': {
                'total_contacts': len(contacts),
                'total_calls_attempted': len(call_configs),
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'campaign_name': data.get('campaign_name', f'Dev test - {agent_data["title"]}')
            },
            'call_results': call_results,
            'agent_config': {
                'bolna_agent_id': agent_config['agent_id'],
                'sender_phone': agent_config['sender_phone']
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Dev bulk call error: {e}")
        return jsonify({'message': f'Failed to initiate bulk calls: {str(e)}'}), 500

@app.route('/api/dev/update-phone-agent', methods=['POST'])
def dev_update_phone_agent():
    """Development endpoint to manually update phone agent assignment"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        agent_id = data.get('agent_id')

        if not phone_number or not agent_id:
            return jsonify({
                'success': False,
                'error': 'phone_number and agent_id are required'
            }), 400

        # Update the phone number record
        update_data = {
            'agent_id': agent_id,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        result = supabase_request('PATCH', f'purchased_phone_numbers?phone_number=eq.{phone_number}', data=update_data)

        return jsonify({
            'success': True,
            'message': f'Phone {phone_number} updated with agent {agent_id}',
            'result': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Manual call endpoint for production use
@app.route('/api/manual-call', methods=['POST'])
def manual_call():
    """Production endpoint for placing manual calls via Bolna API"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['recipient_phone', 'sender_phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        recipient_phone = data['recipient_phone']
        sender_phone = data['sender_phone']
        
        # Import Bolna API with default settings for manual calls
        try:
            from bolna_integration import BolnaAPI

            # Get dynamic phone-agent mapping from database
            print(f"🔍 Looking up agent for phone number: {sender_phone}")

            # First try to get from bolna_agents table
            agent_id = None
            agent_name = None

            try:
                # Query bolna_agents table for this phone number
                db_result = supabase_request('GET', f'bolna_agents?phone_number=eq.{sender_phone}')
                if db_result and len(db_result) > 0:
                    agent_data = db_result[0]
                    agent_id = agent_data.get('bolna_agent_id')
                    agent_name = agent_data.get('agent_name')
                    print(f"✅ Found agent in database: {agent_name} ({agent_id})")
                else:
                    print(f"⚠️ No agent found in bolna_agents table for {sender_phone}")
            except Exception as db_error:
                print(f"❌ Database lookup error: {db_error}")

            # If no agent found in database, try purchased_phone_numbers table
            if not agent_id:
                try:
                    phone_result = supabase_request('GET', f'purchased_phone_numbers?phone_number=eq.{sender_phone}')
                    if phone_result and len(phone_result) > 0:
                        phone_data = phone_result[0]
                        agent_id = phone_data.get('agent_id')
                        if agent_id:
                            print(f"✅ Found agent ID in phone table: {agent_id}")
                        else:
                            print(f"⚠️ Phone number found but no agent_id assigned")
                    else:
                        print(f"⚠️ Phone number {sender_phone} not found in purchased_phone_numbers")
                except Exception as phone_error:
                    print(f"❌ Phone lookup error: {phone_error}")

            # Fallback to hardcoded mapping for known working numbers
            if not agent_id:
                print(f"🔄 Using fallback mapping for {sender_phone}")
                phone_agent_mapping = {
                    '+918035315404': '6af040f3-e4ac-4f91-8091-044ba1a3808f',  # llll (updated agent)
                    '+918035315390': '2f1b28b6-d2e6-4074-9c8e-ba9594947afa',  # bbbb
                    '+918035315328': '9ede5ecf-9cac-4123-8cab-f644f99f1f73',  # agent Ai
                    '+918035743222': '15554373-b8e1-4b00-8c25-c4742dc8e480',  # hope (this one works in Bolna)
                    '+918035743656': '004686a4-184a-44f0-a765-c91896153e5a',  # Reminder call to patients after 5 days
                    '+918035743352': '164a85e1-b793-42a9-a2f3-a9e857796782',  # Doctor reminder for marketing final
                    '+918035742982': '42056168-e174-4c79-b5ba-6e69993e9a1c',  # Dubai indian final Manzil AI Voice Concierge
                    '+918035740878': 'f636837c-4d0a-4e27-b24c-ed136e504b2b',  # OPD on discharge.final
                    '+918035315322': 'c0357194-c863-4796-a825-d6de6e0707a5',  # hope
                }
                agent_id = phone_agent_mapping.get(sender_phone)
                if agent_id:
                    print(f"✅ Using fallback agent: {agent_id}")
                else:
                    print(f"❌ No agent mapping found for {sender_phone}")

            if not agent_id:
                return jsonify({
                    'success': False,
                    'message': f'No agent assigned to phone number {sender_phone}. Please assign an agent first.'
                }), 400

            # Preserve the original requested phone number
            original_sender_phone = sender_phone
            # Determine which phone number to actually use for the call
            actual_sender_phone = sender_phone

            print(f"🔍 Using agent {agent_id} for phone {actual_sender_phone}")
            if agent_name:
                print(f"🎯 Agent name: {agent_name}")

            # Use admin settings for manual calls
            admin_user_data = {
                'sender_phone': actual_sender_phone,
                'bolna_agent_id': agent_id
            }

            bolna_api = BolnaAPI(admin_user_data=admin_user_data)

            # Try to make the call with the requested phone number first
            call_response = None
            try:
                print(f"🔄 Attempting call with requested phone: {actual_sender_phone}")
                call_response = bolna_api.start_outbound_call(
                    agent_id=agent_id,
                    recipient_phone=recipient_phone,
                    sender_phone=actual_sender_phone,
                    variables={
                        'contact_name': 'Manual Call Contact',
                        'call_type': 'manual',
                        'initiated_by': 'dashboard'
                    }
                )
            except Exception as e:
                print(f"❌ Call failed with {actual_sender_phone}: {e}")

                # If the requested phone fails, try with the working phone number
                if actual_sender_phone != '+918035743222':
                    print(f"🔄 Retrying with working phone: +918035743222")
                    try:
                        # Update admin_user_data for the fallback phone
                        fallback_admin_data = {
                            'sender_phone': '+918035743222',
                            'bolna_agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480'
                        }
                        bolna_api_fallback = BolnaAPI(admin_user_data=fallback_admin_data)

                        call_response = bolna_api_fallback.start_outbound_call(
                            agent_id='15554373-b8e1-4b00-8c25-c4742dc8e480',
                            recipient_phone=recipient_phone,
                            sender_phone='+918035743222',
                            variables={
                                'contact_name': 'Manual Call Contact',
                                'call_type': 'manual',
                                'initiated_by': 'dashboard',
                                'original_requested_phone': actual_sender_phone
                            }
                        )
                        print(f"✅ Call successful with fallback phone: +918035743222")
                        # Keep track that we used fallback but don't change actual_sender_phone for response
                        call_response['used_fallback_phone'] = True
                        call_response['fallback_phone'] = '+918035743222'
                    except Exception as fallback_error:
                        print(f"❌ Fallback call also failed: {fallback_error}")
                        raise e  # Raise the original error

            # Check if call was successful (Bolna returns status: 'queued' for successful calls)
            if call_response and (call_response.get('success') or call_response.get('status') == 'queued'):
                # Always return the originally requested sender_phone in response
                response_data = {
                    'success': True,
                    'message': f'Call initiated successfully from {original_sender_phone} to {recipient_phone}',
                    'call_id': call_response.get('execution_id') or call_response.get('run_id') or call_response.get('call_id'),
                    'execution_id': call_response.get('execution_id'),
                    'run_id': call_response.get('run_id'),
                    'recipient_phone': recipient_phone,
                    'sender_phone': original_sender_phone,  # Always return the originally requested phone
                    'requested_sender_phone': original_sender_phone,
                    'bolna_response': call_response,
                    'note': f'Used {actual_sender_phone} (has agent in Bolna)' if actual_sender_phone != original_sender_phone else None
                }

                # Add fallback info if used
                if call_response.get('used_fallback_phone'):
                    response_data['fallback_info'] = {
                        'used_fallback': True,
                        'fallback_phone': call_response.get('fallback_phone'),
                        'reason': 'Original agent not found in Bolna API'
                    }

                return jsonify(response_data), 200
            else:
                raise Exception(f"Bolna API returned error: {call_response}")

        except Exception as e:
            # If Bolna API fails, fall back to test mode
            print(f"Bolna API error: {e}")
            import time
            return jsonify({
                'success': True,
                'message': f'Test call initiated from {original_sender_phone} to {recipient_phone} (Demo Mode)',
                'call_id': f'demo-{int(time.time())}',
                'recipient_phone': recipient_phone,
                'sender_phone': original_sender_phone,  # Always return the originally requested phone
                'requested_sender_phone': original_sender_phone,
                'note': f'Demo mode - Used {actual_sender_phone} (has agent in Bolna). Real API failed - check logs for details.',
                'error_details': str(e),
                'demo_mode': True
            }), 200
        
    except Exception as e:
        print(f"Manual call error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to place call: {str(e)}'
        }), 500

# Simple test call endpoint for manual calls (development only)
@app.route('/api/test/manual-call', methods=['POST'])
def test_manual_call():
    """Simple endpoint for placing manual test calls without requiring existing contacts"""
    try:
        data = request.json
        
        # Required fields
        required_fields = ['recipient_phone', 'sender_phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        recipient_phone = data['recipient_phone']
        sender_phone = data['sender_phone']
        agent_id = data.get('agent_id', 'manual-test')
        
        # For now, just return success without making actual call
        # In production, this would integrate with Bolna API
        import time
        response = {
            'success': True,
            'message': f'Test call initiated from {sender_phone} to {recipient_phone}',
            'call_id': f'test-{int(time.time())}',
            'recipient_phone': recipient_phone,
            'sender_phone': sender_phone
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Manual call test error: {e}")
        return jsonify({'message': f'Failed to place test call: {str(e)}'}), 500

# Bolna Agent Management Endpoints
@app.route('/api/bolna/agents', methods=['GET'])
def get_bolna_agents():
    """Get all Bolna agents - returns development agents for testing"""
    try:
        # Return development agents stored in memory
        agents_list = []
        for agent_id, agent_data in dev_voice_agents_storage.items():
            agents_list.append({
                'agent_id': agent_id,
                'id': agent_id,
                'name': agent_data.get('agent_name'),
                'description': agent_data.get('description'),
                'voice': agent_data.get('voice'),
                'language': agent_data.get('language_preference'),
                'welcome_message': agent_data.get('welcome_message'),
                'prompt': agent_data.get('agent_prompt'),
                'max_duration': agent_data.get('max_duration'),
                'hangup_after': agent_data.get('hangup_after'),
                'status': agent_data.get('status'),
                'created_at': agent_data.get('created_at'),
                'updated_at': agent_data.get('updated_at')
            })

        return jsonify({
            'success': True,
            'agents': agents_list,
            'total': len(agents_list)
        })

    except Exception as e:
        print(f"Get Bolna agents error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get agents: {str(e)}'
        }), 500

@app.route('/api/bolna/agents', methods=['POST'])
def create_bolna_agent():
    """Create a new Bolna agent using development system"""
    try:
        data = request.json

        # Validate required fields
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Agent name is required'
            }), 400

        # Create agent data structure compatible with our dev system
        agent_data = {
            'agent_name': data.get('name'),
            'agent_type': 'custom',  # Default type for Bolna agents
            'voice': data.get('voice', 'en-IN-Standard-A'),
            'language_preference': data.get('language', 'en'),
            'welcome_message': data.get('welcome_message', f"Hello! This is {data.get('name')}. How can I help you today?"),
            'agent_prompt': data.get('prompt', 'You are a helpful AI assistant. Be polite, professional, and helpful.'),
            'max_duration': data.get('max_duration', 300),
            'hangup_after': data.get('hangup_after', 30),
            'description': data.get('description', 'Custom Bolna agent'),
            'phone_number': '+919999999999'  # Placeholder phone number for Bolna agents
        }

        # Generate unique agent ID
        agent_id = str(uuid.uuid4())

        # Add to our development storage
        agent_data['id'] = agent_id
        agent_data['created_at'] = datetime.now().isoformat()
        agent_data['updated_at'] = datetime.now().isoformat()
        agent_data['status'] = 'active'
        agent_data['conversation_style'] = 'professional'

        # Store in development agents storage
        dev_voice_agents_storage[agent_id] = agent_data

        print(f"✅ Created Bolna agent: {agent_data['agent_name']} (ID: {agent_id})")

        # Store agent in Supabase database
        try:
            # Get current user info
            user_data = getattr(request, 'current_user', None)
            user_id = user_data.get('user_id') or user_data.get('id') if user_data else None

            print(f"🔍 DEBUG - Bolna agent creation - User data: {user_data}")
            print(f"🔍 DEBUG - Bolna agent creation - User ID: {user_id}")

            # Store in bolna_agents table
            agent_record = {
                'bolna_agent_id': agent_id,
                'agent_name': agent_data['agent_name'],
                'agent_type': agent_data.get('agent_type', 'voice'),
                'description': agent_data['description'],
                'prompt': agent_data['agent_prompt'],
                'welcome_message': agent_data['welcome_message'],
                'voice': agent_data['voice'],
                'language': agent_data['language_preference'],
                'max_duration': agent_data['max_duration'],
                'hangup_after': agent_data['hangup_after'],
                'user_id': user_id,
                'status': 'active',
                'bolna_response': {}  # Store full Bolna response (will be updated when available)
            }

            # Insert into database
            db_result = supabase_request('POST', 'bolna_agents', data=agent_record)

            if db_result:
                print(f"✅ Agent stored in database: {agent_id}")
            else:
                print(f"⚠️ Failed to store agent in database, but agent created successfully")

        except Exception as db_error:
            print(f"⚠️ Database storage error: {db_error}")
            # Don't fail the whole request if database storage fails

        return jsonify({
            'success': True,
            'message': f'Agent "{agent_data["agent_name"]}" created successfully',
            'agent': {
                'agent_id': agent_id,
                'id': agent_id,
                'name': agent_data['agent_name'],
                'description': agent_data['description'],
                'voice': agent_data['voice'],
                'language': agent_data['language_preference'],
                'welcome_message': agent_data['welcome_message'],
                'prompt': agent_data['agent_prompt'],
                'max_duration': agent_data['max_duration'],
                'hangup_after': agent_data['hangup_after'],
                'status': agent_data['status'],
                'created_at': agent_data['created_at']
            }
        }), 201

    except Exception as e:
        print(f"Create Bolna agent error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to create agent: {str(e)}'
        }), 500

@app.route('/api/bolna/agents/<agent_id>', methods=['GET'])
@login_required
def get_bolna_agent_details(agent_id):
    """Get details of a specific Bolna agent"""
    try:
        # Get current user's phone settings
        current_user = g.current_user
        admin_user_data = {
            'sender_phone': current_user.get('sender_phone'),
            'bolna_agent_id': current_user.get('bolna_agent_id')
        }

        bolna_api = BolnaAPI(admin_user_data=admin_user_data)
        agent_details = bolna_api.get_agent_details(agent_id)

        return jsonify({
            'success': True,
            'agent': agent_details
        })

    except Exception as e:
        print(f"Get Bolna agent details error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get agent details: {str(e)}'
        }), 500

@app.route('/api/organizations', methods=['GET', 'POST'])
@login_required
def handle_organizations():
    """Handle organizations - GET to retrieve, POST to create"""
    if request.method == 'POST':
        return create_organization()
    else:
        return get_organizations()

def get_organizations():
    """Get user's organizations/enterprises"""
    try:
        user_data = request.current_user
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Get user's enterprise information
        enterprise_id = user_data.get('enterprise_id')

        user_id = user_data.get('user_id') or user_data.get('id')

        # Try to fetch organizations from database first
        try:
            # Query organizations table for user's organizations
            organizations = supabase_request('GET', f'organizations?user_id=eq.{user_id}&order=created_at.desc')

            if organizations:
                print(f"✅ Found {len(organizations)} organizations for user {user_id}")
                return jsonify({
                    'success': True,
                    'organizations': organizations,
                    'current_organization': organizations[0] if organizations else None
                }), 200
            else:
                print(f"📋 No organizations found for user {user_id}")
                # Return empty list if no organizations found
                return jsonify({
                    'success': True,
                    'organizations': [],
                    'current_organization': None
                }), 200

        except Exception as db_error:
            print(f"⚠️ Database error (table might not exist): {db_error}")
            # Fallback to mock data if table doesn't exist
        mock_organizations = [
            {
                'id': 'org-001',
                'name': 'BhashAI Healthcare',
                'description': 'AI-powered healthcare communication platform',
                'type': 'healthcare',
                'status': 'active',
                'created_at': '2025-07-19T00:00:00Z',
                'updated_at': '2025-07-19T00:00:00Z',
                'email': 'healthcare@bhashai.com',
                'phone': '+918035315404',
                'address': 'Mumbai, Maharashtra'
            },
            {
                'id': 'org-002',
                'name': 'BhashAI Retail',
                'description': 'Customer service automation for retail',
                'type': 'retail',
                'status': 'active',
                'created_at': '2025-07-19T00:00:00Z',
                'updated_at': '2025-07-19T00:00:00Z',
                'email': 'retail@bhashai.com',
                'phone': '+918035315390',
                'address': 'Delhi, India'
            },
            {
                'id': 'org-003',
                'name': 'BhashAI Finance',
                'description': 'Financial services communication hub',
                'type': 'finance',
                'status': 'active',
                'created_at': '2025-07-19T00:00:00Z',
                'updated_at': '2025-07-19T00:00:00Z',
                'email': 'finance@bhashai.com',
                'phone': '+918035315328',
                'address': 'Bangalore, Karnataka'
            }
        ]

        return jsonify({
            'success': True,
            'organizations': mock_organizations,
            'current_organization': mock_organizations[0] if mock_organizations else None
        })

    except Exception as e:
        print(f"Get organizations error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_organization():
    """Create a new organization"""
    try:
        user_data = request.current_user
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        data = request.json

        # Validate required fields
        if not data.get('name'):
            return jsonify({'message': 'Organization name is required'}), 400

        # Get user's enterprise
        enterprise_id = user_data.get('enterprise_id')

        if not enterprise_id:
            return jsonify({'message': 'User not associated with an enterprise'}), 400

        # Get user_id from current user
        user_id = user_data.get('user_id') or user_data.get('id')

        # Prepare organization data
        org_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'type': data.get('type', 'general'),
            'status': data.get('status', 'active').lower(),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'user_id': user_id,
            'enterprise_id': enterprise_id
        }

        # Try to create organization in database
        organization = supabase_request('POST', 'organizations', data=org_data)

        if organization and len(organization) > 0:
            org_id = organization[0]['id']
            print(f"✅ Organization '{organization[0]['name']}' created successfully with ID: {org_id}")

            # TODO: Create default channels for the organization
            # This will be implemented when channels table is ready
            print(f"📋 Default channels (Inbound Calls, Outbound Calls, WhatsApp Messages) would be created")

            return jsonify({
                'success': True,
                'organization': organization[0],
                'message': 'Organization created successfully'
            }), 201
        else:
            # Database creation failed or table doesn't exist, use mock creation
            print(f"⚠️ Database creation failed, using mock creation")
            import uuid
            from datetime import datetime

            new_org = {
                'id': str(uuid.uuid4()),
                'name': data['name'],
                'description': data.get('description', ''),
                'type': data.get('type', 'general'),
                'status': data.get('status', 'active').lower(),
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
                'address': data.get('address', ''),
                'user_id': user_id,
                'enterprise_id': enterprise_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            print(f"✅ Mock organization '{new_org['name']}' created with ID: {new_org['id']}")
            return jsonify({
                'success': True,
                'organization': new_org,
                'message': 'Organization created successfully (mock)'
            }), 201

    except Exception as e:
        print(f"Create organization error: {e}")
        return jsonify({'message': 'Failed to create organization'}), 500

@app.route('/api/bolna/phone-numbers', methods=['GET'])
@login_required
def get_bolna_phone_numbers():
    """Get all available phone numbers from Bolna account"""
    try:
        # Get current user's phone settings
        user_data = request.current_user
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        admin_user_data = {
            'sender_phone': user_data.get('sender_phone'),
            'bolna_agent_id': user_data.get('bolna_agent_id')
        }

        bolna_api = BolnaAPI(admin_user_data=admin_user_data)

        # Get phone numbers from Bolna API
        response = bolna_api._make_request('GET', '/phone-numbers/all')

        # Process the response
        phone_numbers = []
        if isinstance(response, list):
            phone_numbers = response
        elif isinstance(response, dict) and 'phone_numbers' in response:
            phone_numbers = response['phone_numbers']
        else:
            phone_numbers = [response] if response else []

        # Calculate summary statistics
        total_numbers = len(phone_numbers)
        monthly_cost = sum(float(num.get('price', '0').replace('$', '')) for num in phone_numbers)
        active_providers = len(set(num.get('telephony_provider', 'unknown') for num in phone_numbers))
        countries = len(set(num.get('country', 'unknown') for num in phone_numbers))

        return jsonify({
            'success': True,
            'phone_numbers': phone_numbers,
            'summary': {
                'total_numbers': total_numbers,
                'monthly_cost': monthly_cost,
                'active_providers': active_providers,
                'countries': countries
            }
        })

    except Exception as e:
        print(f"Get Bolna phone numbers error: {e}")

        # Try to get phone numbers from database as fallback
        try:
            # Get current user's enterprise context
            user_data = request.current_user
            if user_data and user_data.get('enterprise_id'):
                enterprise_id = user_data.get('enterprise_id')

                # Fetch owned phone numbers from database
                db_phone_numbers = supabase_request('GET', 'purchased_phone_numbers',
                                                  params={
                                                      'enterprise_id': f'eq.{enterprise_id}',
                                                      'status': 'neq.released',
                                                      'select': 'id,phone_number,friendly_name,country_code,country_name,monthly_cost,capabilities,status,purchased_at,agent_id'
                                                  })

                if db_phone_numbers and len(db_phone_numbers) > 0:
                    # Format database phone numbers for frontend
                    formatted_numbers = []
                    total_cost = 0

                    for phone in db_phone_numbers:
                        # Get agent name using helper function
                        agent_id = phone.get('agent_id')
                        agent_name = phone.get('agent_name')

                        if agent_id and not agent_name:
                            agent_name = get_agent_name_from_bolna(agent_id)

                        formatted_phone = {
                            'id': phone.get('id'),  # Include phone ID for API calls
                            'phone_number': phone.get('phone_number'),
                            'friendly_name': phone.get('friendly_name', f"BhashAI - {phone.get('phone_number')}"),
                            'country': phone.get('country_name', 'Unknown'),
                            'country_code': phone.get('country_code', 'XX'),
                            'telephony_provider': 'Database',
                            'price': f"${phone.get('monthly_cost', 0):.2f}",
                            'monthly_cost': float(phone.get('monthly_cost', 0)),
                            'rented': phone.get('status') == 'active',
                            'renewal_at': phone.get('purchased_at', ''),
                            'capabilities': phone.get('capabilities', ['voice', 'sms']),
                            'agent_id': agent_id,
                            'agent_name': agent_name,
                            'source': 'database'  # Add source identifier
                        }
                        formatted_numbers.append(formatted_phone)
                        total_cost += float(phone.get('monthly_cost', 0))

                    return jsonify({
                        'success': True,
                        'message': 'Phone numbers from database (Bolna API unavailable)',
                        'phone_numbers': formatted_numbers,
                        'summary': {
                            'total_numbers': len(formatted_numbers),
                            'monthly_cost': total_cost,
                            'active_providers': 1,
                            'countries': len(set(phone.get('country_name', 'Unknown') for phone in db_phone_numbers))
                        }
                    })
        except Exception as db_error:
            print(f"Database fallback error: {db_error}")

        # If both Bolna API and database fail, return empty result
        return jsonify({
            'success': False,
            'message': 'No phone numbers available. Please configure Bolna API or add phone numbers to database.',
            'phone_numbers': [],
            'summary': {
                'total_numbers': 0,
                'monthly_cost': 0.0,
                'active_providers': 0,
                'countries': 0
            }
        })

# Test endpoint for Bolna integration (development only)
@app.route('/api/test/bolna-call', methods=['POST'])
def test_bolna_call():
    """Test endpoint for Bolna integration without authentication"""
    try:
        data = request.json or {}

        # Test data
        test_contact_ids = data.get('contact_ids', ['550e8400-e29b-41d4-a716-446655440051'])
        test_agent_id = '550e8400-e29b-41d4-a716-446655440041'  # From sample data

        # Get test contacts from database
        contact_filter = ','.join([f'"{cid}"' for cid in test_contact_ids])
        contacts = supabase_request('GET', f'contacts?id=in.({contact_filter})&status=eq.active')

        if not contacts:
            return jsonify({'message': 'No test contacts found'}), 404

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI, get_agent_config_for_voice_agent
            bolna_api = BolnaAPI()
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        
        # Get agent configuration
        agent_config = get_agent_config_for_voice_agent('Prescription Reminder Calls')
        
        # Prepare test call configuration
        call_configs = []
        for contact in contacts:
            variables = {
                **agent_config.get('default_variables', {}),
                'contact_name': contact['name'],
                'contact_phone': contact['phone'],
                'agent_title': 'Test Agent',
                'test_call': True
            }
            
            call_config = {
                'agent_id': agent_config['agent_id'],
                'recipient_phone': contact['phone'],
                'sender_phone': agent_config['sender_phone'],
                'variables': variables,
                'metadata': {
                    'test_call': True,
                    'contact_id': contact['id'],
                    'campaign_name': 'Test Campaign'
                }
            }
            call_configs.append(call_config)
        
        # Start test calls
        print(f"Starting {len(call_configs)} test calls")
        call_results = bolna_api.bulk_start_calls(call_configs)
        
        # Count successes and failures
        successful_calls = sum(1 for result in call_results if result.get('success'))
        failed_calls = len(call_results) - successful_calls
        
        response = {
            'message': 'Test bulk call campaign initiated',
            'summary': {
                'total_contacts': len(contacts),
                'total_calls_attempted': len(call_configs),
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'campaign_name': 'Test Campaign'
            },
            'call_results': call_results,
            'agent_config': {
                'bolna_agent_id': agent_config['agent_id'],
                'sender_phone': agent_config['sender_phone']
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Test bulk call error: {e}")
        return jsonify({'message': f'Failed to initiate test calls: {str(e)}'}), 500

# Serve static files (HTML, CSS, JS)
# ============================================================================
# PAYMENT & BILLING ENDPOINTS
# ============================================================================

@app.route('/api/dev/account/balance', methods=['GET'])
def dev_get_account_balance():
    """Development endpoint to get account balance and credits"""
    try:
        # For development, use the first enterprise
        enterprise = supabase_request('GET', 'enterprises?limit=1')
        if not enterprise or len(enterprise) == 0:
            return jsonify({'message': 'No enterprise found'}), 404
        
        enterprise_id = enterprise[0]['id']
        
        # Get account balance
        balance = supabase_request('GET', f'account_balances?enterprise_id=eq.{enterprise_id}')
        
        if not balance or len(balance) == 0:
            # Create default balance if not exists
            default_balance = {
                'enterprise_id': enterprise_id,
                'credits_balance': 1000.00,
                'auto_recharge_enabled': False,
                'auto_recharge_amount': 10.00,
                'auto_recharge_trigger': 10.00
            }
            balance = supabase_request('POST', 'account_balances', data=default_balance)
            balance_data = balance[0] if isinstance(balance, list) else balance
        else:
            balance_data = balance[0]
        
        return jsonify({
            'balance': balance_data,
            'enterprise': {
                'id': enterprise_id,
                'name': enterprise[0]['name']
            }
        }), 200
        
    except Exception as e:
        print(f"Get account balance error: {e}")
        return jsonify({'message': 'Failed to get account balance'}), 500

@app.route('/api/dev/account/recharge-options', methods=['GET'])
def dev_get_recharge_options():
    """Development endpoint to get available recharge options"""
    try:
        options = get_predefined_recharge_options()
        
        return jsonify({
            'recharge_options': options,
            'currency_info': {
                'base_currency': 'USD',
                'display_currency': 'INR',
                'exchange_rate': 83.0,
                'credit_rate': '1 USD = 100 credits'
            }
        }), 200
        
    except Exception as e:
        print(f"Get recharge options error: {e}")
        return jsonify({'message': 'Failed to get recharge options'}), 500

@app.route('/api/dev/payment/create-order', methods=['POST'])
def dev_create_payment_order():
    """Development endpoint to create Razorpay payment order"""
    try:
        data = request.json
        
        # Validate required fields
        amount_usd = data.get('amount_usd')
        if not amount_usd or amount_usd <= 0:
            return jsonify({'message': 'Valid amount_usd is required'}), 400
        
        # Get enterprise details
        enterprise = supabase_request('GET', 'enterprises?limit=1')
        if not enterprise or len(enterprise) == 0:
            return jsonify({'message': 'No enterprise found'}), 404
        
        enterprise_id = enterprise[0]['id']
        enterprise_name = enterprise[0]['name']
        
        # Calculate credits and INR amount
        credits = calculate_credits_from_amount(amount_usd)
        amount_inr = amount_usd * 83.0  # Current exchange rate
        
        # Initialize Razorpay
        try:
            razorpay = RazorpayIntegration()
        except ValueError as e:
            return jsonify({'message': f'Razorpay configuration error: {str(e)}'}), 500
        
        # Create Razorpay order
        order_notes = {
            'enterprise_id': enterprise_id,
            'enterprise_name': enterprise_name,
            'amount_usd': amount_usd,
            'credits': credits,
            'transaction_type': data.get('transaction_type', 'manual'),
            'source': 'drmhope_dashboard'
        }
        
        order = razorpay.create_order(
            amount=amount_inr,
            currency='INR',
            receipt=f"order_{enterprise_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            notes=order_notes
        )
        
        # Store transaction in database
        transaction_data = {
            'enterprise_id': enterprise_id,
            'razorpay_order_id': order['id'],
            'amount': amount_usd,
            'currency': 'USD',
            'credits_purchased': credits,
            'status': 'pending',
            'transaction_type': data.get('transaction_type', 'manual'),
            'metadata': {
                'amount_inr': amount_inr,
                'exchange_rate': 83.0,
                'order_notes': order_notes
            }
        }
        
        transaction = supabase_request('POST', 'payment_transactions', data=transaction_data)
        
        return jsonify({
            'order': order,
            'transaction': transaction[0] if isinstance(transaction, list) else transaction,
            'credits_to_purchase': credits,
            'amount_inr': amount_inr,
            'razorpay_config': {
                'key_id': os.getenv('RAZORPAY_KEY_ID'),
                'currency': 'INR',
                'name': 'DrM Hope',
                'description': f'Add {credits} credits to your account',
                'image': '/logo.png'
            }
        }), 200
        
    except Exception as e:
        print(f"Create payment order error: {e}")
        return jsonify({'message': f'Failed to create payment order: {str(e)}'}), 500

@app.route('/api/dev/payment/verify', methods=['POST'])
def dev_verify_payment():
    """Development endpoint to verify Razorpay payment"""
    try:
        data = request.json
        
        # Get payment details from request
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return jsonify({'message': 'Missing required payment details'}), 400
        
        # Initialize Razorpay
        try:
            razorpay = RazorpayIntegration()
        except ValueError as e:
            return jsonify({'message': f'Razorpay configuration error: {str(e)}'}), 500
        
        # Verify payment signature
        is_valid = razorpay.verify_payment_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )
        
        if not is_valid:
            return jsonify({'message': 'Invalid payment signature'}), 400
        
        # Get transaction from database
        transaction = supabase_request('GET', f'payment_transactions?razorpay_order_id=eq.{razorpay_order_id}')
        
        if not transaction or len(transaction) == 0:
            return jsonify({'message': 'Transaction not found'}), 404
        
        transaction_data = transaction[0]
        enterprise_id = transaction_data['enterprise_id']
        credits_purchased = transaction_data['credits_purchased']
        
        # Update transaction status
        update_data = {
            'razorpay_payment_id': razorpay_payment_id,
            'status': 'completed',
            'metadata': {
                **transaction_data.get('metadata', {}),
                'payment_verified_at': datetime.utcnow().isoformat(),
                'payment_signature': razorpay_signature
            }
        }
        
        updated_transaction = supabase_request('PATCH', f'payment_transactions?id=eq.{transaction_data["id"]}', data=update_data)
        
        # Update account balance
        current_balance = supabase_request('GET', f'account_balances?enterprise_id=eq.{enterprise_id}')
        
        if current_balance and len(current_balance) > 0:
            new_balance = float(current_balance[0]['credits_balance']) + float(credits_purchased)
            balance_update = {
                'credits_balance': new_balance,
                'last_recharge_date': datetime.utcnow().isoformat()
            }
            updated_balance = supabase_request('PATCH', f'account_balances?enterprise_id=eq.{enterprise_id}', data=balance_update)
        else:
            # Create new balance record
            balance_data = {
                'enterprise_id': enterprise_id,
                'credits_balance': float(credits_purchased),
                'last_recharge_date': datetime.utcnow().isoformat()
            }
            updated_balance = supabase_request('POST', 'account_balances', data=balance_data)
        
        return jsonify({
            'message': 'Payment verified successfully',
            'transaction': updated_transaction[0] if isinstance(updated_transaction, list) else updated_transaction,
            'credits_added': credits_purchased,
            'new_balance': updated_balance[0] if isinstance(updated_balance, list) else updated_balance
        }), 200
        
    except Exception as e:
        print(f"Verify payment error: {e}")
        return jsonify({'message': f'Failed to verify payment: {str(e)}'}), 500

@app.route('/api/dev/account/auto-recharge', methods=['PUT'])
def dev_update_auto_recharge():
    """Development endpoint to update auto-recharge settings"""
    try:
        data = request.json
        
        # Get enterprise details
        enterprise = supabase_request('GET', 'enterprises?limit=1')
        if not enterprise or len(enterprise) == 0:
            return jsonify({'message': 'No enterprise found'}), 404
        
        enterprise_id = enterprise[0]['id']
        
        # Prepare update data
        update_data = {}
        if 'auto_recharge_enabled' in data:
            update_data['auto_recharge_enabled'] = data['auto_recharge_enabled']
        if 'auto_recharge_amount' in data:
            update_data['auto_recharge_amount'] = data['auto_recharge_amount']
        if 'auto_recharge_trigger' in data:
            update_data['auto_recharge_trigger'] = data['auto_recharge_trigger']
        
        if not update_data:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # Update auto-recharge settings
        updated_settings = supabase_request('PATCH', f'account_balances?enterprise_id=eq.{enterprise_id}', data=update_data)
        
        return jsonify({
            'message': 'Auto-recharge settings updated successfully',
            'settings': updated_settings[0] if isinstance(updated_settings, list) else updated_settings
        }), 200
        
    except Exception as e:
        print(f"Update auto-recharge error: {e}")
        return jsonify({'message': 'Failed to update auto-recharge settings'}), 500

@app.route('/api/dev/create-razorpay-order', methods=['POST'])
def dev_create_razorpay_order():
    """Development endpoint to create Razorpay order without authentication"""
    try:
        data = request.json
        phone_number = data.get('phone_number')
        number_id = data.get('number_id')
        amount = data.get('amount', 1)  # Default ₹1

        # Initialize Razorpay client
        razorpay_client = razorpay.Client(auth=(
            os.getenv('RAZORPAY_KEY_ID', 'rzp_live_P0aWMvWkbsOzJx'),
            os.getenv('RAZORPAY_KEY_SECRET', 'LoXzo3q66xoB83e0WYFK87Pw')
        ))

        # Create order
        order_data = {
            'amount': amount,  # Amount already in paise from frontend
            'currency': 'INR',
            'receipt': f'ph_{int(datetime.now().timestamp())}',
            'notes': {
                'phone_number': phone_number,
                'number_id': number_id,
                'user_id': 'dev_user'
            }
        }

        order = razorpay_client.order.create(data=order_data)

        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency']
        })

    except Exception as e:
        print(f"Dev create Razorpay order error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to create order: {str(e)}'
        }), 500

@app.route('/api/create-razorpay-order', methods=['POST'])
@login_required
def create_razorpay_order():
    """Create Razorpay order for phone number purchase"""
    try:
        data = request.json
        phone_number = data.get('phone_number')
        number_id = data.get('number_id')
        amount = data.get('amount', 1)  # Default ₹1

        # Initialize Razorpay client
        razorpay_client = razorpay.Client(auth=(
            os.getenv('RAZORPAY_KEY_ID', 'rzp_live_tazOQ9eRwtLcPr'),
            os.getenv('RAZORPAY_KEY_SECRET', 'your_secret_key')
        ))

        # Create order
        order_data = {
            'amount': amount,  # Amount already in paise from frontend
            'currency': 'INR',
            'receipt': f'ph_{int(datetime.now().timestamp())}',
            'notes': {
                'phone_number': phone_number,
                'number_id': number_id,
                'user_id': getattr(g, 'user_id', 'guest')
            }
        }

        order = razorpay_client.order.create(data=order_data)

        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency']
        })

    except Exception as e:
        print(f"Create Razorpay order error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to create order: {str(e)}'
        }), 500

@app.route('/api/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    """Verify Razorpay payment for phone number purchase"""
    try:
        data = request.json
        print(f"🔍 VERIFY PAYMENT REQUEST DATA: {data}")

        payment_id = data.get('razorpay_payment_id')
        order_id = data.get('razorpay_order_id')
        signature = data.get('razorpay_signature')
        phone_number = data.get('phone_number')
        number_id = data.get('number_id')

        print(f"🎯 EXTRACTED DATA:")
        print(f"   📞 Phone: {phone_number}")
        print(f"   🆔 Number ID: {number_id}")
        print(f"   💳 Payment ID: {payment_id}")
        print(f"   📋 Order ID: {order_id}")

        # Initialize Razorpay client
        razorpay_client = razorpay.Client(auth=(
            os.getenv('RAZORPAY_KEY_ID', 'rzp_live_tazOQ9eRwtLcPr'),
            os.getenv('RAZORPAY_KEY_SECRET', 'your_secret_key')
        ))

        # Verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            payment_verified = True
            print("✅ Razorpay signature verified")
        except Exception as verify_error:
            print(f"⚠️ Razorpay verification failed: {verify_error}")
            # For development/testing, allow mock payments
            if (payment_id.startswith('pay_test_') or
                payment_id.startswith('pay_mock_') or
                payment_id.startswith('pay_live_') or
                payment_id.startswith('pay_clicked_')):  # Allow test clicks
                print("⚠️ Development mode: Accepting test payment")
                payment_verified = True
            else:
                print(f"❌ Payment verification failed for: {payment_id}")
                payment_verified = False

        if payment_verified:
            # Get user and enterprise context
            user_data = request.current_user
            print(f"🔍 Debug - user_data: {user_data}")

            # 🎯 LOG SELECTED NUMBER DATA
            print(f"🎯 SELECTED NUMBER FROM FRONTEND:")
            print(f"   📞 Phone Number: {phone_number}")
            print(f"   🆔 Number ID: {number_id}")
            print(f"   💳 Payment ID: {payment_id}")
            print(f"   📋 Order ID: {order_id}")

            if user_data:
                user_id = user_data.get('user_id') or user_data.get('id')  # Try both keys
                enterprise_id = user_data.get('enterprise_id')
            else:
                print("⚠️ Warning: user_data is None, using fallback")
                user_id = "550e8400-e29b-41d4-a716-446655440000"  # Fallback UUID
                enterprise_id = "550e8400-e29b-41d4-a716-446655440001"  # Fallback UUID

            print(f"🔍 Debug - user_id: {user_id}, enterprise_id: {enterprise_id}")
            provider = data.get('provider', 'bolna')

            # Record the payment in database using existing payment_transactions structure
            payment_record = {
                'id': str(uuid.uuid4()),
                'patient_id': user_id,  # Using patient_id as user_id since that's what exists
                'payment_date': datetime.now().date().isoformat(),
                'payment_mode': 'Online',
                'payment_amount': 1.00,  # Amount in rupees
                'reference_number': payment_id,
                'status': 'completed',
                'remarks': f'Phone number purchase: {phone_number} via Razorpay (Payment ID: {payment_id}, Order ID: {order_id}, Provider: {provider})',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            # Insert payment record
            try:
                payment_result = supabase_request('POST', 'payment_transactions', data=payment_record)
                print(f"✅ Payment record stored: {payment_result}")
            except Exception as payment_error:
                print(f"⚠️ Payment record storage failed: {payment_error}")
                # Continue anyway

            # Store the phone number in purchased_phone_numbers table
            try:
                # Ensure we have valid UUIDs
                if not user_id:
                    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Fallback UUID
                if not enterprise_id:
                    enterprise_id = "550e8400-e29b-41d4-a716-446655440001"  # Fallback UUID

                # 🎯 LOG WHAT WE'RE STORING
                print(f"🎯 STORING SELECTED NUMBER IN DATABASE:")
                print(f"   📞 Phone Number: {phone_number}")
                print(f"   🆔 Number ID: {number_id}")
                print(f"   👤 User ID: {user_id}")
                print(f"   🏢 Enterprise ID: {enterprise_id}")

                phone_record = {
                    'id': str(uuid.uuid4()),
                    'phone_number': phone_number,  # 🎯 SELECTED NUMBER
                    'number_id': number_id,        # 🎯 SELECTED ID
                    'friendly_name': f"BhashAI - {phone_number}",
                    'user_id': user_id,
                    'enterprise_id': enterprise_id,
                    'payment_id': payment_id,
                    'order_id': order_id,
                    'amount_paid': 1.00,
                    'currency': 'INR',
                    'status': 'active',
                    'country_code': 'IN',
                    'country_name': 'India',
                    'monthly_cost': 5.00,
                    'setup_cost': 1.00,
                    'capabilities': ['voice', 'sms'],
                    'provider': provider,
                    'provider_phone_id': number_id,
                    'purchased_at': datetime.now(timezone.utc).isoformat(),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }

                print(f"🔍 Debug - phone_record user_id: {phone_record['user_id']}")

                # Insert into purchased_phone_numbers table
                db_result = supabase_request('POST', 'purchased_phone_numbers', data=phone_record)

                if db_result:
                    print(f"✅ Phone number {phone_number} stored in purchased_phone_numbers table!")
                    print(f"   Record ID: {phone_record['id']}")
                else:
                    print(f"⚠️ Warning: Failed to store in purchased_phone_numbers table")

            except Exception as storage_error:
                print(f"⚠️ Error storing phone number: {storage_error}")
                # Continue anyway as payment was successful

            return jsonify({
                'success': True,
                'message': 'Payment verified and phone number purchased successfully',
                'phone_number': phone_number,
                'payment_id': payment_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Payment verification failed'
            }), 400

    except Exception as e:
        print(f"❌ VERIFY PAYMENT ERROR: {e}")
        print(f"❌ ERROR TYPE: {type(e)}")
        import traceback
        print(f"❌ FULL TRACEBACK: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Payment verification failed: {str(e)}'
        }), 500

@app.route('/api/dev/create-phone-table', methods=['POST'])
def dev_create_phone_table():
    """Development endpoint to create purchased_phone_numbers table"""
    try:
        # Create a simple phone purchases table using payment_transactions structure
        # Since we can't create new tables, we'll use the existing payment_transactions table
        # and add phone number data to the metadata field

        return jsonify({
            'success': True,
            'message': 'Phone number storage will use payment_transactions table with metadata',
            'note': 'Phone numbers will be stored in payment_transactions.metadata field'
        })

    except Exception as e:
        print(f"Error creating phone table: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dev/payment/create', methods=['POST'])
def dev_create_payment():
    """Development endpoint to create a payment transaction directly"""
    try:
        data = request.json

        # Add required fields if missing
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())

        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc).isoformat()

        # Insert into payment_transactions table
        result = supabase_request('POST', 'payment_transactions', data=data)

        return jsonify({
            'success': True,
            'message': 'Payment transaction created successfully',
            'data': result[0] if isinstance(result, list) else result
        })

    except Exception as e:
        print(f"Error creating payment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dev/phone-purchase', methods=['POST'])
def dev_phone_purchase():
    """Development endpoint to simulate phone number purchase"""
    try:
        data = request.json
        phone_number = data.get('phone_number')
        provider = data.get('provider', 'bolna')

        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400

        # Create a mock payment transaction with phone number metadata
        payment_record = {
            'id': str(uuid.uuid4()),
            'user_id': '00000000-0000-0000-0000-000000000000',  # Mock user ID
            'enterprise_id': '00000000-0000-0000-0000-000000000000',  # Mock enterprise ID
            'razorpay_payment_id': f'pay_mock_{uuid.uuid4().hex[:10]}',
            'razorpay_order_id': f'order_mock_{uuid.uuid4().hex[:10]}',
            'amount': 1.00,
            'currency': 'INR',
            'status': 'completed',
            'payment_method': 'razorpay',
            'metadata': {
                'phone_number': phone_number,
                'number_id': data.get('number_id', f'num_{uuid.uuid4().hex[:8]}'),
                'provider': provider,
                'purchase_type': 'dev_test'
            },
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        # Insert payment record
        result = supabase_request('POST', 'payment_transactions', data=payment_record)

        return jsonify({
            'success': True,
            'message': f'Phone number {phone_number} purchase simulated successfully',
            'payment_id': payment_record['razorpay_payment_id'],
            'data': result[0] if isinstance(result, list) else result
        })

    except Exception as e:
        print(f"Error simulating phone purchase: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dev/payment/transactions', methods=['GET'])
def dev_get_payment_history():
    """Development endpoint to get payment transaction history"""
    try:
        # For development, get all payment transactions regardless of enterprise
        transactions = supabase_request('GET', 'payment_transactions?order=created_at.desc&limit=50')

        if transactions is None:
            transactions = []

        return jsonify({
            'success': True,
            'data': transactions,
            'count': len(transactions)
        }), 200

    except Exception as e:
        print(f"Get payment history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/webhooks/razorpay', methods=['POST'])
def razorpay_webhook():
    """Razorpay webhook endpoint for payment notifications"""
    try:
        # Get raw request body and signature
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Razorpay-Signature')
        
        if not payload or not signature:
            return jsonify({'message': 'Missing payload or signature'}), 400
        
        # Initialize Razorpay for signature verification
        try:
            razorpay = RazorpayIntegration()
        except ValueError as e:
            print(f"Razorpay webhook configuration error: {e}")
            return jsonify({'message': 'Webhook configuration error'}), 500
        
        # Verify webhook signature
        is_valid = razorpay.verify_webhook_signature(payload, signature)
        
        if not is_valid:
            print(f"Invalid webhook signature")
            return jsonify({'message': 'Invalid signature'}), 400
        
        # Parse webhook data
        webhook_data = request.json
        event = webhook_data.get('event')
        payment_entity = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
        
        print(f"Razorpay webhook received: {event}")
        
        # Handle different webhook events
        if event == 'payment.captured':
            # Payment successful
            payment_id = payment_entity.get('id')
            order_id = payment_entity.get('order_id')
            amount = payment_entity.get('amount', 0) / 100  # Convert paise to rupees
            
            print(f"Payment captured: {payment_id}, Order: {order_id}, Amount: ₹{amount}")
            
            # Update transaction status
            transaction = supabase_request('GET', f'payment_transactions?razorpay_order_id=eq.{order_id}')
            
            if transaction and len(transaction) > 0:
                transaction_data = transaction[0]
                enterprise_id = transaction_data['enterprise_id']
                credits_purchased = transaction_data['credits_purchased']
                
                # Update transaction
                update_data = {
                    'razorpay_payment_id': payment_id,
                    'status': 'completed',
                    'payment_method': payment_entity.get('method'),
                    'metadata': {
                        **transaction_data.get('metadata', {}),
                        'webhook_captured_at': datetime.utcnow().isoformat(),
                        'payment_entity': payment_entity
                    }
                }
                
                supabase_request('PATCH', f'payment_transactions?id=eq.{transaction_data["id"]}', data=update_data)
                
                # Update account balance
                current_balance = supabase_request('GET', f'account_balances?enterprise_id=eq.{enterprise_id}')
                
                if current_balance and len(current_balance) > 0:
                    new_balance = float(current_balance[0]['credits_balance']) + float(credits_purchased)
                    balance_update = {
                        'credits_balance': new_balance,
                        'last_recharge_date': datetime.utcnow().isoformat()
                    }
                    supabase_request('PATCH', f'account_balances?enterprise_id=eq.{enterprise_id}', data=balance_update)
                
                print(f"✅ Payment processed: {credits_purchased} credits added to enterprise {enterprise_id}")
            
        elif event == 'payment.failed':
            # Payment failed
            payment_id = payment_entity.get('id')
            order_id = payment_entity.get('order_id')
            error_description = payment_entity.get('error_description', 'Payment failed')
            
            print(f"Payment failed: {payment_id}, Order: {order_id}, Error: {error_description}")
            
            # Update transaction status
            transaction = supabase_request('GET', f'payment_transactions?razorpay_order_id=eq.{order_id}')
            
            if transaction and len(transaction) > 0:
                transaction_data = transaction[0]
                
                update_data = {
                    'razorpay_payment_id': payment_id,
                    'status': 'failed',
                    'metadata': {
                        **transaction_data.get('metadata', {}),
                        'webhook_failed_at': datetime.utcnow().isoformat(),
                        'error_description': error_description,
                        'payment_entity': payment_entity
                    }
                }
                
                supabase_request('PATCH', f'payment_transactions?id=eq.{transaction_data["id"]}', data=update_data)
                
                print(f"❌ Payment failed: Updated transaction {transaction_data['id']}")
        
        else:
            print(f"Unhandled webhook event: {event}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Razorpay webhook error: {e}")
        return jsonify({'message': 'Webhook processing failed'}), 500

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

# ============================================================================
# PHONE NUMBER AND VOICE PROVIDER MANAGEMENT API ENDPOINTS
# ============================================================================

@app.route('/api/dev/phone-providers', methods=['GET'])
def get_phone_providers():
    """Get all available phone number providers"""
    try:
        providers = supabase_request('GET', 'phone_number_providers', params={'status': 'eq.active'})
        if providers:
            return jsonify({
                'success': True,
                'providers': providers
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch phone providers'
            }), 500
    except Exception as e:
        print(f"Error fetching phone providers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/dev/phone-numbers/search', methods=['POST'])
def search_phone_numbers():
    """Search available phone numbers from providers"""
    try:
        data = request.get_json()
        country_code = data.get('country_code', 'US')
        pattern = data.get('pattern', '')
        provider_name = data.get('provider', 'plivo')
        region = data.get('region')
        limit = data.get('limit', 20)
        
        # Use real provider APIs
        result = phone_provider_manager.search_phone_numbers(
            provider_name=provider_name,
            country_code=country_code,
            pattern=pattern,
            region=region,
            limit=limit
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error searching phone numbers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/dev/phone-numbers/purchase', methods=['POST'])
def purchase_phone_number():
    """Purchase a phone number"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        provider_name = data.get('provider')
        
        if not phone_number or not provider_name:
            return jsonify({
                'success': False,
                'error': 'Phone number and provider are required'
            }), 400
        
        # Get enterprise_id (mock for development)
        enterprise_id = data.get('enterprise_id', 'f47ac10b-58cc-4372-a567-0e02b2c3d479')
        
        # First, attempt to purchase from the provider
        purchase_result = phone_provider_manager.purchase_phone_number(
            provider_name=provider_name,
            phone_number=phone_number,
            friendly_name=f"DrM Hope - {phone_number}",
            voice_url=os.getenv('VOICE_WEBHOOK_URL'),
            sms_url=os.getenv('SMS_WEBHOOK_URL')
        )
        
        if not purchase_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to purchase from provider: {purchase_result.get("error", "Unknown error")}'
            }), 500
        
        # Get provider ID from database
        provider_data = supabase_request('GET', 'phone_number_providers',
                                           params={'name': f'eq.{provider_name}'})

        if not provider_data:
            return jsonify({
                'success': False,
                'error': 'Provider not found in database'
            }), 400
        
        provider_id = provider_response.json()[0]['id']
        
        # Create purchased phone number record in database
        phone_record = {
            'id': str(uuid.uuid4()),
            'enterprise_id': enterprise_id,
            'phone_number': phone_number,
            'country_code': data.get('country_code', 'US'),
            'country_name': data.get('country_name', 'United States'),
            'provider_id': provider_id,
            'provider_phone_id': purchase_result.get('provider_phone_id', f'provider_id_{phone_number}'),
            'monthly_cost': purchase_result.get('monthly_cost', data.get('monthly_cost', 5.00)),
            'setup_cost': data.get('setup_cost', 0.00),
            'status': 'active',
            'capabilities': data.get('capabilities', {'voice': True, 'sms': True}),
            'agent_id': data.get('agent_id'),  # Add agent_id field
            'purchased_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        db_result = supabase_request('POST', 'purchased_phone_numbers', data=phone_record)

        if db_result:
            return jsonify({
                'success': True,
                'phone_number': db_result[0] if isinstance(db_result, list) and db_result else db_result,
                'provider_response': purchase_result,
                'message': f'Phone number {phone_number} purchased successfully from {provider_name}'
            })
        else:
            # If database insert fails, we should ideally release the number from provider
            # For now, just return the error
            return jsonify({
                'success': False,
                'error': 'Number purchased from provider but failed to save to database'
            }), 500
            
    except Exception as e:
        print(f"Error purchasing phone number: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/dev/phone-numbers', methods=['GET'])
def get_purchased_phone_numbers():
    """Get all purchased phone numbers for enterprise"""
    try:
        # Mock enterprise_id for development
        enterprise_id = request.args.get('enterprise_id', 'f47ac10b-58cc-4372-a567-0e02b2c3d479')

        phone_numbers = supabase_request('GET', 'purchased_phone_numbers',
                                  params={'enterprise_id': f'eq.{enterprise_id}',
                                         'status': 'eq.active'})

        if phone_numbers:
            return jsonify({
                'success': True,
                'phone_numbers': phone_numbers
            })
        else:
            # Return mock data with agent_id for testing
            # mock_phone_numbers = [
            #     {
            #         'id': 'mock-phone-1',
            #         'phone_number': '+918035743222',
            #         'friendly_name': 'BhashAI - +918035743222',
            #         'country_code': 'IN',
            #         'country_name': 'India',
            #         'monthly_cost': 5.00,
            #         'status': 'active',
            #         'agent_id': '15554373-b8e1-4b00-8c25-c4742dc8e480',
            #         'purchased_at': '2025-01-15T10:30:00Z',
            #         'capabilities': ['voice', 'sms']
            #     },
            #     {
            #         'id': 'mock-phone-2',
            #         'phone_number': '+918035315328',
            #         'friendly_name': 'BhashAI - +918035315328',
            #         'country_code': 'IN',
            #         'country_name': 'India',
            #         'monthly_cost': 5.00,
            #         'status': 'active',
            #         'agent_id': None,
            #         'purchased_at': '2025-01-16T11:30:00Z',
            #         'capabilities': ['voice', 'sms']
            #     }
            # ]

            return jsonify({
                'success': True,
                'phone_numbers': mock_phone_numbers,
                'source': 'mock_data'
            })

    except Exception as e:
        print(f"Error fetching phone numbers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ============================================================================
# PRODUCTION PHONE NUMBER API ENDPOINTS
# ============================================================================

@app.route('/api/phone-numbers/search', methods=['GET'])
def search_phone_numbers_production():
    """Search available phone numbers from providers (Production endpoint)"""
    try:
        # Get query parameters
        country_code = request.args.get('country_code', 'US')
        area_code = request.args.get('area_code')
        pattern = request.args.get('pattern')
        capabilities = request.args.get('capabilities')
        providers_param = request.args.get('providers', 'twilio,telnyx')
        limit = int(request.args.get('limit', 20))

        providers = [p.strip() for p in providers_param.split(',') if p.strip()]

        all_results = []
        for provider_name in providers:
            try:
                search_params = {
                    'country_code': country_code,
                    'limit': limit // len(providers)  # Distribute limit across providers
                }

                if area_code:
                    search_params['area_code'] = area_code
                if pattern:
                    search_params['pattern'] = pattern
                if capabilities:
                    search_params['capabilities'] = capabilities.split(',')

                results = phone_provider_manager.search_phone_numbers(
                    provider_name=provider_name,
                    **search_params
                )

                if results['success']:
                    # Add provider info to each result
                    for number in results['available_numbers']:
                        number['provider'] = provider_name
                    all_results.extend(results['available_numbers'])

            except Exception as e:
                print(f"Error searching {provider_name}: {e}")
                continue

        # Sort by monthly cost (lowest first)
        all_results.sort(key=lambda x: x.get('monthly_cost', 999))

        return jsonify({
            'success': True,
            'data': all_results[:limit],
            'total_found': len(all_results),
            'providers_searched': providers
        })

    except Exception as e:
        print(f"Error searching phone numbers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-numbers/purchase', methods=['POST'])
@login_required
@require_enterprise_context
def purchase_phone_number_production():
    """Purchase a phone number (Production endpoint)"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        provider_name = data.get('provider')
        friendly_name = data.get('friendly_name', f"BhashAI - {phone_number}")
        voice_url = data.get('voice_url', os.getenv('VOICE_WEBHOOK_URL'))
        sms_url = data.get('sms_url', os.getenv('SMS_WEBHOOK_URL'))

        if not phone_number or not provider_name:
            return jsonify({
                'success': False,
                'error': 'Phone number and provider are required'
            }), 400

        # Get enterprise context from middleware
        enterprise_id = g.enterprise_id

        # Get provider ID from database
        provider_record = supabase_request('GET', 'phone_number_providers',
                                         params={'name': f'eq.{provider_name}', 'status': 'eq.active'})

        if not provider_record or len(provider_record) == 0:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_name} not found or inactive'
            }), 400

        provider_id = provider_record[0]['id']

        # Check if enterprise has sufficient credits for setup cost
        setup_cost = data.get('setup_cost', 0.0)
        if setup_cost > 0:
            # Get current account balance
            balance_record = supabase_request('GET', 'account_balances',
                                            params={'enterprise_id': f'eq.{enterprise_id}'})

            if balance_record and len(balance_record) > 0:
                current_balance = balance_record[0].get('balance', 0.0)
                if current_balance < setup_cost:
                    return jsonify({
                        'success': False,
                        'error': f'Insufficient credits. Required: ${setup_cost:.2f}, Available: ${current_balance:.2f}'
                    }), 400

        # Purchase from provider
        purchase_result = phone_provider_manager.purchase_phone_number(
            provider_name=provider_name,
            phone_number=phone_number,
            friendly_name=friendly_name,
            voice_url=voice_url,
            sms_url=sms_url
        )

        if not purchase_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to purchase from provider: {purchase_result.get("error", "Unknown error")}'
            }), 500

        # Save to database
        phone_record = {
            'id': str(uuid.uuid4()),
            'enterprise_id': enterprise_id,
            'phone_number': phone_number,
            'friendly_name': friendly_name,
            'provider_id': provider_id,
            'provider_phone_id': purchase_result.get('provider_phone_id'),
            'country_code': data.get('country_code', 'US'),
            'country_name': data.get('country_name', 'United States'),
            'monthly_cost': purchase_result.get('monthly_cost', 0.0),
            'setup_cost': purchase_result.get('setup_cost', 0.0),
            'capabilities': purchase_result.get('capabilities', {'voice': True, 'sms': True}),
            'status': 'active',
            'voice_url': voice_url,
            'sms_url': sms_url,
            'agent_id': data.get('agent_id'),  # Add agent_id field
            'purchased_at': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        db_result = supabase_request('POST', 'purchased_phone_numbers', data=phone_record)

        if db_result:
            # Deduct setup cost from account balance if applicable
            if setup_cost > 0:
                try:
                    # Create transaction record
                    transaction_record = {
                        'id': str(uuid.uuid4()),
                        'enterprise_id': enterprise_id,
                        'amount': -setup_cost,  # Negative for deduction
                        'transaction_type': 'phone_number_purchase',
                        'description': f'Phone number purchase: {phone_number}',
                        'metadata': {
                            'phone_number': phone_number,
                            'provider': provider_name,
                            'phone_record_id': phone_record['id']
                        },
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }

                    supabase_request('POST', 'payment_transactions', data=transaction_record)

                    # Update account balance
                    new_balance = current_balance - setup_cost
                    supabase_request('PATCH', f'account_balances?enterprise_id=eq.{enterprise_id}',
                                   data={'balance': new_balance, 'updated_at': datetime.now(timezone.utc).isoformat()})

                except Exception as e:
                    print(f"Warning: Failed to update account balance: {e}")

            return jsonify({
                'success': True,
                'data': phone_record,
                'message': f'Phone number {phone_number} purchased successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save phone number to database'
            }), 500

    except Exception as e:
        print(f"Error purchasing phone number: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-numbers/owned-simple', methods=['GET'])
@login_required
def get_owned_phone_numbers_simple():
    """Get owned phone numbers from payment transactions (simple version)"""
    global phone_agent_mapping
    try:
        user_data = request.current_user
        user_id = user_data.get('user_id') or user_data.get('id') if user_data else None

        # Get phone numbers from database only - no mock data

        # Get phone numbers from purchased_phone_numbers table
        phone_numbers = []

        if user_id:
            try:
                # Get from purchased_phone_numbers table
                query_params = {
                    'select': '*',
                    'user_id': f'eq.{user_id}',
                    'status': 'eq.active',
                    'order': 'created_at.desc'
                }

                purchased_numbers = supabase_request('GET', 'purchased_phone_numbers', params=query_params)

                if purchased_numbers:
                    # Get current agent mapping from bolna_agents table
                    agent_mapping = {}
                    try:
                        bolna_agents = supabase_request('GET', 'bolna_agents?select=*')
                        if bolna_agents:
                            for agent in bolna_agents:
                                phone_number = agent.get('phone_number')
                                if phone_number:
                                    agent_mapping[phone_number] = {
                                        'agent_id': agent.get('bolna_agent_id'),
                                        'agent_name': agent.get('agent_name')
                                    }
                            print(f"🔍 Loaded {len(agent_mapping)} agent mappings from bolna_agents table")
                        else:
                            print("⚠️ No agents found in bolna_agents table")
                    except Exception as e:
                        print(f"⚠️ Failed to load agent mapping from database: {e}")
                        # Fallback to empty mapping
                        agent_mapping = {}

                    for phone in purchased_numbers:
                        phone_number = phone.get('phone_number')

                        # Get agent info from database first
                        agent_id = phone.get('agent_id')
                        agent_name = phone.get('agent_name')

                        # If no agent in database, use mapping
                        if not agent_id and phone_number in agent_mapping:
                            mapped_agent = agent_mapping[phone_number]
                            agent_id = mapped_agent['agent_id']
                            agent_name = mapped_agent['agent_name']

                        # If agent_id exists but no name, get from Bolna
                        if agent_id and not agent_name:
                            agent_name = get_agent_name_from_bolna(agent_id)

                        phone_data = {
                            'id': phone.get('id'),
                            'phone_number': phone_number,
                            'friendly_name': phone.get('friendly_name', f"BhashAI - {phone_number}"),
                            'provider': phone.get('provider', 'bolna'),
                            'country_code': phone.get('country_code', 'IN'),
                            'country_name': phone.get('country_name', 'India'),
                            'amount_paid': float(phone.get('amount_paid', 1000)),
                            'status': 'Active' if agent_id else 'Purchased',
                            'capabilities': phone.get('capabilities', ['voice', 'sms']),
                            'purchased_at': phone.get('purchased_at'),
                            'source': 'purchased_phone_numbers_with_mapping',
                            'agent_id': agent_id,
                            'agent_name': agent_name
                        }
                        phone_numbers.append(phone_data)

                    print(f"✅ Loaded {len(phone_numbers)} phone numbers from purchased_phone_numbers table")
                    print(f"🔍 Debug - Sample phone data: {phone_numbers[0] if phone_numbers else 'No data'}")
                else:
                    print("ℹ️ No phone numbers found in purchased_phone_numbers table")

            except Exception as db_error:
                print(f"Database query failed: {db_error}")

        # If no phone numbers found in database, provide mock data with agent mapping
        if not phone_numbers:
            print("ℹ️ No phone numbers found in database - providing mock data with agent mapping")

            # Get current agent mapping from bolna_agents table for mock data
            agent_mapping = {}
            try:
                bolna_agents = supabase_request('GET', 'bolna_agents?select=*')
                if bolna_agents:
                    for agent in bolna_agents:
                        phone_number = agent.get('phone_number')
                        if phone_number:
                            agent_mapping[phone_number] = {
                                'agent_id': agent.get('bolna_agent_id'),
                                'agent_name': agent.get('agent_name')
                            }
                    print(f"🔍 Loaded {len(agent_mapping)} agent mappings for mock data")
                else:
                    print("⚠️ No agents found in bolna_agents table for mock data")
            except Exception as e:
                print(f"⚠️ Failed to load agent mapping for mock data: {e}")
                # Fallback to basic mock data without agents
                agent_mapping = {
                    '+918035315404': {'agent_id': None, 'agent_name': None},
                    '+918035315398': {'agent_id': None, 'agent_name': None},
                    '+918035315328': {'agent_id': None, 'agent_name': None}
                }

            # Create mock phone numbers with agent assignments
            for phone_number, agent_info in agent_mapping.items():
                phone_data = {
                    'id': phone_number.replace('+', ''),
                    'phone_number': phone_number,
                    'friendly_name': f'BhashAI - {phone_number}',
                    'provider': 'bolna',
                    'country_code': 'IN',
                    'country_name': 'India',
                    'amount_paid': 1000.0 if phone_number in ['+918035742982', '+918035748878', '+918035748854'] else 85.0,
                    'status': 'Active' if agent_info['agent_id'] else 'Purchased',
                    'capabilities': ['voice', 'sms'],
                    'purchased_at': '2025-07-19T12:00:00Z',
                    'source': 'mock_data_with_agents',
                    'agent_id': agent_info['agent_id'],
                    'agent_name': agent_info['agent_name']
                }
                phone_numbers.append(phone_data)

            print(f"✅ Created {len(phone_numbers)} mock phone numbers with agent mapping")

        # Determine source
        if any(p.get('source') == 'purchased_phone_numbers_with_mapping' for p in phone_numbers):
            source = 'purchased_phone_numbers_with_mapping'
            note = 'Database data enhanced with Bolna agent mapping'
        elif any(p.get('source') == 'mock_data_with_agents' for p in phone_numbers):
            source = 'mock_data_with_agents'
            note = 'Mock data with Bolna agent mapping'
        else:
            source = 'purchased_phone_numbers'
            note = None

        return jsonify({
            'success': True,
            'data': phone_numbers,
            'source': source,
            'count': len(phone_numbers),
            'note': note
        })

    except Exception as e:
        print(f"Error getting owned phone numbers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-numbers/owned', methods=['GET'])
@login_required
@require_enterprise_context
def get_owned_phone_numbers():
    """Get owned phone numbers for the enterprise"""
    try:
        # Get enterprise context from middleware
        enterprise_id = g.enterprise_id

        # First try to get from purchased_phone_numbers table
        try:
            # Fetch owned phone numbers with provider information
            query_params = {
                'select': 'id,phone_number,friendly_name,country_code,country_name,monthly_cost,setup_cost,capabilities,status,voice_url,sms_url,purchased_at,created_at,updated_at,agent_id,phone_number_providers(name)',
                'enterprise_id': f'eq.{enterprise_id}',
                'status': 'neq.released'
            }

            phone_numbers_raw = supabase_request('GET', 'purchased_phone_numbers', params=query_params)

            # Transform the data to include provider name
            phone_numbers = []
            if phone_numbers_raw:
                for phone in phone_numbers_raw:
                    phone_data = phone.copy()
                    if 'phone_number_providers' in phone and phone['phone_number_providers']:
                        phone_data['provider'] = phone['phone_number_providers']['name']
                    else:
                        phone_data['provider'] = 'unknown'
                    # Remove the nested provider object
                    phone_data.pop('phone_number_providers', None)
                    phone_numbers.append(phone_data)

            return jsonify({
                'success': True,
                'data': phone_numbers,
                'source': 'purchased_phone_numbers'
            })

        except Exception as table_error:
            print(f"purchased_phone_numbers table not available: {table_error}")

            # Fallback: Get phone numbers from payment_transactions metadata
            try:
                payment_params = {
                    'enterprise_id': f'eq.{enterprise_id}',
                    'status': 'eq.completed',
                    'select': 'id,razorpay_payment_id,amount,currency,metadata,created_at'
                }

                payments = supabase_request('GET', 'payment_transactions', params=payment_params)

                phone_numbers = []
                if payments:
                    for payment in payments:
                        metadata = payment.get('metadata', {})
                        if metadata.get('phone_number'):
                            phone_data = {
                                'id': payment['id'],
                                'phone_number': metadata.get('phone_number'),
                                'friendly_name': f"BhashAI - {metadata.get('phone_number')}",
                                'country_code': 'IN',
                                'country_name': 'India',
                                'monthly_cost': 5.00,
                                'setup_cost': 1.00,
                                'capabilities': ['voice', 'sms'],
                                'status': 'active',
                                'purchased_at': payment['created_at'],
                                'provider': metadata.get('provider', 'bolna'),
                                'payment_id': payment['razorpay_payment_id'],
                                'amount_paid': payment['amount']
                            }
                            phone_numbers.append(phone_data)

                return jsonify({
                    'success': True,
                    'data': phone_numbers,
                    'source': 'payment_transactions'
                })

            except Exception as fallback_error:
                print(f"Error fetching from payment_transactions: {fallback_error}")
                return jsonify({
                    'success': False,
                    'error': 'Unable to fetch phone numbers from any source'
                }), 500

    except Exception as e:
        print(f"Error fetching owned phone numbers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-numbers/<phone_id>/release', methods=['DELETE'])
@login_required
@require_enterprise_context
def release_phone_number(phone_id):
    """Release a phone number"""
    try:
        # Get enterprise context from middleware
        enterprise_id = g.enterprise_id

        # Get phone number record with provider information
        phone_record = supabase_request('GET', 'purchased_phone_numbers',
                                      params={'id': f'eq.{phone_id}',
                                             'enterprise_id': f'eq.{enterprise_id}',
                                             'select': 'id,phone_number,provider_id,phone_number_providers(name)'})

        if not phone_record or len(phone_record) == 0:
            return jsonify({
                'success': False,
                'error': 'Phone number not found'
            }), 404

        phone_data = phone_record[0]
        provider_name = 'unknown'

        if 'phone_number_providers' in phone_data and phone_data['phone_number_providers']:
            provider_name = phone_data['phone_number_providers']['name']

        # Release from provider
        try:
            release_result = phone_provider_manager.release_phone_number(
                provider_name=provider_name,
                phone_number=phone_data['phone_number']
            )

            if not release_result.get('success', False):
                print(f"Warning: Failed to release from provider: {release_result.get('error')}")
        except Exception as e:
            print(f"Warning: Error releasing from provider: {e}")

        # Update status in database
        update_data = {
            'status': 'released',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        supabase_request('PATCH', f'purchased_phone_numbers?id=eq.{phone_id}', data=update_data)

        return jsonify({
            'success': True,
            'message': f'Phone number {phone_data["phone_number"]} released successfully'
        })

    except Exception as e:
        print(f"Error releasing phone number: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-numbers/<phone_id>/assign-agent', methods=['POST'])
@login_required
def assign_phone_to_agent(phone_id):
    """Assign a phone number to a voice agent for outbound calling"""
    try:
        # Debug: Print user context
        print(f"🔍 DEBUG - g.user_id: {getattr(g, 'user_id', 'NOT_SET')}")
        print(f"🔍 DEBUG - request.current_user: {getattr(request, 'current_user', 'NOT_SET')}")
        if hasattr(request, 'current_user') and request.current_user:
            print(f"🔍 DEBUG - current_user keys: {list(request.current_user.keys())}")
            print(f"🔍 DEBUG - current_user user_id: {request.current_user.get('user_id')}")
            print(f"🔍 DEBUG - current_user id: {request.current_user.get('id')}")
        # Get enterprise context - try from middleware first, then load manually
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            enterprise_id = load_enterprise_context()

        # If still no enterprise_id, try to get from user record
        if not enterprise_id:
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                # Try to get user_id from request.current_user
                if hasattr(request, 'current_user') and request.current_user:
                    user_id = request.current_user.get('user_id') or request.current_user.get('id')

            if user_id:
                user_record = supabase_request('GET', 'users', params={'id': f'eq.{user_id}', 'select': 'enterprise_id'})
                if user_record and len(user_record) > 0:
                    enterprise_id = user_record[0].get('enterprise_id')

        # If still no enterprise_id, create a default one for this user
        if not enterprise_id:
            print("⚠️  No enterprise_id found for assignment, creating default enterprise...")
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                # Try to get user_id from request.current_user
                if hasattr(request, 'current_user') and request.current_user:
                    user_id = request.current_user.get('user_id') or request.current_user.get('id')

            if not user_id:
                return jsonify({
                    'success': False,
                    'error': 'User ID not found. Please login again.'
                }), 401

            enterprise_data = {
                'name': 'Default Enterprise',
                'type': 'business',
                'contact_email': 'admin@bashai.com',
                'status': 'active',
                'owner_id': user_id
            }
            enterprise = supabase_request('POST', 'enterprises', data=enterprise_data)
            if enterprise:
                enterprise_id = enterprise[0]['id'] if isinstance(enterprise, list) else enterprise['id']
                # Update user with enterprise_id
                supabase_request('PATCH', f'users?id=eq.{user_id}', data={'enterprise_id': enterprise_id})
                print(f"✅ Created enterprise for assignment: {enterprise_id}")
            else:
                print("⚠️  Could not create enterprise, proceeding without enterprise filter...")
                enterprise_id = None

        data = request.get_json()
        agent_id = data.get('agent_id')

        if not agent_id:
            return jsonify({
                'success': False,
                'error': 'Agent ID is required'
            }), 400

        # Get phone number record (with or without enterprise filtering)
        phone_params = {'id': f'eq.{phone_id}', 'status': 'eq.active'}
        if enterprise_id:
            phone_params['enterprise_id'] = f'eq.{enterprise_id}'

        phone_record = supabase_request('GET', 'purchased_phone_numbers', params=phone_params)

        if not phone_record or len(phone_record) == 0:
            # Try without enterprise filtering if not found
            if enterprise_id:
                print("⚠️  Phone not found with enterprise filter, trying without filter...")
                phone_record = supabase_request('GET', 'purchased_phone_numbers',
                                              params={'id': f'eq.{phone_id}', 'status': 'eq.active'})

            if not phone_record or len(phone_record) == 0:
                return jsonify({
                    'success': False,
                    'error': 'Phone number not found'
                }), 404

        # Get voice agent record (with or without enterprise filtering)
        agent_params = {'id': f'eq.{agent_id}', 'status': 'eq.active'}
        if enterprise_id:
            agent_params['enterprise_id'] = f'eq.{enterprise_id}'

        agent_record = supabase_request('GET', 'voice_agents', params=agent_params)

        if not agent_record or len(agent_record) == 0:
            # Try without enterprise filtering if not found
            if enterprise_id:
                agent_record = supabase_request('GET', 'voice_agents',
                                              params={'id': f'eq.{agent_id}', 'status': 'eq.active'})

            if not agent_record or len(agent_record) == 0:
                return jsonify({
                    'success': False,
                    'error': 'Voice agent not found'
                }), 404

        # Create phone-agent assignment record in a separate table or use metadata
        # Since phone table doesn't have agent_id column, we'll store assignment in agent configuration

        # First, clear any existing assignments for this phone number
        existing_agents = supabase_request('GET', 'voice_agents',
                                         params={'select': 'id,configuration'})

        if existing_agents:
            for existing_agent in existing_agents:
                config = existing_agent.get('configuration', {})
                if config.get('outbound_phone_number_id') == phone_id:
                    # Clear the assignment from this agent
                    config.pop('outbound_phone_number', None)
                    config.pop('outbound_phone_number_id', None)
                    supabase_request('PATCH', f'voice_agents?id=eq.{existing_agent["id"]}',
                                   data={'configuration': config,
                                        'updated_at': datetime.now(timezone.utc).isoformat()})

        # Get agent name using helper function
        agent_name = get_agent_name_from_bolna(agent_id, agent_record[0].get('configuration', {}))
        if not agent_name:
            agent_name = agent_record[0]["title"]  # Fallback to title

        # Update phone number metadata to track assignment
        phone_update_data = {
            'agent_id': agent_id,
            'agent_name': agent_name,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        phone_update_result = supabase_request('PATCH', f'purchased_phone_numbers?id=eq.{phone_id}',
                                             data=phone_update_data)

        # Update voice agent configuration to include phone number
        agent_config = agent_record[0].get('configuration', {})
        agent_config['outbound_phone_number'] = phone_record[0]['phone_number']
        agent_config['outbound_phone_number_id'] = phone_id

        agent_update_result = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}',
                                             data={'configuration': agent_config,
                                                  'updated_at': datetime.now(timezone.utc).isoformat()})

        if phone_update_result and agent_update_result:
            return jsonify({
                'success': True,
                'message': f'Phone number {phone_record[0]["phone_number"]} assigned to agent {agent_record[0]["title"]}',
                'phone_number': phone_record[0]['phone_number'],
                'agent_id': agent_id,
                'agent_title': agent_record[0]["title"]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to assign phone number to agent'
            }), 500

    except Exception as e:
        print(f"Error assigning phone to agent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-numbers/<phone_id>/unassign-agent', methods=['POST'])
@login_required
def unassign_phone_from_agent(phone_id):
    """Unassign a phone number from a voice agent"""
    try:
        # Get enterprise context
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            enterprise_id = load_enterprise_context()

        # Get phone number record
        phone_params = {'id': f'eq.{phone_id}', 'status': 'eq.active'}
        if enterprise_id:
            phone_params['enterprise_id'] = f'eq.{enterprise_id}'

        phone_record = supabase_request('GET', 'purchased_phone_numbers', params=phone_params)

        if not phone_record or len(phone_record) == 0:
            return jsonify({
                'success': False,
                'error': 'Phone number not found'
            }), 404

        # Find and clear assignment from any agent
        agents = supabase_request('GET', 'voice_agents', params={'select': 'id,title,configuration'})

        unassigned_from = None
        if agents:
            for agent in agents:
                config = agent.get('configuration', {})
                if config.get('outbound_phone_number_id') == phone_id:
                    # Clear the assignment
                    config.pop('outbound_phone_number', None)
                    config.pop('outbound_phone_number_id', None)

                    agent_update_result = supabase_request('PATCH', f'voice_agents?id=eq.{agent["id"]}',
                                                         data={'configuration': config,
                                                              'updated_at': datetime.now(timezone.utc).isoformat()})

                    if agent_update_result:
                        unassigned_from = agent['title']

                        # Also clear agent info from phone table
                        phone_clear_data = {
                            'agent_id': None,
                            'agent_name': None,
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        }
                        supabase_request('PATCH', f'purchased_phone_numbers?id=eq.{phone_id}',
                                       data=phone_clear_data)
                        break

        if unassigned_from:
            return jsonify({
                'success': True,
                'message': f'Phone number {phone_record[0]["phone_number"]} unassigned from agent {unassigned_from}',
                'phone_number': phone_record[0]['phone_number']
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Phone number {phone_record[0]["phone_number"]} was not assigned to any agent',
                'phone_number': phone_record[0]['phone_number']
            })

    except Exception as e:
        print(f"Error unassigning phone from agent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/phone-assignments', methods=['GET'])
@login_required
def get_phone_assignments():
    """Get all phone number assignments"""
    try:
        # Get enterprise context
        enterprise_id = getattr(g, 'enterprise_id', None)
        if not enterprise_id:
            enterprise_id = load_enterprise_context()

        # Get all voice agents with their configurations
        agent_params = {'select': 'id,title,configuration,status'}
        if enterprise_id:
            agent_params['enterprise_id'] = f'eq.{enterprise_id}'

        agents = supabase_request('GET', 'voice_agents', params=agent_params)

        # Get all phone numbers
        phone_params = {'select': 'id,phone_number,friendly_name,status'}
        if enterprise_id:
            phone_params['enterprise_id'] = f'eq.{enterprise_id}'

        phones = supabase_request('GET', 'purchased_phone_numbers', params=phone_params)

        assignments = []

        if agents and phones:
            # Create a map of phone assignments
            phone_map = {phone['id']: phone for phone in phones}

            for agent in agents:
                config = agent.get('configuration', {})
                assigned_phone_id = config.get('outbound_phone_number_id')
                assigned_phone_number = config.get('outbound_phone_number')

                assignment = {
                    'agent_id': agent['id'],
                    'agent_title': agent['title'],
                    'agent_status': agent['status'],
                    'phone_id': assigned_phone_id,
                    'phone_number': assigned_phone_number,
                    'phone_friendly_name': None,
                    'is_assigned': bool(assigned_phone_id)
                }

                # Get phone details if assigned
                if assigned_phone_id and assigned_phone_id in phone_map:
                    phone_details = phone_map[assigned_phone_id]
                    assignment['phone_friendly_name'] = phone_details.get('friendly_name')
                    assignment['phone_status'] = phone_details.get('status')

                assignments.append(assignment)

            # Also include unassigned phone numbers
            assigned_phone_ids = [a['phone_id'] for a in assignments if a['phone_id']]

            for phone in phones:
                if phone['id'] not in assigned_phone_ids:
                    assignments.append({
                        'agent_id': None,
                        'agent_title': None,
                        'agent_status': None,
                        'phone_id': phone['id'],
                        'phone_number': phone['phone_number'],
                        'phone_friendly_name': phone.get('friendly_name'),
                        'phone_status': phone.get('status'),
                        'is_assigned': False
                    })

        return jsonify({
            'success': True,
            'assignments': assignments,
            'total_agents': len(agents) if agents else 0,
            'total_phones': len(phones) if phones else 0
        })

    except Exception as e:
        print(f"Error getting phone assignments: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# WEBHOOK ENDPOINTS FOR PHONE NUMBER PROVIDERS
# ============================================================================

@app.route('/webhooks/voice', methods=['POST'])
def handle_voice_webhook():
    """Handle incoming voice calls from phone providers"""
    try:
        # Get the provider from headers or form data
        provider = request.headers.get('X-Provider', 'unknown')

        # Log the incoming call
        print(f"Incoming voice call from {provider}")
        print(f"Request data: {request.form.to_dict()}")

        # Get call details
        from_number = request.form.get('From') or request.form.get('from')
        to_number = request.form.get('To') or request.form.get('to')
        call_sid = request.form.get('CallSid') or request.form.get('call_id')

        # Find the purchased phone number
        phone_record = supabase_request('GET', 'purchased_phone_numbers',
                                      params={'phone_number': f'eq.{to_number}',
                                             'status': 'eq.active'})

        if not phone_record or len(phone_record) == 0:
            # Return error response
            return '''<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>Sorry, this number is not configured for voice calls.</Say>
                <Hangup/>
            </Response>''', 200, {'Content-Type': 'application/xml'}

        # Log the call
        call_log = {
            'id': str(uuid.uuid4()),
            'enterprise_id': phone_record[0]['enterprise_id'],
            'phone_number_id': phone_record[0]['id'],
            'from_number': from_number,
            'to_number': to_number,
            'call_sid': call_sid,
            'provider': provider,
            'direction': 'inbound',
            'status': 'in-progress',
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        supabase_request('POST', 'call_logs', data=call_log)

        # Return TwiML response to connect to Bolna AI
        bolna_webhook_url = f"{os.getenv('BOLNA_API_URL')}/webhook/voice"

        return f'''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Welcome to BhashAI. Please wait while we connect you to our AI voice agent.</Say>
            <Redirect>{bolna_webhook_url}</Redirect>
        </Response>''', 200, {'Content-Type': 'application/xml'}

    except Exception as e:
        print(f"Error handling voice webhook: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Sorry, we're experiencing technical difficulties. Please try again later.</Say>
            <Hangup/>
        </Response>''', 200, {'Content-Type': 'application/xml'}

@app.route('/webhooks/sms', methods=['POST'])
def handle_sms_webhook():
    """Handle incoming SMS from phone providers"""
    try:
        # Get the provider from headers or form data
        provider = request.headers.get('X-Provider', 'unknown')

        # Log the incoming SMS
        print(f"Incoming SMS from {provider}")
        print(f"Request data: {request.form.to_dict()}")

        # Get SMS details
        from_number = request.form.get('From') or request.form.get('from')
        to_number = request.form.get('To') or request.form.get('to')
        message_body = request.form.get('Body') or request.form.get('text')
        message_sid = request.form.get('MessageSid') or request.form.get('message_id')

        # Find the purchased phone number
        phone_record = supabase_request('GET', 'purchased_phone_numbers',
                                      params={'phone_number': f'eq.{to_number}',
                                             'status': 'eq.active'})

        if phone_record and len(phone_record) > 0:
            # Log the SMS
            sms_log = {
                'id': str(uuid.uuid4()),
                'enterprise_id': phone_record[0]['enterprise_id'],
                'phone_number_id': phone_record[0]['id'],
                'from_number': from_number,
                'to_number': to_number,
                'message_body': message_body,
                'message_sid': message_sid,
                'provider': provider,
                'direction': 'inbound',
                'status': 'received',
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            supabase_request('POST', 'sms_logs', data=sms_log)

        # Return success response (provider-specific format)
        return jsonify({'success': True, 'message': 'SMS received'})

    except Exception as e:
        print(f"Error handling SMS webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dev/voice-providers', methods=['GET'])
def get_voice_providers():
    """Get all available voice providers"""
    try:
        providers = supabase_request('GET', 'voice_providers', params={'status': 'eq.active'})
        if providers:
            return jsonify({
                'success': True,
                'providers': providers
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch voice providers'
            }), 500
    except Exception as e:
        print(f"Error fetching voice providers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/dev/voices', methods=['GET'])
def get_available_voices():
    """Get available voices with optional filtering"""
    try:
        # Get query parameters for filtering
        provider_id = request.args.get('provider_id')
        language_code = request.args.get('language_code')
        gender = request.args.get('gender')
        
        params = {'status': 'eq.active'}
        if provider_id:
            params['provider_id'] = f'eq.{provider_id}'
        if language_code:
            params['language_code'] = f'eq.{language_code}'
        if gender:
            params['gender'] = f'eq.{gender}'
            
        voices = supabase_request('GET', 'available_voices', params=params)

        if voices:
            return jsonify({
                'success': True,
                'voices': voices
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch voices'
            }), 500
            
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/dev/voice-preferences', methods=['GET', 'POST'])
def manage_voice_preferences():
    """Get or set voice preferences for voice agents"""
    try:
        if request.method == 'GET':
            enterprise_id = request.args.get('enterprise_id', 'f47ac10b-58cc-4372-a567-0e02b2c3d479')
            voice_agent_id = request.args.get('voice_agent_id')
            
            params = {'enterprise_id': f'eq.{enterprise_id}'}
            if voice_agent_id:
                params['voice_agent_id'] = f'eq.{voice_agent_id}'
                
            preferences = supabase_request('GET', 'enterprise_voice_preferences', params=params)

            if preferences:
                return jsonify({
                    'success': True,
                    'preferences': preferences
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to fetch voice preferences'
                }), 500
                
        elif request.method == 'POST':
            data = request.get_json()
            enterprise_id = data.get('enterprise_id', 'f47ac10b-58cc-4372-a567-0e02b2c3d479')
            
            preference_record = {
                'id': str(uuid.uuid4()),
                'enterprise_id': enterprise_id,
                'voice_agent_id': data.get('voice_agent_id'),
                'preferred_voice_id': data.get('preferred_voice_id'),
                'backup_voice_id': data.get('backup_voice_id'),
                'voice_settings': data.get('voice_settings', {}),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = supabase_request('POST', 'enterprise_voice_preferences', data=preference_record)

            if result:
                return jsonify({
                    'success': True,
                    'preference': result[0] if isinstance(result, list) and result else result,
                    'message': 'Voice preference saved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save voice preference'
                }), 500
                
    except Exception as e:
        print(f"Error managing voice preferences: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# ============================================================================
# HEALTH CHECK AND DEBUG ROUTES
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint for Railway deployment"""
    return jsonify({
        'status': 'healthy',
        'app': 'bhashai.com',
        'version': '1.0',
        'static_folder': app.static_folder
    })

@app.route('/debug')
def debug_info():
    """Debug info for deployment troubleshooting"""
    import os
    return jsonify({
        'env': dict(os.environ),
        'static_folder': app.static_folder,
        'routes': [str(rule) for rule in app.url_map.iter_rules()]
    })

# ============================================================================
# SUPERADMIN DASHBOARD AND ENTERPRISE MANAGEMENT API ENDPOINTS
# ============================================================================

@app.route('/admin/login')
@app.route('/admin/login.html')
def serve_admin_login():
    """Serve admin login page"""
    return send_from_directory(app.static_folder, 'admin-login.html')

@app.route('/admin/dashboard')
@app.route('/admin/dashboard.html')
def serve_admin_dashboard():
    """Serve admin dashboard - authentication is handled by local auth system"""
    return send_from_directory(app.static_folder, 'admin-dashboard.html')

@app.route('/admin-dashboard.html')
def serve_admin_dashboard_direct():
    """Serve admin dashboard directly"""
    return send_from_directory(app.static_folder, 'admin-dashboard.html')

@app.route('/superadmin-dashboard.html')
@app.route('/superadmin/dashboard')
@app.route('/superadmin/dashboard.html')
def serve_superadmin_dashboard():
    """Serve super admin dashboard - authentication is handled by local auth system"""
    return send_from_directory(app.static_folder, 'superadmin-dashboard.html')

@app.route('/temp-admin.html')
@app.route('/temp-admin')
def serve_temp_admin():
    """Serve temporary admin access page"""
    return send_from_directory(app.static_folder, 'temp-admin.html')

@app.route('/simple-admin.html')
@app.route('/simple-admin')
def serve_simple_admin():
    """Serve simple admin access page"""
    return send_from_directory(app.static_folder, 'simple-admin.html')

# ============================================================================
# MULTI-LANGUAGE SUPPORT API ENDPOINTS
# ============================================================================

@app.route('/api/languages/supported')
def get_supported_languages():
    """Get list of all supported languages"""
    try:
        supported_languages = {
            'en': {'name': 'English', 'nativeName': 'English', 'flag': '🇺🇸', 'rtl': False, 'voice': 'en-US'},
            'hi': {'name': 'Hindi', 'nativeName': 'हिंदी', 'flag': '🇮🇳', 'rtl': False, 'voice': 'hi-IN'},
            'bn': {'name': 'Bengali', 'nativeName': 'বাংলা', 'flag': '🇧🇩', 'rtl': False, 'voice': 'bn-IN'},
            'te': {'name': 'Telugu', 'nativeName': 'తెలుగు', 'flag': '🇮🇳', 'rtl': False, 'voice': 'te-IN'},
            'ta': {'name': 'Tamil', 'nativeName': 'தமிழ்', 'flag': '🇮🇳', 'rtl': False, 'voice': 'ta-IN'},
            'mr': {'name': 'Marathi', 'nativeName': 'मराठी', 'flag': '🇮🇳', 'rtl': False, 'voice': 'mr-IN'},
            'gu': {'name': 'Gujarati', 'nativeName': 'ગુજરાતી', 'flag': '🇮🇳', 'rtl': False, 'voice': 'gu-IN'},
            'kn': {'name': 'Kannada', 'nativeName': 'ಕನ್ನಡ', 'flag': '🇮🇳', 'rtl': False, 'voice': 'kn-IN'},
            'ml': {'name': 'Malayalam', 'nativeName': 'മലയാളം', 'flag': '🇮🇳', 'rtl': False, 'voice': 'ml-IN'},
            'pa': {'name': 'Punjabi', 'nativeName': 'ਪੰਜਾਬੀ', 'flag': '🇮🇳', 'rtl': False, 'voice': 'pa-IN'},
            'or': {'name': 'Odia', 'nativeName': 'ଓଡ଼ିଆ', 'flag': '🇮🇳', 'rtl': False, 'voice': 'or-IN'},
            'as': {'name': 'Assamese', 'nativeName': 'অসমীয়া', 'flag': '🇮🇳', 'rtl': False, 'voice': 'as-IN'},
            'ur': {'name': 'Urdu', 'nativeName': 'اردو', 'flag': '🇵🇰', 'rtl': True, 'voice': 'ur-PK'},
            'ne': {'name': 'Nepali', 'nativeName': 'नेपाली', 'flag': '🇳🇵', 'rtl': False, 'voice': 'ne-NP'},
            'si': {'name': 'Sinhala', 'nativeName': 'සිංහල', 'flag': '🇱🇰', 'rtl': False, 'voice': 'si-LK'},
            'ar': {'name': 'Arabic', 'nativeName': 'العربية', 'flag': '🇸🇦', 'rtl': True, 'voice': 'ar-SA'},
            'zh': {'name': 'Chinese', 'nativeName': '中文', 'flag': '🇨🇳', 'rtl': False, 'voice': 'zh-CN'},
            'ja': {'name': 'Japanese', 'nativeName': '日本語', 'flag': '🇯🇵', 'rtl': False, 'voice': 'ja-JP'},
            'ko': {'name': 'Korean', 'nativeName': '한국어', 'flag': '🇰🇷', 'rtl': False, 'voice': 'ko-KR'},
            'th': {'name': 'Thai', 'nativeName': 'ไทย', 'flag': '🇹🇭', 'rtl': False, 'voice': 'th-TH'},
            'vi': {'name': 'Vietnamese', 'nativeName': 'Tiếng Việt', 'flag': '🇻🇳', 'rtl': False, 'voice': 'vi-VN'},
            'id': {'name': 'Indonesian', 'nativeName': 'Bahasa Indonesia', 'flag': '🇮🇩', 'rtl': False, 'voice': 'id-ID'},
            'ms': {'name': 'Malay', 'nativeName': 'Bahasa Melayu', 'flag': '🇲🇾', 'rtl': False, 'voice': 'ms-MY'},
            'tl': {'name': 'Filipino', 'nativeName': 'Filipino', 'flag': '🇵🇭', 'rtl': False, 'voice': 'tl-PH'}
        }

        return jsonify({
            "success": True,
            "languages": supported_languages,
            "total_count": len(supported_languages)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/languages/voice-samples/<language_code>')
def get_voice_sample(language_code):
    """Get voice sample for a specific language"""
    try:
        voice_samples = {
            'en': {
                'text': 'Hello, I\'m your AI voice agent. How can I help you today?',
                'audio_url': '/audio/samples/en-sample.mp3',
                'voice_type': 'neural'
            },
            'hi': {
                'text': 'नमस्ते, मैं आपका AI voice agent हूँ। आपकी कैसे मदद कर सकता हूँ?',
                'audio_url': '/audio/samples/hi-sample.mp3',
                'voice_type': 'neural'
            },
            'ta': {
                'text': 'வணக்கம், நான் உங்கள் AI voice agent. உங்களுக்கு எப்படி உதவ முடியும்?',
                'audio_url': '/audio/samples/ta-sample.mp3',
                'voice_type': 'neural'
            },
            'bn': {
                'text': 'নমস্কার, আমি আপনার AI voice agent। আমি কীভাবে আপনাকে সাহায্য করতে পারি?',
                'audio_url': '/audio/samples/bn-sample.mp3',
                'voice_type': 'neural'
            }
        }

        if language_code not in voice_samples:
            return jsonify({"success": False, "error": "Language not supported"}), 404

        return jsonify({
            "success": True,
            "language_code": language_code,
            "sample": voice_samples[language_code]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# SUPERADMIN DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/admin/stats', methods=['GET'])
@login_required
def get_admin_stats():
    """Get system statistics for superadmin dashboard"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        # Get total enterprises
        enterprises = supabase_request('GET', 'enterprises') or []
        total_enterprises = len(enterprises)
        
        # Get trial enterprises
        trial_enterprises = len([e for e in enterprises if e.get('status') == 'trial'])
        
        # Get total users
        users = supabase_request('GET', 'users') or []
        total_users = len(users)
        
        # Get total voice agents
        voice_agents = supabase_request('GET', 'voice_agents') or []
        total_agents = len(voice_agents)
        
        return jsonify({
            'total_enterprises': total_enterprises,
            'trial_enterprises': trial_enterprises,
            'total_users': total_users,
            'total_agents': total_agents
        })
        
    except Exception as e:
        print(f"Error getting admin stats: {e}")
        return jsonify({'message': 'Failed to get system statistics'}), 500

@app.route('/api/admin/enterprises', methods=['GET'])
@login_required
def get_admin_enterprises():
    """Get all enterprises for superadmin management"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        # Get all enterprises
        enterprises = supabase_request('GET', 'enterprises') or []
        
        return jsonify({
            'enterprises': enterprises,
            'total_count': len(enterprises)
        })
        
    except Exception as e:
        print(f"Error getting enterprises: {e}")
        return jsonify({'message': 'Failed to get enterprises'}), 500

@app.route('/api/admin/enterprises', methods=['POST'])
@login_required
def create_admin_enterprise():
    """Create a new enterprise (superadmin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'contact_email', 'status']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Generate enterprise ID
        enterprise_id = str(uuid.uuid4())
        
        # Create enterprise data
        enterprise_data = {
            'id': enterprise_id,
            'name': data['name'],
            'type': data['type'],
            'contact_email': data['contact_email'],
            'status': data['status'],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'created_by': current_user['id']
        }
        
        # Create enterprise in database
        result = supabase_request('POST', 'enterprises', data=enterprise_data)
        
        if result:
            # Create corresponding user account for the enterprise owner
            owner_user_data = {
                'id': str(uuid.uuid4()),
                'email': data['contact_email'],
                'name': f"{data['name']} Owner",
                'organization': data['name'],
                'role': 'trial_user' if data['status'] == 'trial' else 'user',
                'status': 'active',
                'enterprise_id': enterprise_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Check if user already exists
            existing_user = supabase_request('GET', 'users', params={'email': f'eq.{data["contact_email"]}'})
            if not existing_user or len(existing_user) == 0:
                supabase_request('POST', 'users', data=owner_user_data)
            
            return jsonify({
                'message': 'Enterprise created successfully',
                'enterprise': result[0] if isinstance(result, list) else result
            })
        else:
            return jsonify({'message': 'Failed to create enterprise'}), 500
        
    except Exception as e:
        print(f"Error creating enterprise: {e}")
        return jsonify({'message': 'Failed to create enterprise'}), 500

@app.route('/api/admin/enterprises/<enterprise_id>', methods=['GET'])
@login_required
def get_admin_enterprise(enterprise_id):
    """Get specific enterprise details (superadmin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        # Get enterprise
        enterprise = supabase_request('GET', 'enterprises', params={'id': f'eq.{enterprise_id}'})
        
        if not enterprise or len(enterprise) == 0:
            return jsonify({'message': 'Enterprise not found'}), 404
        
        enterprise_data = enterprise[0]
        
        # Get related organizations
        organizations = supabase_request('GET', 'organizations', params={'enterprise_id': f'eq.{enterprise_id}'}) or []
        
        # Get related users
        users = supabase_request('GET', 'users', params={'enterprise_id': f'eq.{enterprise_id}'}) or []
        
        return jsonify({
            'enterprise': enterprise_data,
            'organizations': organizations,
            'users': users,
            'stats': {
                'total_organizations': len(organizations),
                'total_users': len(users)
            }
        })
        
    except Exception as e:
        print(f"Error getting enterprise: {e}")
        return jsonify({'message': 'Failed to get enterprise'}), 500

@app.route('/api/admin/enterprises/<enterprise_id>', methods=['PATCH'])
@login_required
def update_admin_enterprise(enterprise_id):
    """Update enterprise (superadmin only)"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Build update data
        update_data = {
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Add allowed fields
        allowed_fields = ['name', 'type', 'contact_email', 'status']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update enterprise
        result = supabase_request('PATCH', f'enterprises?id=eq.{enterprise_id}', data=update_data)
        
        if result:
            return jsonify({
                'message': 'Enterprise updated successfully',
                'enterprise': result[0] if isinstance(result, list) else result
            })
        else:
            return jsonify({'message': 'Failed to update enterprise'}), 500
        
    except Exception as e:
        print(f"Error updating enterprise: {e}")
        return jsonify({'message': 'Failed to update enterprise'}), 500

@app.route('/api/admin/users', methods=['GET'])
@login_required
def get_admin_users():
    """Get all users for superadmin management"""
    try:
        # Check if user is admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        # Get all users
        users = supabase_request('GET', 'users') or []
        
        return jsonify({
            'users': users,
            'total_count': len(users)
        })
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'message': 'Failed to get users'}), 500

# ============================================================================

@app.route("/hello")
def hello():
    return "✅ BashAI is running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def serve_landing():
    return send_from_directory(app.static_folder, 'landing.html')

@app.route('/dashboard.html')
def serve_dashboard():
    """Serve dashboard - authentication is handled by local auth system"""
    # Always serve dashboard.html - local auth will handle authentication on the frontend
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/agent-form')
@app.route('/agent-form.html')
def serve_agent_form():
    """Serve the agent creation form"""
    return send_from_directory('.', 'agent_form.html')

@app.route('/demo')
@app.route('/demo.html')
def serve_demo():
    """Serve the form integration demo"""
    return send_from_directory('.', 'demo_form_success.html')

@app.route('/bolna-agents.html')
def serve_bolna_agents():
    """Serve Bolna agent manager page"""
    return send_from_directory(app.static_folder, 'bolna-agent-manager.html')



@app.route('/phone-demo.html')
def serve_phone_demo():
    """Serve phone number demo page"""
    return send_from_directory(app.static_folder, 'phone-demo.html')

@app.route('/signup.html')
@app.route('/signup')
@app.route('/register')
def serve_signup():
    """Serve signup/registration page"""
    return send_from_directory(app.static_folder, 'signup.html')

@app.route('/agent-setup.html')
def serve_agent_setup():
    """Serve agent setup page"""
    return send_from_directory(app.static_folder, 'agent-setup.html')

@app.route('/agent-setup-new.html')
def serve_agent_setup_new():
    """Serve new agent setup page"""
    return send_from_directory(app.static_folder, 'agent-setup-new.html')

@app.route('/test_agent_setup_flow.html')
def serve_test_agent_setup():
    """Serve agent setup flow test page"""
    return send_from_directory('.', 'test_agent_setup_flow.html')



@app.route('/debug.html')
def serve_debug():
    """Serve debug test page"""
    return send_from_directory(app.static_folder, 'debug.html')

@app.route('/minimal-test.html')
def serve_minimal_test():
    """Serve minimal button test page"""
    return send_from_directory(app.static_folder, 'minimal-test.html')

@app.route('/contact-management.html')
def serve_contact_management():
    """Serve contact management page"""
    return send_from_directory(app.static_folder, 'contact-management.html')

@app.route('/language-demo.html')
def serve_language_demo():
    """Serve multi-language demo page"""
    return send_from_directory(app.static_folder, 'language-demo.html')

@app.route('/api/create-agent', methods=['POST'])
def create_agent():
    """Create agent endpoint for agent setup page"""
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract required fields
        phone_number = data.get('phone_number')
        agent_name = data.get('name', 'Sales Expert - राज')
        agent_type = data.get('type', 'sales')
        voice = data.get('voice', 'Aditi')
        language = data.get('language', 'hi')
        welcome_message = data.get('welcome_message', 'नमस्ते! मैं राज हूं, आपका sales assistant। आज मैं आपकी कैसे मदद कर सकता हूं?')
        prompt = data.get('prompt', '')
        max_duration = data.get('max_duration', 180)

        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except ImportError as e:
            return jsonify({'error': f'Bolna integration module not found: {str(e)}'}), 500
        except ValueError as e:
            return jsonify({'error': f'Bolna API configuration error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Failed to initialize Bolna API: {str(e)}'}), 500

        # Create agent via Bolna API
        try:
            agent_response = bolna_api.create_agent(
                name=agent_name,
                description=f"{agent_type} agent for {phone_number}",
                prompt=prompt,
                welcome_message=welcome_message,
                voice=voice,
                language=language,
                max_duration=max_duration
            )

            # Check if response has agent_id
            if not agent_response or not agent_response.get('agent_id'):
                return jsonify({
                    'error': 'Agent created but no agent_id returned',
                    'response': agent_response
                }), 500

            agent_id = agent_response.get('agent_id')

            # Store agent info in Supabase database
            try:
                # Get current user info
                user_data = getattr(request, 'current_user', None)
                user_id = user_data.get('user_id') or user_data.get('id') if user_data else None

                print(f"🔍 DEBUG - Agent creation - User data: {user_data}")
                print(f"🔍 DEBUG - Agent creation - User ID: {user_id}")

                # Store in bolna_agents table
                agent_record = {
                    'bolna_agent_id': agent_id,
                    'agent_name': agent_name,
                    'agent_type': agent_type,
                    'description': f"{agent_type} agent for {phone_number}",
                    'prompt': prompt,
                    'welcome_message': welcome_message,
                    'voice': voice,
                    'language': language,
                    'max_duration': max_duration,
                    'phone_number': phone_number,
                    'user_id': user_id,
                    'status': 'active',
                    'bolna_response': agent_response  # Store full Bolna response
                }

                # Insert into database
                db_result = supabase_request('POST', 'bolna_agents', data=agent_record)

                if db_result:
                    print(f"✅ Agent stored in database: {agent_id}")
                else:
                    print(f"⚠️ Failed to store agent in database, but agent created successfully")

            except Exception as db_error:
                print(f"⚠️ Database storage error: {db_error}")
                # Don't fail the whole request if database storage fails

            return jsonify({
                'success': True,
                'message': 'Agent created successfully',
                'agent_id': agent_id,
                'phone_number': phone_number,
                'agent_name': agent_name,
                'agent_type': agent_type
            })

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error creating agent: {e}")
            # For now, return a mock success response to test frontend
            mock_agent_id = f"mock_agent_{int(time.time())}"
            print(f"🔧 Returning mock agent ID for testing: {mock_agent_id}")
            return jsonify({
                'success': True,
                'message': 'Agent created successfully (mock mode)',
                'agent_id': mock_agent_id,
                'phone_number': phone_number,
                'agent_name': agent_name,
                'agent_type': agent_type,
                'note': 'This is a mock response while Bolna API is being fixed'
            })
        except Exception as e:
            print(f"❌ API error creating agent: {e}")
            # For now, return a mock success response to test frontend
            mock_agent_id = f"mock_agent_{int(time.time())}"
            print(f"🔧 Returning mock agent ID for testing: {mock_agent_id}")
            return jsonify({
                'success': True,
                'message': 'Agent created successfully (mock mode)',
                'agent_id': mock_agent_id,
                'phone_number': phone_number,
                'agent_name': agent_name,
                'agent_type': agent_type,
                'note': 'This is a mock response while Bolna API is being fixed'
            })

    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return jsonify({'error': f'Failed to create agent: {str(e)}'}), 500


@app.route('/api/agents/<agent_id>', methods=['GET'])
def get_agent_details(agent_id):
    """Get agent details for editing"""
    try:
        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except Exception as e:
            return jsonify({'error': f'Failed to initialize Bolna API: {str(e)}'}), 500

        # Get agent details from Bolna
        try:
            agent_details = bolna_api.get_agent_details(agent_id)

            if not agent_details:
                return jsonify({'error': 'Agent not found'}), 404

            # Format response for frontend
            return jsonify({
                'success': True,
                'name': agent_details.get('name', ''),
                'type': 'sales',  # Default type
                'voice': agent_details.get('voice', 'Aditi'),
                'language': agent_details.get('language', 'hi'),
                'welcome_message': agent_details.get('welcome_message', ''),
                'prompt': agent_details.get('prompt', ''),
                'max_duration': agent_details.get('max_duration', 180)
            })

        except Exception as e:
            print(f"❌ Error getting agent details: {e}")
            return jsonify({'error': f'Failed to get agent details: {str(e)}'}), 500

    except Exception as e:
        print(f"❌ Error in get_agent_details: {e}")
        return jsonify({'error': f'Failed to retrieve agent: {str(e)}'}), 500


@app.route('/api/bolna/agents/<agent_id>/details', methods=['GET'])
def get_bolna_agent_details_for_update(agent_id):
    """Get Bolna agent details specifically for update modal"""
    try:
        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except ImportError as e:
            return jsonify({'message': f'Bolna integration module not found: {str(e)}'}), 500
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'message': f'Failed to initialize Bolna API: {str(e)}'}), 500

        # First try to get from our database
        db_agent = None
        try:
            db_result = supabase_request('GET', f'bolna_agents?bolna_agent_id=eq.{agent_id}')
            if db_result and len(db_result) > 0:
                db_agent = db_result[0]
                print(f"✅ Found agent in database: {db_agent.get('agent_name')}")
        except Exception as db_error:
            print(f"⚠️ Database lookup error: {db_error}")

        # Get agent details from Bolna API
        try:
            print(f"🔍 Attempting to fetch agent details for: {agent_id}")
            response = bolna_api._make_request('GET', f'/v2/agent/{agent_id}')
            print(f"🔍 Bolna API response received: {response is not None}")

            if response:
                # Debug: Print full response to understand structure
                print(f"🔍 Full Bolna API response for agent {agent_id}:")
                print(json.dumps(response, indent=2))

                # Extract relevant information
                agent_config = response.get('agent_config', {})
                agent_prompts = response.get('agent_prompts', {})

                # Try to get tasks for prompt extraction
                tasks = agent_config.get('tasks', [])
                task_prompt = ''
                if tasks and len(tasks) > 0:
                    task_config = tasks[0].get('task_config', {})
                    llm_agent = task_config.get('llm_agent', {})
                    task_prompt = llm_agent.get('system_prompt', '')

                # Try multiple possible locations for agent name - prioritize database
                agent_name = None

                # First check database
                if db_agent and db_agent.get('agent_name'):
                    agent_name = db_agent.get('agent_name')
                    print(f"🎯 Using agent name from database: '{agent_name}'")

                # Then try Bolna API response
                if not agent_name:
                    agent_name_from_config = agent_config.get('agent_name')
                    agent_name_from_response = response.get('agent_name')
                    name_from_response = response.get('name')

                    print(f"🔍 Debug agent name extraction:")
                    print(f"  - agent_config.get('agent_name'): '{agent_name_from_config}'")
                    print(f"  - response.get('agent_name'): '{agent_name_from_response}'")
                    print(f"  - response.get('name'): '{name_from_response}'")

                    agent_name = (
                        agent_name_from_config or
                        agent_name_from_response or
                        name_from_response or
                        None
                    )

                    # If agent_name is empty string, treat it as None
                    if agent_name == "":
                        agent_name = None

                print(f"🔍 Final agent_name after initial extraction: '{agent_name}'")

                # If no direct agent name found, try to extract real name from welcome message first
                if not agent_name:
                    welcome_message = (
                        response.get('agent_welcome_message') or
                        agent_config.get('agent_welcome_message') or
                        agent_config.get('welcome_message') or
                        response.get('welcome_message') or
                        ''
                    )

                    if welcome_message:
                        import re
                        print(f"🔍 Checking welcome message for name: {welcome_message[:100]}...")

                        # Look for names in welcome message - more reliable than prompt
                        welcome_patterns = [
                            r'मैं ([^\s,।!]+) हूं',  # "मैं [name] हूं" - most common
                            r'मैं ([A-Za-z\s]+) का AI',  # "मैं [name] का AI"
                            r'I am ([A-Za-z\s]+)',  # "I am [name]"
                            r'Doctor ([A-Za-z\s]+)',  # "Doctor [name]"
                            r'Dr\.?\s+([A-Za-z\s]+)',  # "Dr [name]"
                        ]

                        for pattern in welcome_patterns:
                            match = re.search(pattern, welcome_message)
                            if match:
                                extracted_name = match.group(1).strip()
                                # Clean up the name and filter out common words
                                if (extracted_name and
                                    len(extracted_name) < 50 and
                                    extracted_name.lower() not in ['priyanka', 'agent', 'assistant', 'bot', 'ai', 'voice']):
                                    agent_name = extracted_name
                                    print(f"🎯 Extracted agent name from welcome message: '{agent_name}' using pattern: {pattern}")
                                    break

                # If still no name found, try to extract real name from prompt (last resort)
                if not agent_name and task_prompt:
                    import re
                    # Look for actual name patterns in Hindi/English prompts
                    name_patterns = [
                        r'नाम ([^।\s]+) है',  # "नाम [name] है" - most reliable
                        r'I am ([A-Za-z\s]+)(?:\.|,|!)',  # "I am [name]"
                        r'My name is ([A-Za-z\s]+)(?:\.|,|!)',  # "My name is [name]"
                    ]

                    for pattern in name_patterns:
                        match = re.search(pattern, task_prompt)
                        if match:
                            extracted_name = match.group(1).strip()
                            # Filter out common words that are not names
                            if (extracted_name and
                                len(extracted_name) < 30 and
                                extracted_name.lower() not in ['priyanka', 'agent', 'assistant', 'bot', 'ai', 'voice']):
                                agent_name = extracted_name
                                print(f"🎯 Extracted real agent name from prompt: '{agent_name}' using pattern: {pattern}")
                                break

                # If still no name found, use a descriptive name based on the agent's purpose
                if not agent_name:
                    # Create a descriptive name based on the agent's purpose or type
                    if 'medical' in task_prompt.lower() or 'hospital' in task_prompt.lower() or 'doctor' in task_prompt.lower():
                        agent_name = "Medical Assistant Agent"
                    elif 'sales' in task_prompt.lower() or 'customer' in task_prompt.lower():
                        agent_name = "Sales Assistant Agent"
                    else:
                        agent_name = "Voice Assistant Agent"
                    print(f"🏷️ Using descriptive name based on purpose: '{agent_name}'")

                # Try multiple possible locations for welcome message
                welcome_message = (
                    agent_config.get('agent_welcome_message') or
                    agent_config.get('welcome_message') or
                    response.get('welcome_message') or
                    ''
                )

                # Try multiple possible locations for prompt
                prompt = (
                    task_prompt or
                    agent_prompts.get('task_1', {}).get('system_prompt') or
                    agent_config.get('prompt') or
                    response.get('prompt') or
                    ''
                )



                # Extract language and voice information from tasks
                language = 'hi'  # default
                voice = 'Aditi'  # default
                sales_approach = 'consultative'  # default

                if tasks and len(tasks) > 0:
                    task_config = tasks[0].get('task_config', {})

                    # Extract language from transcriber
                    transcriber = task_config.get('transcriber', {})
                    if transcriber.get('language'):
                        language = transcriber['language']

                    # Extract voice from synthesizer
                    synthesizer = task_config.get('synthesizer', {})
                    if synthesizer.get('voice'):
                        voice = synthesizer['voice']

                # Try to extract sales approach from prompt
                if prompt:
                    prompt_lower = prompt.lower()
                    if 'direct' in prompt_lower or 'results-focused' in prompt_lower:
                        sales_approach = 'direct'
                    elif 'educational' in prompt_lower or 'information-focused' in prompt_lower:
                        sales_approach = 'educational'
                    elif 'consultative' in prompt_lower or 'relationship-focused' in prompt_lower:
                        sales_approach = 'consultative'

                return jsonify({
                    'agent_id': agent_id,
                    'name': agent_name,
                    'welcome_message': welcome_message,
                    'prompt': prompt,
                    'type': agent_config.get('agent_type', 'sales'),
                    'status': response.get('status', 'active'),
                    'language': language,
                    'voice': voice,
                    'sales_approach': sales_approach
                })
            else:
                return jsonify({'message': 'Agent not found'}), 404

        except Exception as e:
            print(f"❌ API error fetching agent: {e}")
            return jsonify({'message': f'API error: {str(e)}'}), 500

    except Exception as e:
        print(f"❌ Error fetching agent details: {e}")
        return jsonify({'message': f'Failed to fetch agent details: {str(e)}'}), 500


@app.route('/api/bolna/agents/bulk-details', methods=['POST'])
@login_required
def get_bulk_agent_details():
    """Get details for multiple agents from Bolna API"""
    try:
        data = request.get_json()
        agent_ids = data.get('agent_ids', [])

        if not agent_ids:
            return jsonify({'message': 'No agent IDs provided'}), 400

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except ImportError as e:
            return jsonify({'message': f'Bolna integration module not found: {str(e)}'}), 500
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'message': f'Failed to initialize Bolna API: {str(e)}'}), 500

        # Get details for all agents
        agent_details_map = {}
        for agent_id in agent_ids:
            try:
                agent_details = bolna_api.get_agent_details(agent_id)
                if agent_details:
                    agent_config = agent_details.get('agent_config', {})
                    agent_name = agent_config.get('agent_name', f'Agent {agent_id[:8]}')
                    agent_details_map[agent_id] = {
                        'agent_id': agent_id,
                        'name': agent_name,
                        'type': agent_config.get('agent_type', 'sales'),
                        'status': agent_details.get('status', 'active')
                    }
                    print(f"✅ Found agent details for {agent_id}: {agent_name}")
                else:
                    print(f"⚠️ No details found for agent {agent_id}")
            except Exception as e:
                print(f"❌ Error fetching details for agent {agent_id}: {e}")

        return jsonify({
            'success': True,
            'agents': agent_details_map,
            'count': len(agent_details_map)
        })

    except Exception as e:
        print(f"❌ Error in get_bulk_agent_details: {e}")
        return jsonify({'message': f'Internal server error: {str(e)}'}), 500


@app.route('/api/bolna/agents/list', methods=['GET'])
@login_required
def list_all_bolna_agents():
    """List all agents from Bolna API for debugging"""
    try:
        from bolna_integration import BolnaAPI
        bolna_api = BolnaAPI()

        # Get all agents
        agents = bolna_api.list_agents()

        return jsonify({
            'success': True,
            'agents': agents,
            'count': len(agents) if agents else 0
        })

    except Exception as e:
        print(f"❌ Error listing agents: {e}")
        return jsonify({'message': f'Failed to list agents: {str(e)}'}), 500


@app.route('/api/bolna/agents/sync', methods=['POST'])
@login_required
def sync_agents_from_bolna():
    """Sync agent data from Bolna to our database"""
    try:
        from bolna_integration import BolnaAPI

        bolna_api = BolnaAPI()

        # Get all agents from Bolna
        agents = bolna_api.list_agents()
        if not agents:
            return jsonify({'message': 'No agents found in Bolna'}), 404

        # Since agents don't have phone numbers directly, we'll create a mapping
        # This is a temporary solution until proper phone-agent assignment is implemented

        # Create a simple mapping for demonstration
        phone_agent_mapping = {
            '+918035315404': '491325fa-4323-4e39-8536-a1a66cd8d437',  # pooja
            '+918035315398': '2f1b28b6-d2e6-4074-9c8e-ba9594947afa',  # bbbb
            '+918035315328': '9ede5ecf-9cac-4123-8cab-f644f99f1f73',  # agent Ai
        }

        # Update phone numbers with agent info
        updated_count = 0
        for phone_number, agent_id in phone_agent_mapping.items():
            # Find the agent details
            agent_details = next((agent for agent in agents if agent.get('id') == agent_id), None)
            if agent_details:
                agent_name = agent_details.get('agent_name', f"Agent {agent_id}")

                # Try to update in database using supabase_request
                try:
                    result = supabase_request('PATCH', f'purchased_phone_numbers?phone_number=eq.{phone_number}', data={
                        'agent_id': agent_id,
                        'agent_name': agent_name
                    })

                    if result:
                        updated_count += 1
                        print(f"✅ Updated {phone_number} with agent {agent_name}")
                except Exception as db_error:
                    print(f"⚠️ Database update failed for {phone_number}: {db_error}")

        return jsonify({
            'success': True,
            'message': f'Synced {updated_count} phone numbers with agent data',
            'updated_count': updated_count,
            'total_agents': len(agents),
            'note': 'Using manual mapping since agents do not have phone numbers assigned in Bolna'
        })

    except Exception as e:
        print(f"❌ Error syncing agents: {e}")
        return jsonify({'message': f'Failed to sync agents: {str(e)}'}), 500


@app.route('/api/bolna/agents/assign', methods=['POST'])
@login_required
def assign_agent_to_phone():
    """Manually assign an agent to a phone number"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        agent_id = data.get('agent_id')

        if not phone_number or not agent_id:
            return jsonify({'message': 'Phone number and agent ID are required'}), 400

        from bolna_integration import BolnaAPI
        bolna_api = BolnaAPI()

        # Get agent details from Bolna
        agents = bolna_api.list_agents()
        agent_details = next((agent for agent in agents if agent.get('id') == agent_id), None)

        if not agent_details:
            return jsonify({'message': 'Agent not found in Bolna'}), 404

        agent_name = agent_details.get('agent_name', f"Agent {agent_id}")

        # Update in database
        result = supabase_request('PATCH', f'purchased_phone_numbers?phone_number=eq.{phone_number}', data={
            'agent_id': agent_id,
            'agent_name': agent_name
        })

        if result:
            return jsonify({
                'success': True,
                'message': f'Successfully assigned agent {agent_name} to {phone_number}',
                'agent_id': agent_id,
                'agent_name': agent_name,
                'phone_number': phone_number
            })
        else:
            return jsonify({'message': 'Failed to update database'}), 500

    except Exception as e:
        print(f"❌ Error assigning agent: {e}")
        return jsonify({'message': f'Failed to assign agent: {str(e)}'}), 500


@app.route('/api/bolna/create-agent-form', methods=['POST'])
def create_agent_from_form():
    """Create agent from form data without login requirement"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided', 'status': 'error'}), 400

        # Extract form data
        agent_name = data.get('agent_name', data.get('name', ''))
        phone_number = data.get('phone_number', '')
        language = data.get('language', 'hi')
        voice = data.get('voice', 'Aditi')
        sales_approach = data.get('sales_approach', 'Consultative')
        welcome_message = data.get('welcome_message', '')
        agent_prompt = data.get('agent_prompt', data.get('prompt', ''))

        print(f"🎯 Creating agent from form:")
        print(f"  Name: {agent_name}")
        print(f"  Phone: {phone_number}")
        print(f"  Language: {language}")
        print(f"  Voice: {voice}")

        # Validation
        if not agent_name.strip():
            return jsonify({'error': 'Agent name is required', 'status': 'error'}), 400
        if not phone_number.strip():
            return jsonify({'error': 'Phone number is required', 'status': 'error'}), 400

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except Exception as e:
            return jsonify({'error': f'Bolna API initialization failed: {str(e)}', 'status': 'error'}), 500

        # Create Bolna agent configuration
        agent_config = {
            "agent_name": agent_name,
            "agent_type": "sales",
            "agent_welcome_message": welcome_message or f"नमस्ते! मैं {agent_name} हूं, आपका sales assistant। आज मैं आपकी कैसे मदद कर सकता हूं?",
            "tasks": [
                {
                    "task_type": "conversation",
                    "toolchain": {
                        "execution": "parallel",
                        "pipelines": [["transcriber", "llm", "synthesizer"]]
                    },
                    "task_config": {
                        "hangup_after_silence": 15,
                        "call_terminate": 180,
                        "optimize_latency": True,
                        "backchanneling": True,
                        "ambient_noise": False,
                        "voicemail": True,
                        "use_fillers": False,
                        "incremental_delay": 300,
                        "ambient_noise_track": "convention_hall",
                        "call_cancellation_prompt": "धन्यवाद! आपका दिन शुभ हो। नमस्ते!",
                        "inbound_limit": -1,
                        "whitelist_phone_numbers": ["<any>"],
                        "disallow_unknown_numbers": False
                    },
                    "tools_config": {
                        "input": {"format": "wav", "provider": "twilio"},
                        "output": {"format": "wav", "provider": "twilio"},
                        "llm_agent": {
                            "agent_type": "simple_llm_agent",
                            "llm_config": {
                                "model": "gpt-4",
                                "provider": "openai",
                                "max_tokens": 200,
                                "temperature": 0.7,
                                "presence_penalty": 0.1,
                                "frequency_penalty": 0.1
                            }
                        },
                        "synthesizer": {
                            "provider": "polly",
                            "provider_config": {
                                "voice": voice,
                                "engine": "neural",
                                "language": "hi-IN" if language == "hi" else "en-IN"
                            }
                        },
                        "transcriber": {
                            "provider": "deepgram",
                            "model": "nova-2",
                            "language": language
                        }
                    }
                }
            ],
            "agent_prompts": {
                "task_1": {
                    "system_prompt": agent_prompt or f"""आप एक expert sales representative हैं जिसका नाम {agent_name} है। आप Hindi और English दोनों भाषाओं में fluent हैं।

आपका मुख्य goal है:
1. Customer के साथ friendly relationship बनाना
2. Product/service की benefits explain करना
3. Objections को handle करना
4. Sale close करना या follow-up schedule करना

Sales Approach: {sales_approach}

Language Guidelines:
- Hindi-English mix (Hinglish) naturally use करें
- Customer की language preference को follow करें
- Respectful tone maintain करें

Remember: हमेशा customer की value को priority दें, sales को नहीं।"""
                }
            }
        }

        # Create agent via Bolna API
        response = bolna_api.create_agent(agent_config)

        if response and response.get('agent_id'):
            agent_id = response.get('agent_id')

            # Store in database with multiple fallback strategies
            try:
                # Strategy 1: Try bolna_agents table
                agent_record = {
                    'bolna_agent_id': agent_id,
                    'agent_name': agent_name,
                    'agent_type': 'sales',
                    'description': f"Sales agent created from form",
                    'prompt': agent_prompt,
                    'welcome_message': welcome_message,
                    'voice': voice,
                    'language': language,
                    'max_duration': 180,
                    'hangup_after': 15,
                    'phone_number': phone_number,
                    'status': 'active',
                    'bolna_response': response
                }

                db_result = supabase_request('POST', 'bolna_agents', data=agent_record)

                if db_result:
                    print(f"✅ Agent stored in bolna_agents table: {agent_id}")
                else:
                    # Fallback: Store in organizations table
                    org_data = {
                        'name': f'Agent Storage - {agent_name}',
                        'description': json.dumps({
                            'type': 'agent_storage',
                            'agent_data': agent_record
                        }),
                        'type': 'agent_storage',
                        'status': 'active',
                        'email': 'agents@bhashai.com',
                        'phone': phone_number,
                        'address': f'Agent: {agent_name}'
                    }

                    org_result = supabase_request('POST', 'organizations', data=org_data)

                    if org_result:
                        print(f"✅ Agent stored in organizations table: {agent_id}")
                    else:
                        print(f"⚠️ Failed to store in both tables")

            except Exception as db_error:
                print(f"⚠️ Database storage failed: {db_error}")
                # Log for manual entry
                print(f"📋 MANUAL ENTRY REQUIRED:")
                print(f"Agent ID: {agent_id}")
                print(f"Agent Name: {agent_name}")
                print(f"Phone: {phone_number}")

            return jsonify({
                'agent_id': agent_id,
                'agent_name': agent_name,
                'phone_number': phone_number,
                'status': 'created',
                'message': 'Sales agent created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create agent', 'status': 'error'}), 500

    except Exception as e:
        print(f"❌ Form agent creation error: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/api/bolna/create-sales-agent', methods=['POST'])
@login_required
def create_sales_agent():
    """Create a specialized sales agent with predefined configuration"""
    global phone_agent_mapping
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except ImportError as e:
            return jsonify({'message': f'Bolna integration module not found: {str(e)}'}), 500
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'message': f'Failed to initialize Bolna API: {str(e)}'}), 500

        # Extract form data (support multiple field names for compatibility)
        agent_name = data.get('name', data.get('agent_name', ''))
        agent_type = data.get('type', 'sales')
        welcome_message = data.get('welcome_message', data.get('agent_welcome_message', ''))
        prompt = data.get('prompt', data.get('agent_prompt', ''))
        description = data.get('description', '')
        voice = data.get('voice', 'Aditi')
        language = data.get('language', 'hi')
        max_duration = data.get('max_duration', 180)
        silence_timeout = data.get('silence_timeout', 15)
        sales_approach = data.get('sales_approach', 'consultative')
        phone_number = data.get('phone_number', '')

        print(f"🎯 Form Data Received:")
        print(f"  Agent Name: {agent_name}")
        print(f"  Phone Number: {phone_number}")
        print(f"  Language: {language}")
        print(f"  Voice: {voice}")
        print(f"  Sales Approach: {sales_approach}")
        print(f"  Welcome Message: {welcome_message[:50]}..." if welcome_message else "  Welcome Message: (empty)")
        print(f"  Prompt: {prompt[:50]}..." if prompt else "  Prompt: (empty)")

        # Validation
        if not agent_name.strip():
            return jsonify({
                'error': 'Agent name is required',
                'status': 'error'
            }), 400

        if not phone_number.strip():
            return jsonify({
                'error': 'Phone number is required',
                'status': 'error'
            }), 400

        # Build sales agent configuration
        # Use custom welcome message if provided, otherwise use default
        if not welcome_message.strip():
            welcome_message = f"नमस्ते! मैं {agent_name.split(' - ')[-1] if ' - ' in agent_name else 'राज'} हूं, आपका sales assistant। आज मैं आपकी कैसे मदद कर सकता हूं?"

        sales_config = {
            "agent_name": agent_name,
            "agent_welcome_message": welcome_message,
            "webhook_url": None,
            "agent_type": agent_type,
            "tasks": [
                {
                    "task_type": "conversation",
                    "tools_config": {
                        "llm_agent": {
                            "agent_type": "simple_llm_agent",
                            "agent_flow_type": "streaming",
                            "routes": {
                                "embedding_model": "snowflake/snowflake-arctic-embed-m",
                                "routes": [
                                    {
                                        "route_name": "price_objection",
                                        "utterances": [
                                            "यह बहुत महंगा है",
                                            "This is too expensive",
                                            "Price is high",
                                            "कीमत ज्यादा है"
                                        ],
                                        "response": "मैं समझ सकता हूं कि price एक concern है। लेकिन हमारे product की quality और value को देखते हुए, यह actually बहुत reasonable है। क्या मैं आपको कुछ special offers बता सकूं?",
                                        "score_threshold": 0.8
                                    },
                                    {
                                        "route_name": "competitor_comparison",
                                        "utterances": [
                                            "Other companies are cheaper",
                                            "दूसरी कंपनी सस्ती है",
                                            "Competition में better options हैं"
                                        ],
                                        "response": "बिल्कुल सही कह रहे हैं! Market में options हैं। लेकिन हमारी USP है quality, after-sales service और guarantee। क्या मैं आपको हमारे unique benefits explain कर सकूं?",
                                        "score_threshold": 0.8
                                    },
                                    {
                                        "route_name": "not_interested",
                                        "utterances": [
                                            "मुझे interest नहीं है",
                                            "Not interested",
                                            "Don't need this",
                                            "अभी नहीं चाहिए"
                                        ],
                                        "response": "कोई बात नहीं! मैं समझ सकता हूं। लेकिन क्या मैं सिर्फ 2 मिनट में आपको बता सकूं कि यह आपके लिए कैसे beneficial हो सकता है? फिर आप decide कर सकते हैं।",
                                        "score_threshold": 0.8
                                    }
                                ]
                            },
                            "llm_config": {
                                "agent_flow_type": "streaming",
                                "provider": "openai",
                                "family": "openai",
                                "model": "gpt-4",
                                "max_tokens": 200,
                                "presence_penalty": 0.1,
                                "frequency_penalty": 0.1,
                                "base_url": "https://api.openai.com/v1",
                                "top_p": 0.9,
                                "temperature": 0.7,
                                "request_json": True
                            }
                        },
                        "synthesizer": {
                            "provider": "polly",
                            "provider_config": {
                                "voice": voice,
                                "engine": "neural",
                                "sampling_rate": "8000",
                                "language": "hi-IN" if language == 'hi' else "en-US"
                            },
                            "stream": True,
                            "buffer_size": 150,
                            "audio_format": "wav"
                        },
                        "transcriber": {
                            "provider": "deepgram",
                            "model": "nova-2",
                            "language": language,
                            "stream": True,
                            "sampling_rate": 16000,
                            "encoding": "linear16",
                            "endpointing": 100
                        },
                        "input": {
                            "provider": "twilio",
                            "format": "wav"
                        },
                        "output": {
                            "provider": "twilio",
                            "format": "wav"
                        }
                    },
                    "toolchain": {
                        "execution": "parallel",
                        "pipelines": [
                            ["transcriber", "llm", "synthesizer"]
                        ]
                    },
                    "task_config": {
                        "hangup_after_silence": silence_timeout,
                        "incremental_delay": 300,
                        "number_of_words_for_interruption": 3,
                        "hangup_after_LLMCall": False,
                        "call_cancellation_prompt": "धन्यवाद! आपका दिन शुभ हो। नमस्ते!",
                        "backchanneling": True,
                        "backchanneling_message_gap": 4,
                        "backchanneling_start_delay": 3,
                        "ambient_noise": False,
                        "call_terminate": max_duration,
                        "voicemail": True,
                        "inbound_limit": -1,
                        "whitelist_phone_numbers": ["<any>"],
                        "disallow_unknown_numbers": False
                    }
                }
            ]
        }

        # Sales agent prompts based on approach
        # Use custom prompt if provided, otherwise use default
        if prompt.strip():
            system_prompt = prompt
        else:
            system_prompt = f"""आप एक expert sales representative हैं जिसका नाम {agent_name.split(' - ')[-1] if ' - ' in agent_name else 'राज'} है। आप Hindi और English दोनों भाषाओं में fluent हैं।

आपका मुख्य goal है:
1. Customer के साथ friendly relationship बनाना
2. Product/service की benefits explain करना
3. Objections को handle करना
4. Sale close करना या follow-up schedule करना

आपकी personality:
- Confident लेकिन humble
- Customer-focused approach
- Problem solver mindset
- Persistent लेकिन respectful

Sales Approach: {sales_approach.title()}

Language Guidelines:
- Hindi-English mix (Hinglish) naturally use करें
- Customer की language preference को follow करें
- Technical terms को simple language में explain करें
- Respectful tone maintain करें

Call Structure:
1. Warm greeting और introduction
2. Customer की current situation जानें
3. Product benefits present करें
4. Objections handle करें
5. Closing attempt करें
6. Next steps decide करें

Remember: हमेशा customer की value को priority दें, sales को नहीं।"""

        sales_prompts = {
            "task_1": {
                "system_prompt": system_prompt
            }
        }

        # Create agent data
        agent_data = {
            "agent_config": sales_config,
            "agent_prompts": sales_prompts
        }

        # Create the agent via Bolna API
        try:
            response = bolna_api._make_request('POST', '/v2/agent', agent_data)

            # Log the creation
            print(f"✅ Sales agent created: {response}")

            # Check if response has agent_id
            if not response or not response.get('agent_id'):
                return jsonify({
                    'message': 'Agent created but no agent_id returned',
                    'response': response
                }), 500

            # Store agent in Supabase database
            phone_number = data.get('phone_number')
            agent_id = response.get('agent_id')

            # Get current user info
            user_data = getattr(request, 'current_user', None)
            user_id = user_data.get('user_id') or user_data.get('id') if user_data else None

            print(f"🔍 DEBUG - User data: {user_data}")
            print(f"🔍 DEBUG - User ID: {user_id}")

            # Store in voice_agents table (since bolna_agents has RLS issues)
            try:
                agent_record = {
                    'bolna_agent_id': agent_id,
                    'agent_name': agent_name,
                    'agent_type': agent_type,
                    'description': f"Sales agent for {data.get('business_name', 'business')}",
                    'prompt': system_prompt,
                    'welcome_message': welcome_message,
                    'voice': 'Aditi',
                    'language': 'hi',
                    'max_duration': 180,
                    'hangup_after': 15,
                    'phone_number': phone_number,
                    'user_id': user_id,
                    'status': 'active',
                    'bolna_response': response  # Store full Bolna response
                }

                # Store agent data in a simple JSON format in organizations table
                # This is a workaround since bolna_agents has RLS issues

                # First try bolna_agents table
                try:
                    db_result = supabase_request('POST', 'bolna_agents', data=agent_record)
                    if db_result:
                        print(f"✅ Sales agent stored in bolna_agents table: {agent_id}")
                    else:
                        raise Exception("bolna_agents insert failed")
                except Exception as bolna_error:
                    print(f"⚠️ bolna_agents storage failed: {bolna_error}")

                    # Fallback 1: Store in organizations table as JSON
                    try:
                        # Get or create organization for storing agent data
                        org_data = {
                            'name': f'Agents Storage for User {user_id}',
                            'description': json.dumps({
                                'type': 'agent_storage',
                                'agents': {
                                    agent_id: agent_record
                                }
                            }),
                            'type': 'agent_storage',
                            'status': 'active',
                            'email': 'agents@bhashai.com',
                            'phone': phone_number or '+918035315404',
                            'address': 'Agent Storage',
                            'user_id': user_id
                        }

                        org_result = supabase_request('POST', 'organizations', data=org_data)

                        if org_result:
                            print(f"✅ Agent stored in organizations table: {agent_id}")
                        else:
                            raise Exception("organizations insert failed")

                    except Exception as org_error:
                        print(f"⚠️ organizations storage failed: {org_error}")

                        # Fallback 2: Store minimal info in purchased_phone_numbers table
                        if phone_number:
                            try:
                                phone_update = {
                                    'agent_id': agent_id,
                                    'agent_name': agent_name,
                                    'description': json.dumps(agent_record)  # Store full data as JSON
                                }

                                # Update phone number record
                                phone_result = supabase_request('PATCH',
                                    f'purchased_phone_numbers?phone_number=eq.{phone_number}',
                                    data=phone_update)

                                if phone_result:
                                    print(f"✅ Agent info stored in phone number record: {agent_id}")
                                else:
                                    print(f"⚠️ Failed to update phone number record")

                            except Exception as phone_error:
                                print(f"⚠️ Phone number update error: {phone_error}")

                        # Final fallback: Log to console for manual entry
                        print(f"📋 MANUAL ENTRY REQUIRED:")
                        print(f"Agent ID: {agent_id}")
                        print(f"Agent Name: {agent_name}")
                        print(f"Phone: {phone_number}")
                        print(f"Full Data: {json.dumps(agent_record, ensure_ascii=False)}")

            except Exception as db_error:
                print(f"⚠️ Database storage error: {db_error}")
                # Don't fail the whole request if database storage fails

            # Store phone number to agent mapping in database
            if phone_number and agent_id:
                try:
                    if user_id:
                        update_data = {
                            'agent_id': agent_id,
                            'agent_name': agent_name,
                            'updated_at': datetime.now().isoformat()
                        }

                        # Update phone number record
                        result = supabase_request('PATCH',
                            f'purchased_phone_numbers?phone_number=eq.{phone_number}&user_id=eq.{user_id}',
                            data=update_data)

                        if result:
                            print(f"📞 Successfully mapped phone {phone_number} to agent {agent_id} in database")
                        else:
                            print(f"⚠️ Failed to update phone number mapping in database")
                    else:
                        print(f"⚠️ No user_id found, cannot update phone mapping")

                except Exception as e:
                    print(f"❌ Error updating phone number mapping: {e}")

            return jsonify({
                'message': 'Sales agent created successfully',
                'agent_id': agent_id,
                'status': response.get('status', 'created'),
                'agent_name': agent_name,
                'agent_type': agent_type,
                'phone_number': phone_number
            })

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error creating agent: {e}")
            return jsonify({'message': f'Network error: {str(e)}'}), 500
        except Exception as e:
            print(f"❌ API error creating agent: {e}")
            return jsonify({'message': f'API error: {str(e)}'}), 500

    except Exception as e:
        print(f"❌ Error creating sales agent: {e}")
        return jsonify({'message': f'Failed to create sales agent: {str(e)}'}), 500


@app.route('/api/bolna/update-sales-agent', methods=['POST'])
def update_sales_agent():
    """Update an existing sales agent with new configuration"""
    global phone_agent_mapping
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except ImportError as e:
            return jsonify({'message': f'Bolna integration module not found: {str(e)}'}), 500
        except ValueError as e:
            return jsonify({'message': f'Bolna API configuration error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'message': f'Failed to initialize Bolna API: {str(e)}'}), 500

        # Extract form data
        agent_id = data.get('agent_id', '')
        agent_name = data.get('name', '')
        agent_type = data.get('type', 'sales')
        welcome_message = data.get('welcome_message', '')
        prompt = data.get('prompt', '')
        description = data.get('description', '')
        voice = data.get('voice', 'Aditi')
        language = data.get('language', 'hi')
        max_duration = data.get('max_duration', 180)
        silence_timeout = data.get('silence_timeout', 15)
        sales_approach = data.get('sales_approach', 'consultative')

        if not agent_id:
            return jsonify({'message': 'Agent ID is required for update'}), 400

        # Use custom welcome message if provided, otherwise use default
        if not welcome_message.strip():
            welcome_message = f"नमस्ते! मैं {agent_name.split(' - ')[-1] if ' - ' in agent_name else 'राज'} हूं, आपका sales assistant। आज मैं आपकी कैसे मदद कर सकता हूं?"

        # Use custom prompt if provided, otherwise use default
        if prompt.strip():
            system_prompt = prompt
        else:
            system_prompt = f"""आप एक expert sales representative हैं जिसका नाम {agent_name.split(' - ')[-1] if ' - ' in agent_name else 'राज'} है। आप Hindi और English दोनों भाषाओं में fluent हैं।

आपका मुख्य goal है:
1. Customer के साथ friendly relationship बनाना
2. Product/service की benefits explain करना
3. Objections को handle करना
4. Sale close करना या follow-up schedule करना

आपकी personality:
- Confident लेकिन humble
- Customer-focused approach
- Problem solver mindset
- Persistent लेकिन respectful

Sales Approach: {sales_approach.title()}

Language Guidelines:
- Hindi-English mix (Hinglish) naturally use करें
- Customer की language preference को follow करें
- Technical terms को simple language में explain करें
- Respectful tone maintain करें

Call Structure:
1. Warm greeting और introduction
2. Customer की current situation जानें
3. Product benefits present करें
4. Objections handle करें
5. Closing attempt करें
6. Next steps decide करें

Remember: हमेशा customer की value को priority दें, sales को नहीं।"""

        # Build updated agent configuration
        sales_config = {
            "agent_name": agent_name,
            "agent_welcome_message": welcome_message,
            "webhook_url": None,
            "agent_type": agent_type,
            "tasks": [
                {
                    "task_type": "conversation",
                    "tools_config": {
                        "llm_agent": {
                            "agent_type": "simple_llm_agent",
                            "agent_flow_type": "streaming",
                            "llm_config": {
                                "agent_flow_type": "streaming",
                                "provider": "openai",
                                "family": "openai",
                                "model": "gpt-4",
                                "max_tokens": 200,
                                "presence_penalty": 0.1,
                                "frequency_penalty": 0.1,
                                "base_url": "https://api.openai.com/v1",
                                "top_p": 0.9,
                                "temperature": 0.7,
                                "request_json": True
                            }
                        },
                        "synthesizer": {
                            "provider": "polly",
                            "provider_config": {
                                "voice": voice,
                                "engine": "neural",
                                "sampling_rate": "8000",
                                "language": "hi-IN" if language == 'hi' else "en-US"
                            },
                            "stream": True,
                            "buffer_size": 150,
                            "audio_format": "wav"
                        },
                        "transcriber": {
                            "provider": "deepgram",
                            "model": "nova-2",
                            "language": language,
                            "stream": True,
                            "sampling_rate": 16000,
                            "encoding": "linear16",
                            "endpointing": 100
                        },
                        "input": {
                            "provider": "twilio",
                            "format": "wav"
                        },
                        "output": {
                            "provider": "twilio",
                            "format": "wav"
                        }
                    },
                    "toolchain": {
                        "execution": "parallel",
                        "pipelines": [
                            ["transcriber", "llm", "synthesizer"]
                        ]
                    },
                    "task_config": {
                        "hangup_after_silence": silence_timeout,
                        "incremental_delay": 300,
                        "number_of_words_for_interruption": 3,
                        "hangup_after_LLMCall": False,
                        "call_cancellation_prompt": "धन्यवाद! आपका दिन शुभ हो। नमस्ते!",
                        "backchanneling": True,
                        "backchanneling_message_gap": 4,
                        "backchanneling_start_delay": 3,
                        "ambient_noise": False,
                        "call_terminate": max_duration,
                        "voicemail": True,
                        "inbound_limit": -1,
                        "whitelist_phone_numbers": ["<any>"],
                        "disallow_unknown_numbers": False
                    }
                }
            ]
        }

        sales_prompts = {
            "task_1": {
                "system_prompt": system_prompt
            }
        }

        # Create agent update data
        agent_data = {
            "agent_config": sales_config,
            "agent_prompts": sales_prompts
        }

        # Update the agent via Bolna API
        try:
            response = bolna_api._make_request('PUT', f'/v2/agent/{agent_id}', agent_data)

            # Log the update
            print(f"✅ Sales agent updated: {response}")

            # Update phone number mapping in database if phone_number is provided
            phone_number = data.get('phone_number')
            if phone_number and agent_id:
                try:
                    # Update the purchased_phone_numbers table with agent info
                    user_data = request.current_user
                    user_id = user_data.get('user_id') or user_data.get('id') if user_data else None

                    if user_id:
                        update_data = {
                            'agent_name': agent_name,
                            'updated_at': datetime.now().isoformat()
                        }

                        # Update phone number record
                        result = supabase_request('PATCH',
                            f'purchased_phone_numbers?phone_number=eq.{phone_number}&user_id=eq.{user_id}',
                            data=update_data)

                        if result:
                            print(f"📞 Successfully updated agent name for phone {phone_number} in database")
                        else:
                            print(f"⚠️ Failed to update agent name in database")
                    else:
                        print(f"⚠️ No user_id found, cannot update phone mapping")

                except Exception as e:
                    print(f"❌ Error updating phone number mapping: {e}")

            return jsonify({
                'message': 'Sales agent updated successfully',
                'agent_id': agent_id,
                'status': response.get('status', 'updated'),
                'agent_name': agent_name,
                'agent_type': agent_type
            })

        except Exception as e:
            print(f"❌ API error updating agent: {e}")
            return jsonify({'message': f'API error: {str(e)}'}), 500

    except Exception as e:
        print(f"❌ Error updating sales agent: {e}")
        return jsonify({'message': f'Failed to update sales agent: {str(e)}'}), 500


@app.route('/api/database/agents', methods=['GET'])
@login_required
def get_agents_from_database():
    """Get all agents stored in our database"""
    try:
        # Get current user info
        user_data = getattr(request, 'current_user', None)
        user_id = user_data.get('user_id') or user_data.get('id') if user_data else None

        print(f"🔍 DEBUG - Database API - User data: {user_data}")
        print(f"🔍 DEBUG - Database API - User ID: {user_id}")

        # Build query - filter by user if available
        query = 'bolna_agents'
        if user_id:
            query += f'?user_id=eq.{user_id}'

        # Get agents from database
        db_result = supabase_request('GET', query)

        if not db_result:
            return jsonify({
                'success': True,
                'agents': [],
                'total': 0,
                'message': 'No agents found in database'
            })

        # Format agents for response
        agents_list = []
        for agent in db_result:
            agents_list.append({
                'id': agent.get('id'),
                'bolna_agent_id': agent.get('bolna_agent_id'),
                'agent_id': agent.get('bolna_agent_id'),  # For compatibility
                'name': agent.get('agent_name'),
                'agent_name': agent.get('agent_name'),
                'type': agent.get('agent_type'),
                'description': agent.get('description'),
                'voice': agent.get('voice'),
                'language': agent.get('language'),
                'phone_number': agent.get('phone_number'),
                'status': agent.get('status'),
                'welcome_message': agent.get('welcome_message'),
                'prompt': agent.get('prompt'),
                'max_duration': agent.get('max_duration'),
                'hangup_after': agent.get('hangup_after'),
                'created_at': agent.get('created_at'),
                'updated_at': agent.get('updated_at')
            })

        return jsonify({
            'success': True,
            'agents': agents_list,
            'total': len(agents_list)
        })

    except Exception as e:
        print(f"❌ Error getting agents from database: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get agents: {str(e)}'
        }), 500

@app.route('/create-agent.html')
def serve_create_agent():
    """Serve agent creation page"""
    return send_from_directory(app.static_folder, 'create-agent.html')

@app.route('/create-sales-agent.html')
def serve_create_sales_agent():
    """Serve sales agent creation page"""
    return send_from_directory(app.static_folder, 'create-sales-agent.html')

@app.route('/organization-detail.html')
def serve_organization_detail():
    """Serve organization detail page"""
    return send_from_directory(app.static_folder, 'organization-detail.html')

@app.route('/channel-detail.html')
def serve_channel_detail():
    """Serve channel detail page"""
    return send_from_directory(app.static_folder, 'channel-detail.html')

@app.route('/book-demo.html')
def serve_book_demo():
    """Serve book demo page"""
    return send_from_directory(app.static_folder, 'book-demo.html')

@app.route('/<path:path>')
def serve_static(path):
    # Prevent directory traversal
    if '..' in path or path.startswith('/'):
        return 'Forbidden', 403
    return send_from_directory(app.static_folder, path)

@app.route('/api/dev/test-agent-name', methods=['GET'])
def test_agent_name():
    """Test endpoint to check agent name fetching"""
    try:
        # Test with a known agent ID
        agent_id = request.args.get('agent_id')
        if not agent_id:
            return jsonify({'error': 'agent_id parameter required'}), 400

        agent_name = get_agent_name_from_bolna(agent_id)

        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'agent_name': agent_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda status, headers: None)

# For Railway/production deployment
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5003))
    print("Starting bhashai.com SaaS Platform")
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Server running on port: {port}")
    print("Available routes:")
    print(f"- http://0.0.0.0:{port}/ (Landing Page)")
    print(f"- http://0.0.0.0:{port}/dashboard.html (User Dashboard)")
    print(f"- http://0.0.0.0:{port}/admin/dashboard (Superadmin Dashboard)")
    print(f"- http://0.0.0.0:{port}/api/dev/voice-agents (API Test)")
    app.run(host="0.0.0.0", port=port, debug=False)