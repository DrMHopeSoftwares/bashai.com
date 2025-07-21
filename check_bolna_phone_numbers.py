#!/usr/bin/env python3
"""
Check available phone numbers in Bolna account
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_bolna_phone_numbers():
    """Get all available phone numbers from Bolna API"""
    
    api_key = os.getenv('BOLNA_API_KEY')
    base_url = os.getenv('BOLNA_API_URL', 'https://api.bolna.ai')
    
    if not api_key:
        print("❌ BOLNA_API_KEY not found in environment variables")
        return None
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print("🔍 Fetching phone numbers from Bolna API...")
        print(f"📡 API URL: {base_url}")
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # Try the phone numbers endpoint
        response = requests.get(
            f"{base_url}/phone-numbers/all",
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            phone_numbers = response.json()
            print("✅ Successfully fetched phone numbers!")
            return phone_numbers
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try alternative endpoints
            print("\n🔄 Trying alternative endpoints...")
            
            # Try /phone-numbers without /all
            alt_response = requests.get(
                f"{base_url}/phone-numbers",
                headers=headers,
                timeout=30
            )
            
            if alt_response.status_code == 200:
                print("✅ Alternative endpoint worked!")
                return alt_response.json()
            else:
                print(f"❌ Alternative endpoint also failed: {alt_response.status_code}")
                print(f"Response: {alt_response.text}")
            
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def display_phone_numbers(phone_numbers):
    """Display phone numbers in a formatted way"""
    
    if not phone_numbers:
        print("📱 No phone numbers found")
        return
    
    print("\n" + "="*60)
    print("📱 YOUR BOLNA PHONE NUMBERS")
    print("="*60)
    
    if isinstance(phone_numbers, list):
        if len(phone_numbers) == 0:
            print("📭 No phone numbers available in your account")
        else:
            for i, number in enumerate(phone_numbers, 1):
                print(f"\n📞 Phone Number {i}:")
                if isinstance(number, dict):
                    for key, value in number.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"   Number: {number}")
    
    elif isinstance(phone_numbers, dict):
        if 'phone_numbers' in phone_numbers:
            numbers = phone_numbers['phone_numbers']
            if len(numbers) == 0:
                print("📭 No phone numbers available in your account")
            else:
                for i, number in enumerate(numbers, 1):
                    print(f"\n📞 Phone Number {i}:")
                    if isinstance(number, dict):
                        for key, value in number.items():
                            print(f"   {key}: {value}")
                    else:
                        print(f"   Number: {number}")
        else:
            print("📋 Raw Response:")
            print(json.dumps(phone_numbers, indent=2))
    
    print("\n" + "="*60)

def main():
    print("🚀 Bolna Phone Numbers Checker")
    print("="*40)
    
    # Check environment
    api_key = os.getenv('BOLNA_API_KEY')
    if not api_key or api_key == 'your-bolna-api-key-here':
        print("❌ Please set your BOLNA_API_KEY in .env file")
        return
    
    # Get phone numbers
    phone_numbers = get_bolna_phone_numbers()
    
    # Display results
    display_phone_numbers(phone_numbers)
    
    # Show current default
    default_phone = os.getenv('BOLNA_SENDER_PHONE', '+918035743222')
    print(f"\n🔧 Current Default Sender Phone: {default_phone}")
    
    print("\n💡 Tip: You can assign different numbers to different admins!")
    print("   Use the admin phone settings API to configure individual numbers.")

if __name__ == "__main__":
    main()
