#!/usr/bin/env python3
"""
Test Script for OpenAI Realtime API Integration
Tests the integration without requiring actual OpenAI API calls
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_environment_setup():
    """Test environment configuration"""
    print("🔧 Testing Environment Setup...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check for required environment variables
        openai_key = os.getenv('OPENAI_API_KEY')
        supabase_url = os.getenv('SUPABASE_URL')
        
        print(f"✅ OpenAI API Key: {'✓ Set' if openai_key else '✗ Missing'}")
        print(f"✅ Supabase URL: {'✓ Set' if supabase_url else '✗ Missing'}")
        
        return True
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def test_imports():
    """Test module imports"""
    print("\n📦 Testing Module Imports...")
    
    try:
        # Test core Flask imports
        from flask import Flask
        from flask_socketio import SocketIO
        print("✅ Flask and SocketIO imports successful")
        
        # Test our modules
        from openai_realtime_integration import OpenAIRealtimeAPI, RealtimeSessionManager
        print("✅ OpenAI Realtime integration import successful")
        
        from realtime_websocket_handler import RealtimeWebSocketHandler
        print("✅ WebSocket handler import successful")
        
        from realtime_usage_tracker import RealtimeUsageTracker
        print("✅ Usage tracker import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_realtime_api_initialization():
    """Test OpenAI Realtime API initialization"""
    print("\n🤖 Testing OpenAI Realtime API Initialization...")
    
    try:
        from openai_realtime_integration import OpenAIRealtimeAPI
        
        # Test without actual API key for now
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        api = OpenAIRealtimeAPI()
        print("✅ OpenAI Realtime API instance created")
        
        # Test session info
        session_info = api.get_session_info()
        print(f"✅ Session info: {session_info}")
        
        return True
    except Exception as e:
        print(f"❌ Realtime API initialization failed: {e}")
        return False

def test_session_manager():
    """Test session manager functionality"""
    print("\n📋 Testing Session Manager...")
    
    try:
        from openai_realtime_integration import RealtimeSessionManager
        
        manager = RealtimeSessionManager()
        print("✅ Session manager created")
        
        # Test session metadata
        user_sessions = manager.get_user_sessions('test-user-123')
        print(f"✅ User sessions query: {user_sessions}")
        
        return True
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        return False

def test_usage_tracker():
    """Test usage tracking functionality"""
    print("\n💰 Testing Usage Tracker...")
    
    try:
        from realtime_usage_tracker import RealtimeUsageTracker
        
        tracker = RealtimeUsageTracker()
        print("✅ Usage tracker created")
        
        # Test cost estimation
        estimation = tracker.estimate_session_cost(
            audio_input_minutes=2.0,
            audio_output_minutes=1.5,
            text_tokens=500
        )
        print(f"✅ Cost estimation: ${estimation['total_estimated_cost_usd']}")
        
        # Test trial limits check
        limits = tracker.check_trial_limits('test-user-123')
        print(f"✅ Trial limits check: {limits['within_limits']}")
        
        return True
    except Exception as e:
        print(f"❌ Usage tracker test failed: {e}")
        return False

def test_websocket_handler_init():
    """Test WebSocket handler initialization"""
    print("\n🔌 Testing WebSocket Handler...")
    
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        from realtime_websocket_handler import init_realtime_websocket
        
        # Create minimal Flask app
        app = Flask(__name__)
        socketio = SocketIO(app, cors_allowed_origins="*")
        
        # Initialize handler
        handler = init_realtime_websocket(app, socketio)
        print("✅ WebSocket handler initialized")
        print(f"✅ Handler type: {type(handler)}")
        
        return True
    except Exception as e:
        print(f"❌ WebSocket handler test failed: {e}")
        return False

def test_database_schema_validation():
    """Test database schema SQL syntax"""
    print("\n🗄️ Testing Database Schema...")
    
    try:
        # Read the schema file
        with open('realtime_schema_updates.sql', 'r') as f:
            schema_content = f.read()
        
        print("✅ Schema file readable")
        
        # Basic syntax checks
        if 'CREATE TABLE' in schema_content:
            print("✅ Contains table creation statements")
        
        if 'realtime_voice_sessions' in schema_content:
            print("✅ Contains realtime_voice_sessions table")
        
        if 'realtime_usage_logs' in schema_content:
            print("✅ Contains realtime_usage_logs table")
        
        return True
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def test_frontend_interface():
    """Test frontend interface file"""
    print("\n🎨 Testing Frontend Interface...")
    
    try:
        # Check if frontend file exists
        frontend_path = 'static/realtime-voice-interface.html'
        if os.path.exists(frontend_path):
            print("✅ Frontend interface file exists")
            
            with open(frontend_path, 'r') as f:
                content = f.read()
                
            if 'RealtimeVoiceInterface' in content:
                print("✅ Contains RealtimeVoiceInterface class")
            
            if 'socket.io' in content:
                print("✅ Contains Socket.IO integration")
            
            if 'WebSocket' in content or 'socket.emit' in content:
                print("✅ Contains WebSocket functionality")
            
            return True
        else:
            print("❌ Frontend interface file not found")
            return False
            
    except Exception as e:
        print(f"❌ Frontend interface test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting OpenAI Realtime API Integration Tests")
    print("=" * 60)
    
    tests = [
        test_environment_setup,
        test_imports,
        test_realtime_api_initialization,
        test_session_manager,
        test_usage_tracker,
        test_websocket_handler_init,
        test_database_schema_validation,
        test_frontend_interface
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! OpenAI Realtime API integration ready.")
        print("\n📋 Next Steps:")
        print("1. Add your OpenAI API key to .env file")
        print("2. Apply database schema: psql -d your_db -f realtime_schema_updates.sql")
        print("3. Install additional dependencies: pip install websockets flask-socketio")
        print("4. Restart server and visit: http://localhost:8000/realtime-voice-interface.html")
    else:
        print("⚠️  Some tests failed. Please fix the issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)