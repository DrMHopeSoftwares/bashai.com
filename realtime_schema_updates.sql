-- OpenAI Realtime API Database Schema Updates
-- Add tables for tracking realtime voice sessions and usage

-- Table for realtime voice sessions
CREATE TABLE IF NOT EXISTS realtime_voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    voice_agent_id UUID,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    openai_session_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    
    -- Session configuration
    voice_model VARCHAR(100) DEFAULT 'alloy',
    language VARCHAR(10) DEFAULT 'en-US',
    instructions TEXT,
    
    -- Session metrics
    duration_seconds INTEGER DEFAULT 0,
    audio_input_duration_seconds INTEGER DEFAULT 0,
    audio_output_duration_seconds INTEGER DEFAULT 0,
    transcript_length INTEGER DEFAULT 0,
    
    -- Billing and usage
    api_calls_count INTEGER DEFAULT 0,
    estimated_cost_usd DECIMAL(10, 4) DEFAULT 0.00,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints (removed foreign keys due to potential type mismatches)
    -- Foreign keys can be added later once table structures are confirmed
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_realtime_sessions_user_id ON realtime_voice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_realtime_sessions_status ON realtime_voice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_realtime_sessions_started_at ON realtime_voice_sessions(started_at);

-- Table for conversation transcripts
CREATE TABLE IF NOT EXISTS realtime_conversation_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    
    -- Message details
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text', -- 'text', 'audio', 'function_call'
    
    -- Audio metadata (if applicable)
    audio_duration_ms INTEGER,
    audio_format VARCHAR(20),
    
    -- Timing
    message_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sequence_number INTEGER NOT NULL,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraint removed due to potential type issues
    -- CONSTRAINT fk_transcripts_session FOREIGN KEY (session_id) REFERENCES realtime_voice_sessions(id) ON DELETE CASCADE
);

-- Index for conversation retrieval
CREATE INDEX IF NOT EXISTS idx_transcripts_session_id ON realtime_conversation_transcripts(session_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_sequence ON realtime_conversation_transcripts(session_id, sequence_number);

-- Table for realtime API usage tracking
CREATE TABLE IF NOT EXISTS realtime_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,
    
    -- Usage details
    usage_type VARCHAR(50) NOT NULL, -- 'audio_input', 'audio_output', 'text_generation'
    quantity INTEGER NOT NULL, -- duration in seconds, tokens, etc.
    unit VARCHAR(20) NOT NULL, -- 'seconds', 'tokens', 'characters'
    
    -- Cost calculation
    rate_per_unit DECIMAL(10, 6) DEFAULT 0.000000,
    total_cost_usd DECIMAL(10, 4) DEFAULT 0.00,
    
    -- Billing info
    is_trial BOOLEAN DEFAULT FALSE,
    enterprise_id UUID,
    
    -- Timestamps
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints removed due to potential type issues
    -- CONSTRAINT fk_realtime_usage_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    -- CONSTRAINT fk_realtime_usage_session FOREIGN KEY (session_id) REFERENCES realtime_voice_sessions(id) ON DELETE SET NULL
);

-- Index for usage queries
CREATE INDEX IF NOT EXISTS idx_realtime_usage_user_id ON realtime_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_realtime_usage_session_id ON realtime_usage_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_realtime_usage_logged_at ON realtime_usage_logs(logged_at);

-- Add realtime capabilities to voice_agents table
ALTER TABLE voice_agents 
ADD COLUMN IF NOT EXISTS supports_realtime BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS realtime_config JSONB DEFAULT '{}';

-- Update existing voice agents to support realtime
UPDATE voice_agents 
SET supports_realtime = TRUE,
    realtime_config = jsonb_build_object(
        'enabled', true,
        'voice_model', 'alloy',
        'language', 'hi-IN',
        'max_session_duration_minutes', 30
    )
WHERE configuration->>'provider' = 'bolna' OR configuration IS NULL;

-- Create trial_limits table if it doesn't exist
CREATE TABLE IF NOT EXISTS trial_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) UNIQUE NOT NULL,
    daily_limit INTEGER DEFAULT 0,
    monthly_limit INTEGER DEFAULT 0,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add realtime trial limits
