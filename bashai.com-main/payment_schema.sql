-- Payment and Credit Management Schema for DrM Hope Platform
-- Add payment tables to support Razorpay integration

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

-- Create update triggers (with IF NOT EXISTS check)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_account_balances_updated_at'
    ) THEN
        CREATE TRIGGER update_account_balances_updated_at BEFORE UPDATE ON account_balances
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_payment_transactions_updated_at'
    ) THEN
        CREATE TRIGGER update_payment_transactions_updated_at BEFORE UPDATE ON payment_transactions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

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

-- RLS Policies for account_balances (with IF NOT EXISTS check)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'account_balances' AND policyname = 'Users can view their enterprise balance'
    ) THEN
        CREATE POLICY "Users can view their enterprise balance" ON account_balances
            FOR SELECT USING (
                enterprise_id IN (
                    SELECT enterprise_id FROM users
                    WHERE email = auth.email() AND status = 'active'
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'account_balances' AND policyname = 'Users can update their enterprise balance'
    ) THEN
        CREATE POLICY "Users can update their enterprise balance" ON account_balances
            FOR UPDATE USING (
                enterprise_id IN (
                    SELECT enterprise_id FROM users
                    WHERE email = auth.email() AND status = 'active'
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'account_balances' AND policyname = 'System can insert enterprise balances'
    ) THEN
        CREATE POLICY "System can insert enterprise balances" ON account_balances
            FOR INSERT WITH CHECK (
                enterprise_id IN (
                    SELECT enterprise_id FROM users
                    WHERE email = auth.email() AND status = 'active'
                )
            );
    END IF;
END $$;

-- RLS Policies for payment_transactions
CREATE POLICY "Users can view their enterprise transactions" ON payment_transactions
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

CREATE POLICY "System can insert payment transactions" ON payment_transactions
    FOR INSERT WITH CHECK (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

CREATE POLICY "System can update payment transactions" ON payment_transactions
    FOR UPDATE USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

-- RLS Policies for credit_usage_logs
CREATE POLICY "Users can view their enterprise credit usage" ON credit_usage_logs
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

CREATE POLICY "System can insert credit usage logs" ON credit_usage_logs
    FOR INSERT WITH CHECK (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

-- Insert default balance for existing enterprise
INSERT INTO account_balances (enterprise_id, credits_balance, auto_recharge_enabled, auto_recharge_amount, auto_recharge_trigger)
SELECT id, 1000.00, FALSE, 10.00, 10.00
FROM enterprises
WHERE NOT EXISTS (
    SELECT 1 FROM account_balances WHERE enterprise_id = enterprises.id
);

-- Create function to check and trigger auto-recharge
CREATE OR REPLACE FUNCTION check_auto_recharge()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if auto-recharge is enabled and balance is below trigger
    IF EXISTS (
        SELECT 1 FROM account_balances 
        WHERE enterprise_id = NEW.enterprise_id 
        AND auto_recharge_enabled = TRUE
        AND (credits_balance - NEW.credits_used) <= auto_recharge_trigger
    ) THEN
        -- Log that auto-recharge should be triggered
        INSERT INTO payment_transactions (
            enterprise_id,
            amount,
            credits_purchased,
            status,
            transaction_type,
            metadata
        )
        SELECT 
            enterprise_id,
            auto_recharge_amount,
            auto_recharge_amount * 100, -- 1 USD = 100 credits
            'pending',
            'auto_recharge',
            jsonb_build_object('triggered_by', 'low_balance', 'trigger_amount', auto_recharge_trigger)
        FROM account_balances
        WHERE enterprise_id = NEW.enterprise_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-recharge check
CREATE TRIGGER trigger_auto_recharge_check
    AFTER INSERT ON credit_usage_logs
    FOR EACH ROW
    EXECUTE FUNCTION check_auto_recharge();