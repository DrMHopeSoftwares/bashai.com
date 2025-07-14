#!/usr/bin/env python3
"""
Test script for phone provider integration
Run this script to test both Plivo and Twilio integrations
"""

import os
import json
from dotenv import load_dotenv
from phone_provider_integration import phone_provider_manager
from plivo_integration import PlivoAPI
from twilio_integration import TwilioAPI

def test_provider_status():
    """Test provider availability and status"""
    print("=== Provider Status Test ===")
    status = phone_provider_manager.get_provider_status()
    print(json.dumps(status, indent=2))
    print()

def test_plivo_integration():
    """Test Plivo integration"""
    print("=== Plivo Integration Test ===")
    try:
        plivo = PlivoAPI()
        print(f"Plivo mock mode: {plivo.use_mock}")
        
        # Test search
        result = plivo.search_phone_numbers(country_iso='US', pattern='555', limit=2)
        print("Plivo search result:")
        print(json.dumps(result, indent=2))
        
        # Test purchase (mock)
        if result['success'] and result['available_numbers']:
            first_number = result['available_numbers'][0]['phone_number']
            purchase_result = plivo.purchase_phone_number(first_number)
            print(f"\nPlivo purchase test for {first_number}:")
            print(json.dumps(purchase_result, indent=2))
        
    except Exception as e:
        print(f"Plivo test error: {e}")
    print()

def test_twilio_integration():
    """Test Twilio integration"""
    print("=== Twilio Integration Test ===")
    try:
        twilio = TwilioAPI()
        print(f"Twilio mock mode: {twilio.use_mock}")
        print(f"Account SID: {twilio.account_sid}")
        
        # Test search
        result = twilio.search_phone_numbers(country_code='US', area_code='415', limit=2)
        print("Twilio search result:")
        print(json.dumps(result, indent=2))
        
        # Test purchase (mock)
        if result['success'] and result['available_numbers']:
            first_number = result['available_numbers'][0]['phone_number']
            purchase_result = twilio.purchase_phone_number(first_number, friendly_name="Test Number")
            print(f"\nTwilio purchase test for {first_number}:")
            print(json.dumps(purchase_result, indent=2))
        
    except Exception as e:
        print(f"Twilio test error: {e}")
    print()

def test_unified_manager():
    """Test unified phone provider manager"""
    print("=== Unified Manager Test ===")
    
    # Test Plivo through manager
    print("Testing Plivo via manager:")
    plivo_result = phone_provider_manager.search_phone_numbers(
        provider_name='plivo',
        country_code='US',
        pattern='555',
        limit=2
    )
    print(json.dumps(plivo_result, indent=2))
    
    print("\nTesting Twilio via manager:")
    twilio_result = phone_provider_manager.search_phone_numbers(
        provider_name='twilio',
        country_code='US',
        pattern='415',
        limit=2
    )
    print(json.dumps(twilio_result, indent=2))
    print()

def test_api_endpoints():
    """Test that our Flask app endpoints work"""
    print("=== API Endpoints Test ===")
    
    import requests
    
    try:
        # Test Plivo search
        response = requests.post('http://localhost:8000/api/dev/phone-numbers/search', 
                               json={
                                   'country_code': 'US',
                                   'provider': 'plivo',
                                   'pattern': '555',
                                   'limit': 2
                               })
        print("Plivo API endpoint test:")
        print(json.dumps(response.json(), indent=2))
        
        # Test Twilio search
        response = requests.post('http://localhost:8000/api/dev/phone-numbers/search', 
                               json={
                                   'country_code': 'US',
                                   'provider': 'twilio',
                                   'pattern': '415',
                                   'limit': 2
                               })
        print("\nTwilio API endpoint test:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"API endpoint test error: {e}")
        print("Make sure Flask app is running on port 8000")
    print()

def main():
    """Run all tests"""
    # Load environment variables
    load_dotenv()
    
    print("🧪 Phone Provider Integration Test Suite")
    print("=" * 50)
    
    test_provider_status()
    test_plivo_integration()
    test_twilio_integration()
    test_unified_manager()
    test_api_endpoints()
    
    print("✅ All tests completed!")
    print("\n📝 Notes:")
    print("- If providers show 'mock_mode: true', add real credentials to .env")
    print("- Plivo credentials: PLIVO_AUTH_ID and PLIVO_AUTH_TOKEN")
    print("- Twilio credentials: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
    print("- Get Twilio Auth Token from: https://console.twilio.com/")
    print("- Get Plivo credentials from: https://console.plivo.com/")

if __name__ == "__main__":
    main()