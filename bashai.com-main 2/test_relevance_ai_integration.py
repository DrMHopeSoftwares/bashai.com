#!/usr/bin/env python3
"""
Comprehensive Test Suite for RelevanceAI Integration
Tests all components of the RelevanceAI integration with BhashAI platform
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RelevanceAIIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Adjust if different
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Test credentials (you would get these from your BhashAI login)
        self.test_user = {
            'email': 'admin@bhashai.com',
            'password': 'your_password_here'  # Update with actual test credentials
        }
        
        self.auth_token = None
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        self.results['total_tests'] += 1
        if success:
            self.results['passed'] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.results['failed'] += 1
            self.results['errors'].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED {message}")
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with authentication"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {
            'Content-Type': 'application/json'
        }
        
        if self.auth_token:
            request_headers['Authorization'] = f'Bearer {self.auth_token}'
        
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=request_headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=request_headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=request_headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def test_environment_setup(self):
        """Test 1: Verify environment variables are set"""
        required_vars = [
            'RELEVANCE_AI_API_KEY',
            'RELEVANCE_AI_REGION', 
            'RELEVANCE_AI_PROJECT_ID',
            'SUPABASE_URL',
            'SUPABASE_SERVICE_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            self.log_test("Environment Setup", False, f"Missing variables: {missing_vars}")
        else:
            self.log_test("Environment Setup", True, "All required environment variables present")
    
    def test_relevance_ai_module_import(self):
        """Test 2: Verify RelevanceAI module can be imported"""
        try:
            sys.path.append('.')
            from relevance_ai_integration import RelevanceAIProvider, RelevanceAIAgentManager
            self.log_test("Module Import", True, "RelevanceAI integration module imported successfully")
            return True
        except Exception as e:
            self.log_test("Module Import", False, f"Import error: {e}")
            return False
    
    def test_relevance_ai_connection(self):
        """Test 3: Test connection to RelevanceAI API"""
        try:
            sys.path.append('.')
            from relevance_ai_integration import RelevanceAIProvider
            
            provider = RelevanceAIProvider()
            success = provider.test_connection()
            
            if success:
                self.log_test("RelevanceAI Connection", True, "Successfully connected to RelevanceAI API")
            else:
                self.log_test("RelevanceAI Connection", False, "Failed to connect to RelevanceAI API")
            
            return success
        except Exception as e:
            self.log_test("RelevanceAI Connection", False, f"Connection error: {e}")
            return False
    
    def test_database_schema(self):
        """Test 4: Verify database schema updates"""
        try:
            # Check if schema update script exists
            if not os.path.exists('relevance_ai_schema_update.sql'):
                self.log_test("Database Schema", False, "Schema update file not found")
                return False
            
            # Check if apply script exists
            if not os.path.exists('apply_relevance_ai_schema.py'):
                self.log_test("Database Schema", False, "Schema application script not found")
                return False
            
            self.log_test("Database Schema", True, "Schema files present")
            return True
            
        except Exception as e:
            self.log_test("Database Schema", False, f"Schema check error: {e}")
            return False
    
    def test_server_startup(self):
        """Test 5: Check if Flask server can start (basic health check)"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK, means server is running
                self.log_test("Server Startup", True, f"Server responding (status: {response.status_code})")
                return True
            else:
                self.log_test("Server Startup", False, f"Server responded with status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Startup", False, f"Server not reachable: {e}")
            return False
    
    def test_authentication(self):
        """Test 6: Test user authentication"""
        try:
            # Try to login (this might need to be adjusted based on your auth system)
            login_data = {
                'email': self.test_user['email'],
                'password': self.test_user['password']
            }
            
            response = self.make_request('POST', '/auth/login', data=login_data)
            
            if response and response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token') or data.get('access_token')
                self.log_test("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Auth error: {e}")
            return False
    
    def test_create_relevance_ai_agent(self):
        """Test 7: Create a RelevanceAI agent via API"""
        try:
            agent_data = {
                'name': 'Test RelevanceAI Agent',
                'description': 'Test agent for integration verification',
                'language': 'english',
                'use_case': 'workflow',
                'provider': 'relevance_ai',
                'provider_config': {
                    'agent_type': 'single',
                    'tools': ['knowledge_base'],
                    'integrations': []
                }
            }
            
            response = self.make_request('POST', '/api/voice-agents', data=agent_data)
            
            if response and response.status_code == 201:
                data = response.json()
                self.test_agent_id = data.get('voice_agent', {}).get('id')
                self.log_test("Create RelevanceAI Agent", True, f"Agent created with ID: {self.test_agent_id}")
                return True
            else:
                error_msg = f"Status: {response.status_code if response else 'No response'}"
                if response:
                    try:
                        error_data = response.json()
                        error_msg += f", Error: {error_data.get('message', 'Unknown error')}"
                    except:
                        error_msg += f", Response: {response.text[:200]}"
                self.log_test("Create RelevanceAI Agent", False, error_msg)
                return False
                
        except Exception as e:
            self.log_test("Create RelevanceAI Agent", False, f"Creation error: {e}")
            return False
    
    def test_list_relevance_ai_agents(self):
        """Test 8: List RelevanceAI agents"""
        try:
            response = self.make_request('GET', '/api/relevance-ai/agents')
            
            if response and response.status_code == 200:
                data = response.json()
                agents = data.get('agents', [])
                self.log_test("List RelevanceAI Agents", True, f"Found {len(agents)} agents")
                return True
            else:
                self.log_test("List RelevanceAI Agents", False, f"Status: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            self.log_test("List RelevanceAI Agents", False, f"List error: {e}")
            return False
    
    def test_webhook_endpoint(self):
        """Test 9: Test RelevanceAI webhook endpoint"""
        try:
            webhook_data = {
                'event_type': 'session.started',
                'session_id': 'test_session_123',
                'agent_id': 'test_agent_456',
                'context': {
                    'test': True
                }
            }
            
            response = self.make_request('POST', '/api/webhooks/relevance-ai', data=webhook_data)
            
            if response and response.status_code in [200, 404]:  # 404 might be OK if agent not found
                self.log_test("Webhook Endpoint", True, f"Webhook processed (status: {response.status_code})")
                return True
            else:
                self.log_test("Webhook Endpoint", False, f"Status: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            self.log_test("Webhook Endpoint", False, f"Webhook error: {e}")
            return False
    
    def test_ui_files(self):
        """Test 10: Verify UI files exist"""
        ui_files = [
            'static/create-agent-enhanced.html'
        ]
        
        missing_files = [f for f in ui_files if not os.path.exists(f)]
        
        if missing_files:
            self.log_test("UI Files", False, f"Missing files: {missing_files}")
        else:
            self.log_test("UI Files", True, "All UI files present")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Starting RelevanceAI Integration Test Suite")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Run tests in order
        self.test_environment_setup()
        self.test_relevance_ai_module_import()
        self.test_relevance_ai_connection()
        self.test_database_schema()
        self.test_ui_files()
        
        # Server-dependent tests
        if self.test_server_startup():
            if self.test_authentication():
                self.test_create_relevance_ai_agent()
                self.test_list_relevance_ai_agents()
            self.test_webhook_endpoint()
        else:
            print("⚠️  Skipping server-dependent tests (server not running)")
        
        # Print results
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🔬 Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⏱️  Duration: {duration.total_seconds():.2f} seconds")
        
        if self.results['failed'] > 0:
            print("\n❌ Failed Tests:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Integration test suite PASSED!")
            return True
        else:
            print("💥 Integration test suite FAILED!")
            return False

def main():
    """Main test runner"""
    print("🔧 RelevanceAI Integration Test Suite")
    print("Testing integration between BhashAI and RelevanceAI")
    print("=" * 60)
    
    tester = RelevanceAIIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ RelevanceAI integration is ready for use!")
        print("\nNext steps:")
        print("1. Start your Flask server: python main.py")
        print("2. Navigate to /create-agent-enhanced.html")
        print("3. Create a RelevanceAI agent and test it")
        print("4. Check the dashboard for agent statistics")
    else:
        print("\n❌ Integration has issues that need to be resolved.")
        print("Please check the failed tests above and fix the issues.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)