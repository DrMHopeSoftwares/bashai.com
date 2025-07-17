-- RelevanceAI Schema Updates for BhashAI Platform
-- Add support for RelevanceAI provider in voice_agents table

-- 1. Add provider_type column to voice_agents table if it doesn't exist
ALTER TABLE voice_agents 
ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50) DEFAULT 'bolna' CHECK (provider_type IN ('bolna', 'relevance_ai', 'openai_realtime'));

-- 2. Add RelevanceAI specific configuration columns
ALTER TABLE voice_agents 
ADD COLUMN IF NOT EXISTS relevance_ai_agent_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS relevance_ai_config JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS relevance_ai_session_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS provider_config JSONB DEFAULT '{}';

-- 3. Create index for faster lookups by provider type
CREATE INDEX IF NOT EXISTS idx_voice_agents_provider_type ON voice_agents(provider_type);
CREATE INDEX IF NOT EXISTS idx_voice_agents_relevance_ai_agent_id ON voice_agents(relevance_ai_agent_id);

-- 4. Create RelevanceAI sessions table for tracking conversations
CREATE TABLE IF NOT EXISTS relevance_ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    relevance_session_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'timeout')),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    enterprise_id UUID REFERENCES enterprises(id),
    
    UNIQUE(voice_agent_id, relevance_session_id)
);

-- 5. Create RelevanceAI conversation messages table
CREATE TABLE IF NOT EXISTS relevance_ai_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES relevance_ai_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('user', 'agent', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    enterprise_id UUID REFERENCES enterprises(id)
);

