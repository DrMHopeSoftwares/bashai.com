-- Phone Number and Voice Management Schema for DrM Hope Platform
-- Fixed version without update_updated_at_column() dependency

-- First, create the update function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create phone_number_providers table
CREATE TABLE IF NOT EXISTS phone_number_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    api_endpoint VARCHAR(500),
    api_key_required BOOLEAN DEFAULT TRUE,
    supported_countries JSONB DEFAULT '[]',
    pricing_model JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create purchased_phone_numbers table
CREATE TABLE IF NOT EXISTS purchased_phone_numbers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    provider_id UUID REFERENCES phone_number_providers(id) ON DELETE RESTRICT,
    provider_phone_id VARCHAR(255), -- Provider's internal ID for the number
    monthly_cost DECIMAL(10,2) DEFAULT 0.00,
    setup_cost DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    capabilities JSONB DEFAULT '{}', -- voice, sms, mms capabilities
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(phone_number, provider_id)
);

-- Create voice_providers table
CREATE TABLE IF NOT EXISTS voice_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(500),
    api_key_required BOOLEAN DEFAULT TRUE,
    supported_languages JSONB DEFAULT '[]',
    voice_quality VARCHAR(50) DEFAULT 'standard' CHECK (voice_quality IN ('standard', 'premium', 'neural')),
    pricing_per_character DECIMAL(8,6) DEFAULT 0.0001,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create available_voices table
CREATE TABLE IF NOT EXISTS available_voices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID REFERENCES voice_providers(id) ON DELETE CASCADE,
    voice_id VARCHAR(100) NOT NULL, -- Provider's voice ID
    voice_name VARCHAR(100) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    language_name VARCHAR(100) NOT NULL,
    accent VARCHAR(100),
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'neutral')),
    age_group VARCHAR(50) DEFAULT 'adult' CHECK (age_group IN ('child', 'adult', 'elderly')),
    voice_quality VARCHAR(50) DEFAULT 'standard' CHECK (voice_quality IN ('standard', 'premium', 'neural')),
    sample_text TEXT,
    sample_audio_url VARCHAR(500),
    pricing_tier VARCHAR(50) DEFAULT 'standard',
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider_id, voice_id)
);

-- Create enterprise_voice_preferences table
CREATE TABLE IF NOT EXISTS enterprise_voice_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE CASCADE,
    preferred_voice_id UUID REFERENCES available_voices(id) ON DELETE SET NULL,
    backup_voice_id UUID REFERENCES available_voices(id) ON DELETE SET NULL,
    voice_settings JSONB DEFAULT '{}', -- speed, pitch, volume settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(enterprise_id, voice_agent_id)
);

-- Create phone_number_usage_logs table
CREATE TABLE IF NOT EXISTS phone_number_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    phone_number_id UUID REFERENCES purchased_phone_numbers(id) ON DELETE CASCADE,
    voice_agent_id UUID REFERENCES voice_agents(id) ON DELETE SET NULL,
    usage_type VARCHAR(50) DEFAULT 'outbound_call' CHECK (usage_type IN ('outbound_call', 'inbound_call', 'sms', 'mms')),
    duration_seconds INTEGER,
    cost DECIMAL(10,4) DEFAULT 0.0000,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create update triggers (now that the function exists)
