-- Migration script to fix users table for enterprise isolation
-- This adds the missing enterprise_id column and updates existing data

-- Step 1: Add enterprise_id column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS enterprise_id UUID;

-- Step 2: Add foreign key constraint
ALTER TABLE users ADD CONSTRAINT fk_users_enterprise_id 
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE SET NULL;

-- Step 3: Update existing users to link them to enterprises
-- This assumes that users with the same organization name should be linked to the same enterprise

-- First, let's create enterprises for existing organizations if they don't exist
INSERT INTO enterprises (id, name, type, contact_email, status, owner_id)
SELECT 
    uuid_generate_v4(),
    DISTINCT u.organization,
    'trial',
    COALESCE(MIN(u.email), 'contact@' || LOWER(REPLACE(u.organization, ' ', '')) || '.com'),
    'active',
    MIN(u.id)
FROM users u
WHERE u.organization IS NOT NULL 
AND u.organization != ''
AND NOT EXISTS (
    SELECT 1 FROM enterprises e 
    WHERE e.name = u.organization
)
GROUP BY u.organization;

-- Step 4: Update users to set their enterprise_id based on organization name
UPDATE users 
SET enterprise_id = (
    SELECT e.id 
    FROM enterprises e 
    WHERE e.name = users.organization
)
WHERE users.organization IS NOT NULL 
AND users.organization != ''
AND users.enterprise_id IS NULL;

-- Step 5: Create a default enterprise for users without an organization
INSERT INTO enterprises (id, name, type, contact_email, status)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'Default Enterprise',
    'trial',
    'admin@drmhope.com',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Step 6: Update users without enterprise_id to use default enterprise
UPDATE users 
SET enterprise_id = '00000000-0000-0000-0000-000000000000'
WHERE enterprise_id IS NULL;

-- Step 7: Add NOT NULL constraint to enterprise_id (optional, for data integrity)
-- ALTER TABLE users ALTER COLUMN enterprise_id SET NOT NULL;

-- Step 8: Create index for better performance
CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON users(enterprise_id);

-- Step 9: Verify the migration
SELECT 
    'Migration Results:' as info,
    COUNT(*) as total_users,
    COUNT(enterprise_id) as users_with_enterprise,
    COUNT(DISTINCT enterprise_id) as unique_enterprises
FROM users;

-- Show sample data after migration
SELECT 
    u.email,
    u.name,
    u.organization,
    e.name as enterprise_name,
    u.enterprise_id
FROM users u
LEFT JOIN enterprises e ON u.enterprise_id = e.id
LIMIT 10; 