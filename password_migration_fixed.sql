-- Add encrypted password column to users table (FIXED VERSION)
-- This SQL adds a password column with bcrypt encryption support

-- First, ensure the pgcrypto extension is enabled for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add password column to the users table
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS password_hash text;

-- Function to hash password using bcrypt (cost factor 12 for security)
CREATE OR REPLACE FUNCTION hash_password(password text)
RETURNS text AS $$
BEGIN
  RETURN crypt(password, gen_salt('bf', 12));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify password
CREATE OR REPLACE FUNCTION verify_password(password text, hash text)
RETURNS boolean AS $$
BEGIN
  RETURN crypt(password, hash) = hash;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update existing indexes to include the new column structure
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users USING btree (email);
CREATE INDEX IF NOT EXISTS idx_users_organization ON public.users USING btree (organization);
CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON public.users USING btree (enterprise_id);

-- Add trigger function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists and create new one
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON COLUMN public.users.password_hash IS 'Bcrypt hashed password with cost factor 12';
COMMENT ON FUNCTION hash_password(text) IS 'Hash a plain text password using bcrypt';
COMMENT ON FUNCTION verify_password(text, text) IS 'Verify a plain text password against a bcrypt hash';
