#!/usr/bin/env python3
"""
Test with real API phone numbers instead of mock numbers
"""

import requests
import json
import time

def test_real_api_numbers():
    """Test with actual phone numbers from API"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🎯 **TESTING WITH REAL API PHONE NUMBERS**")
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
    
    # Step 2: Get Real Phone Numbers from API
    print(f"\n2. 📱 **Loading Real Phone Numbers from API**")
    
    bolna_response = requests.get(f"{base_url}/api/bolna/phone-numbers", headers=headers)
    if bolna_response.status_code == 200:
        bolna_result = bolna_response.json()
        available_numbers = bolna_result.get('phone_numbers', [])
        print(f"✅ Loaded {len(available_numbers)} real phone numbers from API")
        
        if available_numbers:
            # Use first available number
            test_number = available_numbers[0]
            print(f"   📞 Selected Real Number: {test_number.get('phone_number')}")
            print(f"   🆔 Real Number ID: {test_number.get('id')}")
            print(f"   💰 Price: {test_number.get('price')}")
            print(f"   🏢 Provider: {test_number.get('telephony_provider')}")
        else:
            print("⚠️ No real numbers available from API")
            return False
    else:
        print(f"❌ Failed to load phone numbers: {bolna_response.status_code}")
        return False
    
    # Step 3: Create Order with Real Number
    print(f"\n3. 🛒 **Creating Order with Real API Number**")
    
    order_data = {
        "amount": 100,  # ₹1 in paise
        "currency": "INR",
        "phone_number": test_number.get('phone_number'),  # Real API number
        "number_id": test_number.get('id')  # Real API number ID
    }
    
    print(f"   📋 Real Phone Number: {order_data['phone_number']}")
    print(f"   🆔 Real Number ID: {order_data['number_id']}")
    print(f"   💰 Amount: ₹{order_data['amount'] / 100}")
    
    order_response = requests.post(f"{base_url}/api/dev/create-razorpay-order", json=order_data)
    
    if order_response.status_code == 200:
        order_result = order_response.json()
        order_id = order_result.get('order_id')
        print(f"✅ Razorpay order created with real number")
        print(f"   Order ID: {order_id}")
        print(f"   Amount: ₹{order_result.get('amount') / 100}")
    else:
        print(f"❌ Order creation failed: {order_response.status_code}")
        return False
    
    # Step 4: Simulate Payment with Real Number
    print(f"\n4. 💳 **Payment Verification with Real Number**")
    
    payment_data = {
        "razorpay_payment_id": f"pay_live_{int(time.time())}",
        "razorpay_order_id": order_id,
        "razorpay_signature": f"live_signature_{int(time.time())}",
        "phone_number": test_number.get('phone_number'),  # Real API number
        "number_id": test_number.get('id'),  # Real API number ID
        "provider": "bolna"
    }
    
    print(f"   📞 Storing Real Number: {payment_data['phone_number']}")
    print(f"   🆔 Real Number ID: {payment_data['number_id']}")
    
    verify_response = requests.post(f"{base_url}/api/verify-payment", json=payment_data, headers=headers)
    
    if verify_response.status_code == 200:
        verify_result = verify_response.json()
        print(f"✅ Payment verified with real API number")
        print(f"   Message: {verify_result.get('message', 'Success')}")
    else:
        print(f"⚠️ Payment verification failed: {verify_response.status_code}")
    
    # Step 5: Verify Real Number in Database
    print(f"\n5. 🔍 **Database Verification - Real API Number**")
    
    time.sleep(2)
    
    owned_response = requests.get(f"{base_url}/api/phone-numbers/owned-simple", headers=headers)
    if owned_response.status_code == 200:
        owned_result = owned_response.json()
        numbers = owned_result.get('data', [])
        
        print(f"✅ Retrieved {len(numbers)} purchased numbers")
        
        # Look for our real API phone number
        found_real_phone = False
        for i, phone in enumerate(numbers, 1):
            print(f"   {i}. {phone.get('phone_number')} - {phone.get('status')} (₹{phone.get('amount_paid')})")
            if phone.get('phone_number') == test_number.get('phone_number'):
                found_real_phone = True
                print(f"      🎉 REAL API PHONE NUMBER FOUND IN DATABASE!")
                print(f"      📞 Number: {phone.get('phone_number')}")
                print(f"      💰 Amount: ₹{phone.get('amount_paid')}")
                print(f"      📅 Date: {phone.get('purchase_date')}")
        
        if found_real_phone:
            print(f"\n🎉 **SUCCESS! Real API phone number stored correctly!**")
            return True
        else:
            print(f"\n⚠️ **Real API phone number not found in database**")
            return False
    else:
        print(f"❌ Could not verify database: {owned_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_real_api_numbers()
    exit(0 if success else 1)
