#!/usr/bin/env python3
"""
Test script to check if bhashai.com deployment is working
"""

import requests
import json

def test_endpoints():
    base_url = "https://bhashai.com"
    
    endpoints_to_test = [
        "/",
        "/health", 
        "/hello",
        "/api/health",
        "/landing.html",
        "/dashboard.html",
        "/simple-admin.html",
        "/api/admin/enterprises"
    ]
    
    print("🔍 Testing bhashai.com deployment...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            status = f"✅ {response.status_code}" if response.status_code < 400 else f"❌ {response.status_code}"
            print(f"{status} | {endpoint}")
            
            # Show content type for successful responses
            if response.status_code < 400:
                content_type = response.headers.get('content-type', 'unknown')
                print(f"      Content-Type: {content_type}")
                
        except requests.exceptions.RequestException as e:
            print(f"💥 ERROR | {endpoint} - {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Quick Fix Test - Try creating enterprise via API:")
    
    # Try to create enterprise directly via API
    enterprise_data = {
        "name": "Test Enterprise",
        "type": "healthcare", 
        "contact_email": "test@example.com",
        "status": "trial"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/admin/enterprises",
            json=enterprise_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code < 400:
            print(f"✅ API WORKS! Enterprise creation: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ API Failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"💥 API Error: {str(e)}")

if __name__ == "__main__":
    test_endpoints()