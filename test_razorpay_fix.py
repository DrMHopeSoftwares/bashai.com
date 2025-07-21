#!/usr/bin/env python3
"""
Test Razorpay Buy Number Fix
"""

import requests
import json

def test_razorpay_fix():
    """Test if Razorpay Buy Number is working"""
    
    print("🔧 Testing Razorpay Buy Number Fix")
    print("="*40)
    
    try:
        print("🌐 Testing dashboard page...")
        response = requests.get('http://127.0.0.1:5001/dashboard.html', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for global function fixes
            global_fixes = [
                'window.testBuyNumber = function()',
                'window.buyNumberWithRazorpay = async function(',
                'window.debugBuyButton = function()',
                'onclick="window.testBuyNumber()"',
                'onclick="window.buyNumberWithRazorpay('
            ]
            
            found_fixes = []
            for fix in global_fixes:
                if fix in content:
                    found_fixes.append(fix)
            
            print(f"✅ Found {len(found_fixes)}/5 global function fixes:")
            for fix in found_fixes:
                print(f"   ✓ {fix}")
            
            # Check for Razorpay integration
            razorpay_elements = [
                'checkout.razorpay.com',
                'typeof Razorpay',
                'new Razorpay(options)',
                'rzp.open()',
                'razorpay_payment_id'
            ]
            
            found_razorpay = []
            for element in razorpay_elements:
                if element in content:
                    found_razorpay.append(element)
            
            print(f"\n💳 Found {len(found_razorpay)}/5 Razorpay elements:")
            for element in found_razorpay:
                print(f"   ✓ {element}")
            
            # Check for debug functions
            debug_elements = [
                'BUY NUMBER FUNCTION TEST',
                'debugBuyButton',
                'console.log',
                'typeof window.testBuyNumber',
                'Buy Number functions ready'
            ]
            
            found_debug = []
            for element in debug_elements:
                if element in content:
                    found_debug.append(element)
            
            print(f"\n🔍 Found {len(found_debug)}/5 debug elements:")
            for element in found_debug:
                print(f"   ✓ {element}")
            
            return len(found_fixes) >= 4 and len(found_razorpay) >= 4
            
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
    
    print("1. 🌐 **Open Dashboard:**")
    print("   → Go to: http://127.0.0.1:5001/dashboard.html")
    print("   → Login with your credentials")
    print("   → Wait for page to fully load")
    
    print(f"\n2. 🔍 **Check Console (F12):**")
    print("   → Press F12 → Console tab")
    print("   → Look for: 'BUY NUMBER FUNCTION TEST'")
    print("   → Should see: '✅ Buy Number functions ready!'")
    
    print(f"\n3. 🛒 **Test Buy Button:**")
    print("   → Click green 'Test Buy' button")
    print("   → OR click 'Buy Number' on any phone")
    print("   → Should show confirmation dialog")
    print("   → Should open Razorpay popup")
    
    print(f"\n4. 💻 **Console Testing:**")
    print("   → In console, type: window.debugBuyButton()")
    print("   → Should show all checks ✅")
    print("   → Type: window.testBuyNumber()")
    print("   → Should trigger buy process")

def show_troubleshooting_steps():
    """Show troubleshooting steps"""
    
    print(f"\n🚨 Troubleshooting:")
    print("="*20)
    
    print("❌ **If 'Test Buy' button missing:**")
    print("   → Hard refresh: Ctrl+Shift+R")
    print("   → Clear cache and reload")
    print("   → Check if logged in properly")
    
    print(f"\n❌ **If functions not found:**")
    print("   → Wait 3-5 seconds after page load")
    print("   → Check console for errors")
    print("   → Try: window.debugBuyButton()")
    
    print(f"\n❌ **If Razorpay doesn't open:**")
    print("   → Check internet connection")
    print("   → Disable ad blockers")
    print("   → Try different browser")
    print("   → Check console for Razorpay errors")
    
    print(f"\n❌ **If still not working:**")
    print("   → Go to: http://127.0.0.1:5001/test-buy-button.html")
    print("   → Use dedicated test page")
    print("   → Check all debug information")

if __name__ == "__main__":
    success = test_razorpay_fix()
    show_testing_instructions()
    show_troubleshooting_steps()
    
    if success:
        print(f"\n🎉 Razorpay Buy Number Fix Applied Successfully!")
        print(f"🛒 Functions are now globally accessible!")
        print(f"💳 Test the 'Test Buy' button!")
    else:
        print(f"\n⚠️ Please follow testing instructions manually")
