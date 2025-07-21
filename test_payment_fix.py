#!/usr/bin/env python3
"""
Test Payment Error Fix
"""

import requests
import json

def test_payment_fix():
    """Test if payment error fixes are applied"""
    
    print("💳 Testing Payment Error Fix")
    print("="*35)
    
    try:
        print("🌐 Testing dashboard page...")
        response = requests.get('http://127.0.0.1:5001/dashboard.html', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for test key
            test_key_elements = [
                'rzp_test_9WzaAHedOuKzjI',
                'Test key for development',
                'Test mode'
            ]
            
            found_test_key = []
            for element in test_key_elements:
                if element in content:
                    found_test_key.append(element)
            
            print(f"🔑 Found {len(found_test_key)}/3 test key elements:")
            for element in found_test_key:
                print(f"   ✓ {element}")
            
            # Check for error handling
            error_handling = [
                'rzp.on(\'payment.failed\'',
                'response.error.description',
                'Payment failed:',
                'retry: {',
                'max_count: 3'
            ]
            
            found_error_handling = []
            for element in error_handling:
                if element in content:
                    found_error_handling.append(element)
            
            print(f"\n🚨 Found {len(found_error_handling)}/5 error handling elements:")
            for element in found_error_handling:
                print(f"   ✓ {element}")
            
            # Check for test mode warnings
            test_warnings = [
                'TEST MODE',
                'No real payment will be charged',
                'test mode warning',
                'Test cancelled'
            ]
            
            found_warnings = []
            for warning in test_warnings:
                if warning in content:
                    found_warnings.append(warning)
            
            print(f"\n⚠️ Found {len(found_warnings)}/4 test mode warnings:")
            for warning in found_warnings:
                print(f"   ✓ {warning}")
            
            return len(found_test_key) >= 1 and len(found_error_handling) >= 3
            
        else:
            print(f"❌ Dashboard not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_testing_instructions():
    """Show testing instructions"""
    
    print(f"\n🧪 Testing Instructions:")
    print("="*25)
    
    print("1. 🌐 **Open Fixed Test Page:**")
    print("   → Go to: http://127.0.0.1:5001/razorpay-test-fixed.html")
    print("   → Click 'Buy Test Number (Fixed)'")
    print("   → Use test card details provided")
    
    print(f"\n2. 🛒 **Main Dashboard Test:**")
    print("   → Go to: http://127.0.0.1:5001/dashboard.html")
    print("   → Click green 'Test Buy' button")
    print("   → Confirm test mode dialog")
    print("   → Use test card in Razorpay popup")
    
    print(f"\n3. 💳 **Test Card Details:**")
    print("   → Card: 4111 1111 1111 1111")
    print("   → Expiry: 12/25 (any future date)")
    print("   → CVV: 123 (any 3 digits)")
    print("   → Name: Test User")
    
    print(f"\n4. 🔍 **What Should Happen:**")
    print("   → Razorpay popup opens successfully")
    print("   → Test card payment goes through")
    print("   → Success message appears")
    print("   → NO 'Something went wrong' error")

def show_troubleshooting():
    """Show troubleshooting steps"""
    
    print(f"\n🚨 Troubleshooting:")
    print("="*20)
    
    print("❌ **If still getting 'Payment Failed':**")
    print("   → Make sure using TEST card: 4111 1111 1111 1111")
    print("   → Don't use real card numbers in test mode")
    print("   → Check internet connection")
    print("   → Try different browser")
    
    print(f"\n❌ **If Razorpay doesn't open:**")
    print("   → Hard refresh: Ctrl+Shift+R")
    print("   → Disable ad blockers")
    print("   → Check console for errors")
    print("   → Try: /razorpay-test-fixed.html")
    
    print(f"\n❌ **If functions not found:**")
    print("   → Wait 3-5 seconds after page load")
    print("   → Check console: window.testBuyNumber")
    print("   → Try: window.debugBuyButton()")
    
    print(f"\n✅ **Success Indicators:**")
    print("   → Blue toast: 'Testing Buy Number function...'")
    print("   → Dialog: 'TEST MODE' confirmation")
    print("   → Blue toast: 'Redirecting to Razorpay...'")
    print("   → Razorpay popup with test form")
    print("   → Green toast: 'Payment successful!'")

if __name__ == "__main__":
    success = test_payment_fix()
    show_testing_instructions()
    show_troubleshooting()
    
    if success:
        print(f"\n🎉 Payment Error Fix Applied Successfully!")
        print(f"💳 Now using TEST mode - no real charges!")
        print(f"🚨 Proper error handling added!")
        print(f"🛒 Test with card: 4111 1111 1111 1111!")
    else:
        print(f"\n⚠️ Please follow testing instructions manually")
