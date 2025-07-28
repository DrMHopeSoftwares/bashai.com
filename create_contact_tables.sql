-- Create voice_agents table (for Clinivoice integration)
CREATE TABLE IF NOT EXISTS voice_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL CHECK (category IN ('Inbound Calls', 'Outbound Calls', 'WhatsApp Messages')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused')),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create contacts table for agent-specific contact management
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone, voice_agent_id) -- Prevent duplicate phone numbers per agent
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_voice_agents_enterprise_id ON voice_agents(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_voice_agents_category ON voice_agents(category);
CREATE INDEX IF NOT EXISTS idx_contacts_voice_agent_id ON contacts(voice_agent_id);
CREATE INDEX IF NOT EXISTS idx_contacts_enterprise_id ON contacts(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);

-- Enable Row Level Security (RLS)
ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for voice_agents
CREATE POLICY "Users can view voice agents for their enterprise" ON voice_agents
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Users can insert voice agents for their enterprise" ON voice_agents
    FOR INSERT WITH CHECK (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Users can update voice agents for their enterprise" ON voice_agents
    FOR UPDATE USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Users can delete voice agents for their enterprise" ON voice_agents
    FOR DELETE USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

-- RLS Policies for contacts
CREATE POLICY "Users can view contacts for their enterprise" ON contacts
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Users can insert contacts for their enterprise" ON contacts
    FOR INSERT WITH CHECK (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Users can update contacts for their enterprise" ON contacts
    FOR UPDATE USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Users can delete contacts for their enterprise" ON contacts
    FOR DELETE USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

-- Insert sample voice agents
INSERT INTO voice_agents (id, title, description, url, category, status, enterprise_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440021', 'Patient Appointment Booking', 'AI assistant for scheduling patient appointments and managing calendar', 'https://api.clinivoice.com/voice/betser/appointments', 'Inbound Calls', 'active', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440022', 'Prescription Reminder Calls', 'Automated calls to remind patients about prescription refills', 'https://api.clinivoice.com/voice/betser/prescriptions', 'Outbound Calls', 'active', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440023', 'Lab Results Notification', 'WhatsApp messages to notify patients about lab results availability', 'https://api.clinivoice.com/whatsapp/betser/lab-results', 'WhatsApp Messages', 'active', '550e8400-e29b-41d4-a716-446655440002');

-- Insert sample contacts
INSERT INTO contacts (id, name, phone, status, voice_agent_id, enterprise_id) VALUES
    -- Contacts for Patient Appointment Booking (Inbound Calls)
    ('550e8400-e29b-41d4-a716-446655440031', 'pratik', '+917030281823', 'active', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440032', 'Murali', '+919373111709', 'inactive', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440033', 'gaesh', '+918552836916', 'active', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440002'),
    
    -- Contacts for Prescription Reminder Calls (Outbound Calls)
    ('550e8400-e29b-41d4-a716-446655440034', 'Shaib', '+917972096556', 'active', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440035', 'gaurav', '+919822202396', 'active', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440036', 'Toufiq', '+919168524623', 'inactive', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440037', 'priyanka', '+918806151882', 'active', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440002'),
    
    -- Contacts for Lab Results Notification (WhatsApp Messages)
    ('550e8400-e29b-41d4-a716-446655440038', 'vijay sharma', '+919770454591', 'active', '550e8400-e29b-41d4-a716-446655440023', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440039', 'Bindavan patel', '+917898491078', 'active', '550e8400-e29b-41d4-a716-446655440023', '550e8400-e29b-41d4-a716-446655440002'),
    ('550e8400-e29b-41d4-a716-446655440040', 'shailesh', '+917385188459', 'active', '550e8400-e29b-41d4-a716-446655440023', '550e8400-e29b-41d4-a716-446655440002');
