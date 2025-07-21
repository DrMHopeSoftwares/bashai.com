#!/usr/bin/env python3
"""
Test Razorpay order amount to ensure it shows ₹1 not ₹100
"""

import requests
import json

def test_razorpay_amount():
    """Test that Razorpay order shows correct ₹1 amount"""
    
    base_url = "http://127.0.0.1:5004"
    
    print("🎯 **TESTING RAZORPAY AMOUNT**")
    print("=" * 50)
    
    # Login first
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
    
    # Create order with ₹1 amount
    order_data = {
        "amount": 100,  # 100 paise = ₹1
        "currency": "INR",
        "phone_number": "+918035741234",
        "number_id": "test_123"
    }
    
    print(f"\n📋 **Creating Razorpay Order**")
    print(f"   Frontend sending: {order_data['amount']} paise")
    print(f"   Expected in Razorpay: ₹{order_data['amount'] / 100}")
    
    order_response = requests.post(f"{base_url}/api/dev/create-razorpay-order", json=order_data)
    
    if order_response.status_code == 200:
        order_result = order_response.json()
        razorpay_amount = order_result.get('amount')
        
        print(f"✅ Order created successfully")
        print(f"   Order ID: {order_result.get('order_id')}")
        print(f"   Razorpay Amount: {razorpay_amount} paise")
        print(f"   Razorpay Amount in ₹: ₹{razorpay_amount / 100}")
        
        if razorpay_amount == 100:
            print(f"🎉 **SUCCESS! Razorpay will show ₹1.00**")
            return True
        else:
            print(f"❌ **ERROR! Razorpay will show ₹{razorpay_amount / 100} instead of ₹1**")
            return False
    else:
        print(f"❌ Order creation failed: {order_response.status_code}")
        try:
            error_detail = order_response.json()
            print(f"   Error: {error_detail}")
        except:
            print(f"   Raw response: {order_response.text}")
        return False

if __name__ == "__main__":
    success = test_razorpay_amount()
    exit(0 if success else 1)