INSERT INTO trial_limits (resource_type, daily_limit, monthly_limit, description, created_at, updated_at)
VALUES 
    ('realtime_minutes', 30, 300, 'Daily and monthly limits for realtime voice session minutes', NOW(), NOW()),
    ('realtime_sessions', 10, 100, 'Daily and monthly limits for number of realtime voice sessions', NOW(), NOW())
ON CONFLICT (resource_type) DO NOTHING;

-- Table for realtime voice model configurations
CREATE TABLE IF NOT EXISTS realtime_voice_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    
    -- Model capabilities
    supported_languages JSONB DEFAULT '[]',
    voice_options JSONB DEFAULT '[]',
    max_session_duration_minutes INTEGER DEFAULT 60,
    
    -- Pricing (per minute)
    cost_per_minute_usd DECIMAL(10, 4) DEFAULT 0.0600,
    
    -- Model status
    is_active BOOLEAN DEFAULT TRUE,
    is_beta BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    description TEXT,
    provider VARCHAR(50) DEFAULT 'openai',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert OpenAI realtime models
INSERT INTO realtime_voice_models (
    model_name, display_name, supported_languages, voice_options, 
    cost_per_minute_usd, is_beta, description
) VALUES 
(
    'gpt-4o-realtime-preview',
    'GPT-4o Realtime (Preview)',
    '["en-US", "hi-IN", "es-ES", "fr-FR", "de-DE", "ja-JP", "ko-KR", "pt-BR", "zh-CN"]',
    '["alloy", "echo", "fable", "onyx", "nova", "shimmer"]',
    0.0600,
    TRUE,
    'OpenAI GPT-4o with real-time speech-to-speech capabilities. Supports multiple languages and voices.'
)
ON CONFLICT (model_name) DO NOTHING;

-- Function to update session duration
CREATE OR REPLACE FUNCTION update_realtime_session_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.ended_at - NEW.started_at));
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update duration
DROP TRIGGER IF EXISTS trigger_update_realtime_session_duration ON realtime_voice_sessions;
CREATE TRIGGER trigger_update_realtime_session_duration
    BEFORE UPDATE ON realtime_voice_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_realtime_session_duration();

-- Row Level Security (RLS) policies
ALTER TABLE realtime_voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE realtime_conversation_transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE realtime_usage_logs ENABLE ROW LEVEL SECURITY;

-- Policies for realtime_voice_sessions
CREATE POLICY "Users can view their own realtime sessions" ON realtime_voice_sessions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own realtime sessions" ON realtime_voice_sessions
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own realtime sessions" ON realtime_voice_sessions
    FOR UPDATE USING (user_id = auth.uid());

-- Policies for realtime_conversation_transcripts
CREATE POLICY "Users can view transcripts from their sessions" ON realtime_conversation_transcripts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM realtime_voice_sessions rvs 
            WHERE rvs.id = session_id AND rvs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert transcripts to their sessions" ON realtime_conversation_transcripts
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM realtime_voice_sessions rvs 
            WHERE rvs.id = session_id AND rvs.user_id = auth.uid()
        )
    );

-- Policies for realtime_usage_logs
CREATE POLICY "Users can view their own usage logs" ON realtime_usage_logs
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Service can insert usage logs" ON realtime_usage_logs
    FOR INSERT WITH CHECK (true);

-- Grant permissions for application user
GRANT SELECT, INSERT, UPDATE ON realtime_voice_sessions TO authenticated;
GRANT SELECT, INSERT ON realtime_conversation_transcripts TO authenticated;
GRANT SELECT, INSERT ON realtime_usage_logs TO authenticated;
GRANT SELECT ON realtime_voice_models TO authenticated;

-- Create view for session analytics
CREATE OR REPLACE VIEW realtime_session_analytics AS
SELECT 
    user_id,
    DATE(started_at) as session_date,
    COUNT(*) as total_sessions,
    SUM(duration_seconds) as total_duration_seconds,
    AVG(duration_seconds) as avg_duration_seconds,
    SUM(estimated_cost_usd) as total_cost_usd,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_sessions,
    COUNT(*) FILTER (WHERE status = 'error') as error_sessions
FROM realtime_voice_sessions
GROUP BY user_id, DATE(started_at)
ORDER BY session_date DESC;

-- Grant access to analytics view
GRANT SELECT ON realtime_session_analytics TO authenticated;