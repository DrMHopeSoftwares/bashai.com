"""
Realtime API Usage Tracking and Billing Module
Handles cost calculation, trial limits, and usage analytics for OpenAI Realtime API
"""

import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

class RealtimeUsageTracker:
    """Tracks and calculates usage costs for OpenAI Realtime API"""
    
    def __init__(self):
        # Pricing per minute (as of OpenAI Realtime API preview)
        self.PRICING = {
            'gpt-4o-realtime-preview': {
                'audio_input_per_minute': Decimal('0.1000'),    # $0.10 per minute of audio input
                'audio_output_per_minute': Decimal('0.2000'),   # $0.20 per minute of audio output
                'text_tokens_per_1k': Decimal('0.0050')        # $0.005 per 1K text tokens
            }
        }
        
        # Trial limits
        self.TRIAL_LIMITS = {
            'daily_minutes': 30,
            'monthly_minutes': 300,
            'daily_sessions': 10,
            'monthly_sessions': 100
        }
        
        # Cost tracking
        self.session_costs = {}

    def start_session_tracking(self, session_id: str, user_id: str, model: str = 'gpt-4o-realtime-preview') -> Dict:
        """
        Initialize tracking for a new realtime session
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            model: OpenAI model being used
            
        Returns:
            Dict: Session tracking info
        """
        session_info = {
            'session_id': session_id,
            'user_id': user_id,
            'model': model,
            'started_at': datetime.now(timezone.utc),
            'ended_at': None,
            'audio_input_seconds': 0,
            'audio_output_seconds': 0,
            'text_tokens_used': 0,
            'estimated_cost_usd': Decimal('0.00'),
            'cost_breakdown': {
                'audio_input_cost': Decimal('0.00'),
                'audio_output_cost': Decimal('0.00'),
                'text_cost': Decimal('0.00')
            }
        }
        
        self.session_costs[session_id] = session_info
        return session_info

    def track_audio_input(self, session_id: str, duration_seconds: int) -> Dict:
        """
        Track audio input usage
        
        Args:
            session_id: Session identifier
            duration_seconds: Duration of audio input in seconds
            
        Returns:
            Dict: Updated session info
        """
        if session_id not in self.session_costs:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.session_costs[session_id]
        session['audio_input_seconds'] += duration_seconds
        
        # Calculate cost
        minutes = Decimal(session['audio_input_seconds']) / Decimal(60)
        model_pricing = self.PRICING.get(session['model'], self.PRICING['gpt-4o-realtime-preview'])
        
        session['cost_breakdown']['audio_input_cost'] = minutes * model_pricing['audio_input_per_minute']
        
        self._update_total_cost(session_id)
        return session

    def track_audio_output(self, session_id: str, duration_seconds: int) -> Dict:
        """
        Track audio output usage
        
        Args:
            session_id: Session identifier
            duration_seconds: Duration of audio output in seconds
            
        Returns:
            Dict: Updated session info
        """
        if session_id not in self.session_costs:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.session_costs[session_id]
        session['audio_output_seconds'] += duration_seconds
        
        # Calculate cost
        minutes = Decimal(session['audio_output_seconds']) / Decimal(60)
        model_pricing = self.PRICING.get(session['model'], self.PRICING['gpt-4o-realtime-preview'])
        
        session['cost_breakdown']['audio_output_cost'] = minutes * model_pricing['audio_output_per_minute']
        
        self._update_total_cost(session_id)
        return session

    def track_text_tokens(self, session_id: str, token_count: int) -> Dict:
        """
        Track text token usage
        
        Args:
            session_id: Session identifier
            token_count: Number of tokens used
            
        Returns:
            Dict: Updated session info
        """
        if session_id not in self.session_costs:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.session_costs[session_id]
        session['text_tokens_used'] += token_count
        
        # Calculate cost (per 1K tokens)
        thousands = Decimal(session['text_tokens_used']) / Decimal(1000)
        model_pricing = self.PRICING.get(session['model'], self.PRICING['gpt-4o-realtime-preview'])
        
        session['cost_breakdown']['text_cost'] = thousands * model_pricing['text_tokens_per_1k']
        
        self._update_total_cost(session_id)
        return session

    def end_session_tracking(self, session_id: str) -> Dict:
        """
        End session tracking and finalize costs
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict: Final session info with costs
        """
        if session_id not in self.session_costs:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.session_costs[session_id]
        session['ended_at'] = datetime.now(timezone.utc)
        
        # Calculate total session duration
        if session['started_at'] and session['ended_at']:
            duration = session['ended_at'] - session['started_at']
            session['total_duration_seconds'] = int(duration.total_seconds())
        
        return session

    def _update_total_cost(self, session_id: str):
        """Update total estimated cost for session"""
        session = self.session_costs[session_id]
        breakdown = session['cost_breakdown']
        
        session['estimated_cost_usd'] = (
            breakdown['audio_input_cost'] + 
            breakdown['audio_output_cost'] + 
            breakdown['text_cost']
        )

    def get_session_cost(self, session_id: str) -> Optional[Dict]:
        """Get cost information for a session"""
        return self.session_costs.get(session_id)

    def check_trial_limits(self, user_id: str) -> Dict:
        """
        Check if user has exceeded trial limits
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict: Trial limit status
        """
        # This would typically query the database for user's usage
        # For now, returning a mock response
        
        today = datetime.now(timezone.utc).date()
        current_month = today.replace(day=1)
        
        # In a real implementation, query the database
        daily_usage = self._get_user_daily_usage(user_id, today)
        monthly_usage = self._get_user_monthly_usage(user_id, current_month)
        
        return {
            'within_limits': True,
            'daily_minutes_used': daily_usage['minutes'],
            'daily_minutes_limit': self.TRIAL_LIMITS['daily_minutes'],
            'daily_sessions_used': daily_usage['sessions'],
            'daily_sessions_limit': self.TRIAL_LIMITS['daily_sessions'],
            'monthly_minutes_used': monthly_usage['minutes'],
            'monthly_minutes_limit': self.TRIAL_LIMITS['monthly_minutes'],
            'monthly_sessions_used': monthly_usage['sessions'],
            'monthly_sessions_limit': self.TRIAL_LIMITS['monthly_sessions'],
            'can_start_session': daily_usage['sessions'] < self.TRIAL_LIMITS['daily_sessions']
        }

    def _get_user_daily_usage(self, user_id: str, date) -> Dict:
        """Get user's usage for a specific date (mock implementation)"""
        # In real implementation, query realtime_usage_logs table
        return {
            'minutes': 5,
            'sessions': 2,
            'cost_usd': Decimal('0.50')
        }

    def _get_user_monthly_usage(self, user_id: str, month_start) -> Dict:
        """Get user's usage for current month (mock implementation)"""
        # In real implementation, query realtime_usage_logs table
        return {
            'minutes': 45,
            'sessions': 15,
            'cost_usd': Decimal('4.50')
        }

    def log_usage_to_database(self, session_info: Dict, user_id: str, enterprise_id: str = None):
        """
        Log usage information to database
        
        Args:
            session_info: Session tracking information
            user_id: User identifier
            enterprise_id: Enterprise identifier (optional)
        """
        try:
            # Import here to avoid circular imports
            from main import supabase_request
            
            # Log session record
            session_record = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'session_id': session_info['session_id'],
                'openai_session_id': session_info.get('openai_session_id'),
                'status': 'completed' if session_info.get('ended_at') else 'active',
                'voice_model': 'alloy',  # Default voice
                'language': 'hi-IN',     # Default language
                'instructions': 'Default realtime voice assistant',
                'duration_seconds': session_info.get('total_duration_seconds', 0),
                'audio_input_duration_seconds': session_info['audio_input_seconds'],
                'audio_output_duration_seconds': session_info['audio_output_seconds'],
                'transcript_length': session_info['text_tokens_used'],
                'api_calls_count': 1,
                'estimated_cost_usd': float(session_info['estimated_cost_usd']),
                'started_at': session_info['started_at'].isoformat(),
                'ended_at': session_info['ended_at'].isoformat() if session_info.get('ended_at') else None
            }
            
            supabase_request('POST', 'realtime_voice_sessions', data=session_record)
            
            # Log individual usage entries
            usage_logs = []
            
            # Audio input usage
            if session_info['audio_input_seconds'] > 0:
                usage_logs.append({
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'session_id': session_info['session_id'],
                    'usage_type': 'audio_input',
                    'quantity': session_info['audio_input_seconds'],
                    'unit': 'seconds',
                    'rate_per_unit': float(self.PRICING['gpt-4o-realtime-preview']['audio_input_per_minute'] / 60),
                    'total_cost_usd': float(session_info['cost_breakdown']['audio_input_cost']),
                    'is_trial': True,  # Assuming trial user
                    'enterprise_id': enterprise_id
                })
            
            # Audio output usage
            if session_info['audio_output_seconds'] > 0:
                usage_logs.append({
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'session_id': session_info['session_id'],
                    'usage_type': 'audio_output',
                    'quantity': session_info['audio_output_seconds'],
                    'unit': 'seconds',
                    'rate_per_unit': float(self.PRICING['gpt-4o-realtime-preview']['audio_output_per_minute'] / 60),
                    'total_cost_usd': float(session_info['cost_breakdown']['audio_output_cost']),
                    'is_trial': True,
                    'enterprise_id': enterprise_id
                })
            
            # Text token usage
            if session_info['text_tokens_used'] > 0:
                usage_logs.append({
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'session_id': session_info['session_id'],
                    'usage_type': 'text_generation',
                    'quantity': session_info['text_tokens_used'],
                    'unit': 'tokens',
                    'rate_per_unit': float(self.PRICING['gpt-4o-realtime-preview']['text_tokens_per_1k'] / 1000),
                    'total_cost_usd': float(session_info['cost_breakdown']['text_cost']),
                    'is_trial': True,
                    'enterprise_id': enterprise_id
                })
            
            # Batch insert usage logs
            for log_entry in usage_logs:
                supabase_request('POST', 'realtime_usage_logs', data=log_entry)
                
        except Exception as e:
            print(f"Error logging usage to database: {e}")

    def get_user_usage_summary(self, user_id: str, days: int = 30) -> Dict:
        """
        Get usage summary for a user over specified days
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            
        Returns:
            Dict: Usage summary
        """
        try:
            from main import supabase_request
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Query sessions
            sessions = supabase_request('GET', 'realtime_voice_sessions', params={
                'user_id': f'eq.{user_id}',
                'started_at': f'gte.{start_date.isoformat()}',
                'select': '*'
            })
            
            if not sessions:
                sessions = []
            
            # Calculate totals
            total_sessions = len(sessions)
            total_duration_seconds = sum(s.get('duration_seconds', 0) for s in sessions)
            total_cost = sum(s.get('estimated_cost_usd', 0) for s in sessions)
            
            # Get today's usage
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_sessions = [s for s in sessions if 
                            datetime.fromisoformat(s['started_at'].replace('Z', '+00:00')) >= today_start]
            
            today_duration = sum(s.get('duration_seconds', 0) for s in today_sessions)
            today_cost = sum(s.get('estimated_cost_usd', 0) for s in today_sessions)
            
            return {
                'total_sessions': total_sessions,
                'total_duration_minutes': round(total_duration_seconds / 60, 2),
                'total_cost_usd': round(total_cost, 4),
                'average_session_duration_minutes': round((total_duration_seconds / 60) / max(total_sessions, 1), 2),
                'today_sessions': len(today_sessions),
                'today_duration_minutes': round(today_duration / 60, 2),
                'today_cost_usd': round(today_cost, 4),
                'trial_limits': self.check_trial_limits(user_id),
                'period_days': days
            }
            
        except Exception as e:
            print(f"Error getting usage summary: {e}")
            return {
                'total_sessions': 0,
                'total_duration_minutes': 0,
                'total_cost_usd': 0,
                'average_session_duration_minutes': 0,
                'today_sessions': 0,
                'today_duration_minutes': 0,
                'today_cost_usd': 0,
                'trial_limits': self.check_trial_limits(user_id),
                'period_days': days
            }

    def estimate_session_cost(self, audio_input_minutes: float, audio_output_minutes: float, 
                            text_tokens: int = 0, model: str = 'gpt-4o-realtime-preview') -> Dict:
        """
        Estimate cost for a session before it starts
        
        Args:
            audio_input_minutes: Expected audio input duration
            audio_output_minutes: Expected audio output duration
            text_tokens: Expected text token usage
            model: OpenAI model to use
            
        Returns:
            Dict: Cost estimation
        """
        pricing = self.PRICING.get(model, self.PRICING['gpt-4o-realtime-preview'])
        
        audio_input_cost = Decimal(str(audio_input_minutes)) * pricing['audio_input_per_minute']
        audio_output_cost = Decimal(str(audio_output_minutes)) * pricing['audio_output_per_minute']
        text_cost = Decimal(text_tokens / 1000) * pricing['text_tokens_per_1k']
        
        total_cost = audio_input_cost + audio_output_cost + text_cost
        
        return {
            'model': model,
            'audio_input_minutes': audio_input_minutes,
            'audio_output_minutes': audio_output_minutes,
            'text_tokens': text_tokens,
            'cost_breakdown': {
                'audio_input_cost_usd': float(audio_input_cost),
                'audio_output_cost_usd': float(audio_output_cost),
                'text_cost_usd': float(text_cost)
            },
            'total_estimated_cost_usd': float(total_cost),
            'pricing_rates': {
                'audio_input_per_minute': float(pricing['audio_input_per_minute']),
                'audio_output_per_minute': float(pricing['audio_output_per_minute']),
                'text_per_1k_tokens': float(pricing['text_tokens_per_1k'])
            }
        }


# Global usage tracker instance
usage_tracker = RealtimeUsageTracker()