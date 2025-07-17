-- Complete Database Setup and Population Script for DrM Hope Platform
-- Run this script to set up all tables and populate with test data

-- Step 1: Create financial tables (if they don't exist)
-- This creates account_balances, payment_transactions, and credit_usage_logs tables
\echo 'Creating financial tables...'
\i payment_schema.sql

-- Step 2: Ensure phone and voice tables exist
\echo 'Creating phone and voice management tables...'
\i phone_voice_schema_fixed.sql

-- Step 3: Populate all tables with test data
\echo 'Populating all tables with test data...'
\i populate_test_data.sql

-- Step 4: Verify the setup
\echo 'Verifying database setup...'

-- Show table counts
SELECT 'enterprises' as table_name, COUNT(*) as record_count FROM enterprises
UNION ALL
SELECT 'organizations', COUNT(*) FROM organizations
UNION ALL
SELECT 'channels', COUNT(*) FROM channels
UNION ALL
SELECT 'voice_agents', COUNT(*) FROM voice_agents
UNION ALL
SELECT 'contacts', COUNT(*) FROM contacts
UNION ALL
SELECT 'call_logs', COUNT(*) FROM call_logs
UNION ALL
SELECT 'activity_logs', COUNT(*) FROM activity_logs
UNION ALL
SELECT 'purchased_phone_numbers', COUNT(*) FROM purchased_phone_numbers
UNION ALL
SELECT 'enterprise_voice_preferences', COUNT(*) FROM enterprise_voice_preferences
UNION ALL
SELECT 'phone_number_usage_logs', COUNT(*) FROM phone_number_usage_logs
UNION ALL
SELECT 'account_balances', COUNT(*) FROM account_balances
UNION ALL
SELECT 'payment_transactions', COUNT(*) FROM payment_transactions
UNION ALL
SELECT 'credit_usage_logs', COUNT(*) FROM credit_usage_logs
ORDER BY table_name;

\echo 'Database setup and population complete!'