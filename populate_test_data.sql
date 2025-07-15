-- Populate All Tables with Test Data for DrM Hope Platform
-- This script creates test data for all tables in the system

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- First, let's check and create the financial tables if they don't exist
-- (Run payment_schema.sql first if these tables don't exist)

-- 1. Populate channels for each organization
INSERT INTO channels (name, description, status, organization_id, configuration)
SELECT 
    channel_type.name,
    CASE 
        WHEN channel_type.name = 'Inbound Calls' THEN 'Handle incoming calls from customers'
        WHEN channel_type.name = 'Outbound Calls' THEN 'Make outgoing calls to customers'
        WHEN channel_type.name = 'WhatsApp Messages' THEN 'Send and receive WhatsApp messages'
    END as description,
    'active' as status,
    org.id as organization_id,
    CASE 
        WHEN channel_type.name = 'Inbound Calls' THEN '{"max_wait_time": 30, "greeting_message": "Welcome to our service"}'::jsonb
        WHEN channel_type.name = 'Outbound Calls' THEN '{"max_attempts": 3, "retry_interval": 300}'::jsonb
        WHEN channel_type.name = 'WhatsApp Messages' THEN '{"api_key": "demo_key", "webhook_url": "https://demo.webhook.com"}'::jsonb
    END as configuration
FROM organizations org
CROSS JOIN (
    VALUES ('Inbound Calls'), ('Outbound Calls'), ('WhatsApp Messages')
) AS channel_type(name)
WHERE NOT EXISTS (
    SELECT 1 FROM channels c 
    WHERE c.organization_id = org.id AND c.name = channel_type.name
);

-- 2. Populate call_logs with sample data
INSERT INTO call_logs (
    voice_agent_id, contact_id, phone_number, call_type, status, duration,
    ai_score, resolution, transcript_url, call_cost, metadata, started_at, ended_at
)
SELECT 
    va.id as voice_agent_id,
    c.id as contact_id,
    c.phone as phone_number,
    CASE WHEN random() > 0.5 THEN 'inbound' ELSE 'outbound' END as call_type,
    CASE 
        WHEN random() > 0.8 THEN 'failed'
        WHEN random() > 0.1 THEN 'completed'
        ELSE 'no_answer'
    END as status,
    floor(random() * 600 + 30)::integer as duration, -- 30-630 seconds
    floor(random() * 40 + 60)::integer as ai_score, -- 60-100 score
    CASE 
        WHEN random() > 0.7 THEN 'Issue resolved'
        WHEN random() > 0.4 THEN 'Follow-up required'
        ELSE 'Transferred to agent'
    END as resolution,
    'https://storage.example.com/transcripts/' || uuid_generate_v4() || '.txt' as transcript_url,
    (random() * 5 + 0.5)::numeric(10,2) as call_cost,
    jsonb_build_object(
        'sentiment', CASE WHEN random() > 0.5 THEN 'positive' ELSE 'neutral' END,
        'language', 'en-US',
        'keywords', ARRAY['support', 'help', 'question']
    ) as metadata,
    NOW() - (random() * interval '30 days') as started_at,
    NOW() - (random() * interval '30 days') + (floor(random() * 600 + 30) * interval '1 second') as ended_at
FROM voice_agents va
JOIN contacts c ON c.voice_agent_id = va.id
CROSS JOIN generate_series(1, 5) -- 5 calls per contact
WHERE NOT EXISTS (
    SELECT 1 FROM call_logs WHERE voice_agent_id = va.id
)
LIMIT 100; -- Limit to 100 call logs total

-- 3. Populate activity_logs
INSERT INTO activity_logs (
    user_id, action, entity_type, entity_id, description, metadata
)
SELECT 
    u.id as user_id,
    action_type.action,
    'voice_agent' as entity_type,
    va.id as entity_id,
    CASE 
        WHEN action_type.action = 'create' THEN 'Created voice agent: ' || va.title
        WHEN action_type.action = 'update' THEN 'Updated voice agent: ' || va.title
        WHEN action_type.action = 'delete' THEN 'Deleted voice agent: ' || va.title
        WHEN action_type.action = 'view' THEN 'Viewed voice agent: ' || va.title
    END as description,
    jsonb_build_object(
        'ip_address', '192.168.1.' || floor(random() * 255),
        'user_agent', 'Mozilla/5.0',
        'session_id', uuid_generate_v4()
    ) as metadata
FROM users u
JOIN voice_agents va ON va.enterprise_id = u.enterprise_id
CROSS JOIN (
    VALUES ('create'), ('update'), ('view')
) AS action_type(action)
WHERE u.status = 'active'
AND NOT EXISTS (
    SELECT 1 FROM activity_logs WHERE user_id = u.id
)
LIMIT 50; -- Limit to 50 activity logs

-- 4. Get phone number provider IDs
DO $$
DECLARE
    plivo_id UUID;
    twilio_id UUID;
    telnyx_id UUID;
BEGIN
    SELECT id INTO plivo_id FROM phone_number_providers WHERE name = 'Plivo';
    SELECT id INTO twilio_id FROM phone_number_providers WHERE name = 'Twilio';
    SELECT id INTO telnyx_id FROM phone_number_providers WHERE name = 'Telnyx';
    
    -- 5. Populate purchased_phone_numbers
    INSERT INTO purchased_phone_numbers (
        enterprise_id, phone_number, country_code, country_name, provider_id,
        provider_phone_id, monthly_cost, setup_cost, status, capabilities, expires_at
    )
    SELECT 
        e.id as enterprise_id,
        CASE 
            WHEN provider.id = plivo_id THEN '+1' || (2000000000 + floor(random() * 999999999)::bigint)::text
            WHEN provider.id = twilio_id THEN '+1' || (3000000000 + floor(random() * 999999999)::bigint)::text
            ELSE '+1' || (4000000000 + floor(random() * 999999999)::bigint)::text
        END as phone_number,
        'US' as country_code,
        'United States' as country_name,
        provider.id as provider_id,
        'PN' || substring(uuid_generate_v4()::text, 1, 16) as provider_phone_id,
        CASE 
            WHEN provider.id = plivo_id THEN 5.00
            WHEN provider.id = twilio_id THEN 1.00
            ELSE 2.00
        END as monthly_cost,
        0.00 as setup_cost,
        'active' as status,
        '{"voice": true, "sms": true, "mms": false}'::jsonb as capabilities,
        NOW() + interval '1 year' as expires_at
    FROM enterprises e
    CROSS JOIN (
        SELECT id FROM phone_number_providers WHERE status = 'active' LIMIT 3
    ) provider
    WHERE NOT EXISTS (
        SELECT 1 FROM purchased_phone_numbers WHERE enterprise_id = e.id
    )
    LIMIT 10; -- 10 phone numbers total
END $$;

-- 6. Get voice provider and voice IDs
DO $$
DECLARE
    aws_polly_id UUID;
    elevenlabs_id UUID;
    voice1_id UUID;
    voice2_id UUID;
    voice3_id UUID;
BEGIN
    SELECT id INTO aws_polly_id FROM voice_providers WHERE name = 'aws_polly';
    SELECT id INTO elevenlabs_id FROM voice_providers WHERE name = 'elevenlabs';
    
    SELECT id INTO voice1_id FROM available_voices WHERE provider_id = aws_polly_id AND voice_name = 'Joanna' LIMIT 1;
    SELECT id INTO voice2_id FROM available_voices WHERE provider_id = aws_polly_id AND voice_name = 'Matthew' LIMIT 1;
    SELECT id INTO voice3_id FROM available_voices WHERE provider_id = elevenlabs_id LIMIT 1;
    
    -- 7. Populate enterprise_voice_preferences
    INSERT INTO enterprise_voice_preferences (
        enterprise_id, voice_agent_id, preferred_voice_id, backup_voice_id, voice_settings
    )
    SELECT 
        va.enterprise_id,
        va.id as voice_agent_id,
        CASE 
            WHEN random() > 0.6 THEN voice1_id
            WHEN random() > 0.3 THEN voice2_id
            ELSE voice3_id
        END as preferred_voice_id,
        CASE 
            WHEN random() > 0.5 THEN voice2_id
            ELSE voice1_id
        END as backup_voice_id,
        jsonb_build_object(
            'speed', 1.0 + (random() * 0.4 - 0.2), -- 0.8 to 1.2
            'pitch', 1.0 + (random() * 0.2 - 0.1), -- 0.9 to 1.1
            'volume', 0.8 + (random() * 0.2), -- 0.8 to 1.0
            'emphasis', CASE WHEN random() > 0.5 THEN 'moderate' ELSE 'strong' END
        ) as voice_settings
    FROM voice_agents va
    WHERE NOT EXISTS (
        SELECT 1 FROM enterprise_voice_preferences 
        WHERE enterprise_id = va.enterprise_id AND voice_agent_id = va.id
    );
END $$;

-- 8. Populate phone_number_usage_logs
INSERT INTO phone_number_usage_logs (
    enterprise_id, phone_number_id, voice_agent_id, usage_type, duration_seconds, cost, metadata
)
SELECT 
    pn.enterprise_id,
    pn.id as phone_number_id,
    va.id as voice_agent_id,
    CASE 
        WHEN random() > 0.7 THEN 'inbound_call'
        WHEN random() > 0.4 THEN 'outbound_call'
        WHEN random() > 0.2 THEN 'sms'
        ELSE 'mms'
    END as usage_type,
    CASE 
        WHEN random() > 0.5 THEN floor(random() * 600 + 30)::integer -- calls: 30-630 seconds
        ELSE NULL -- SMS/MMS don't have duration
    END as duration_seconds,
    (random() * 2 + 0.01)::numeric(10,4) as cost,
    jsonb_build_object(
        'destination', '+1' || (5000000000 + floor(random() * 999999999)::bigint)::text,
        'status', 'completed',
        'direction', CASE WHEN random() > 0.5 THEN 'inbound' ELSE 'outbound' END
    ) as metadata
FROM purchased_phone_numbers pn
JOIN voice_agents va ON va.enterprise_id = pn.enterprise_id
CROSS JOIN generate_series(1, 10) -- 10 usage logs per phone number
WHERE pn.status = 'active'
AND NOT EXISTS (
    SELECT 1 FROM phone_number_usage_logs WHERE phone_number_id = pn.id
)
LIMIT 100; -- Limit to 100 usage logs

-- 9. Populate account_balances (financial table)
INSERT INTO account_balances (
    enterprise_id, credits_balance, currency, auto_recharge_enabled, 
    auto_recharge_amount, auto_recharge_trigger, last_recharge_date
)
SELECT 
    e.id as enterprise_id,
    (random() * 5000 + 100)::numeric(10,2) as credits_balance, -- 100-5100 credits
    'USD' as currency,
    random() > 0.5 as auto_recharge_enabled,
    CASE 
        WHEN random() > 0.7 THEN 100.00
        WHEN random() > 0.4 THEN 50.00
        ELSE 25.00
    END as auto_recharge_amount,
    CASE 
        WHEN random() > 0.5 THEN 50.00
        ELSE 25.00
    END as auto_recharge_trigger,
    NOW() - (random() * interval '90 days') as last_recharge_date
FROM enterprises e
WHERE NOT EXISTS (
    SELECT 1 FROM account_balances WHERE enterprise_id = e.id
);

-- 10. Populate payment_transactions (financial table)
INSERT INTO payment_transactions (
    enterprise_id, razorpay_payment_id, razorpay_order_id, amount, currency,
    credits_purchased, status, payment_method, transaction_type, metadata
)
SELECT 
    e.id as enterprise_id,
    'pay_' || substring(md5(random()::text), 1, 14) as razorpay_payment_id,
    'order_' || substring(md5(random()::text), 1, 14) as razorpay_order_id,
    CASE 
        WHEN random() > 0.7 THEN 100.00
        WHEN random() > 0.4 THEN 50.00
        ELSE 25.00
    END as amount,
    'INR' as currency,
    CASE 
        WHEN random() > 0.7 THEN 10000.00
        WHEN random() > 0.4 THEN 5000.00
        ELSE 2500.00
    END as credits_purchased,
    CASE 
        WHEN random() > 0.9 THEN 'failed'
        WHEN random() > 0.1 THEN 'completed'
        ELSE 'pending'
    END as status,
    CASE 
        WHEN random() > 0.7 THEN 'card'
        WHEN random() > 0.4 THEN 'upi'
        WHEN random() > 0.2 THEN 'netbanking'
        ELSE 'wallet'
    END as payment_method,
    CASE 
        WHEN random() > 0.8 THEN 'auto_recharge'
        ELSE 'manual'
    END as transaction_type,
    jsonb_build_object(
        'customer_email', 'customer' || floor(random() * 1000) || '@example.com',
        'customer_phone', '+91' || (9000000000 + floor(random() * 999999999)::bigint)::text,
        'notes', 'Credit purchase for voice services'
    ) as metadata
FROM enterprises e
CROSS JOIN generate_series(1, 5) -- 5 transactions per enterprise
WHERE NOT EXISTS (
    SELECT 1 FROM payment_transactions WHERE enterprise_id = e.id
)
LIMIT 50; -- Limit to 50 transactions

-- 11. Populate credit_usage_logs (financial table)
INSERT INTO credit_usage_logs (
    enterprise_id, voice_agent_id, contact_id, credits_used, cost_per_credit,
    service_type, duration_seconds, call_id, metadata
)
SELECT 
    va.enterprise_id,
    va.id as voice_agent_id,
    c.id as contact_id,
    (random() * 10 + 0.1)::numeric(8,4) as credits_used, -- 0.1-10.1 credits
    0.01::numeric(8,4) as cost_per_credit,
    CASE 
        WHEN random() > 0.8 THEN 'sms'
        WHEN random() > 0.6 THEN 'whatsapp'
        ELSE 'voice_call'
    END as service_type,
    CASE 
        WHEN random() > 0.2 THEN floor(random() * 600 + 30)::integer -- calls: 30-630 seconds
        ELSE NULL -- SMS/WhatsApp don't have duration
    END as duration_seconds,
    'call_' || substring(md5(random()::text), 1, 16) as call_id,
    jsonb_build_object(
        'provider', CASE WHEN random() > 0.5 THEN 'twilio' ELSE 'plivo' END,
        'destination_country', 'US',
        'quality_score', floor(random() * 40 + 60)::integer
    ) as metadata
FROM voice_agents va
JOIN contacts c ON c.voice_agent_id = va.id
CROSS JOIN generate_series(1, 3) -- 3 usage logs per contact
WHERE NOT EXISTS (
    SELECT 1 FROM credit_usage_logs WHERE voice_agent_id = va.id
)
LIMIT 200; -- Limit to 200 usage logs

-- Update timestamps to make data more realistic
UPDATE call_logs SET ended_at = started_at + (duration * interval '1 second') WHERE ended_at < started_at;
UPDATE activity_logs SET created_at = NOW() - (random() * interval '60 days');
UPDATE phone_number_usage_logs SET created_at = NOW() - (random() * interval '30 days');
UPDATE credit_usage_logs SET created_at = NOW() - (random() * interval '30 days');
UPDATE payment_transactions SET created_at = NOW() - (random() * interval '90 days'), updated_at = created_at;

-- Summary of populated data
DO $$
DECLARE
    channels_count INTEGER;
    call_logs_count INTEGER;
    activity_logs_count INTEGER;
    purchased_numbers_count INTEGER;
    voice_prefs_count INTEGER;
    usage_logs_count INTEGER;
    balances_count INTEGER;
    transactions_count INTEGER;
    credit_logs_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO channels_count FROM channels;
    SELECT COUNT(*) INTO call_logs_count FROM call_logs;
    SELECT COUNT(*) INTO activity_logs_count FROM activity_logs;
    SELECT COUNT(*) INTO purchased_numbers_count FROM purchased_phone_numbers;
    SELECT COUNT(*) INTO voice_prefs_count FROM enterprise_voice_preferences;
    SELECT COUNT(*) INTO usage_logs_count FROM phone_number_usage_logs;
    SELECT COUNT(*) INTO balances_count FROM account_balances;
    SELECT COUNT(*) INTO transactions_count FROM payment_transactions;
    SELECT COUNT(*) INTO credit_logs_count FROM credit_usage_logs;
    
    RAISE NOTICE 'Test data populated successfully:';
    RAISE NOTICE '- Channels: %', channels_count;
    RAISE NOTICE '- Call Logs: %', call_logs_count;
    RAISE NOTICE '- Activity Logs: %', activity_logs_count;
    RAISE NOTICE '- Purchased Phone Numbers: %', purchased_numbers_count;
    RAISE NOTICE '- Voice Preferences: %', voice_prefs_count;
    RAISE NOTICE '- Phone Usage Logs: %', usage_logs_count;
    RAISE NOTICE '- Account Balances: %', balances_count;
    RAISE NOTICE '- Payment Transactions: %', transactions_count;
    RAISE NOTICE '- Credit Usage Logs: %', credit_logs_count;
END $$;