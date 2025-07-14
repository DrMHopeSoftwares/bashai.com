#!/usr/bin/env python3
"""
Test organization creation endpoint to debug the issue
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_organization_creation():
    """Test the organization creation endpoint"""
    
    print("=== Testing Organization Creation ===")
    
    # Test data (matching the screenshot)
    test_data = {
        "name": "hope",
        "type": "Healthcare", 
        "contact_email": "test@example.com"
    }
    
    base_url = "http://127.0.0.1:3000"
    endpoint = f"{base_url}/api/enterprises"
    
    print(f"Testing endpoint: {endpoint}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Test without authentication first
        print("\n1. Testing without authentication...")
        response = requests.post(endpoint, json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Properly returns 401 for unauthenticated requests")
        
        # Test with invalid auth header
        print("\n2. Testing with invalid authentication...")
        headers = {
            "Authorization": "Bearer invalid_token",
            "Content-Type": "application/json"
        }
        response = requests.post(endpoint, json=test_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Test direct database connection
        print("\n3. Testing direct database creation...")
        test_direct_db_creation()
        
    except requests.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 3000")
    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_direct_db_creation():
    """Test creating organization directly in database"""
    try:
        import main
        from unittest.mock import Mock
        
        # Mock authenticated user
        mock_user = {
            'user_id': 'test_user_123',
            'email': 'test@example.com'
        }
        
        # Test the supabase_request function directly
        data = {
            'name': 'Test Organization',
            'type': 'Healthcare',
            'contact_email': 'test@example.com',
            'owner_id': 'test_user_123',
            'status': 'active'
        }
        
        print("Testing direct Supabase insertion...")
        print(f"SUPABASE_AVAILABLE: {main.SUPABASE_AVAILABLE}")
        
        if main.SUPABASE_AVAILABLE:
            # This would test the actual database connection
            result = main.supabase_request(
                'enterprises',
                'POST',
                data=data
            )
            print(f"Direct DB Result: {result}")
        else:
            print("❌ Supabase not available - check environment variables")
            
    except Exception as e:
        print(f"❌ Direct DB test error: {e}")

if __name__ == "__main__":
    test_organization_creation()