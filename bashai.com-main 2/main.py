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
from relevance_ai_integration import RelevanceAIProvider, RelevanceAIAgentManager, create_relevance_agent_config
from razorpay_integration import RazorpayIntegration, calculate_credits_from_amount, get_predefined_recharge_options
from phone_provider_integration import phone_provider_manager
from auth_routes import auth_bp
from functools import wraps
from flask_socketio import SocketIO

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)  # Enable CORS for all routes

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Redirect non-www to www for consistent domain access
@app.before_request
def redirect_non_www():
    host = request.host
    if host.startswith("bhashai.com"):
        return redirect(request.url.replace("://bhashai.com", "://www.bhashai.com"), code=301)

# Auth system already initialized via auth_routes.py

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Initialize OpenAI Realtime WebSocket handler
from realtime_websocket_handler import init_realtime_websocket
realtime_handler = init_realtime_websocket(app, socketio)

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
    print(f"🔍 Supabase request: {method} {url} with params: {params}")
    
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
        
        print(f"🔍 Response status: {response.status_code}")
        response.raise_for_status()
        result = response.json() if response.content else None
        print(f"🔍 Response data: {result}")
        return result
    
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
        print(f"🔍 Getting enterprises for user_id: {user_id}")
        print(f"🔍 Supabase available: {SUPABASE_AVAILABLE}")

        # Log API call for trial users
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            log_trial_activity(user_id, 'api_call', {'endpoint': '/api/enterprises', 'method': 'GET'})

        enterprises = supabase_request('GET', 'enterprises', params={'owner_id': f'eq.{user_id}'})
        print(f"🔍 Enterprises result: {enterprises}")

        return jsonify({'enterprises': enterprises or []})

    except Exception as e:
        print(f"❌ Get enterprises error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Failed to get enterprises: {str(e)}'}), 500

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
    """Create voice agent with multi-provider support (Bolna, RelevanceAI, OpenAI)"""
    try:
        user_id = g.user_id
        enterprise_id = g.enterprise_id
        data = request.json

        # Log API call for trial users
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            log_trial_activity(user_id, 'api_call', {'endpoint': '/api/voice-agents', 'method': 'POST'})

        # Required fields
        required_fields = ['name', 'language', 'use_case']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400

        # Get provider type (default to bolna for backward compatibility)
        provider_type = data.get('provider', 'bolna').lower()
        allowed_providers = ['bolna', 'relevance_ai', 'openai_realtime']
        
        if provider_type not in allowed_providers:
            return jsonify({
                'message': f'Invalid provider. Allowed providers: {allowed_providers}',
                'allowed_providers': allowed_providers
            }), 400

        # Trial users are limited to Hindi/Hinglish and basic providers
        if hasattr(g, 'trial_status') and g.trial_status.get('is_trial'):
            allowed_languages = ['hindi', 'hinglish', 'hi-IN']
            if data['language'].lower() not in allowed_languages:
                return jsonify({
                    'message': 'Trial users can only create Hindi/Hinglish voice agents',
                    'allowed_languages': allowed_languages
                }), 403
            
            # Trial users can't use RelevanceAI (premium feature)
            if provider_type == 'relevance_ai':
                return jsonify({
                    'message': 'RelevanceAI is a premium feature. Please upgrade your plan.',
                    'allowed_providers': ['bolna', 'openai_realtime']
                }), 403

        # Base voice agent data
        voice_agent_data = {
            'name': data['name'],
            'language': data['language'],
            'use_case': data['use_case'],
            'provider_type': provider_type,
            'calling_number': data.get('calling_number'),
            'status': 'trial' if hasattr(g, 'trial_status') and g.trial_status.get('is_trial') else 'active',
            'created_by': user_id,
            'enterprise_id': enterprise_id,
            'configuration': data.get('configuration', {}),
            'provider_config': data.get('provider_config', {}),
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        # Provider-specific initialization
        external_agent_id = None
        external_config = {}

        if provider_type == 'relevance_ai':
            try:
                # Initialize RelevanceAI manager
                relevance_manager = RelevanceAIAgentManager()
                
                # Create agent in RelevanceAI
                relevance_config = {
                    'name': data['name'],
                    'description': data.get('description', f"AI agent for {data['use_case']}"),
                    'language': data['language'],
                    'use_case': data['use_case'],
                    'integrations': data.get('integrations', []),
                    'tools': data.get('tools', [])
                }
                
                if data['use_case'] in ['workflow', 'automation', 'dataprocess']:
                    relevance_agent = relevance_manager.create_workflow_agent(relevance_config)
                else:
                    relevance_agent = relevance_manager.create_voice_agent(relevance_config)
                
                external_agent_id = relevance_agent.get('id')
                external_config = relevance_agent
                
                # Add RelevanceAI specific fields
                voice_agent_data.update({
                    'relevance_ai_agent_id': external_agent_id,
                    'relevance_ai_config': external_config
                })
                
                print(f"✅ RelevanceAI agent created: {external_agent_id}")
                
            except Exception as e:
                print(f"❌ Failed to create RelevanceAI agent: {e}")
                return jsonify({
                    'message': f'Failed to create RelevanceAI agent: {str(e)}',
                    'provider': 'relevance_ai'
                }), 500

        elif provider_type == 'bolna':
            # Existing Bolna logic (keep existing behavior)
            pass
            
        elif provider_type == 'openai_realtime':
            # OpenAI Realtime configuration
            voice_agent_data['provider_config'] = {
                'model': data.get('model', 'gpt-4o-realtime-preview'),
                'temperature': data.get('temperature', 0.7),
                'system_prompt': data.get('system_prompt', 'You are a helpful AI assistant.')
            }

        # Create voice agent in database
        voice_agent = supabase_request('POST', 'voice_agents', data=voice_agent_data)
        
        if not voice_agent:
            return jsonify({'message': 'Failed to create voice agent in database'}), 500

        # Add provider info to response
        response_data = {
            'voice_agent': voice_agent,
            'provider': {
                'type': provider_type,
                'external_agent_id': external_agent_id,
                'config': external_config
            }
        }

        return jsonify(response_data), 201

    except Exception as e:
        print(f"Create voice agent error: {e}")
        return jsonify({'message': f'Failed to create voice agent: {str(e)}'}), 500

# RelevanceAI specific endpoints
@app.route('/api/relevance-ai/agents', methods=['GET'])
@login_required
@require_enterprise_context
def list_relevance_ai_agents():
    """List all RelevanceAI agents for the enterprise"""
    try:
        enterprise_id = g.enterprise_id
        
        # Get RelevanceAI agents from database
        agents = supabase_request('GET', f'voice_agents?enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai&order=created_at.desc')
        
        return jsonify({'agents': agents or []}), 200
        
    except Exception as e:
        print(f"List RelevanceAI agents error: {e}")
        return jsonify({'message': 'Failed to list RelevanceAI agents'}), 500

@app.route('/api/relevance-ai/agents/<agent_id>/sessions', methods=['POST'])
@login_required
@require_enterprise_context
def create_relevance_ai_session(agent_id):
    """Create a new RelevanceAI conversation session"""
    try:
        enterprise_id = g.enterprise_id
        data = request.json
        
        # Verify agent exists and belongs to enterprise
        agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not agent or len(agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        agent_data = agent[0]
        external_agent_id = agent_data.get('relevance_ai_agent_id')
        
        if not external_agent_id:
            return jsonify({'message': 'RelevanceAI agent ID not found'}), 400
        
        # Create session via RelevanceAI
        relevance_manager = RelevanceAIAgentManager()
        session = relevance_manager.provider.create_session(
            agent_id=external_agent_id,
            session_config=data.get('config', {})
        )
        
        # Store session in database
        session_data = {
            'voice_agent_id': agent_id,
            'relevance_session_id': session['session_id'],
            'agent_id': external_agent_id,
            'status': 'active',
            'context': data.get('context', {}),
            'enterprise_id': enterprise_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        db_session = supabase_request('POST', 'relevance_ai_sessions', data=session_data)
        
        return jsonify({
            'session': db_session,
            'relevance_session': session
        }), 201
        
    except Exception as e:
        print(f"Create RelevanceAI session error: {e}")
        return jsonify({'message': f'Failed to create session: {str(e)}'}), 500

@app.route('/api/relevance-ai/sessions/<session_id>/messages', methods=['POST'])
@login_required
@require_enterprise_context
def send_relevance_ai_message(session_id):
    """Send a message to a RelevanceAI session"""
    try:
        enterprise_id = g.enterprise_id
        data = request.json
        
        message = data.get('message')
        if not message:
            return jsonify({'message': 'Message content is required'}), 400
        
        # Get session from database
        session = supabase_request('GET', f'relevance_ai_sessions?id=eq.{session_id}&enterprise_id=eq.{enterprise_id}')
        if not session or len(session) == 0:
            return jsonify({'message': 'Session not found'}), 404
        
        session_data = session[0]
        external_agent_id = session_data['agent_id']
        relevance_session_id = session_data['relevance_session_id']
        
        # Send message via RelevanceAI
        relevance_manager = RelevanceAIAgentManager()
        response = relevance_manager.provider.send_message(
            agent_id=external_agent_id,
            session_id=relevance_session_id,
            message=message,
            context=data.get('context', {})
        )
        
        # Store user message in database
        user_message_data = {
            'session_id': session_id,
            'message_type': 'user',
            'content': message,
            'metadata': data.get('context', {}),
            'enterprise_id': enterprise_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        supabase_request('POST', 'relevance_ai_messages', data=user_message_data)
        
        # Store agent response in database
        agent_response = response.get('response', '')
        if agent_response:
            agent_message_data = {
                'session_id': session_id,
                'message_type': 'agent',
                'content': agent_response,
                'metadata': response.get('metadata', {}),
                'enterprise_id': enterprise_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            supabase_request('POST', 'relevance_ai_messages', data=agent_message_data)
        
        return jsonify({
            'response': response,
            'session_id': session_id
        }), 200
        
    except Exception as e:
        print(f"Send RelevanceAI message error: {e}")
        return jsonify({'message': f'Failed to send message: {str(e)}'}), 500

@app.route('/api/relevance-ai/sessions/<session_id>/history', methods=['GET'])
@login_required
@require_enterprise_context
def get_relevance_ai_session_history(session_id):
    """Get conversation history for a RelevanceAI session"""
    try:
        enterprise_id = g.enterprise_id
        
        # Verify session belongs to enterprise
        session = supabase_request('GET', f'relevance_ai_sessions?id=eq.{session_id}&enterprise_id=eq.{enterprise_id}')
        if not session or len(session) == 0:
            return jsonify({'message': 'Session not found'}), 404
        
        # Get messages for this session
        messages = supabase_request('GET', f'relevance_ai_messages?session_id=eq.{session_id}&order=timestamp.asc')
        
        return jsonify({
            'session_id': session_id,
            'messages': messages or []
        }), 200
        
    except Exception as e:
        print(f"Get RelevanceAI session history error: {e}")
        return jsonify({'message': 'Failed to get session history'}), 500

@app.route('/api/relevance-ai/agents/<agent_id>/analytics', methods=['GET'])
@login_required
@require_enterprise_context
def get_relevance_ai_analytics(agent_id):
    """Get analytics for a RelevanceAI agent"""
    try:
        enterprise_id = g.enterprise_id
        
        # Verify agent exists and belongs to enterprise
        agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not agent or len(agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        agent_data = agent[0]
        external_agent_id = agent_data.get('relevance_ai_agent_id')
        
        # Get analytics from RelevanceAI
        relevance_manager = RelevanceAIAgentManager()
        analytics = relevance_manager.provider.get_analytics(external_agent_id)
        
        # Get session statistics from database
        sessions_count = supabase_request('GET', f'relevance_ai_sessions?voice_agent_id=eq.{agent_id}&select=id')
        completed_sessions = supabase_request('GET', f'relevance_ai_sessions?voice_agent_id=eq.{agent_id}&status=eq.completed&select=id')
        total_messages = supabase_request('GET', f'relevance_ai_messages?session_id=in.(select id from relevance_ai_sessions where voice_agent_id={agent_id})&select=id')
        
        local_analytics = {
            'total_sessions': len(sessions_count) if sessions_count else 0,
            'completed_sessions': len(completed_sessions) if completed_sessions else 0,
            'total_messages': len(total_messages) if total_messages else 0,
            'success_rate': (len(completed_sessions) / len(sessions_count) * 100) if sessions_count else 0
        }
        
        return jsonify({
            'agent_id': agent_id,
            'external_analytics': analytics,
            'local_analytics': local_analytics
        }), 200
        
    except Exception as e:
        print(f"Get RelevanceAI analytics error: {e}")
        return jsonify({'message': 'Failed to get analytics'}), 500

@app.route('/api/relevance-ai/tools', methods=['GET'])
@login_required
@require_enterprise_context
def list_relevance_ai_tools():
    """List available RelevanceAI tools for the enterprise"""
    try:
        enterprise_id = g.enterprise_id
        
        tools = supabase_request('GET', f'relevance_ai_tools?enterprise_id=eq.{enterprise_id}&is_active=eq.true&order=created_at.desc')
        
        return jsonify({'tools': tools or []}), 200
        
    except Exception as e:
        print(f"List RelevanceAI tools error: {e}")
        return jsonify({'message': 'Failed to list tools'}), 500

# RelevanceAI Agent Prompt Management Endpoints
@app.route('/api/relevance-ai/agents/<agent_id>/prompt', methods=['GET'])
@login_required
@require_enterprise_context
def get_relevance_ai_agent_prompt(agent_id):
    """Get the current system prompt for a RelevanceAI agent"""
    try:
        enterprise_id = g.enterprise_id
        
        # Verify agent belongs to enterprise
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        # Get current prompt from RelevanceAI
        from relevance_ai_integration_fixed import RelevanceAIProvider
        provider = RelevanceAIProvider()
        
        try:
            # Get agent details from RelevanceAI
            agent_details = provider.get_agent(agent_id)
            agent_data = agent_details.get('agent_data')
            
            if hasattr(agent_data, 'metadata'):
                current_prompt = getattr(agent_data.metadata, 'system_prompt', '')
                agent_name = getattr(agent_data.metadata, 'name', 'Unknown')
                last_updated = getattr(agent_data.metadata, 'update_date_', 'Unknown')
            else:
                current_prompt = ''
                agent_name = 'Unknown'
                last_updated = 'Unknown'
            
            return jsonify({
                'agent_id': agent_id,
                'agent_name': agent_name,
                'system_prompt': current_prompt,
                'prompt_length': len(current_prompt),
                'last_updated': last_updated
            }), 200
            
        except Exception as e:
            return jsonify({'message': f'Failed to retrieve prompt: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Get RelevanceAI prompt error: {e}")
        return jsonify({'message': 'Failed to get agent prompt'}), 500

@app.route('/api/relevance-ai/agents/<agent_id>/prompt', methods=['PUT'])
@login_required
@require_enterprise_context
def update_relevance_ai_agent_prompt(agent_id):
    """Update the system prompt for a RelevanceAI agent"""
    try:
        enterprise_id = g.enterprise_id
        data = request.json
        new_prompt = data.get('system_prompt', '').strip()
        
        if not new_prompt:
            return jsonify({'message': 'System prompt is required'}), 400
        
        # Verify agent belongs to enterprise
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        # Update prompt in RelevanceAI
        from relevance_ai_integration_fixed import RelevanceAIProvider
        provider = RelevanceAIProvider()
        
        try:
            # Update the agent prompt
            success = provider.update_agent_prompt(agent_id, new_prompt)
            
            if success:
                # Update last modified in our database
                update_data = {
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'provider_config': {
                        **voice_agent[0].get('provider_config', {}),
                        'last_prompt_update': datetime.now(timezone.utc).isoformat(),
                        'prompt_length': len(new_prompt)
                    }
                }
                
                supabase_request('PATCH', f'voice_agents?id=eq.{agent_id}', data=update_data)
                
                return jsonify({
                    'message': 'Agent prompt updated successfully',
                    'agent_id': agent_id,
                    'prompt_length': len(new_prompt),
                    'updated_at': update_data['updated_at']
                }), 200
            else:
                return jsonify({'message': 'Failed to update prompt in RelevanceAI'}), 500
                
        except Exception as e:
            return jsonify({'message': f'Failed to update prompt: {str(e)}'}), 500
        
    except Exception as e:
        print(f"Update RelevanceAI prompt error: {e}")
        return jsonify({'message': 'Failed to update agent prompt'}), 500

@app.route('/api/relevance-ai/agents/<agent_id>/test-prompt', methods=['POST'])
@login_required  
@require_enterprise_context
def test_relevance_ai_agent_prompt(agent_id):
    """Test a RelevanceAI agent with a sample message"""
    try:
        enterprise_id = g.enterprise_id
        data = request.json
        test_message = data.get('message', 'Hello, I need to book an appointment with Dr. Murali')
        
        # Verify agent belongs to enterprise
        voice_agent = supabase_request('GET', f'voice_agents?id=eq.{agent_id}&enterprise_id=eq.{enterprise_id}&provider_type=eq.relevance_ai')
        if not voice_agent or len(voice_agent) == 0:
            return jsonify({'message': 'RelevanceAI agent not found'}), 404
        
        # Test the agent using our working API format
        import requests
        import os
        
        api_key = os.getenv('RELEVANCE_AI_API_KEY')
        region = os.getenv('RELEVANCE_AI_REGION', 'f1db6c') 
        project_id = os.getenv('RELEVANCE_AI_PROJECT_ID')
        
        headers = {
            "Authorization": f"{project_id}:{api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "agent_id": agent_id,
            "message": {
                "role": "user",
                "content": test_message
            }
        }
        
        response = requests.post(
            f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger",
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'status': 'test_initiated',
                'conversation_id': result.get('conversation_id'),
                'job_id': result.get('job_info', {}).get('job_id'),
                'test_message': test_message,
                'agent_id': agent_id
            }), 200
        else:
            return jsonify({
                'message': f'Test failed with status {response.status_code}',
                'error': response.text
            }), 500
            
    except Exception as e:
        print(f"Test RelevanceAI agent error: {e}")
        return jsonify({'message': 'Failed to test agent'}), 500

@app.route('/api/relevance-ai/tools', methods=['POST'])
@login_required
@require_enterprise_context
def create_relevance_ai_tool():
    """Create a new RelevanceAI tool"""
    try:
        enterprise_id = g.enterprise_id
        user_id = g.user_id
        data = request.json
        
        required_fields = ['name', 'tool_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Create tool via RelevanceAI
        relevance_manager = RelevanceAIAgentManager()
        tool_config = {
            'name': data['name'],
            'description': data.get('description', ''),
            'type': data['tool_type'],
            'config': data.get('config', {})
        }
        
        relevance_tool = relevance_manager.provider.create_tool(tool_config)
        
        # Store tool in database
        tool_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'tool_type': data['tool_type'],
            'config': data.get('config', {}),
            'relevance_tool_id': relevance_tool.get('id'),
            'enterprise_id': enterprise_id,
            'created_by': user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        db_tool = supabase_request('POST', 'relevance_ai_tools', data=tool_data)
        
        return jsonify({
            'tool': db_tool,
            'relevance_tool': relevance_tool
        }), 201
        
    except Exception as e:
        print(f"Create RelevanceAI tool error: {e}")
        return jsonify({'message': f'Failed to create tool: {str(e)}'}), 500

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

