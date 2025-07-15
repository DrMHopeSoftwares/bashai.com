-- Add agent welcome message and prompt fields to voice_agents table
-- These will allow users to customize the AI agent behavior from the UI

ALTER TABLE voice_agents 
ADD COLUMN IF NOT EXISTS welcome_message TEXT,
ADD COLUMN IF NOT EXISTS agent_prompt TEXT,
ADD COLUMN IF NOT EXISTS conversation_style VARCHAR(100) DEFAULT 'professional',
ADD COLUMN IF NOT EXISTS language_preference VARCHAR(50) DEFAULT 'hinglish';

-- Update existing agents with default messages
UPDATE voice_agents 
SET 
    welcome_message = CASE 
        WHEN title LIKE '%Appointment%' THEN 'Hello! This is an AI assistant from Ayushmann Healthcare. I''m calling to help you with appointment scheduling. How can I assist you today?'
        WHEN title LIKE '%Prescription%' THEN 'Hello! This is a friendly reminder call from Ayushmann Healthcare about your prescription. I''m here to help ensure you don''t miss your medication.'
        WHEN title LIKE '%Lab Results%' THEN 'Hello! I''m calling from Ayushmann Healthcare with an update about your lab results. This is an automated call to keep you informed.'
        WHEN title LIKE '%Delivery%' THEN 'Hello! This is Raftaar Logistics calling about your delivery. I''m here to provide you with an update on your shipment.'
        WHEN title LIKE '%Customer Support%' THEN 'Hello! Thank you for contacting Raftaar Logistics. I''m an AI assistant here to help with your inquiries and provide support.'
        ELSE 'Hello! This is an AI assistant. How can I help you today?'
    END,
    agent_prompt = CASE 
        WHEN title LIKE '%Appointment%' THEN 'You are a helpful healthcare appointment booking assistant. Be professional, empathetic, and efficient. Always confirm appointment details clearly. Ask for preferred dates and times. Handle rescheduling requests professionally.'
        WHEN title LIKE '%Prescription%' THEN 'You are a medication reminder assistant. Be caring and informative. Remind patients about their prescriptions, ask about any side effects, and provide guidance on medication timing. Always encourage patients to consult their doctor for medical advice.'
        WHEN title LIKE '%Lab Results%' THEN 'You are a lab results notification assistant. Be clear, professional, and reassuring. Inform patients that their results are ready for pickup or review. Direct them to contact their doctor for interpretation. Maintain patient confidentiality.'
        WHEN title LIKE '%Delivery%' THEN 'You are a delivery update assistant. Be helpful and informative about package status, delivery times, and address confirmations. Handle delivery issues professionally and provide tracking information when available.'
        WHEN title LIKE '%Customer Support%' THEN 'You are a customer support assistant. Be patient, helpful, and solution-oriented. Address customer concerns, provide information about services, and escalate complex issues to human agents when necessary.'
        ELSE 'You are a helpful AI assistant. Be professional, courteous, and helpful in all interactions.'
    END,
    conversation_style = CASE 
        WHEN title LIKE '%Healthcare%' OR title LIKE '%Appointment%' OR title LIKE '%Prescription%' OR title LIKE '%Lab%' THEN 'empathetic'
        WHEN title LIKE '%Delivery%' OR title LIKE '%Customer%' THEN 'professional'
        ELSE 'friendly'
    END,
    language_preference = 'hinglish'
WHERE welcome_message IS NULL OR agent_prompt IS NULL;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_voice_agents_language ON voice_agents(language_preference);
CREATE INDEX IF NOT EXISTS idx_voice_agents_style ON voice_agents(conversation_style);