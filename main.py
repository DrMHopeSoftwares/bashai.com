from flask import Flask

app = Flask(__name__)
import os
import sys
import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, send_from_directory, g, redirect
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

# Redirect non-www to www for consistent domain access
@app.before_request
def redirect_non_www():
    host = request.host
    if host.startswith("bhashai.com"):
        return redirect(request.url.replace("://bhashai.com", "://www.bhashai.com"), code=301)

# Auth system already initialized via auth_routes.py

# Register authentication blueprint
app.register_blueprint(auth_bp)

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
@require_enterprise_context
@check_trial_limits(feature='basic_voice_agent', usage_type='voice_agent_creation')
def create_voice_agent():
    """Create voice agent with trial limitations"""
    try:
        user_id = g.user_id
        enterprise_id = g.enterprise_id  # Now available from middleware
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

        voice_agent_data = {
            'name': data['name'],
            'language': data['language'],
            'use_case': data['use_case'],
            'calling_number': data.get('calling_number'),  # Add calling number field
            'status': 'trial' if hasattr(g, 'trial_status') and g.trial_status.get('is_trial') else 'active',
            'created_by': user_id,
            'enterprise_id': enterprise_id,  # 🔥 CRITICAL FIX: Add enterprise_id
            'configuration': data.get('configuration', {}),
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

@app.route('/api/call-logs', methods=['GET'])
@login_required
def get_call_logs():
    """Get call logs for the user's enterprise"""
    try:
        user_id = g.user_id
        
        # Get user's enterprise
        user = supabase_request('GET', f'users?id=eq.{user_id}&select=enterprise_id,role')
        if not user or len(user) == 0:
            return jsonify({'message': 'User not found'}), 404
        
        user_data = user[0]
        enterprise_id = user_data['enterprise_id']
        
        # Get query parameters
        limit = request.args.get('limit', 50)
        offset = request.args.get('offset', 0)
        voice_agent_id = request.args.get('voice_agent_id')
        status = request.args.get('status')
        
        # Build query
        query_params = f'enterprise_id=eq.{enterprise_id}&order=created_at.desc&limit={limit}&offset={offset}'
        
        if voice_agent_id:
            query_params += f'&voice_agent_id=eq.{voice_agent_id}'
        if status:
            query_params += f'&status=eq.{status}'
        
        # Get call logs
        call_logs = supabase_request('GET', f'call_logs?{query_params}&select=*,contacts(name,phone),voice_agents(title)')
        
        return jsonify({'call_logs': call_logs or []}), 200
        
    except Exception as e:
        print(f"Get call logs error: {e}")
        return jsonify({'message': 'Failed to get call logs'}), 500

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
@app.route('/api/dev/voice-agents', methods=['GET'])
def dev_get_voice_agents():
    """Development endpoint to get voice agents without authentication"""
    try:
        voice_agents = supabase_request('GET', 'voice_agents?select=*,organizations(name),channels(name)')
        return jsonify({'voice_agents': voice_agents or []}), 200
    except Exception as e:
        print(f"Dev get voice agents error: {e}")
        return jsonify({'message': 'Failed to get voice agents'}), 500

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
        # Get voice agent details
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        return jsonify({'voice_agent': voice_agent[0]}), 200
        
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
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=*')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        agent_data = voice_agent[0]
        prompts = {
            'welcome_message': agent_data.get('welcome_message', ''),
            'agent_prompt': agent_data.get('agent_prompt', ''),
            'conversation_style': agent_data.get('conversation_style', 'professional'),
            'language_preference': agent_data.get('language_preference', 'hinglish'),
            'title': agent_data.get('title', ''),
            'description': agent_data.get('description', '')
        }
        
        return jsonify({'prompts': prompts}), 200
        
    except Exception as e:
        print(f"Dev get agent prompts error: {e}")
        return jsonify({'message': 'Failed to get agent prompts'}), 500

@app.route('/api/dev/voice-agents/<agent_id>/prompts', methods=['PUT'])
def dev_update_agent_prompts(agent_id):
    """Development endpoint to update agent prompts and configuration"""
    try:
        data = request.json
        
        # Validate agent exists
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&select=*')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'Voice agent not found'}), 404
        
        # Prepare update data
        update_data = {}
        if 'welcome_message' in data:
            update_data['welcome_message'] = data['welcome_message']
        if 'agent_prompt' in data:
            update_data['agent_prompt'] = data['agent_prompt']
        if 'conversation_style' in data:
            update_data['conversation_style'] = data['conversation_style']
        if 'language_preference' in data:
            update_data['language_preference'] = data['language_preference']
        
        if not update_data:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # Update agent prompts
        updated_agent = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}', data=update_data)
        
        return jsonify({
            'message': 'Agent prompts updated successfully',
            'agent_id': agent_id,
            'updated_fields': list(update_data.keys())
        }), 200
        
    except Exception as e:
        print(f"Dev update agent prompts error: {e}")
        return jsonify({'message': 'Failed to update agent prompts'}), 500

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
        
        # Initialize Bolna API
        try:
            from bolna_integration import BolnaAPI, get_agent_config_for_voice_agent
            bolna_api = BolnaAPI()
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
        agent_id = data.get('agent_id', 'manual-call')
        
        # Import Bolna API
        try:
            from bolna_integration import BolnaAPI
            bolna_api = BolnaAPI()
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Bolna API not configured: {str(e)}',
                'note': 'Please configure BOLNA_API_KEY and BOLNA_API_URL environment variables'
            }), 500
        
        # Get agent configuration
        from bolna_integration import get_agent_config_for_voice_agent
        agent_config = get_agent_config_for_voice_agent('Manual Call Agent')
        
        # Prepare call variables
        variables = {
            'contact_name': data.get('contact_name', 'Valued Customer'),
            'agent_title': 'Manual Call Assistant',
            'greeting': 'Hello, this is a call from BhashAI. How can I assist you today?',
            'purpose': 'manual_assistance',
            'language': 'hinglish'
        }
        
        # Make actual Bolna API call
        call_result = bolna_api.start_outbound_call(
            agent_id=agent_config['agent_id'],
            recipient_phone=recipient_phone,
            sender_phone=sender_phone,
            variables=variables,
            metadata={
                'initiated_by': 'web_interface',
                'call_type': 'manual',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        response = {
            'success': True,
            'message': f'Real call initiated via Bolna API to {recipient_phone}',
            'call_id': call_result.get('call_id'),
            'recipient_phone': recipient_phone,
            'sender_phone': sender_phone,
            'bolna_response': call_result
        }
        
        return jsonify(response), 200
        
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

@app.route('/api/dev/payment/transactions', methods=['GET'])
def dev_get_payment_history():
    """Development endpoint to get payment transaction history"""
    try:
        # Get enterprise details
        enterprise = supabase_request('GET', 'enterprises?limit=1')
        if not enterprise or len(enterprise) == 0:
            return jsonify({'message': 'No enterprise found'}), 404
        
        enterprise_id = enterprise[0]['id']
        
        # Get payment transactions
        transactions = supabase_request('GET', f'payment_transactions?enterprise_id=eq.{enterprise_id}&order=created_at.desc&limit=50')
        
        return jsonify({
            'transactions': transactions or [],
            'enterprise_id': enterprise_id
        }), 200
        
    except Exception as e:
        print(f"Get payment history error: {e}")
        return jsonify({'message': 'Failed to get payment history'}), 500

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
        response = supabase_request('GET', 'phone_number_providers', params={'status': 'eq.active'})
        if response.status_code == 200:
            providers = response.json()
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
        provider_response = supabase_request('GET', 'phone_number_providers', 
                                           params={'name': f'eq.{provider_name}'})
        
        if provider_response.status_code != 200 or not provider_response.json():
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
            'purchased_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        db_response = supabase_request('POST', 'purchased_phone_numbers', data=phone_record)
        
        if db_response.status_code == 201:
            return jsonify({
                'success': True,
                'phone_number': db_response.json()[0],
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
        
        response = supabase_request('GET', 'purchased_phone_numbers', 
                                  params={'enterprise_id': f'eq.{enterprise_id}',
                                         'status': 'eq.active'})
        
        if response.status_code == 200:
            phone_numbers = response.json()
            return jsonify({
                'success': True,
                'phone_numbers': phone_numbers
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch phone numbers'
            }), 500
            
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

@app.route('/api/phone-numbers/owned', methods=['GET'])
@login_required
@require_enterprise_context
def get_owned_phone_numbers():
    """Get owned phone numbers for the enterprise"""
    try:
        # Get enterprise context from middleware
        enterprise_id = g.enterprise_id

        # Fetch owned phone numbers with provider information
        # Using a more complex query to join with providers table
        query_params = {
            'select': 'id,phone_number,friendly_name,country_code,country_name,monthly_cost,setup_cost,capabilities,status,voice_url,sms_url,purchased_at,created_at,updated_at,phone_number_providers(name)',
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
            'data': phone_numbers
        })

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
@require_enterprise_context
def assign_phone_to_agent(phone_id):
    """Assign a phone number to a voice agent for outbound calling"""
    try:
        # Get enterprise context from middleware
        enterprise_id = g.enterprise_id
        data = request.get_json()
        agent_id = data.get('agent_id')

        if not agent_id:
            return jsonify({
                'success': False,
                'error': 'Agent ID is required'
            }), 400

        # Verify phone number belongs to enterprise
        phone_record = supabase_request('GET', 'purchased_phone_numbers',
                                      params={'id': f'eq.{phone_id}',
                                             'enterprise_id': f'eq.{enterprise_id}',
                                             'status': 'eq.active'})

        if not phone_record or len(phone_record) == 0:
            return jsonify({
                'success': False,
                'error': 'Phone number not found'
            }), 404

        # Verify voice agent belongs to enterprise
        agent_record = supabase_request('GET', 'voice_agents',
                                      params={'id': f'eq.{agent_id}',
                                             'enterprise_id': f'eq.{enterprise_id}',
                                             'status': 'eq.active'})

        if not agent_record or len(agent_record) == 0:
            return jsonify({
                'success': False,
                'error': 'Voice agent not found'
            }), 404

        # Update voice agent configuration to include phone number
        agent_config = agent_record[0].get('configuration', {})
        agent_config['outbound_phone_number'] = phone_record[0]['phone_number']
        agent_config['outbound_phone_number_id'] = phone_id

        update_result = supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}',
                                       data={'configuration': agent_config,
                                            'updated_at': datetime.now(timezone.utc).isoformat()})

        if update_result:
            return jsonify({
                'success': True,
                'message': f'Phone number {phone_record[0]["phone_number"]} assigned to agent {agent_record[0]["title"]}'
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
        response = supabase_request('GET', 'voice_providers', params={'status': 'eq.active'})
        if response.status_code == 200:
            providers = response.json()
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
            
        response = supabase_request('GET', 'available_voices', params=params)
        
        if response.status_code == 200:
            voices = response.json()
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
                
            response = supabase_request('GET', 'enterprise_voice_preferences', params=params)
            
            if response.status_code == 200:
                preferences = response.json()
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
            
            response = supabase_request('POST', 'enterprise_voice_preferences', data=preference_record)
            
            if response.status_code == 201:
                return jsonify({
                    'success': True,
                    'preference': response.json()[0],
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

@app.route('/phone-numbers.html')
def serve_phone_numbers():
    """Serve phone numbers management page"""
    return send_from_directory(app.static_folder, 'phone-numbers.html')

@app.route('/create-agent.html')
def serve_create_agent():
    """Serve agent creation page"""
    return send_from_directory(app.static_folder, 'create-agent.html')

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

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda status, headers: None)

# For Railway/production deployment
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print("Starting bhashai.com SaaS Platform")
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Server running on port: {port}")
    print("Available routes:")
    print(f"- http://0.0.0.0:{port}/ (Landing Page)")
    print(f"- http://0.0.0.0:{port}/dashboard.html (User Dashboard)")
    print(f"- http://0.0.0.0:{port}/admin/dashboard (Superadmin Dashboard)")
    print(f"- http://0.0.0.0:{port}/api/dev/voice-agents (API Test)")
    app.run(host="0.0.0.0", port=port, debug=False)