"""
Trial Access Control Middleware
Handles trial limitations and access controls for BhashAI platform
"""

from functools import wraps
from flask import jsonify, g, request
from datetime import datetime, timezone
import json

class TrialLimitations:
    """Define trial user limitations"""
    
    # API call limits per day
    MAX_API_CALLS_PER_DAY = 100
    
    # Voice agent usage limits
    MAX_VOICE_MINUTES_PER_DAY = 60  # 1 hour per day
    MAX_VOICE_MINUTES_TOTAL = 300   # 5 hours total for trial
    
    # Feature limitations
    ALLOWED_FEATURES = [
        'basic_voice_agent',
        'hindi_support',
        'basic_analytics',
        'trial_dashboard'
    ]
    
    RESTRICTED_FEATURES = [
        'advanced_analytics',
        'custom_voice_models',
        'api_integrations',
        'white_label',
        'priority_support',
        'bulk_operations',
        'advanced_reporting'
    ]
    
    # Enterprise limitations
    MAX_ENTERPRISES = 1
    MAX_USERS_PER_ENTERPRISE = 3
    MAX_VOICE_AGENTS = 2

def check_trial_limits(feature=None, usage_type=None):
    """Decorator to check trial limitations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip if user is not authenticated
            if not hasattr(g, 'current_user') or not g.current_user:
                return f(*args, **kwargs)
            
            user_id = g.user_id
            
            try:
                # Get user data from request context or database
                from main import supabase_request, check_trial_status
                
                users = supabase_request('GET', 'users', params={'id': f'eq.{user_id}'})
                
                if not users or len(users) == 0:
                    return jsonify({'error': 'User not found'}), 404
                
                user = users[0]
                trial_status = check_trial_status(user)
                
                # If not a trial user, allow access
                if not trial_status.get('is_trial', False):
                    return f(*args, **kwargs)
                
                # Check if trial has expired
                if trial_status.get('expired', False):
                    return jsonify({
                        'error': 'Trial expired',
                        'message': 'Your 14-day free trial has expired. Please upgrade to continue using BhashAI.',
                        'trial_status': trial_status,
                        'upgrade_url': '/upgrade'
                    }), 403
                
                # Check feature restrictions
                if feature and feature in TrialLimitations.RESTRICTED_FEATURES:
                    return jsonify({
                        'error': 'Feature not available in trial',
                        'message': f'The {feature} feature is not available in the trial version. Please upgrade to access this feature.',
                        'trial_status': trial_status,
                        'upgrade_url': '/upgrade'
                    }), 403
                
                # Check usage limits
                if usage_type:
                    usage_check = check_usage_limits(user_id, usage_type, trial_status)
                    if not usage_check['allowed']:
                        return jsonify({
                            'error': 'Usage limit exceeded',
                            'message': usage_check['message'],
                            'trial_status': trial_status,
                            'usage_info': usage_check,
                            'upgrade_url': '/upgrade'
                        }), 429
                
                # Add trial status to response context
                g.trial_status = trial_status
                
                return f(*args, **kwargs)
                
            except Exception as e:
                print(f"Error checking trial limits: {e}")
                # Allow access if there's an error (fail open)
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def check_usage_limits(user_id, usage_type, trial_status):
    """Check specific usage limits for trial users"""
    try:
        from main import supabase_request
        
        today = datetime.now(timezone.utc).date().isoformat()
        
        if usage_type == 'api_calls':
            # Check daily API call limit
            logs = supabase_request('GET', 'activity_logs', params={
                'user_id': f'eq.{user_id}',
                'activity_type': f'eq.api_call',
                'created_at': f'gte.{today}T00:00:00Z'
            })
            
            daily_calls = len(logs) if logs else 0
            
            if daily_calls >= TrialLimitations.MAX_API_CALLS_PER_DAY:
                return {
                    'allowed': False,
                    'message': f'Daily API call limit exceeded ({TrialLimitations.MAX_API_CALLS_PER_DAY} calls/day)',
                    'current_usage': daily_calls,
                    'limit': TrialLimitations.MAX_API_CALLS_PER_DAY,
                    'reset_time': f'{today}T23:59:59Z'
                }
        
        elif usage_type == 'voice_minutes':
            # Check voice usage limits
            logs = supabase_request('GET', 'call_logs', params={
                'user_id': f'eq.{user_id}',
                'created_at': f'gte.{today}T00:00:00Z'
            })
            
            daily_minutes = sum(log.get('duration_minutes', 0) for log in logs) if logs else 0
            
            if daily_minutes >= TrialLimitations.MAX_VOICE_MINUTES_PER_DAY:
                return {
                    'allowed': False,
                    'message': f'Daily voice usage limit exceeded ({TrialLimitations.MAX_VOICE_MINUTES_PER_DAY} minutes/day)',
                    'current_usage': daily_minutes,
                    'limit': TrialLimitations.MAX_VOICE_MINUTES_PER_DAY,
                    'reset_time': f'{today}T23:59:59Z'
                }
            
            # Check total trial usage
            all_logs = supabase_request('GET', 'call_logs', params={
                'user_id': f'eq.{user_id}'
            })
            
            total_minutes = sum(log.get('duration_minutes', 0) for log in all_logs) if all_logs else 0
            
            if total_minutes >= TrialLimitations.MAX_VOICE_MINUTES_TOTAL:
                return {
                    'allowed': False,
                    'message': f'Total trial voice usage limit exceeded ({TrialLimitations.MAX_VOICE_MINUTES_TOTAL} minutes total)',
                    'current_usage': total_minutes,
                    'limit': TrialLimitations.MAX_VOICE_MINUTES_TOTAL
                }
        
        elif usage_type == 'enterprise_creation':
            # Check enterprise creation limit
            enterprises = supabase_request('GET', 'enterprises', params={
                'owner_id': f'eq.{user_id}'
            })
            
            enterprise_count = len(enterprises) if enterprises else 0
            
            if enterprise_count >= TrialLimitations.MAX_ENTERPRISES:
                return {
                    'allowed': False,
                    'message': f'Trial users can create only {TrialLimitations.MAX_ENTERPRISES} enterprise',
                    'current_usage': enterprise_count,
                    'limit': TrialLimitations.MAX_ENTERPRISES
                }
        
        elif usage_type == 'voice_agent_creation':
            # Check voice agent creation limit
            agents = supabase_request('GET', 'voice_agents', params={
                'created_by': f'eq.{user_id}'
            })
            
            agent_count = len(agents) if agents else 0
            
            if agent_count >= TrialLimitations.MAX_VOICE_AGENTS:
                return {
                    'allowed': False,
                    'message': f'Trial users can create only {TrialLimitations.MAX_VOICE_AGENTS} voice agents',
                    'current_usage': agent_count,
                    'limit': TrialLimitations.MAX_VOICE_AGENTS
                }
        
        return {'allowed': True}
        
    except Exception as e:
        print(f"Error checking usage limits: {e}")
        # Allow access if there's an error
        return {'allowed': True}

def log_trial_activity(user_id, activity_type, details=None):
    """Log trial user activity for usage tracking"""
    try:
        from main import supabase_request
        
        activity_data = {
            'user_id': user_id,
            'activity_type': activity_type,
            'details': json.dumps(details) if details else None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        supabase_request('POST', 'activity_logs', data=activity_data)
        
    except Exception as e:
        print(f"Error logging trial activity: {e}")

def get_trial_usage_summary(user_id):
    """Get comprehensive usage summary for trial user"""
    try:
        from main import supabase_request
        
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Get API calls today
        api_logs = supabase_request('GET', 'activity_logs', params={
            'user_id': f'eq.{user_id}',
            'activity_type': f'eq.api_call',
            'created_at': f'gte.{today}T00:00:00Z'
        })
        
        # Get voice usage
        voice_logs_today = supabase_request('GET', 'call_logs', params={
            'user_id': f'eq.{user_id}',
            'created_at': f'gte.{today}T00:00:00Z'
        })
        
        voice_logs_total = supabase_request('GET', 'call_logs', params={
            'user_id': f'eq.{user_id}'
        })
        
        # Get enterprises and voice agents
        enterprises = supabase_request('GET', 'enterprises', params={
            'owner_id': f'eq.{user_id}'
        })
        
        voice_agents = supabase_request('GET', 'voice_agents', params={
            'created_by': f'eq.{user_id}'
        })
        
        return {
            'api_calls': {
                'today': len(api_logs) if api_logs else 0,
                'limit': TrialLimitations.MAX_API_CALLS_PER_DAY,
                'remaining': max(0, TrialLimitations.MAX_API_CALLS_PER_DAY - (len(api_logs) if api_logs else 0))
            },
            'voice_usage': {
                'today_minutes': sum(log.get('duration_minutes', 0) for log in voice_logs_today) if voice_logs_today else 0,
                'total_minutes': sum(log.get('duration_minutes', 0) for log in voice_logs_total) if voice_logs_total else 0,
                'daily_limit': TrialLimitations.MAX_VOICE_MINUTES_PER_DAY,
                'total_limit': TrialLimitations.MAX_VOICE_MINUTES_TOTAL
            },
            'resources': {
                'enterprises': len(enterprises) if enterprises else 0,
                'voice_agents': len(voice_agents) if voice_agents else 0,
                'enterprise_limit': TrialLimitations.MAX_ENTERPRISES,
                'voice_agent_limit': TrialLimitations.MAX_VOICE_AGENTS
            },
            'features': {
                'allowed': TrialLimitations.ALLOWED_FEATURES,
                'restricted': TrialLimitations.RESTRICTED_FEATURES
            }
        }
        
    except Exception as e:
        print(f"Error getting trial usage summary: {e}")
        return {}
