#!/usr/bin/env python3
"""
Test specific number +918035315404 that user clicked but didn't store
"""

import requests
import json
import time

def test_specific_number_315404():
    """Test the specific number user clicked: +918035315404"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🎯 **TESTING SPECIFIC NUMBER: +918035315404**")
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
    
    # Step 2: Get Available Numbers and find the specific one
    print(f"\n2. 📱 **Finding Specific Number: +918035315404**")
    
    bolna_response = requests.get(f"{base_url}/api/bolna/phone-numbers", headers=headers)
    if bolna_response.status_code == 200:
        bolna_result = bolna_response.json()
        available_numbers = bolna_result.get('phone_numbers', [])
        print(f"✅ Loaded {len(available_numbers)} available numbers")
        
        # Find the specific number user clicked
        target_number = None
        for number in available_numbers:
            if number.get('phone_number') == '+918035315404':
                target_number = number
                break
        
        if target_number:
            print(f"🎯 **FOUND TARGET NUMBER:**")
            print(f"   📞 Phone: {target_number.get('phone_number')}")
            print(f"   🆔 ID: {target_number.get('id')}")
            print(f"   💰 Price: {target_number.get('price')}")
            print(f"   🏢 Provider: {target_number.get('telephony_provider')}")
        else:
            print(f"❌ Target number +918035315404 not found in available numbers!")
            print(f"📋 Available numbers:")
            for i, number in enumerate(available_numbers, 1):
                print(f"   {i}. {number.get('phone_number')}")
            return False
    else:
        print(f"❌ Failed to load phone numbers: {bolna_response.status_code}")
        return False
    
    # Step 3: Test clicking this specific number
    print(f"\n3. 🎯 **Simulating Click on +918035315404**")
    
    clicked_phone = target_number.get('phone_number')
    clicked_id = target_number.get('id')
    
    print(f"👆 **USER CLICKS: Buy Number for +918035315404**")
    print(f"   📞 Clicked Phone: {clicked_phone}")
    print(f"   🆔 Clicked ID: {clicked_id}")
    
    # Step 4: Create Order
    print(f"\n4. 🛒 **Creating Order for +918035315404**")
    
    order_data = {
        "amount": 100,  # ₹1 in paise
        "currency": "INR",
        "phone_number": clicked_phone,
        "number_id": clicked_id
    }
    
    print(f"   📋 Order Data:")
    print(f"      📞 Phone: {order_data['phone_number']}")
    print(f"      🆔 ID: {order_data['number_id']}")
    print(f"      💰 Amount: ₹{order_data['amount'] / 100}")
    
    order_response = requests.post(f"{base_url}/api/dev/create-razorpay-order", json=order_data)
    
    if order_response.status_code == 200:
        order_result = order_response.json()
        order_id = order_result.get('order_id')
        print(f"   ✅ Order created successfully")
        print(f"      Order ID: {order_id}")
    else:
        print(f"   ❌ Order creation failed: {order_response.status_code}")
        print(f"   Response: {order_response.text}")
        return False
    
    # Step 5: Simulate Payment
    print(f"\n5. 💳 **Payment for +918035315404**")
    
    payment_data = {
        "razorpay_payment_id": f"pay_clicked_315404_{int(time.time())}",  # Use pay_clicked_ format
        "razorpay_order_id": order_id,
        "razorpay_signature": f"sig_clicked_315404_{int(time.time())}",
        "phone_number": clicked_phone,
        "number_id": clicked_id,
        "provider": "bolna"
    }
    
    print(f"   📋 Payment Data:")
    print(f"      📞 Phone: {payment_data['phone_number']}")
    print(f"      🆔 ID: {payment_data['number_id']}")
    print(f"      💳 Payment ID: {payment_data['razorpay_payment_id']}")
    
    verify_response = requests.post(f"{base_url}/api/verify-payment", json=payment_data, headers=headers)
    
    if verify_response.status_code == 200:
        verify_result = verify_response.json()
        print(f"   ✅ Payment verified successfully")
        print(f"      Message: {verify_result.get('message', 'Success')}")
    else:
        print(f"   ❌ Payment verification failed: {verify_response.status_code}")
        print(f"   Response: {verify_response.text}")
        return False
    
    # Step 6: Check if number is stored
    print(f"\n6. 🔍 **Checking Database for +918035315404**")
    
    time.sleep(2)
    
    owned_response = requests.get(f"{base_url}/api/phone-numbers/owned-simple", headers=headers)
    if owned_response.status_code == 200:
        owned_result = owned_response.json()
        numbers = owned_result.get('data', [])
        
        print(f"✅ Retrieved {len(numbers)} total purchased numbers")
        
        # Look specifically for +918035315404
        found_target = False
        for phone in numbers:
            if phone.get('phone_number') == '+918035315404':
                found_target = True
                print(f"🎉 **TARGET NUMBER FOUND IN DATABASE!**")
                print(f"   📞 Number: {phone.get('phone_number')}")
                print(f"   💰 Amount: ₹{phone.get('amount_paid')}")
                print(f"   📅 Date: {phone.get('purchase_date')}")
                print(f"   🆔 Record ID: {phone.get('id')}")
                break
        
        if not found_target:
            print(f"❌ **TARGET NUMBER NOT FOUND IN DATABASE!**")
            print(f"❌ Looking for: +918035315404")
            print(f"📋 **Numbers in database:**")
            for i, phone in enumerate(numbers, 1):
                print(f"   {i}. {phone.get('phone_number')} - ₹{phone.get('amount_paid')}")
            return False
        else:
            print(f"\n🎉 **SUCCESS! +918035315404 stored correctly!**")
            return True
    else:
        print(f"❌ Could not check database: {owned_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_specific_number_315404()
    exit(0 if success else 1)