DROP TRIGGER IF EXISTS update_phone_number_providers_updated_at ON phone_number_providers;
CREATE TRIGGER update_phone_number_providers_updated_at BEFORE UPDATE ON phone_number_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_purchased_phone_numbers_updated_at ON purchased_phone_numbers;
CREATE TRIGGER update_purchased_phone_numbers_updated_at BEFORE UPDATE ON purchased_phone_numbers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_voice_providers_updated_at ON voice_providers;
CREATE TRIGGER update_voice_providers_updated_at BEFORE UPDATE ON voice_providers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_available_voices_updated_at ON available_voices;
CREATE TRIGGER update_available_voices_updated_at BEFORE UPDATE ON available_voices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_enterprise_voice_preferences_updated_at ON enterprise_voice_preferences;
CREATE TRIGGER update_enterprise_voice_preferences_updated_at BEFORE UPDATE ON enterprise_voice_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_purchased_phone_numbers_enterprise_id ON purchased_phone_numbers(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_purchased_phone_numbers_phone_number ON purchased_phone_numbers(phone_number);
CREATE INDEX IF NOT EXISTS idx_purchased_phone_numbers_country_code ON purchased_phone_numbers(country_code);
CREATE INDEX IF NOT EXISTS idx_available_voices_provider_id ON available_voices(provider_id);
CREATE INDEX IF NOT EXISTS idx_available_voices_language_code ON available_voices(language_code);
CREATE INDEX IF NOT EXISTS idx_available_voices_gender ON available_voices(gender);
CREATE INDEX IF NOT EXISTS idx_enterprise_voice_preferences_enterprise_id ON enterprise_voice_preferences(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_phone_number_usage_logs_enterprise_id ON phone_number_usage_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_phone_number_usage_logs_created_at ON phone_number_usage_logs(created_at);

-- Enable Row Level Security
ALTER TABLE phone_number_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchased_phone_numbers ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE available_voices ENABLE ROW LEVEL SECURITY;
ALTER TABLE enterprise_voice_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE phone_number_usage_logs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist to avoid conflicts
DROP POLICY IF EXISTS "Users can view their enterprise phone numbers" ON purchased_phone_numbers;
DROP POLICY IF EXISTS "Users can manage their enterprise phone numbers" ON purchased_phone_numbers;
DROP POLICY IF EXISTS "Users can view their enterprise voice preferences" ON enterprise_voice_preferences;
DROP POLICY IF EXISTS "Users can manage their enterprise voice preferences" ON enterprise_voice_preferences;
DROP POLICY IF EXISTS "Users can view their enterprise phone usage" ON phone_number_usage_logs;
DROP POLICY IF EXISTS "Public can view phone number providers" ON phone_number_providers;
DROP POLICY IF EXISTS "Public can view voice providers" ON voice_providers;
DROP POLICY IF EXISTS "Public can view available voices" ON available_voices;

-- RLS Policies for purchased_phone_numbers
CREATE POLICY "Users can view their enterprise phone numbers" ON purchased_phone_numbers
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

CREATE POLICY "Users can manage their enterprise phone numbers" ON purchased_phone_numbers
    FOR ALL USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

-- RLS Policies for enterprise_voice_preferences
CREATE POLICY "Users can view their enterprise voice preferences" ON enterprise_voice_preferences
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

CREATE POLICY "Users can manage their enterprise voice preferences" ON enterprise_voice_preferences
    FOR ALL USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

-- RLS Policies for phone_number_usage_logs
CREATE POLICY "Users can view their enterprise phone usage" ON phone_number_usage_logs
    FOR SELECT USING (
        enterprise_id IN (
            SELECT enterprise_id FROM users
            WHERE email = auth.email() AND status = 'active'
        )
    );

-- Allow public read access to providers and voices for browsing
CREATE POLICY "Public can view phone number providers" ON phone_number_providers
    FOR SELECT USING (status = 'active');

CREATE POLICY "Public can view voice providers" ON voice_providers
    FOR SELECT USING (status = 'active');

CREATE POLICY "Public can view available voices" ON available_voices
    FOR SELECT USING (status = 'active');

-- Insert default phone number providers (with conflict handling)
INSERT INTO phone_number_providers (name, api_endpoint, supported_countries, pricing_model) 
VALUES
('Plivo', 'https://api.plivo.com/v1', 
 '["US", "UK", "CA", "AU", "IN", "DE", "FR", "ES", "IT", "NL", "BE", "SE", "NO", "DK", "FI"]',
 '{"monthly_cost": 5.0, "setup_cost": 0.0, "per_minute": 0.02}'),
('Twilio', 'https://api.twilio.com/2010-04-01', 
 '["US", "UK", "CA", "AU", "IN", "DE", "FR", "ES", "IT", "NL", "BE", "SE", "NO", "DK", "FI", "JP", "SG", "HK"]',
 '{"monthly_cost": 1.0, "setup_cost": 0.0, "per_minute": 0.0125}'),
('Telnyx', 'https://api.telnyx.com/v2', 
 '["US", "UK", "CA", "AU", "IN", "DE", "FR", "ES", "IT", "NL", "BE", "SE", "NO", "DK", "FI"]',
 '{"monthly_cost": 2.0, "setup_cost": 0.0, "per_minute": 0.01}')
ON CONFLICT (name) DO NOTHING;

-- Insert default voice providers (with conflict handling)
INSERT INTO voice_providers (name, display_name, api_endpoint, supported_languages, voice_quality, pricing_per_character) 
VALUES
('aws_polly', 'AWS Polly', 'https://polly.amazonaws.com', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"]',
 'neural', 0.000016),
('elevenlabs', 'ElevenLabs', 'https://api.elevenlabs.io/v1', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"]',
 'premium', 0.0003),
('deepgram', 'Deepgram', 'https://api.deepgram.com/v1', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR"]',
 'neural', 0.000012),
('azure_speech', 'Azure Speech', 'https://speech.microsoft.com/cognitiveservices/v1', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"]',
 'neural', 0.000020),
('cartesia', 'Cartesia', 'https://api.cartesia.ai/tts', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR"]',
 'premium', 0.000025),
('rime', 'Rime', 'https://api.rime.ai/v1', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE", "it-IT"]',
 'neural', 0.000018),
('smallest', 'Smallest AI', 'https://api.smallest.ai/v1', 
 '["en-US", "en-GB", "en-AU", "en-IN", "hi-IN", "es-ES", "fr-FR", "de-DE"]',
 'standard', 0.000010),
('sarvam', 'Sarvam AI', 'https://api.sarvam.ai/text-to-speech', 
 '["hi-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "gu-IN", "bn-IN", "mr-IN", "pa-IN"]',
 'neural', 0.000015)
ON CONFLICT (name) DO NOTHING;

-- Insert sample voices for AWS Polly
INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'Joanna', 'Joanna', 'en-US', 'English (United States)', 'United States', 'female', 'neural', 'This is the text you can play using Joanna'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'Matthew', 'Matthew', 'en-US', 'English (United States)', 'United States', 'male', 'neural', 'This is the text you can play using Matthew'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'Amy', 'Amy', 'en-GB', 'English (United Kingdom)', 'British', 'female', 'neural', 'This is the text you can play using Amy'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'Aditi', 'Aditi', 'hi-IN', 'Hindi (India)', 'Indian', 'female', 'neural', 'This is the text you can play using Aditi'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

-- Insert sample voices for ElevenLabs
INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'EXAVITQu4vr4xnSDxMaL', 'Bella', 'en-US', 'English (United States)', 'American', 'female', 'premium', 'This is the text you can play using Bella'
FROM voice_providers p WHERE p.name = 'elevenlabs'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'ErXwobaYiN019PkySvjV', 'Antoni', 'en-US', 'English (United States)', 'American', 'male', 'premium', 'This is the text you can play using Antoni'
FROM voice_providers p WHERE p.name = 'elevenlabs'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

-- Insert sample voices for other providers
INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'maya-young-female', 'Maya - Young Australian Female', 'en-AU', 'English (Australia)', 'Australian', 'female', 'neural', 'This is the text you can play using Maya - Young Australian Female'
FROM voice_providers p WHERE p.name = 'elevenlabs'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'gregory', 'Gregory', 'en-US', 'English (United States)', 'American', 'male', 'neural', 'This is the text you can play using Gregory'
FROM voice_providers p WHERE p.name = 'elevenlabs'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

-- Add more sample voices for different providers and languages
INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'kevin', 'Kevin', 'en-US', 'English (United States)', 'American', 'male', 'neural', 'This is the text you can play using Kevin'
FROM voice_providers p WHERE p.name = 'elevenlabs'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'filiz', 'Filiz', 'tr-TR', 'Turkish (Turkey)', 'Turkish', 'female', 'neural', 'This is the text you can play using Filiz'
FROM voice_providers p WHERE p.name = 'azure_speech'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'elin', 'Elin', 'sv-SE', 'Swedish', 'Swedish', 'female', 'neural', 'This is the text you can play using Elin'
FROM voice_providers p WHERE p.name = 'azure_speech'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'astrid', 'Astrid', 'sv-SE', 'Swedish', 'Swedish', 'female', 'standard', 'This is the text you can play using Astrid'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'tatyana', 'Tatyana', 'ru-RU', 'Russian', 'Russian', 'female', 'neural', 'This is the text you can play using Tatyana'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'maxim', 'Maxim', 'ru-RU', 'Russian', 'Russian', 'male', 'neural', 'This is the text you can play using Maxim'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'carmen', 'Carmen', 'ro-RO', 'Romanian', 'Romanian', 'female', 'standard', 'This is the text you can play using Carmen'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'cristiano', 'Cristiano', 'pt-PT', 'Portuguese (Portugal)', 'Portuguese', 'male', 'neural', 'This is the text you can play using Cristiano'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;

INSERT INTO available_voices (provider_id, voice_id, voice_name, language_code, language_name, accent, gender, voice_quality, sample_text)
SELECT p.id, 'vitoria', 'Vitória', 'pt-BR', 'Portuguese (Brazil)', 'Brazilian', 'female', 'neural', 'This is the text you can play using Vitória'
FROM voice_providers p WHERE p.name = 'aws_polly'
ON CONFLICT (provider_id, voice_id) DO NOTHING;