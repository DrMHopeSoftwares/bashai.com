"""
Razorpay Payment Gateway Integration for DrM Hope Platform
Handles payment processing, order creation, and webhook verification
"""

import os
import hmac
import hashlib
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class RazorpayIntegration:
    def __init__(self):
        self.key_id = os.getenv('RAZORPAY_KEY_ID')
        self.key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        self.webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET')
        self.base_url = 'https://api.razorpay.com/v1'
        
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials not found in environment variables")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Razorpay API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        auth = (self.key_id, self.key_secret)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, auth=auth, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, auth=auth, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, auth=auth, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Razorpay API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise
    
    def create_order(self, amount: float, currency: str = 'INR', receipt: str = None, 
                    notes: Dict = None) -> Dict:
        """
        Create a Razorpay order for payment processing
        
        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code (INR, USD, etc.)
            receipt: Custom receipt identifier
            notes: Additional metadata
            
        Returns:
            Dict containing order details including order_id
        """
        # Convert amount to smallest currency unit
        amount_in_paise = int(amount * 100) if currency == 'INR' else int(amount * 100)
        
        order_data = {
            'amount': amount_in_paise,
            'currency': currency,
            'receipt': receipt or f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'notes': notes or {}
        }
        
        try:
            order = self._make_request('POST', '/orders', order_data)
            print(f"Razorpay order created successfully: {order['id']}")
            return order
        except Exception as e:
            print(f"Failed to create Razorpay order: {e}")
            raise
    
    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, 
                                razorpay_signature: str) -> bool:
        """
        Verify payment signature from Razorpay
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            # Create signature string
            body = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.key_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, razorpay_signature)
            
        except Exception as e:
            print(f"Payment signature verification failed: {e}")
            return False
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from Razorpay
        
        Args:
            payload: Raw request body
            signature: X-Razorpay-Signature header value
            
        Returns:
            Boolean indicating if signature is valid
        """
        if not self.webhook_secret:
            print("Webhook secret not configured")
            return False
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            print(f"Webhook signature verification failed: {e}")
            return False
    
    def get_payment_details(self, payment_id: str) -> Dict:
        """
        Get payment details from Razorpay
        
        Args:
            payment_id: Payment ID from Razorpay
            
        Returns:
            Dict containing payment details
        """
        try:
            payment = self._make_request('GET', f'/payments/{payment_id}')
            return payment
        except Exception as e:
            print(f"Failed to get payment details: {e}")
            raise
    
    def refund_payment(self, payment_id: str, amount: float = None, notes: Dict = None) -> Dict:
        """
        Create a refund for a payment
        
        Args:
            payment_id: Payment ID to refund
            amount: Amount to refund (in currency units, not paise)
            notes: Additional metadata
            
        Returns:
            Dict containing refund details
        """
        refund_data = {
            'notes': notes or {}
        }
        
        if amount is not None:
            refund_data['amount'] = int(amount * 100)  # Convert to paise
        
        try:
            refund = self._make_request('POST', f'/payments/{payment_id}/refund', refund_data)
            print(f"Refund created successfully: {refund['id']}")
            return refund
        except Exception as e:
            print(f"Failed to create refund: {e}")
            raise

# Credit and payment utility functions
def calculate_credits_from_amount(amount_usd: float) -> float:
    """Convert USD amount to credits (1 USD = 100 credits)"""
    return amount_usd * 100

def calculate_amount_from_credits(credits: float) -> float:
    """Convert credits to USD amount (100 credits = 1 USD)"""
    return credits / 100

def convert_usd_to_inr(amount_usd: float, exchange_rate: float = 83.0) -> float:
    """Convert USD to INR using current exchange rate"""
    return amount_usd * exchange_rate

def get_predefined_recharge_options():
    """Get predefined recharge amount options"""
    return [
        {'usd': 10, 'inr': 830, 'credits': 1000, 'label': 'Add $10 worth of more funds'},
        {'usd': 50, 'inr': 4150, 'credits': 5000, 'label': 'Add $50 worth of more funds'},
        {'usd': 75, 'inr': 6225, 'credits': 7500, 'label': 'Add $75 worth of more funds'},
        {'usd': 100, 'inr': 8300, 'credits': 10000, 'label': 'Add $100 worth of more funds'},
        {'usd': 250, 'inr': 20750, 'credits': 25000, 'label': 'Add $250 worth of more funds'},
        {'usd': 500, 'inr': 41500, 'credits': 50000, 'label': 'Add $500 worth of more funds'},
        {'usd': 1000, 'inr': 83000, 'credits': 100000, 'label': 'Add $1000 worth of more funds'},
    ]

# Test function for development
def test_razorpay_integration():
    """Test Razorpay integration with sample data"""
    try:
        razorpay = RazorpayIntegration()
        
        # Test order creation
        test_amount = 10.00  # $10 USD
        test_notes = {
            'enterprise_id': 'test-enterprise-123',
            'credits': calculate_credits_from_amount(test_amount),
            'type': 'manual_recharge'
        }
        
        order = razorpay.create_order(
            amount=test_amount,
            currency='INR',
            receipt=f"test_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            notes=test_notes
        )
        
        print("✅ Razorpay integration test successful!")
        print(f"Test order created: {order['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Razorpay integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Razorpay Integration")
    print("=" * 40)
    
    # Check environment variables
    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    
    if not key_id or not key_secret:
        print("❌ Razorpay credentials not found")
        print("Please add to .env file:")
        print("RAZORPAY_KEY_ID=your_key_id")
        print("RAZORPAY_KEY_SECRET=your_key_secret")
        print("RAZORPAY_WEBHOOK_SECRET=your_webhook_secret")
    else:
        print("✅ Razorpay credentials found")
        print("📋 Recharge options:")
        for option in get_predefined_recharge_options():
            print(f"   ${option['usd']} = ₹{option['inr']} = {option['credits']} credits")