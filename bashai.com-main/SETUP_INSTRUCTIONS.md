# Database Setup Instructions for DrM Hope Platform

## Current Status
✅ **Application is running successfully** on port 8080  
✅ **Basic tables exist** (enterprises, organizations, voice_agents, contacts)  
✅ **Channels populated** - Added 6 channels for existing organizations  
❌ **Financial tables missing** - Need to create account_balances, payment_transactions, credit_usage_logs  

## Step-by-Step Setup

### 1. Create Missing Financial Tables

Go to your **Supabase Dashboard**:
1. Visit: https://app.supabase.com/
2. Navigate to: **SQL Editor** > **New Query**
3. Copy and paste the contents of `payment_schema.sql` 
4. Click **Run** to execute

### 2. Verify Phone and Voice Tables (Optional)

If you encounter any issues with phone/voice tables:
1. In Supabase SQL Editor, create another new query
2. Copy and paste the contents of `phone_voice_schema_fixed.sql`
3. Click **Run** to execute

### 3. Populate All Tables with Test Data

After creating the tables, run:
```bash
python populate_database_rest.py
```

## What Will Be Created

### Financial Tables:
- **account_balances**: Credit balances for each enterprise
- **payment_transactions**: Razorpay payment records  
- **credit_usage_logs**: Usage tracking for voice services

### Test Data Added:
- ✅ **6 Channels** (Inbound/Outbound/WhatsApp for each organization)
- 🔄 **Call Logs** (50+ sample call records)
- 🔄 **Activity Logs** (30+ user activity records)
- 🔄 **Phone Numbers** (10+ purchased numbers with providers)
- 🔄 **Voice Preferences** (Voice settings for each agent)
- 🔄 **Usage Logs** (Phone and credit usage tracking)
- 🔄 **Financial Data** (Account balances, payments, credit usage)

## Current Database State

```
enterprises                   :        1 record
organizations                 :        1 record  
channels                      :        1 record   ✅ POPULATED
voice_agents                  :        1 record
contacts                      :        1 record
call_logs                     :        1 record
activity_logs                 :        1 record
purchased_phone_numbers       :        1 record
enterprise_voice_preferences  :        1 record
phone_number_usage_logs       :        1 record
account_balances              :    MISSING ❌
payment_transactions          :    MISSING ❌
credit_usage_logs             :    MISSING ❌
```

## Files Created

- ✅ `payment_schema.sql` - Creates financial tables
- ✅ `phone_voice_schema_fixed.sql` - Creates phone/voice tables  
- ✅ `populate_test_data.sql` - SQL-based population script
- ✅ `populate_database_rest.py` - REST API-based population script
- ✅ `create_financial_tables_manual.py` - Table existence checker
- ✅ `run_database_setup.py` - Original comprehensive setup script

## Next Steps

1. **Execute `payment_schema.sql` in Supabase SQL Editor**
2. **Run the population script**: `python populate_database_rest.py`
3. **Verify your application** works with the new test data

Your application is already running successfully - this is just adding the missing financial functionality and comprehensive test data to make development and testing easier!