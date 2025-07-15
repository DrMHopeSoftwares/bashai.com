#!/usr/bin/env python3
"""
Apply password column migration to Supabase using direct PostgreSQL connection
This script adds encrypted password support to the existing users table
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_connection():
    """Get direct PostgreSQL connection to Supabase"""
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise ValueError("SUPABASE_URL not found in environment variables")
    
    # Extract connection details from Supabase URL
    # Format: https://project-ref.supabase.co
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    # Supabase PostgreSQL connection details
    connection_params = {
        'host': f'db.{project_ref}.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': os.getenv('SUPABASE_DB_PASSWORD', 'your-db-password')  # You need to set this
    }
    
    return psycopg2.connect(**connection_params)

def apply_password_migration():
    """Apply the password column migration to Supabase"""
    
    print("🚀 Starting Supabase Password Migration (Direct Connection)")
    print("=" * 60)
    
    # SQL statements to execute
    sql_statements = [
        # Enable pgcrypto extension
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        
        # Add password column
        "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS password_hash text;",
        
        # Add constraint for password
        """ALTER TABLE public.users 
           ADD CONSTRAINT IF NOT EXISTS users_password_hash_check 
           CHECK (password_hash IS NOT NULL OR created_at < NOW());""",
        
        # Create password hashing function
        """CREATE OR REPLACE FUNCTION hash_password(password text)
           RETURNS text AS $$
           BEGIN
             RETURN crypt(password, gen_salt('bf', 12));
           END;
           $$ LANGUAGE plpgsql SECURITY DEFINER;""",
        
        # Create password verification function
        """CREATE OR REPLACE FUNCTION verify_password(password text, hash text)
           RETURNS boolean AS $$
           BEGIN
             RETURN crypt(password, hash) = hash;
           END;
           $$ LANGUAGE plpgsql SECURITY DEFINER;""",
        
        # Create indexes
        "CREATE INDEX IF NOT EXISTS idx_users_email ON public.users USING btree (email);",
        "CREATE INDEX IF NOT EXISTS idx_users_organization ON public.users USING btree (organization);",
        "CREATE INDEX IF NOT EXISTS idx_users_enterprise_id ON public.users USING btree (enterprise_id);",
        
        # Create update trigger function
        """CREATE OR REPLACE FUNCTION update_updated_at_column()
           RETURNS TRIGGER AS $$
           BEGIN
               NEW.updated_at = NOW();
               RETURN NEW;
           END;
           $$ LANGUAGE plpgsql;""",
        
        # Create trigger
        """DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
           CREATE TRIGGER update_users_updated_at 
               BEFORE UPDATE ON public.users 
               FOR EACH ROW 
               EXECUTE FUNCTION update_updated_at_column();""",
        
        # Add comments
        "COMMENT ON COLUMN public.users.password_hash IS 'Bcrypt hashed password with cost factor 12';",
        "COMMENT ON FUNCTION hash_password(text) IS 'Hash a plain text password using bcrypt';",
        "COMMENT ON FUNCTION verify_password(text, text) IS 'Verify a plain text password against a bcrypt hash';"
    ]
    
    try:
        # Try to connect to Supabase
        print("🔄 Attempting to connect to Supabase database...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        print("✅ Connected to Supabase database successfully!")
        print(f"📝 Executing {len(sql_statements)} SQL statements...")
        
        success_count = 0
        
        for i, sql_statement in enumerate(sql_statements, 1):
            try:
                print(f"\n🔄 Executing statement {i}/{len(sql_statements)}...")
                print(f"📝 SQL: {sql_statement[:100]}{'...' if len(sql_statement) > 100 else ''}")
                
                cursor.execute(sql_statement)
                conn.commit()
                
                print(f"✅ Statement {i} executed successfully")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Statement {i} failed: {str(e)}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 Migration Summary:")
        print(f"✅ Successful statements: {success_count}/{len(sql_statements)}")
        
        if success_count == len(sql_statements):
            print("🎉 Password migration completed successfully!")
            return True
        else:
            print("⚠️  Some statements failed. Please check the errors above.")
            return False
            
    except psycopg2.Error as e:
        print(f"❌ Database connection error: {e}")
        print("\n💡 Alternative: Use Supabase Dashboard SQL Editor")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Run the SQL from add_password_column.sql file")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_password_functions():
    """Test the password hashing and verification functions"""
    
    print("\n🧪 Testing password functions...")
    
    try:
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        # Test password hashing
        test_password = "test123"
        cursor.execute("SELECT hash_password(%s) as password_hash", (test_password,))
        result = cursor.fetchone()
        
        if result:
            password_hash = result[0]
            print(f"✅ Password hashing works! Hash: {password_hash[:20]}...")
            
            # Test password verification
            cursor.execute("SELECT verify_password(%s, %s) as is_valid", (test_password, password_hash))
            verify_result = cursor.fetchone()
            
            if verify_result and verify_result[0]:
                print("✅ Password verification works!")
            else:
                print("❌ Password verification failed!")
        else:
            print("❌ Password hashing failed!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error testing password functions: {e}")

def show_manual_instructions():
    """Show manual instructions for applying the migration"""
    
    print("\n" + "=" * 60)
    print("📖 MANUAL MIGRATION INSTRUCTIONS")
    print("=" * 60)
    print("\nIf automatic migration failed, you can apply it manually:")
    print("\n1. Go to Supabase Dashboard: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to 'SQL Editor' in the left sidebar")
    print("4. Copy and paste the following SQL:")
    print("\n" + "-" * 40)
    
    with open('add_password_column.sql', 'r') as f:
        print(f.read())
    
    print("-" * 40)
    print("\n5. Click 'Run' to execute the SQL")
    print("6. Verify that the migration was successful")

if __name__ == "__main__":
    success = apply_password_migration()
    
    if success:
        test_password_functions()
        
        print("\n" + "=" * 60)
        print("🎯 Migration completed successfully!")
        print("\n📖 Usage Examples:")
        print("1. Hash password: SELECT hash_password('plain_password');")
        print("2. Verify password: SELECT verify_password('plain_password', password_hash);")
        print("3. Insert user: INSERT INTO users (email, name, organization, password_hash) VALUES ('user@example.com', 'John', 'Corp', hash_password('password123'));")
    else:
        show_manual_instructions()
