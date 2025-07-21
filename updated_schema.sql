-- Updated DrM Hope SaaS Platform Database Schema
-- Enterprise → Organizations → Channels → Voice Agents → Contacts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enterprises table (Trial owners) - matches existing structure
CREATE TABLE IF NOT EXISTS enterprises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) DEFAULT 'trial' CHECK (type IN ('trial', 'premium', 'enterprise')),
    contact_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'trial', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id UUID
);

-- Create users table (Enterprise admins and users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('super_admin', 'enterprise_admin', 'org_admin', 'user')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create organizations table (Under each enterprise)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100) DEFAULT 'general' CHECK (type IN ('healthcare', 'retail', 'finance', 'education', 'general')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create channels table (Inbound, Outbound, WhatsApp for each organization)
CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL CHECK (name IN ('Inbound Calls', 'Outbound Calls', 'WhatsApp Messages')),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, organization_id) -- Each org has one of each channel type
);

-- Create voice_agents table (AI agents within channels)
CREATE TABLE IF NOT EXISTS voice_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused')),
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create contacts table (Agent-specific contacts)
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone, voice_agent_id) -- Prevent duplicate phone numbers per agent
);

-- Create call_logs table (for analytics)
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    phone_number VARCHAR(20),
    duration INTEGER, -- in seconds
    status VARCHAR(50) CHECK (status IN ('completed', 'failed', 'in_progress', 'missed')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create activity_logs table (for dashboard activity)
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON users(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_organizations_enterprise_id ON organizations(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_channels_organization_id ON channels(organization_id);
CREATE INDEX IF NOT EXISTS idx_voice_agents_channel_id ON voice_agents(channel_id);
CREATE INDEX IF NOT EXISTS idx_voice_agents_organization_id ON voice_agents(organization_id);
CREATE INDEX IF NOT EXISTS idx_voice_agents_enterprise_id ON voice_agents(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_contacts_voice_agent_id ON contacts(voice_agent_id);
CREATE INDEX IF NOT EXISTS idx_contacts_organization_id ON contacts(organization_id);
CREATE INDEX IF NOT EXISTS idx_contacts_enterprise_id ON contacts(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);
CREATE INDEX IF NOT EXISTS idx_call_logs_enterprise_id ON call_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_organization_id ON call_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_created_at ON call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_enterprise_id ON activity_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_organization_id ON activity_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE enterprises ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for enterprises
CREATE POLICY "Users can view their own enterprise" ON enterprises
    FOR SELECT USING (
        id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

CREATE POLICY "Enterprise admins can update their enterprise" ON enterprises
    FOR UPDATE USING (
        id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND role IN ('enterprise_admin', 'super_admin')
        )
    );

-- RLS Policies for users
CREATE POLICY "Users can view users in their enterprise" ON users
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        email = auth.email() OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

-- RLS Policies for organizations
CREATE POLICY "Users can view organizations in their enterprise" ON organizations
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

CREATE POLICY "Enterprise admins can manage organizations" ON organizations
    FOR ALL USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND role IN ('enterprise_admin', 'super_admin')
        )
    );

-- RLS Policies for channels
CREATE POLICY "Users can view channels in their enterprise" ON channels
    FOR SELECT USING (
        organization_id IN (
            SELECT id FROM organizations
            WHERE enterprise_id IN (
                SELECT enterprise_id FROM users
                WHERE email = auth.email() AND status = 'active'
            )
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

CREATE POLICY "Enterprise and org admins can manage channels" ON channels
    FOR ALL USING (
        organization_id IN (
            SELECT id FROM organizations
            WHERE enterprise_id IN (
                SELECT enterprise_id FROM users
                WHERE email = auth.email() AND role IN ('enterprise_admin', 'org_admin', 'super_admin')
            )
        )
    );

-- RLS Policies for voice_agents
CREATE POLICY "Users can view voice agents in their enterprise" ON voice_agents
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

CREATE POLICY "Users can manage voice agents in their enterprise" ON voice_agents
    FOR ALL USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

-- RLS Policies for contacts
CREATE POLICY "Users can view contacts in their enterprise" ON contacts
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

CREATE POLICY "Users can manage contacts in their enterprise" ON contacts
    FOR ALL USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

-- RLS Policies for call_logs and activity_logs (similar pattern)
CREATE POLICY "Users can view call logs in their enterprise" ON call_logs
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

CREATE POLICY "Users can view activity logs in their enterprise" ON activity_logs
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        ) OR
        EXISTS (
            SELECT 1 FROM users
            WHERE email = auth.email() AND role = 'super_admin'
        )
    );

-- Insert sample data
-- Sample Enterprise (Trial owner)
INSERT INTO enterprises (id, name, description, status, trial_start_date, trial_end_date) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'Hope', 'Hope Enterprise - AI Voice Solutions Trial', 'trial', NOW(), NOW() + INTERVAL '14 days');

-- Sample Enterprise Admin (Trial user)
INSERT INTO users (id, email, name, role, status, enterprise_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440011', 'admin@hope.com', 'Hope Admin', 'enterprise_admin', 'active', '550e8400-e29b-41d4-a716-446655440001');

-- Sample Organizations under Hope Enterprise
INSERT INTO organizations (id, name, description, type, status, enterprise_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440021', 'Ayushmann', 'Ayushmann Healthcare Services', 'healthcare', 'active', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440022', 'Raftaar', 'Raftaar Logistics Solutions', 'general', 'active', '550e8400-e29b-41d4-a716-446655440001');

-- Sample Channels for Ayushmann
INSERT INTO channels (id, name, description, status, organization_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440031', 'Inbound Calls', 'Handle incoming patient calls', 'active', '550e8400-e29b-41d4-a716-446655440021'),
    ('550e8400-e29b-41d4-a716-446655440032', 'Outbound Calls', 'Make calls to patients', 'active', '550e8400-e29b-41d4-a716-446655440021'),
    ('550e8400-e29b-41d4-a716-446655440033', 'WhatsApp Messages', 'Send automated WhatsApp messages', 'active', '550e8400-e29b-41d4-a716-446655440021');

-- Sample Channels for Raftaar
INSERT INTO channels (id, name, description, status, organization_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440034', 'Inbound Calls', 'Handle incoming customer calls', 'active', '550e8400-e29b-41d4-a716-446655440022'),
    ('550e8400-e29b-41d4-a716-446655440035', 'Outbound Calls', 'Make calls to customers', 'active', '550e8400-e29b-41d4-a716-446655440022'),
    ('550e8400-e29b-41d4-a716-446655440036', 'WhatsApp Messages', 'Send delivery notifications', 'active', '550e8400-e29b-41d4-a716-446655440022');

-- Sample Voice Agents for Ayushmann
INSERT INTO voice_agents (id, title, description, url, status, channel_id, organization_id, enterprise_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440041', 'Patient Appointment Booking', 'AI assistant for scheduling patient appointments', 'https://api.clinivoice.com/voice/ayushmann/appointments', 'active', '550e8400-e29b-41d4-a716-446655440031', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440042', 'Prescription Reminder Calls', 'Automated calls for prescription refills', 'https://api.clinivoice.com/voice/ayushmann/prescriptions', 'active', '550e8400-e29b-41d4-a716-446655440032', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440043', 'Lab Results Notification', 'WhatsApp notifications for lab results', 'https://api.clinivoice.com/whatsapp/ayushmann/lab-results', 'active', '550e8400-e29b-41d4-a716-446655440033', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001');

-- Sample Voice Agents for Raftaar
INSERT INTO voice_agents (id, title, description, url, status, channel_id, organization_id, enterprise_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440044', 'Customer Support', 'AI assistant for customer inquiries', 'https://api.clinivoice.com/voice/raftaar/support', 'active', '550e8400-e29b-41d4-a716-446655440034', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440045', 'Delivery Follow-up', 'Automated delivery status calls', 'https://api.clinivoice.com/voice/raftaar/delivery', 'active', '550e8400-e29b-41d4-a716-446655440035', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440046', 'Delivery Notifications', 'WhatsApp delivery updates', 'https://api.clinivoice.com/whatsapp/raftaar/delivery', 'active', '550e8400-e29b-41d4-a716-446655440036', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001');

-- Sample Contacts for Ayushmann Voice Agents
INSERT INTO contacts (id, name, phone, status, voice_agent_id, channel_id, organization_id, enterprise_id) VALUES
    -- Contacts for Patient Appointment Booking (Ayushmann - Inbound)
    ('550e8400-e29b-41d4-a716-446655440051', 'Dr. Pratik', '+917030281823', 'active', '550e8400-e29b-41d4-a716-446655440041', '550e8400-e29b-41d4-a716-446655440031', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440052', 'Nurse Murali', '+919373111709', 'inactive', '550e8400-e29b-41d4-a716-446655440041', '550e8400-e29b-41d4-a716-446655440031', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440053', 'Patient Gaesh', '+918552836916', 'active', '550e8400-e29b-41d4-a716-446655440041', '550e8400-e29b-41d4-a716-446655440031', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),

    -- Contacts for Prescription Reminder Calls (Ayushmann - Outbound)
    ('550e8400-e29b-41d4-a716-446655440054', 'Patient Shaib', '+917972096556', 'active', '550e8400-e29b-41d4-a716-446655440042', '550e8400-e29b-41d4-a716-446655440032', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440055', 'Patient Gaurav', '+919822202396', 'active', '550e8400-e29b-41d4-a716-446655440042', '550e8400-e29b-41d4-a716-446655440032', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440056', 'Patient Toufiq', '+919168524623', 'inactive', '550e8400-e29b-41d4-a716-446655440042', '550e8400-e29b-41d4-a716-446655440032', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),

    -- Contacts for Lab Results Notification (Ayushmann - WhatsApp)
    ('550e8400-e29b-41d4-a716-446655440057', 'Patient Vijay', '+919770454591', 'active', '550e8400-e29b-41d4-a716-446655440043', '550e8400-e29b-41d4-a716-446655440033', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440058', 'Patient Bindavan', '+917898491078', 'active', '550e8400-e29b-41d4-a716-446655440043', '550e8400-e29b-41d4-a716-446655440033', '550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440001');

-- Sample Contacts for Raftaar Voice Agents
INSERT INTO contacts (id, name, phone, status, voice_agent_id, channel_id, organization_id, enterprise_id) VALUES
    -- Contacts for Customer Support (Raftaar - Inbound)
    ('550e8400-e29b-41d4-a716-446655440061', 'Customer Rahul', '+918765432109', 'active', '550e8400-e29b-41d4-a716-446655440044', '550e8400-e29b-41d4-a716-446655440034', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440062', 'Customer Priya', '+919876543210', 'active', '550e8400-e29b-41d4-a716-446655440044', '550e8400-e29b-41d4-a716-446655440034', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),

    -- Contacts for Delivery Follow-up (Raftaar - Outbound)
    ('550e8400-e29b-41d4-a716-446655440063', 'Customer Amit', '+917654321098', 'active', '550e8400-e29b-41d4-a716-446655440045', '550e8400-e29b-41d4-a716-446655440035', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440064', 'Customer Neha', '+918543210987', 'active', '550e8400-e29b-41d4-a716-446655440045', '550e8400-e29b-41d4-a716-446655440035', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),

    -- Contacts for Delivery Notifications (Raftaar - WhatsApp)
    ('550e8400-e29b-41d4-a716-446655440065', 'Customer Suresh', '+919432108765', 'active', '550e8400-e29b-41d4-a716-446655440046', '550e8400-e29b-41d4-a716-446655440036', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440066', 'Customer Kavya', '+918321097654', 'active', '550e8400-e29b-41d4-a716-446655440046', '550e8400-e29b-41d4-a716-446655440036', '550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440001');
