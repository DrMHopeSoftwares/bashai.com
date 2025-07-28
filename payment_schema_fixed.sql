-- Payment and Credit Management Schema for DrM Hope Platform
-- Fixed version that handles existing objects gracefully

-- Create account_balances table
CREATE TABLE IF NOT EXISTS account_balances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    credits_balance DECIMAL(10,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    auto_recharge_enabled BOOLEAN DEFAULT FALSE,
    auto_recharge_amount DECIMAL(10,2) DEFAULT 10.00,
    auto_recharge_trigger DECIMAL(10,2) DEFAULT 10.00,
    last_recharge_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(enterprise_id)
);

-- Create payment_transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    razorpay_payment_id VARCHAR(255) UNIQUE,
    razorpay_order_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    credits_purchased DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    payment_method VARCHAR(50),
    transaction_type VARCHAR(50) DEFAULT 'manual' CHECK (transaction_type IN ('manual', 'auto_recharge')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create credit_usage_logs table
CREATE TABLE IF NOT EXISTS credit_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    credits_used DECIMAL(8,4) NOT NULL,
    cost_per_credit DECIMAL(8,4) DEFAULT 0.01,
    service_type VARCHAR(50) DEFAULT 'voice_call' CHECK (service_type IN ('voice_call', 'sms', 'whatsapp')),
    duration_seconds INTEGER,
    call_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_account_balances_enterprise_id ON account_balances(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_enterprise_id ON payment_transactions(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_razorpay_id ON payment_transactions(razorpay_payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS idx_credit_usage_enterprise_id ON credit_usage_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_created_at ON credit_usage_logs(created_at);

-- Enable Row Level Security
ALTER TABLE account_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_usage_logs ENABLE ROW LEVEL SECURITY;

-- Insert default balance for existing enterprises
INSERT INTO account_balances (enterprise_id, credits_balance, auto_recharge_enabled, auto_recharge_amount, auto_recharge_trigger)
SELECT id, 1000.00, FALSE, 10.00, 10.00
FROM enterprises
WHERE NOT EXISTS (
    SELECT 1 FROM account_balances WHERE enterprise_id = enterprises.id
)
ON CONFLICT (enterprise_id) DO NOTHING;