-- DrM Hope SaaS Platform Database Schema
-- Run this in your Supabase SQL editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enterprises table
CREATE TABLE IF NOT EXISTS enterprises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('super_admin', 'admin', 'user')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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

-- Create call_logs table (for future analytics)
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    duration INTEGER, -- in seconds
    status VARCHAR(50) CHECK (status IN ('completed', 'failed', 'in_progress')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create activity_logs table (for dashboard recent activity)
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON users(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_voice_agents_enterprise_id ON voice_agents(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_voice_agents_category ON voice_agents(category);
CREATE INDEX IF NOT EXISTS idx_contacts_voice_agent_id ON contacts(voice_agent_id);
CREATE INDEX IF NOT EXISTS idx_contacts_enterprise_id ON contacts(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);
CREATE INDEX IF NOT EXISTS idx_call_logs_enterprise_id ON call_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_created_at ON call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_enterprise_id ON activity_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE enterprises ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for enterprises
CREATE POLICY "Users can view enterprises they belong to" ON enterprises
    FOR SELECT USING (
        id IN (
            SELECT enterprise_id FROM users 
            WHERE email = auth.email() AND status = 'active'
        ) OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Admins can insert enterprises" ON enterprises
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Admins can update enterprises" ON enterprises
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Super admins can delete enterprises" ON enterprises
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role = 'super_admin'
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
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Admins can insert users" ON users
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Admins can update users" ON users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        ) OR email = auth.email()
    );

CREATE POLICY "Admins can delete users" ON users
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
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
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "Admins can manage voice agents" ON voice_agents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE email = auth.email() AND role IN ('super_admin', 'admin')
        )
    );

-- RLS Policies for call_logs
CREATE POLICY "Users can view call logs in their enterprise" ON call_logs
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

-- RLS Policies for activity_logs
CREATE POLICY "Users can view activity logs in their enterprise" ON activity_logs
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

-- Insert sample data
INSERT INTO enterprises (id, name, description, status) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'TechCorp Solutions', 'Leading technology solutions provider', 'active'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Healthcare Innovations', 'Advanced healthcare technology company', 'active'),
    ('550e8400-e29b-41d4-a716-446655440003', 'EduTech Partners', 'Educational technology solutions', 'pending');

-- Insert sample users (Note: You'll need to create these users in Supabase Auth first)
INSERT INTO users (id, email, name, role, status, enterprise_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440011', 'admin@drmhope.com', 'Dr. Murali B.K.', 'super_admin', 'active', NULL),
    ('550e8400-e29b-41d4-a716-446655440012', 'john.doe@techcorp.com', 'John Doe', 'admin', 'active', '550e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440013', 'jane.smith@healthcare.com', 'Jane Smith', 'user', 'active', '550e8400-e29b-41d4-a716-446655440002');

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

-- Insert sample activity logs
INSERT INTO activity_logs (enterprise_id, activity_type, description, status) VALUES
    ('550e8400-e29b-41d4-a716-446655440002', 'call_completed', 'Patient Registration Call', 'completed'),
    ('550e8400-e29b-41d4-a716-446655440002', 'call_completed', 'Discharge Follow-up Call', 'completed'),
    ('550e8400-e29b-41d4-a716-446655440001', 'call_in_progress', 'Referral Doctor Call', 'in_progress');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_enterprises_updated_at BEFORE UPDATE ON enterprises FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_voice_agents_updated_at BEFORE UPDATE ON voice_agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
