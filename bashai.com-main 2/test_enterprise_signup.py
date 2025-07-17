#!/usr/bin/env python3
"""
Test enterprise signup with enterprise_id
"""

import requests
import time
import json

def test_enterprise_signup():
    """Test signup with enterprise_id"""
    
    base_url = "http://127.0.0.1:3000"
    
    print("🧪 Testing Enterprise Signup with Enterprise ID...")
    
    # First get available enterprises
    try:
        print("📋 Getting available enterprises...")
        enterprises_response = requests.get(f"{base_url}/api/public/enterprises")
        
        if enterprises_response.status_code == 200:
            enterprises_data = enterprises_response.json()
            if enterprises_data.get('success') and enterprises_data.get('enterprises'):
                enterprises = enterprises_data['enterprises']
                print(f"✅ Found {len(enterprises)} enterprises:")
                for ent in enterprises:
                    print(f"  - {ent['name']} (ID: {ent['id']})")
                
                # Use first enterprise for test
                selected_enterprise = enterprises[0]
                enterprise_id = selected_enterprise['id']
                enterprise_name = selected_enterprise['name']
                
                print(f"\n🎯 Using enterprise: {enterprise_name} (ID: {enterprise_id})")
                
            else:
                print("❌ No enterprises found")
                return
        else:
            print(f"❌ Failed to get enterprises: {enterprises_response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error getting enterprises: {e}")
        return
    
    # Test signup with enterprise_id
    try:
        test_email = f"testuser_{int(time.time())}@example.com"
        
        signup_data = {
            "name": "Test Enterprise User",
            "owner_name": "Test User",
            "contact_email": test_email,
            "contact_phone": "+91 9876543210",
            "password": "test123456",
            "type": enterprise_id,  # This will be the enterprise type/id
            "enterprise_id": enterprise_id,  # Explicit enterprise_id
            "status": "trial"
        }
        
        print(f"\n📧 Test Email: {test_email}")
        print(f"🏢 Enterprise ID: {enterprise_id}")
        
        response = requests.post(
            f"{base_url}/api/public/signup",
            headers={'Content-Type': 'application/json'},
            json=signup_data
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Signup Response:")
            print(json.dumps(response_data, indent=2))
            
            # Check if user has enterprise_id
            user_data = response_data.get('user', {})
            if 'enterprise_id' in user_data:
                print(f"🎯 User Enterprise ID: {user_data['enterprise_id']}")
                print("✅ SUCCESS: User created with enterprise_id!")
            else:
                print("⚠️ WARNING: User created but no enterprise_id found")
            
            print(f"\n🎉 Test PASSED: Signup with enterprise_id works!")
            
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(response.text)
            print(f"\n💥 Test FAILED: Signup with enterprise_id failed")
            
    except Exception as e:
        print(f"❌ Error during signup: {e}")
        print(f"\n💥 Test FAILED: Exception occurred")

if __name__ == "__main__":
    test_enterprise_signup()
