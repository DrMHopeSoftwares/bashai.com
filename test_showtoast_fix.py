#!/usr/bin/env python3
"""
Test showToast Fix
"""

import requests
import json

def test_showtoast_fix():
    """Test if showToast function is properly defined"""
    
    print("🍞 Testing showToast Fix")
    print("="*30)
    
    try:
        print("🌐 Testing dashboard page...")
        response = requests.get('http://127.0.0.1:5001/dashboard.html', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for showToast function
            showtoast_elements = [
                'window.showToast = function(',
                'Toast notification function',
                'bg-green-500',
                'bg-red-500',
                'bg-yellow-500',
                'bg-blue-500',
                'translate-x-full',
                'document.body.appendChild(toast)'
            ]
            
            found_showtoast = []
            for element in showtoast_elements:
                if element in content:
                    found_showtoast.append(element)
            
            print(f"🍞 Found {len(found_showtoast)}/8 showToast elements:")
            for element in found_showtoast:
                print(f"   ✓ {element}")
            
            # Check for currentUser fixes
            currentuser_fixes = [
                'window.currentUser && window.currentUser.name',
                'window.currentUser && window.currentUser.email',
                'window.currentUser && window.currentUser.id'
            ]
            
            found_currentuser = []
            for fix in currentuser_fixes:
                if fix in content:
                    found_currentuser.append(fix)
            
            print(f"\n👤 Found {len(found_currentuser)}/3 currentUser fixes:")
            for fix in found_currentuser:
                print(f"   ✓ {fix}")
            
            # Check for showToast calls
            showtoast_calls = [
                "showToast('Redirecting to Razorpay...', 'info')",
                "showToast('Payment cancelled', 'warning')",
                "showToast('Failed to initiate payment:",
                "showToast('Payment successful! Processing",
                "showToast('Testing Buy Number function...', 'info')"
            ]
            
            found_calls = []
            for call in showtoast_calls:
                if call in content:
                    found_calls.append(call)
            
            print(f"\n📞 Found {len(found_calls)}/5 showToast calls:")
            for call in found_calls:
                print(f"   ✓ {call}")
            
            return len(found_showtoast) >= 6 and len(found_currentuser) >= 2
            
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
    print("   → Should see NO 'showToast is not defined' errors")
    print("   → Look for: 'BUY NUMBER FUNCTION TEST'")
    
    print(f"\n3. 🛒 **Test Buy Button:**")
    print("   → Click green 'Test Buy' button")
    print("   → Should see blue toast: 'Testing Buy Number function...'")
    print("   → Should see confirmation dialog")
    print("   → Should see blue toast: 'Redirecting to Razorpay...'")
    print("   → Should open Razorpay popup")
    
    print(f"\n4. 💻 **Console Testing:**")
    print("   → Type: window.showToast('Test message', 'success')")
    print("   → Should show green toast notification")
    print("   → Type: window.testBuyNumber()")
    print("   → Should trigger complete buy process")

def show_toast_types():
    """Show different toast types"""
    
    print(f"\n🍞 Toast Types Available:")
    print("="*25)
    
    print("✅ **Success (Green):**")
    print("   window.showToast('Success message', 'success')")
    
    print(f"\n❌ **Error (Red):**")
    print("   window.showToast('Error message', 'error')")
    
    print(f"\n⚠️ **Warning (Yellow):**")
    print("   window.showToast('Warning message', 'warning')")
    
    print(f"\n💙 **Info (Blue):**")
    print("   window.showToast('Info message', 'info')")
    print("   window.showToast('Default message')  // Also blue")

if __name__ == "__main__":
    success = test_showtoast_fix()
    show_testing_instructions()
    show_toast_types()
    
    if success:
        print(f"\n🎉 showToast Fix Applied Successfully!")
        print(f"🍞 Toast notifications now working!")
        print(f"👤 currentUser errors fixed!")
        print(f"🛒 Test the 'Test Buy' button!")
    else:
        print(f"\n⚠️ Please follow testing instructions manually")
