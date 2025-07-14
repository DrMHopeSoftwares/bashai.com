-- Add encrypted password column to users table
-- This SQL adds a password column with bcrypt encryption support

-- First, ensure the pgcrypto extension is enabled for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add password column to the users table
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS password_hash text;

-- Add constraint to ensure password is not null for new users
-- (We'll make it nullable initially to handle existing users)
ALTER TABLE public.users 
ADD CONSTRAINT users_password_hash_check 
CHECK (password_hash IS NOT NULL OR created_at < NOW());

-- Create index on password_hash for performance (optional, usually not needed)
-- CREATE INDEX IF NOT EXISTS idx_users_password_hash ON public.users USING btree (password_hash) TABLESPACE pg_default;

-- Updated complete table schema with password column
/*
CREATE TABLE IF NOT EXISTS public.users (
  id uuid not null default extensions.uuid_generate_v4 (),
  email text not null,
  name text not null,
  organization text not null,
  password_hash text, -- Added encrypted password column
  role text not null default 'user'::text,
  status text not null default 'active'::text,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  enterprise_id uuid null,
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email),
  constraint users_enterprise_id_fkey foreign KEY (enterprise_id) references enterprises (id),
  constraint users_role_check check (
    (
      role = any (
        array['admin'::text, 'user'::text, 'manager'::text]
      )
    )
  ),
  constraint users_status_check check (
    (
      status = any (
        array['active'::text, 'inactive'::text, 'pending'::text]
      )
    )
  ),
  constraint users_password_hash_check check (password_hash IS NOT NULL OR created_at < NOW())
) TABLESPACE pg_default;
*/

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

-- Example usage for inserting user with encrypted password:
/*
INSERT INTO public.users (email, name, organization, password_hash, role, status)
VALUES (
  'user@example.com',
  'John Doe',
  'Example Corp',
  hash_password('user_plain_password'),
  'user',
  'active'
);
*/

-- Example usage for password verification:
/*
SELECT verify_password('user_plain_password', password_hash) as password_valid
FROM public.users 
WHERE email = 'user@example.com';
*/

-- Update existing indexes to include the new column structure
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users USING btree (email) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_users_organization ON public.users USING btree (organization) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON public.users USING btree (enterprise_id) TABLESPACE pg_default;

-- Optional: Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON COLUMN public.users.password_hash IS 'Bcrypt hashed password with cost factor 12';
COMMENT ON FUNCTION hash_password(text) IS 'Hash a plain text password using bcrypt';
COMMENT ON FUNCTION verify_password(text, text) IS 'Verify a plain text password against a bcrypt hash';
