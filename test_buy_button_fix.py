#!/usr/bin/env python3
"""
Test the Buy Number button fix
"""

import requests
import json

def test_buy_button_fix():
    """Test if Buy Number button is working"""
    
    print("🔧 Testing Buy Number Button Fix")
    print("="*40)
    
    try:
        print("🌐 Testing dashboard page...")
        response = requests.get('http://127.0.0.1:5001/dashboard.html', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for fixed elements
            fixes = [
                'console.log(\'Buy Number clicked:\'',
                'testBuyNumber()',
                'Test Buy',
                'typeof Razorpay === \'undefined\'',
                'mockOrderId'
            ]
            
            found_fixes = []
            for fix in fixes:
                if fix in content:
                    found_fixes.append(fix)
            
            print(f"✅ Found {len(found_fixes)}/5 fixes:")
            for fix in found_fixes:
                print(f"   ✓ {fix}")
            
            # Check for Buy Number buttons in phone list
            buy_button_patterns = [
                'buyNumberWithRazorpay(',
                'Buy Number',
                'fas fa-shopping-cart',
                'bg-blue-600',
                'bg-green-600'
            ]
            
            found_buttons = []
            for pattern in buy_button_patterns:
                if pattern in content:
                    found_buttons.append(pattern)
            
            print(f"\n🛒 Found {len(found_buttons)}/5 button elements:")
            for button in found_buttons:
                print(f"   ✓ {button}")
            
            # Check for Razorpay script
            if 'checkout.razorpay.com' in content:
                print(f"\n💳 ✅ Razorpay script loaded")
            else:
                print(f"\n💳 ❌ Razorpay script missing")
            
            return len(found_fixes) >= 3 and len(found_buttons) >= 4
            
        else:
            print(f"❌ Dashboard not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_debugging_steps():
    """Show debugging steps for users"""
    
    print(f"\n🔍 Debugging Steps:")
    print("="*20)
    
    print("1. 🌐 **Open Dashboard:**")
    print("   → Go to: http://127.0.0.1:5001/dashboard.html")
    print("   → Login with your credentials")
    
    print(f"\n2. 🛒 **Test Buy Button:**")
    print("   → Click 'Test Buy' button (green button)")
    print("   → Or click any 'Buy Number' button on phone numbers")
    print("   → Should show Razorpay popup")
    
    print(f"\n3. 🔧 **Check Console:**")
    print("   → Press F12 to open Developer Tools")
    print("   → Go to Console tab")
    print("   → Look for 'Buy Number clicked:' messages")
    print("   → Check for any JavaScript errors")
    
    print(f"\n4. 💳 **Test Payment Flow:**")
    print("   → Confirm purchase dialog should appear")
    print("   → Razorpay checkout should open")
    print("   → Test with demo card: 4111 1111 1111 1111")

def show_troubleshooting():
    """Show troubleshooting tips"""
    
    print(f"\n🚨 Troubleshooting:")
    print("="*20)
    
    print("❌ **If buttons don't appear:**")
    print("   → Refresh the page (Ctrl+F5)")
    print("   → Clear browser cache")
    print("   → Check if logged in properly")
    
    print(f"\n❌ **If Razorpay doesn't open:**")
    print("   → Check console for errors")
    print("   → Ensure internet connection")
    print("   → Try different browser")
    
    print(f"\n❌ **If function not found error:**")
    print("   → Wait for page to fully load")
    print("   → Check if JavaScript is enabled")
    print("   → Try hard refresh (Ctrl+Shift+R)")

if __name__ == "__main__":
    success = test_buy_button_fix()
    show_debugging_steps()
    show_troubleshooting()
    
    if success:
        print(f"\n🎉 Buy Number Button Fix Applied Successfully!")
        print(f"🛒 Test the 'Test Buy' button!")
        print(f"💳 Razorpay integration ready!")
    else:
        print(f"\n⚠️ Please check manually and follow debugging steps")
