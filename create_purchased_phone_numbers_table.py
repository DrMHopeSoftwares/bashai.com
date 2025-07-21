#!/usr/bin/env python3
"""
Create purchased_phone_numbers table in Supabase database
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def create_purchased_phone_numbers_table():
    """Create purchased_phone_numbers table in Supabase"""
    
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
    
    print("🔧 Creating purchased_phone_numbers table...")
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS public.purchased_phone_numbers (
        id uuid NOT NULL DEFAULT gen_random_uuid(),
        phone_number character varying(20) NOT NULL,
        number_id character varying(100) NULL,
        friendly_name character varying(255) NULL,
        user_id uuid NULL,
        enterprise_id uuid NULL,
        payment_id character varying(100) NULL,
        order_id character varying(100) NULL,
        amount_paid numeric(10, 2) NULL DEFAULT 0.00,
        currency character varying(3) NULL DEFAULT 'INR'::character varying,
        status character varying(20) NULL DEFAULT 'active'::character varying,
        country_code character varying(5) NULL DEFAULT 'IN'::character varying,
        country_name character varying(100) NULL DEFAULT 'India'::character varying,
        monthly_cost numeric(10, 2) NULL DEFAULT 5.00,
        setup_cost numeric(10, 2) NULL DEFAULT 1.00,
        capabilities text[] NULL DEFAULT array['voice'::text, 'sms'::text],
        provider character varying(50) NULL DEFAULT 'bolna'::character varying,
        provider_phone_id character varying(100) NULL,
        purchased_at timestamp with time zone NULL DEFAULT now(),
        expires_at timestamp with time zone NULL,
        last_used_at timestamp with time zone NULL,
        created_at timestamp with time zone NULL DEFAULT now(),
        updated_at timestamp with time zone NULL DEFAULT now(),
        CONSTRAINT purchased_phone_numbers_pkey PRIMARY KEY (id),
        CONSTRAINT purchased_phone_numbers_number_id_enterprise_id_key UNIQUE (number_id, enterprise_id),
        CONSTRAINT purchased_phone_numbers_phone_number_enterprise_id_key UNIQUE (phone_number, enterprise_id)
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_purchased_phone_numbers_enterprise_id ON purchased_phone_numbers(enterprise_id);
    CREATE INDEX IF NOT EXISTS idx_purchased_phone_numbers_phone_number ON purchased_phone_numbers(phone_number);
    CREATE INDEX IF NOT EXISTS idx_purchased_phone_numbers_status ON purchased_phone_numbers(status);
    """
    
    try:
        # Use the SQL endpoint to execute the DDL
        sql_url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
        
        response = requests.post(
            sql_url,
            headers=headers,
            json={'query': create_table_sql}
        )
        
        if response.status_code == 200:
            print("✅ purchased_phone_numbers table created successfully!")
            return True
        else:
            print(f"❌ Failed to create table: {response.status_code} - {response.text}")
            
            # Try alternative approach using direct SQL execution
            print("🔄 Trying alternative approach...")
            
            # Try using the database URL directly
            db_url = f"{SUPABASE_URL}/rest/v1/"
            
            # Create a simple test to see if we can access the database
            test_response = requests.get(f"{db_url}purchased_phone_numbers?limit=1", headers=headers)
            
            if test_response.status_code == 404:
                print("✅ Table doesn't exist, which is expected")
                
                # Try to create using a different method - insert a dummy record to force table creation
                print("🔄 Creating table by inserting sample data...")
                
                sample_data = {
                    'phone_number': '+919999999999',
                    'friendly_name': 'Test Number',
                    'enterprise_id': '00000000-0000-0000-0000-000000000000',
                    'status': 'test'
                }
                
                insert_response = requests.post(
                    f"{db_url}purchased_phone_numbers",
                    headers=headers,
                    json=sample_data
                )
                
                if insert_response.status_code == 201:
                    print("✅ Table created via data insertion!")
                    
                    # Now delete the test record
                    delete_response = requests.delete(
                        f"{db_url}purchased_phone_numbers?phone_number=eq.+919999999999",
                        headers=headers
                    )
                    
                    if delete_response.status_code == 204:
                        print("✅ Test record cleaned up")
                    
                    return True
                else:
                    print(f"❌ Failed to create table via insertion: {insert_response.status_code} - {insert_response.text}")
                    return False
            else:
                print(f"❌ Unexpected response: {test_response.status_code} - {test_response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    success = create_purchased_phone_numbers_table()
    exit(0 if success else 1)
