# Supabase Database Tables List

This document provides a comprehensive list of all tables in the DrM Hope SaaS Platform database.

## Database Connection
- **URL**: https://ymvfueudlippmfeqdqro.supabase.co
- **Environment**: Production

## Core Tables (Currently Accessible)

### 1. **enterprises**
- Primary table for trial owners/enterprise accounts
- Columns: id, name, description, status, type, contact_email, owner_id, created_at, updated_at

### 2. **users**
- User accounts within enterprises
- Columns: id, email, name, role, status, enterprise_id, created_at, updated_at

### 3. **organizations**
- Organizations under each enterprise (e.g., "Ayushmann", "Raftaar")
- Columns: id, name, description, type, status, enterprise_id, created_at, updated_at

### 4. **channels**
- Communication channels for each organization (Inbound Calls, Outbound Calls, WhatsApp Messages)
- Columns: id, name, description, status, organization_id, configuration, created_at, updated_at

### 5. **voice_agents**
- AI voice agents within channels
- Columns: id, title, description, url, status, channel_id, organization_id, enterprise_id, configuration, created_at, updated_at

### 6. **contacts**
- Agent-specific contacts for voice agents
- Columns: id, name, phone, status, voice_agent_id, channel_id, organization_id, enterprise_id, created_at, updated_at

## Additional Tables (From Schema Files)

### Analytics & Logging Tables

### 7. **call_logs**
- Records of all calls made/received
- Columns: id, voice_agent_id, contact_id, phone_number, duration, status, organization_id, enterprise_id, created_at

### 8. **activity_logs**
- Dashboard activity tracking
- Columns: id, enterprise_id, organization_id, user_id, activity_type, description, status, created_at

### Payment & Credits Tables

### 9. **account_balances**
- Enterprise credit balances and auto-recharge settings
- Columns: id, enterprise_id, credits_balance, currency, auto_recharge_enabled, auto_recharge_amount, auto_recharge_trigger, last_recharge_date, created_at, updated_at

### 10. **payment_transactions**
- Payment history and transactions
- Columns: id, enterprise_id, razorpay_payment_id, razorpay_order_id, amount, currency, credits_purchased, status, payment_method, transaction_type, metadata, created_at, updated_at

### 11. **credit_usage_logs**
- Detailed credit consumption tracking
- Columns: id, enterprise_id, voice_agent_id, contact_id, credits_used, cost_per_credit, service_type, duration_seconds, call_id, metadata, created_at

### Phone & Voice Provider Tables

### 12. **phone_number_providers**
- Available phone number providers (Plivo, Twilio, Telnyx)
- Columns: id, name, api_endpoint, api_key_required, supported_countries, pricing_model, status, created_at, updated_at

### 13. **purchased_phone_numbers**
- Phone numbers purchased by enterprises
- Columns: id, enterprise_id, phone_number, country_code, country_name, provider_id, provider_phone_id, monthly_cost, setup_cost, status, capabilities, purchased_at, expires_at, created_at, updated_at

### 14. **voice_providers**
- Text-to-speech providers (AWS Polly, ElevenLabs, etc.)
- Columns: id, name, display_name, api_endpoint, api_key_required, supported_languages, voice_quality, pricing_per_character, status, created_at, updated_at

### 15. **available_voices**
- Available voices from each provider
- Columns: id, provider_id, voice_id, voice_name, language_code, language_name, accent, gender, age_group, voice_quality, sample_text, sample_audio_url, pricing_tier, status, metadata, created_at, updated_at

### 16. **enterprise_voice_preferences**
- Voice preferences for each enterprise/agent
- Columns: id, enterprise_id, voice_agent_id, preferred_voice_id, backup_voice_id, voice_settings, created_at, updated_at

### 17. **phone_number_usage_logs**
- Phone number usage tracking
- Columns: id, enterprise_id, phone_number_id, voice_agent_id, usage_type, duration_seconds, cost, metadata, created_at

### Missing/Inaccessible Tables

The following tables were checked but not found or are inaccessible:
- **contact_lists** - Might not be created yet
- **profiles** - Might not be created yet

## Database Hierarchy

```
Enterprise (Trial Owner)
├── Organizations (e.g., "Ayushmann", "Raftaar")
│   ├── Channels (Inbound Calls, Outbound Calls, WhatsApp)
│   │   ├── Voice Agents (AI assistants)
│   │   │   └── Contacts (Agent-specific contacts)
│   │   │   └── Call Logs
│   │   └── Phone Numbers
│   └── Voice Preferences
├── Users (Enterprise users)
├── Account Balance
├── Payment Transactions
└── Credit Usage Logs
```

## Row Level Security (RLS)

All tables have Row Level Security enabled with policies that ensure:
- Users can only access data within their enterprise
- Super admins have access to all data
- Enterprise admins can manage their enterprise data
- Regular users have read access to their enterprise data

## Indexes

Performance indexes are created on:
- Foreign key columns (enterprise_id, organization_id, etc.)
- Email addresses
- Phone numbers
- Timestamps (created_at)
- Status columns

## Triggers

- All tables with `updated_at` columns have triggers to automatically update the timestamp on modifications
- Auto-recharge trigger for payment processing when credits are low