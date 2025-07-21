#!/usr/bin/env python3
"""
Test specific button clicks - simulate clicking different Buy Number buttons
"""

import requests
import json
import time

def test_specific_button_clicks():
    """Test clicking specific Buy Number buttons"""
    
    base_url = "http://127.0.0.1:5003"
    
    print("🎯 **TESTING SPECIFIC BUTTON CLICKS**")
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
    
    # Step 2: Get Available Numbers (like dashboard does)
    print(f"\n2. 📱 **Loading Available Numbers (Dashboard Simulation)**")
    
    bolna_response = requests.get(f"{base_url}/api/bolna/phone-numbers", headers=headers)
    if bolna_response.status_code == 200:
        bolna_result = bolna_response.json()
        available_numbers = bolna_result.get('phone_numbers', [])
        print(f"✅ Dashboard loaded {len(available_numbers)} numbers")
        
        print(f"📋 **Available Numbers (like in dashboard):**")
        for i, number in enumerate(available_numbers, 1):
            print(f"   {i}. 📞 {number.get('phone_number')} (ID: {number.get('id')[:8]}...)")
            print(f"      💰 Price: {number.get('price')} | Provider: {number.get('telephony_provider')}")
    else:
        print(f"❌ Failed to load phone numbers: {bolna_response.status_code}")
        return False
    
    # Step 3: Simulate clicking SPECIFIC button (like user clicking 3rd number)
    print(f"\n3. 🎯 **Simulating User Clicking SPECIFIC Button**")
    
    # Let's say user clicks on the 3rd number's "Buy Number" button
    if len(available_numbers) >= 3:
        selected_index = 2  # 3rd number (0-indexed)
        clicked_number = available_numbers[selected_index]
        
        print(f"👆 **USER CLICKS: Buy Number button for #{selected_index + 1}**")
        print(f"   📞 Clicked Number: {clicked_number.get('phone_number')}")
        print(f"   🆔 Clicked ID: {clicked_number.get('id')}")
        print(f"   💰 Price: {clicked_number.get('price')}")
        
        # This simulates: onclick="window.buyNumberWithRazorpay('${number.phone_number}', '${number.id}')"
        clicked_phone = clicked_number.get('phone_number')
        clicked_id = clicked_number.get('id')
        
        print(f"\n🔄 **Processing Click (buyNumberWithRazorpay function)**")
        print(f"   📋 phoneNumber parameter: {clicked_phone}")
        print(f"   🆔 numberId parameter: {clicked_id}")
        
        # Step 4: Create Order (like frontend does)
        print(f"\n4. 🛒 **Creating Order for Clicked Number**")
        
        order_data = {
            "amount": 100,  # ₹1 in paise
            "currency": "INR",
            "phone_number": clicked_phone,  # Exactly what user clicked
            "number_id": clicked_id         # Exactly what user clicked
        }
        
        print(f"   📋 Order Data:")
        print(f"      📞 Phone: {order_data['phone_number']}")
        print(f"      🆔 ID: {order_data['number_id']}")
        print(f"      💰 Amount: ₹{order_data['amount'] / 100}")
        
        order_response = requests.post(f"{base_url}/api/dev/create-razorpay-order", json=order_data)
        
        if order_response.status_code == 200:
            order_result = order_response.json()
            order_id = order_result.get('order_id')
            print(f"   ✅ Order created for clicked number")
            print(f"      Order ID: {order_id}")
        else:
            print(f"   ❌ Order creation failed: {order_response.status_code}")
            return False
        
        # Step 5: Simulate Payment (like Razorpay callback)
        print(f"\n5. 💳 **Payment for Clicked Number**")
        
        payment_data = {
            "razorpay_payment_id": f"pay_clicked_{int(time.time())}",
            "razorpay_order_id": order_id,
            "razorpay_signature": f"clicked_signature_{int(time.time())}",
            "phone_number": clicked_phone,  # Exactly what user clicked
            "number_id": clicked_id,        # Exactly what user clicked
            "provider": "bolna"
        }
        
        print(f"   📋 Payment Data:")
        print(f"      📞 Phone: {payment_data['phone_number']}")
        print(f"      🆔 ID: {payment_data['number_id']}")
        print(f"      💳 Payment ID: {payment_data['razorpay_payment_id']}")
        
        verify_response = requests.post(f"{base_url}/api/verify-payment", json=payment_data, headers=headers)
        
        if verify_response.status_code == 200:
            verify_result = verify_response.json()
            print(f"   ✅ Payment verified for clicked number")
            print(f"      Message: {verify_result.get('message', 'Success')}")
        else:
            print(f"   ⚠️ Payment verification failed: {verify_response.status_code}")
            return False
        
        # Step 6: Verify EXACTLY the clicked number is stored
        print(f"\n6. 🔍 **Verifying CLICKED Number in Database**")
        
        time.sleep(2)
        
        owned_response = requests.get(f"{base_url}/api/phone-numbers/owned-simple", headers=headers)
        if owned_response.status_code == 200:
            owned_result = owned_response.json()
            numbers = owned_result.get('data', [])
            
            print(f"✅ Retrieved {len(numbers)} purchased numbers")
            
            # Look for EXACTLY the number user clicked
            found_clicked_number = False
            for phone in numbers:
                if phone.get('phone_number') == clicked_phone:
                    found_clicked_number = True
                    print(f"🎉 **CLICKED NUMBER FOUND IN DATABASE!**")
                    print(f"   📞 Clicked: {clicked_phone}")
                    print(f"   📞 Stored: {phone.get('phone_number')}")
                    print(f"   💰 Amount: ₹{phone.get('amount_paid')}")
                    print(f"   📅 Date: {phone.get('purchase_date')}")
                    break
            
            if found_clicked_number:
                print(f"\n🎉 **SUCCESS! Clicked number stored correctly!**")
                print(f"✅ User clicked: {clicked_phone}")
                print(f"✅ Database stored: {clicked_phone}")
                print(f"✅ Button click → Database storage working!")
                return True
            else:
                print(f"\n❌ **FAILED! Clicked number not found in database**")
                print(f"❌ User clicked: {clicked_phone}")
                print(f"❌ Not found in database")
                return False
        else:
            print(f"❌ Could not verify database: {owned_response.status_code}")
            return False
    else:
        print(f"❌ Not enough numbers available for test")
        return False

if __name__ == "__main__":
    success = test_specific_button_clicks()
    exit(0 if success else 1)
