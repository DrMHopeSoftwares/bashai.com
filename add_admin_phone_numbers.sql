-- Add phone number fields to users table for admin-specific Bolna integration
-- This allows each admin to have their own sender phone number for voice calls

-- Add phone number column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS sender_phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS bolna_agent_id VARCHAR(255);

-- Add comments for clarity
COMMENT ON COLUMN users.sender_phone IS 'Admin-specific phone number for outbound calls via Bolna API';
COMMENT ON COLUMN users.bolna_agent_id IS 'Admin-specific Bolna agent ID for voice calls';

-- Update existing admin users with default phone numbers (optional)
-- You can customize these phone numbers for each admin
UPDATE users 
SET sender_phone = '+918035743222', 
    bolna_agent_id = '15554373-b8e1-4b00-8c25-c4742dc8e480'
WHERE role IN ('admin', 'super_admin', 'manager') 
AND sender_phone IS NULL;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_users_sender_phone ON users(sender_phone);
CREATE INDEX IF NOT EXISTS idx_users_bolna_agent_id ON users(bolna_agent_id);
