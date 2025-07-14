-- Add calling_number field to voice_agents table
-- This allows each voice agent to have their own calling number instead of using the hardcoded one

-- Check if the column already exists before adding it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'voice_agents' 
        AND column_name = 'calling_number'
    ) THEN
        ALTER TABLE voice_agents ADD COLUMN calling_number VARCHAR(20);
        RAISE NOTICE 'Column calling_number added to voice_agents table';
    ELSE
        RAISE NOTICE 'Column calling_number already exists in voice_agents table';
    END IF;
END $$;

-- Add comment to the column for documentation
COMMENT ON COLUMN voice_agents.calling_number IS 'Phone number used by this voice agent for outbound calls';