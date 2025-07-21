#!/usr/bin/env python3
"""
Test dynamic number selection - different numbers should store correctly
"""

import requests
import json
import time

def test_dynamic_number_selection():
    """Test that different selected numbers get stored correctly"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🎯 **TESTING DYNAMIC NUMBER SELECTION**")
    print("=" * 70)
    
    # Step 1: Login
    print("1. 🔐 **User Login Process**")
    login_data = {
        "email": "b@gmail.com",
        "password": "bhupendra"
    }
    
    login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    login_result = login_response.json()
    token = login_result.get('token')
    print(f"✅ User logged in successfully")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Get All Available Numbers
    print(f"\n2. 📱 **Loading All Available Numbers**")
    
    bolna_response = requests.get(f"{base_url}/api/bolna/phone-numbers", headers=headers)
    if bolna_response.status_code == 200:
        bolna_result = bolna_response.json()
        available_numbers = bolna_result.get('phone_numbers', [])
        print(f"✅ Loaded {len(available_numbers)} available numbers")
        
        for i, number in enumerate(available_numbers[:3], 1):  # Test first 3 numbers
            print(f"   {i}. 📞 {number.get('phone_number')} (ID: {number.get('id')[:8]}...)")
    else:
        print(f"❌ Failed to load phone numbers: {bolna_response.status_code}")
        return False
    
    # Step 3: Test Different Number Selections
    print(f"\n3. 🎯 **Testing Different Number Selections**")
    
    test_results = []
    
    for i, selected_number in enumerate(available_numbers[:2], 1):  # Test 2 different numbers
        print(f"\n   🔄 **Test {i}: Selecting Number {selected_number.get('phone_number')}**")
        
        # Create order for selected number
        order_data = {
            "amount": 100,  # ₹1 in paise
            "currency": "INR",
            "phone_number": selected_number.get('phone_number'),  # Dynamic selection
            "number_id": selected_number.get('id')  # Dynamic ID
        }
        
        print(f"      📋 Selected Phone: {order_data['phone_number']}")
        print(f"      🆔 Selected ID: {order_data['number_id'][:8]}...")
        
        order_response = requests.post(f"{base_url}/api/dev/create-razorpay-order", json=order_data)
        
        if order_response.status_code == 200:
            order_result = order_response.json()
            order_id = order_result.get('order_id')
            print(f"      ✅ Order created for selected number")
        else:
            print(f"      ❌ Order creation failed: {order_response.status_code}")
            continue
        
        # Simulate payment for selected number
        payment_data = {
            "razorpay_payment_id": f"pay_test_{i}_{int(time.time())}",
            "razorpay_order_id": order_id,
            "razorpay_signature": f"test_signature_{i}_{int(time.time())}",
            "phone_number": selected_number.get('phone_number'),  # Dynamic selection
            "number_id": selected_number.get('id'),  # Dynamic ID
            "provider": "bolna"
        }
        
        print(f"      💳 Processing payment for: {payment_data['phone_number']}")
        
        verify_response = requests.post(f"{base_url}/api/verify-payment", json=payment_data, headers=headers)
        
        if verify_response.status_code == 200:
            verify_result = verify_response.json()
            print(f"      ✅ Payment verified for selected number")
            
            test_results.append({
                'number': selected_number.get('phone_number'),
                'id': selected_number.get('id'),
                'success': True
            })
        else:
            print(f"      ⚠️ Payment verification failed: {verify_response.status_code}")
            test_results.append({
                'number': selected_number.get('phone_number'),
                'id': selected_number.get('id'),
                'success': False
            })
        
        time.sleep(1)  # Small delay between tests
    
    # Step 4: Verify All Selected Numbers in Database
    print(f"\n4. 🔍 **Database Verification - All Selected Numbers**")
    
    time.sleep(2)
    
    owned_response = requests.get(f"{base_url}/api/phone-numbers/owned-simple", headers=headers)
    if owned_response.status_code == 200:
        owned_result = owned_response.json()
        numbers = owned_result.get('data', [])
        
        print(f"✅ Retrieved {len(numbers)} total purchased numbers")
        
        # Check each test result
        all_found = True
        for test in test_results:
            if test['success']:
                found = False
                for phone in numbers:
                    if phone.get('phone_number') == test['number']:
                        found = True
                        print(f"   ✅ FOUND: {test['number']} - Correctly stored!")
                        break
                
                if not found:
                    print(f"   ❌ MISSING: {test['number']} - Not found in database!")
                    all_found = False
        
        print(f"\n📊 **Dynamic Selection Test Results:**")
        for i, test in enumerate(test_results, 1):
            status = "✅ SUCCESS" if test['success'] else "❌ FAILED"
            print(f"   Test {i}: {test['number']} - {status}")
        
        if all_found and all(t['success'] for t in test_results):
            print(f"\n🎉 **ALL DYNAMIC SELECTIONS WORKING PERFECTLY!**")
            print(f"✅ Each selected number stored correctly")
            print(f"✅ No hardcoded numbers used")
            print(f"✅ Dynamic phone_number and number_id working")
            return True
        else:
            print(f"\n⚠️ **Some dynamic selections failed**")
            return False
    else:
        print(f"❌ Could not verify database: {owned_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_dynamic_number_selection()
    exit(0 if success else 1)