-- 6. Create RelevanceAI tools table for custom tools
CREATE TABLE IF NOT EXISTS relevance_ai_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tool_type VARCHAR(100) NOT NULL,
    config JSONB DEFAULT '{}',
    relevance_tool_id VARCHAR(255),
    enterprise_id UUID REFERENCES enterprises(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 7. Create RelevanceAI workflows table
CREATE TABLE IF NOT EXISTS relevance_ai_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(100) NOT NULL,
    config JSONB DEFAULT '{}',
    relevance_workflow_id VARCHAR(255),
    enterprise_id UUID REFERENCES enterprises(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 8. Create RelevanceAI integrations table
CREATE TABLE IF NOT EXISTS relevance_ai_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    integration_type VARCHAR(100) NOT NULL, -- slack, sheets, email, etc.
    config JSONB DEFAULT '{}',
    relevance_integration_id VARCHAR(255),
    enterprise_id UUID REFERENCES enterprises(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(enterprise_id, integration_type, name)
);

-- 9. Create junction table for voice_agents and RelevanceAI tools
CREATE TABLE IF NOT EXISTS voice_agent_relevance_tools (
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    tool_id UUID REFERENCES relevance_ai_tools(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (voice_agent_id, tool_id)
);

-- 10. Create junction table for voice_agents and RelevanceAI integrations
CREATE TABLE IF NOT EXISTS voice_agent_relevance_integrations (
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    integration_id UUID REFERENCES relevance_ai_integrations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (voice_agent_id, integration_id)
);

-- 11. Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_relevance_ai_sessions_voice_agent_id ON relevance_ai_sessions(voice_agent_id);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_sessions_enterprise_id ON relevance_ai_sessions(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_sessions_status ON relevance_ai_sessions(status);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_messages_session_id ON relevance_ai_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_messages_timestamp ON relevance_ai_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_tools_enterprise_id ON relevance_ai_tools(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_workflows_enterprise_id ON relevance_ai_workflows(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_relevance_ai_integrations_enterprise_id ON relevance_ai_integrations(enterprise_id);

-- 12. Create updated_at trigger for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
DROP TRIGGER IF EXISTS update_relevance_ai_sessions_updated_at ON relevance_ai_sessions;
CREATE TRIGGER update_relevance_ai_sessions_updated_at 
    BEFORE UPDATE ON relevance_ai_sessions 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_relevance_ai_tools_updated_at ON relevance_ai_tools;
CREATE TRIGGER update_relevance_ai_tools_updated_at 
    BEFORE UPDATE ON relevance_ai_tools 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_relevance_ai_workflows_updated_at ON relevance_ai_workflows;
CREATE TRIGGER update_relevance_ai_workflows_updated_at 
    BEFORE UPDATE ON relevance_ai_workflows 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_relevance_ai_integrations_updated_at ON relevance_ai_integrations;
CREATE TRIGGER update_relevance_ai_integrations_updated_at 
    BEFORE UPDATE ON relevance_ai_integrations 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 13. Enable Row Level Security (RLS) for enterprise isolation
ALTER TABLE relevance_ai_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE relevance_ai_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE relevance_ai_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE relevance_ai_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE relevance_ai_integrations ENABLE ROW LEVEL SECURITY;

-- 14. Create RLS policies for enterprise isolation
-- Sessions policies
CREATE POLICY relevance_ai_sessions_enterprise_isolation ON relevance_ai_sessions
    FOR ALL
    USING (enterprise_id = current_setting('app.current_enterprise_id')::UUID);

-- Messages policies  
CREATE POLICY relevance_ai_messages_enterprise_isolation ON relevance_ai_messages
    FOR ALL
    USING (enterprise_id = current_setting('app.current_enterprise_id')::UUID);

-- Tools policies
CREATE POLICY relevance_ai_tools_enterprise_isolation ON relevance_ai_tools
    FOR ALL
    USING (enterprise_id = current_setting('app.current_enterprise_id')::UUID);

-- Workflows policies
CREATE POLICY relevance_ai_workflows_enterprise_isolation ON relevance_ai_workflows
    FOR ALL
    USING (enterprise_id = current_setting('app.current_enterprise_id')::UUID);

-- Integrations policies
CREATE POLICY relevance_ai_integrations_enterprise_isolation ON relevance_ai_integrations
    FOR ALL
    USING (enterprise_id = current_setting('app.current_enterprise_id')::UUID);

-- 15. Create view for agent analytics including RelevanceAI data
CREATE OR REPLACE VIEW voice_agent_analytics AS
SELECT 
    va.id,
    va.name,
    va.provider_type,
    va.enterprise_id,
    va.created_at,
    CASE 
        WHEN va.provider_type = 'relevance_ai' THEN 
            (SELECT COUNT(*) FROM relevance_ai_sessions WHERE voice_agent_id = va.id)
        ELSE 
            (SELECT COUNT(*) FROM call_logs WHERE voice_agent_id = va.id)
    END as total_interactions,
    CASE 
        WHEN va.provider_type = 'relevance_ai' THEN 
            (SELECT COUNT(*) FROM relevance_ai_sessions WHERE voice_agent_id = va.id AND status = 'completed')
        ELSE 
            (SELECT COUNT(*) FROM call_logs WHERE voice_agent_id = va.id AND status = 'completed')
    END as successful_interactions,
    CASE 
        WHEN va.provider_type = 'relevance_ai' THEN 
            (SELECT AVG(EXTRACT(EPOCH FROM (ended_at - created_at))) 
             FROM relevance_ai_sessions 
             WHERE voice_agent_id = va.id AND ended_at IS NOT NULL)
        ELSE NULL
    END as avg_session_duration_seconds
FROM voice_agents va;

-- 16. Create function to migrate existing voice agents to include provider_type
CREATE OR REPLACE FUNCTION migrate_existing_voice_agents_provider()
RETURNS VOID AS $$
BEGIN
    -- Update existing voice agents to have 'bolna' as default provider
    UPDATE voice_agents 
    SET provider_type = 'bolna' 
    WHERE provider_type IS NULL;
    
    -- Log the migration
    RAISE NOTICE 'Updated % existing voice agents with default provider_type', 
        (SELECT COUNT(*) FROM voice_agents WHERE provider_type = 'bolna');
END;
$$ LANGUAGE plpgsql;

-- Run the migration
SELECT migrate_existing_voice_agents_provider();

-- 17. Insert sample RelevanceAI tools for common use cases
INSERT INTO relevance_ai_tools (name, description, tool_type, config, enterprise_id, created_by, relevance_tool_id) 
VALUES 
    ('Knowledge Base Search', 'Search and retrieve information from knowledge base', 'knowledge_search', 
     '{"search_type": "semantic", "max_results": 5}', 
     (SELECT id FROM enterprises LIMIT 1), 
     (SELECT id FROM users WHERE role = 'super_admin' LIMIT 1),
     'kb_search_001'),
    ('Appointment Scheduler', 'Schedule and manage appointments', 'calendar_integration',
     '{"calendar_provider": "google", "booking_window_days": 30}',
     (SELECT id FROM enterprises LIMIT 1),
     (SELECT id FROM users WHERE role = 'super_admin' LIMIT 1),
     'scheduler_001'),
    ('Email Notification', 'Send automated email notifications', 'email_automation',
     '{"template_engine": "mustache", "delivery_tracking": true}',
     (SELECT id FROM enterprises LIMIT 1),
     (SELECT id FROM users WHERE role = 'super_admin' LIMIT 1),
     'email_001')
ON CONFLICT DO NOTHING;

-- 18. Create function to get RelevanceAI agent configuration
CREATE OR REPLACE FUNCTION get_relevance_ai_config(agent_id UUID)
RETURNS JSONB AS $$
DECLARE
    config JSONB;
BEGIN
    SELECT 
        jsonb_build_object(
            'agent_id', relevance_ai_agent_id,
            'config', relevance_ai_config,
            'session_id', relevance_ai_session_id,
            'provider_config', provider_config,
            'tools', (
                SELECT jsonb_agg(jsonb_build_object(
                    'id', t.id,
                    'name', t.name,
                    'type', t.tool_type,
                    'relevance_id', t.relevance_tool_id
                ))
                FROM relevance_ai_tools t
                JOIN voice_agent_relevance_tools vart ON t.id = vart.tool_id
                WHERE vart.voice_agent_id = agent_id
            ),
            'integrations', (
                SELECT jsonb_agg(jsonb_build_object(
                    'id', i.id,
                    'name', i.name,
                    'type', i.integration_type,
                    'relevance_id', i.relevance_integration_id
                ))
                FROM relevance_ai_integrations i
                JOIN voice_agent_relevance_integrations vari ON i.id = vari.integration_id
                WHERE vari.voice_agent_id = agent_id
            )
        ) INTO config
    FROM voice_agents
    WHERE id = agent_id AND provider_type = 'relevance_ai';
    
    RETURN COALESCE(config, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- 19. Add comments for documentation
COMMENT ON TABLE relevance_ai_sessions IS 'Tracks RelevanceAI conversation sessions for voice agents';
COMMENT ON TABLE relevance_ai_messages IS 'Stores individual messages in RelevanceAI conversations';
COMMENT ON TABLE relevance_ai_tools IS 'Manages custom tools available for RelevanceAI agents';
COMMENT ON TABLE relevance_ai_workflows IS 'Stores RelevanceAI workflow configurations';
COMMENT ON TABLE relevance_ai_integrations IS 'Manages third-party integrations for RelevanceAI agents';

COMMENT ON COLUMN voice_agents.provider_type IS 'AI provider: bolna, relevance_ai, or openai_realtime';
COMMENT ON COLUMN voice_agents.relevance_ai_agent_id IS 'External RelevanceAI agent identifier';
COMMENT ON COLUMN voice_agents.relevance_ai_config IS 'RelevanceAI specific configuration and settings';
COMMENT ON COLUMN voice_agents.provider_config IS 'Provider-specific configuration for all providers';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ RelevanceAI schema update completed successfully!';
    RAISE NOTICE '📊 Tables created: relevance_ai_sessions, relevance_ai_messages, relevance_ai_tools, relevance_ai_workflows, relevance_ai_integrations';
    RAISE NOTICE '🔧 Voice agents table updated with provider support';
    RAISE NOTICE '🛡️  Row Level Security enabled for enterprise isolation';
    RAISE NOTICE '📈 Analytics view updated for multi-provider support';
END $$;