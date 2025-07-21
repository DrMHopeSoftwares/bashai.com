-- Create dedicated table for storing Bolna AI agents
-- This table will store all Bolna agent information and link to our voice_agents

-- Create bolna_agents table
CREATE TABLE IF NOT EXISTS bolna_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bolna_agent_id VARCHAR(255) NOT NULL UNIQUE, -- Bolna AI agent ID
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) DEFAULT 'voice',
    description TEXT,
    prompt TEXT,
    welcome_message TEXT,
    voice VARCHAR(100),
    language VARCHAR(10),
    max_duration INTEGER DEFAULT 300,
    hangup_after INTEGER DEFAULT 30,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused')),
    
    -- Link to our internal voice_agents table
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE SET NULL,
    
    -- Link to phone number
    phone_number VARCHAR(20),
    
    -- User/Organization info
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    
    -- Bolna API response data (store full response for debugging)
    bolna_response JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_bolna_agents_bolna_agent_id ON bolna_agents(bolna_agent_id);
CREATE INDEX IF NOT EXISTS idx_bolna_agents_phone_number ON bolna_agents(phone_number);
CREATE INDEX IF NOT EXISTS idx_bolna_agents_user_id ON bolna_agents(user_id);
CREATE INDEX IF NOT EXISTS idx_bolna_agents_enterprise_id ON bolna_agents(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_bolna_agents_status ON bolna_agents(status);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bolna_agents_updated_at 
    BEFORE UPDATE ON bolna_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for clarity
COMMENT ON TABLE bolna_agents IS 'Store Bolna AI agents created via Bolna API';
COMMENT ON COLUMN bolna_agents.bolna_agent_id IS 'Unique agent ID returned from Bolna API';
COMMENT ON COLUMN bolna_agents.voice_agent_id IS 'Link to internal voice_agents table';
COMMENT ON COLUMN bolna_agents.bolna_response IS 'Full JSON response from Bolna API for debugging';

-- Show the table structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'bolna_agents' 
ORDER BY ordinal_position;
