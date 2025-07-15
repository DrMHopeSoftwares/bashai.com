# DrM Hope SaaS Platform - Setup Guide

This guide will help you set up the DrM Hope SaaS Platform with full Supabase integration.

## Prerequisites

- Python 3.8 or higher
- A Supabase account and project
- Git (optional, for version control)

## Step 1: Supabase Setup

### 1.1 Create a Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Create a new project
3. Wait for the project to be fully initialized

### 1.2 Set Up Database Schema
✅ **You already have the database tables set up!**

Your existing schema includes:
- `enterprises` table with fields: id, name, type, contact_email, status, owner_id
- `users` table with fields: id, email, name, organization, role, status

To add sample data:
1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy the contents of `sample_data.sql` and run it in the SQL Editor
4. This will add sample users and enterprises for testing

### 1.3 Configure Authentication
1. In your Supabase dashboard, go to Authentication > Settings
2. Make sure "Enable email confirmations" is turned OFF for development
3. Go to Authentication > Users
4. Manually create the admin user:
   - Email: `admin@drmhope.com`
   - Password: `DrMHope@2024`
   - Confirm the user immediately

### 1.4 Get API Keys
1. Go to Settings > API in your Supabase dashboard
2. Copy the following values:
   - Project URL
   - Anon (public) key
   - Service role (secret) key

## Step 2: Local Environment Setup

### 2.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 2.2 Environment Configuration
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your Supabase credentials:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   SECRET_KEY=your-secret-key-here
   ```

### 2.3 Run the Application
```bash
python main.py
```

The application will start on `http://localhost:5000`

## Step 3: Testing the Setup

### 3.1 Test Supabase Connection
First, test your connection:
```bash
python test_connection.py
```
This will verify your Supabase setup and check if sample data exists.

### 3.2 Access the Landing Page
1. Open your browser and go to `http://localhost:5000`
2. You should see the DrM Hope SaaS landing page

### 3.3 Test Authentication
1. Scroll down to the login section
2. Use the demo credentials:
   - Email: `admin@drmhope.com`
   - Password: `DrMHope@2024`
3. You should be redirected to the dashboard

### 3.4 Test Dashboard Functionality
1. Check if the dashboard loads with real data from Supabase
2. Try adding a new organization (with type and contact email)
3. Try adding a new user (with organization field)
4. Verify that the statistics update correctly

## Step 4: Troubleshooting

### Common Issues

#### 1. "Missing Supabase configuration" Error
- Make sure your `.env` file exists and contains the correct Supabase credentials
- Verify that the SUPABASE_URL and SUPABASE_SERVICE_KEY are set correctly

#### 2. Authentication Fails
- Ensure you've created the admin user in Supabase Auth
- Check that the user is confirmed (not pending email confirmation)
- Verify the password matches exactly

#### 3. Database Connection Issues
- Make sure you've run the `supabase_schema.sql` script
- Check that your Supabase project is active and not paused
- Verify the Project URL is correct

#### 4. RLS Policy Issues
- If you get permission errors, check that the RLS policies are created correctly
- Make sure the user exists in both Supabase Auth and your users table
- Verify the email addresses match exactly

#### 5. CORS Issues
- The Flask app includes CORS support, but if you encounter issues, check your browser's developer console
- Make sure you're accessing the app via the correct URL

### Debug Mode
To enable debug mode for more detailed error messages:
1. Set `FLASK_DEBUG=True` in your `.env` file
2. The Flask app runs with `debug=True` by default in development

## Step 5: Production Deployment

### 5.1 Environment Variables
For production deployment, make sure to:
1. Set `FLASK_ENV=production`
2. Use a strong, unique `SECRET_KEY`
3. Consider using environment-specific Supabase projects

### 5.2 Security Considerations
1. Never commit your `.env` file to version control
2. Use strong passwords for all accounts
3. Regularly rotate your API keys
4. Enable email confirmations in production
5. Set up proper logging and monitoring

### 5.3 Scaling Considerations
1. Consider using a production WSGI server like Gunicorn
2. Set up proper database connection pooling
3. Implement caching where appropriate
4. Monitor your Supabase usage and upgrade plans as needed

## Next Steps

Once you have the basic platform running:

1. **Phase 3: Clinivoice Integration**
   - Integrate the Hindi-native AI voice agent
   - Add voice agent management UI
   - Implement call logging and analytics

2. **Enhanced Features**
   - Real-time notifications
   - Advanced user management
   - Detailed analytics and reporting
   - API rate limiting and security enhancements

3. **Frontend Improvements**
   - Consider migrating to React or Vue.js
   - Implement real-time updates with WebSockets
   - Add mobile responsiveness improvements

## Support

If you encounter any issues during setup:
1. Check the browser console for JavaScript errors
2. Check the Flask application logs for backend errors
3. Verify your Supabase project status and logs
4. Ensure all environment variables are set correctly

For additional support, refer to the Supabase documentation at [docs.supabase.com](https://docs.supabase.com).
