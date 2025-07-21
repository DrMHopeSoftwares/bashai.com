-- Add bolna_agent_id column to voice_agents table
-- This will store the Bolna AI agent ID when agents are created

-- Add bolna_agent_id column to voice_agents table
ALTER TABLE voice_agents ADD COLUMN IF NOT EXISTS bolna_agent_id VARCHAR(255);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_voice_agents_bolna_agent_id ON voice_agents(bolna_agent_id);

-- Add comment for clarity
COMMENT ON COLUMN voice_agents.bolna_agent_id IS 'Bolna AI agent ID returned from Bolna API when agent is created';

-- Optional: Add unique constraint if each Bolna agent should only be linked to one voice_agent
-- ALTER TABLE voice_agents ADD CONSTRAINT unique_bolna_agent_id UNIQUE (bolna_agent_id);

-- Update existing records (if needed) - set to NULL for now
-- UPDATE voice_agents SET bolna_agent_id = NULL WHERE bolna_agent_id IS NULL;

-- Show the updated table structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'voice_agents' 
ORDER BY ordinal_position;
