-- Sample data for your existing DrM Hope SaaS Platform schema
-- Run this in your Supabase SQL editor after setting up authentication

-- First, you need to create the admin user in Supabase Auth:
-- Go to Authentication > Users in your Supabase dashboard
-- Click "Add user" and create:
-- Email: admin@drmhope.com
-- Password: DrMHope@2024
-- Make sure to confirm the user

-- Insert sample users (make sure the admin user exists in Supabase Auth first)
INSERT INTO public.users (id, email, name, organization, role, status) VALUES
    ('550e8400-e29b-41d4-a716-446655440011', 'admin@drmhope.com', 'Dr. Murali B.K.', 'DrM Hope Softwares', 'admin', 'active'),
    ('550e8400-e29b-41d4-a716-446655440012', 'john.doe@techcorp.com', 'John Doe', 'TechCorp Solutions', 'manager', 'active'),
    ('550e8400-e29b-41d4-a716-446655440013', 'jane.smith@healthcare.com', 'Jane Smith', 'Healthcare Innovations', 'user', 'active'),
    ('550e8400-e29b-41d4-a716-446655440014', 'mike.wilson@edutech.com', 'Mike Wilson', 'EduTech Partners', 'user', 'active')
ON CONFLICT (email) DO NOTHING;

-- Insert sample enterprises
INSERT INTO public.enterprises (id, name, type, contact_email, status, owner_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'TechCorp Solutions', 'General Business', 'contact@techcorp.com', 'active', '550e8400-e29b-41d4-a716-446655440012'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Healthcare Innovations', 'Healthcare', 'info@healthcare-innovations.com', 'active', '550e8400-e29b-41d4-a716-446655440013'),
    ('550e8400-e29b-41d4-a716-446655440003', 'EduTech Partners', 'Education', 'hello@edutech-partners.com', 'Pending', '550e8400-e29b-41d4-a716-446655440014'),
    ('550e8400-e29b-41d4-a716-446655440004', 'FinanceFlow Corp', 'Finance', 'support@financeflow.com', 'active', '550e8400-e29b-41d4-a716-446655440011'),
    ('550e8400-e29b-41d4-a716-446655440005', 'RetailMax Solutions', 'Retail', 'contact@retailmax.com', 'Pending', '550e8400-e29b-41d4-a716-446655440011')
ON CONFLICT (id) DO NOTHING;

-- Update users to match their organizations (optional, since your schema uses text field)
UPDATE public.users SET organization = 'TechCorp Solutions' WHERE email = 'john.doe@techcorp.com';
UPDATE public.users SET organization = 'Healthcare Innovations' WHERE email = 'jane.smith@healthcare.com';
UPDATE public.users SET organization = 'EduTech Partners' WHERE email = 'mike.wilson@edutech.com';

-- Verify the data
SELECT 'Users Count' as table_name, COUNT(*) as count FROM public.users
UNION ALL
SELECT 'Enterprises Count' as table_name, COUNT(*) as count FROM public.enterprises;

-- Show sample data
SELECT 'Sample Users:' as info;
SELECT email, name, organization, role, status FROM public.users LIMIT 5;

SELECT 'Sample Enterprises:' as info;
SELECT name, type, contact_email, status FROM public.enterprises LIMIT 5;
