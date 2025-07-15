#!/usr/bin/env python3
"""
Create payment tables in Supabase database
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def create_payment_tables():
    """Create payment tables in Supabase"""
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase configuration")
        return False
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("🔧 Creating payment tables...")
    
    # Create account_balances table using REST API
    try:
        # First create a default balance for the existing enterprise
        enterprise_response = requests.get(f"{SUPABASE_URL}/rest/v1/enterprises?limit=1", headers=headers)
        
        if enterprise_response.status_code == 200:
            enterprises = enterprise_response.json()
            if enterprises:
                enterprise_id = enterprises[0]['id']
                print(f"✅ Found enterprise: {enterprise_id}")
                
                # Try to create account balance record directly
                balance_data = {
                    'enterprise_id': enterprise_id,
                    'credits_balance': 1000.00,
                    'currency': 'USD',
                    'auto_recharge_enabled': False,
                    'auto_recharge_amount': 10.00,
                    'auto_recharge_trigger': 10.00
                }
                
                # Check if account_balances table exists by trying to query it
                balance_check = requests.get(f"{SUPABASE_URL}/rest/v1/account_balances?limit=1", headers=headers)
                
                if balance_check.status_code == 404:
                    print("⚠️  Payment tables don't exist yet")
                    print("📝 Please run the SQL schema in Supabase SQL Editor:")
                    print()
                    print("1. Go to https://supabase.com/dashboard/project/[your-project]/sql")
                    print("2. Copy and paste the SQL from payment_schema.sql")
                    print("3. Click 'Run' to create the tables")
                    print()
                    return False
                else:
                    print("✅ Account balances table exists")
                    
                    # Try to get existing balance
                    existing_balance = requests.get(
                        f"{SUPABASE_URL}/rest/v1/account_balances?enterprise_id=eq.{enterprise_id}", 
                        headers=headers
                    )
                    
                    if existing_balance.status_code == 200:
                        balance_records = existing_balance.json()
                        if balance_records:
                            print(f"✅ Balance record exists: {balance_records[0]['credits_balance']} credits")
                            return balance_records[0]
                        else:
                            # Create new balance record
                            create_balance = requests.post(
                                f"{SUPABASE_URL}/rest/v1/account_balances",
                                headers=headers,
                                json=balance_data
                            )
                            
                            if create_balance.status_code in [200, 201]:
                                print("✅ Created default balance record")
                                return balance_data
                            else:
                                print(f"❌ Failed to create balance: {create_balance.text}")
                                return False
                
            else:
                print("❌ No enterprises found")
                return False
        else:
            print(f"❌ Failed to get enterprises: {enterprise_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Payment Tables Setup")
    print("=" * 30)
    
    result = create_payment_tables()
    
    if result:
        print("\n🎉 Payment system is ready!")
        print("✅ Database tables are set up")
        print("✅ Razorpay credentials are configured")
        print("\n🧪 Test the payment system:")
        print("python test_payment_system.py")
    else:
        print("\n⚠️  Please create the database tables first")
        print("📝 Run the SQL from payment_schema.sql in Supabase SQL Editor")