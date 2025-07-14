# Clerk Authentication Integration Guide
## DrM Hope SaaS Platform (CliniVoice)

This guide walks you through setting up Clerk authentication for trial visitors in your DrM Hope SaaS Platform.

## 🚀 Quick Start

### Step 1: Create Clerk Account

1. Go to [https://clerk.com](https://clerk.com) and sign up for a free account
2. Create a new application called "DrM Hope SaaS Platform" or "CliniVoice"
3. Choose "JavaScript" as your framework (since we're using vanilla JS frontend)

### Step 2: Configure Clerk Application

1. **Authentication Methods**: Enable email/password authentication
2. **Social Logins** (optional): Enable Google, GitHub, etc. for easier signup
3. **User Profile**: Configure required fields (name, email)
4. **Appearance**: Customize the look to match your brand colors

### Step 3: Get API Keys

From your Clerk Dashboard:

1. Go to **API Keys** section
2. Copy the following keys:
   - **Publishable Key** (starts with `pk_test_` or `pk_live_`)
   - **Secret Key** (starts with `sk_test_` or `sk_live_`)
   - **JWT Verification Key** (optional, for manual verification)

### Step 4: Update Environment Variables

Update your `.env` file with the Clerk keys:

```bash
# Clerk Configuration
CLERK_PUBLISHABLE_KEY=pk_test_your-publishable-key-here
CLERK_SECRET_KEY=sk_test_your-secret-key-here
CLERK_JWT_KEY=your-jwt-verification-key-here
CLERK_FRONTEND_API=your-frontend-api-url-here

# Existing Supabase Configuration (keep these)
SUPABASE_URL=https://ymvfueudlippmfeqdqro.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

The updated requirements.txt includes:
- PyJWT==2.8.0 (for JWT verification)
- cryptography==41.0.7 (for JWT cryptographic operations)

### Step 6: Configure Allowed Origins

In your Clerk Dashboard:

1. Go to **Domains** section
2. Add your allowed origins:
   - `http://localhost:8000` (for development)
   - `http://localhost:3000` (if using different port)
   - `https://your-production-domain.com` (for production)

### Step 7: Test the Integration

1. Start your Flask application:
   ```bash
   python main.py
   ```

2. Run the test script:
   ```bash
   python test_clerk_integration.py
   ```

3. Open your browser and go to `http://localhost:8000`

4. Click "Start Free Trial" to test the Clerk signup flow

## 🔧 Features Implemented

### Frontend Integration
- ✅ Clerk JavaScript SDK loaded in landing page
- ✅ Trial signup buttons trigger Clerk authentication
- ✅ Fallback to custom form if Clerk fails
- ✅ Automatic redirect to dashboard after signup

### Backend Integration
- ✅ JWT verification middleware (`clerk_auth.py`)
- ✅ Protected routes with `@require_auth` decorator
- ✅ Trial user creation and management
- ✅ Webhook handler for Clerk events
- ✅ Supabase integration for user data sync

### Trial Management
- ✅ 14-day trial period
- ✅ Usage limitations (API calls, voice minutes)
- ✅ Feature restrictions for trial users
- ✅ Trial status tracking and expiration handling

## 🎯 Trial User Limitations

### Usage Limits
- **API Calls**: 100 per day
- **Voice Minutes**: 60 per day, 300 total
- **Enterprises**: 1 maximum
- **Voice Agents**: 2 maximum
- **Users per Enterprise**: 3 maximum

### Feature Access
**Allowed Features:**
- Basic voice agent
- Hindi/Hinglish support
- Basic analytics
- Trial dashboard

**Restricted Features:**
- Advanced analytics
- Custom voice models
- API integrations
- White label options
- Priority support
- Bulk operations
- Advanced reporting

## 🔐 Security Features

### Authentication
- JWT-based session verification
- Secure token validation
- Authorized parties checking
- Automatic token refresh

### Trial Security
- Usage tracking and limits
- Feature access control
- Trial expiration enforcement
- Activity logging

## 📊 API Endpoints

### Authentication
- `GET /auth/me` - Get current user info
- `POST /auth/clerk-trial-signup` - Create trial account
- `POST /webhooks/clerk` - Handle Clerk events

### Trial Management
- `GET /api/trial-status` - Get trial status
- `GET /api/trial-usage` - Get usage summary
- `GET /api/enterprises` - List enterprises (with limits)
- `POST /api/enterprises` - Create enterprise (with limits)
- `POST /api/voice-agents` - Create voice agent (with limits)

## 🚀 Production Deployment

### Clerk Configuration
1. **Upgrade to Production**: Switch from test keys to live keys
2. **Configure Webhooks**: Set up webhooks for user events
3. **Set Allowed Origins**: Add your production domain
4. **Configure Rate Limits**: Set appropriate rate limits

### Security Checklist
- [ ] Use HTTPS in production
- [ ] Set secure CORS policies
- [ ] Configure proper webhook signatures
- [ ] Set up monitoring and logging
- [ ] Configure backup authentication method
- [ ] Set up user data export/import

### Environment Variables (Production)
```bash
CLERK_PUBLISHABLE_KEY=pk_live_your-live-publishable-key
CLERK_SECRET_KEY=sk_live_your-live-secret-key
CLERK_WEBHOOK_SECRET=whsec_your-webhook-secret
```

## 🔧 Troubleshooting

### Common Issues

**1. "Clerk is not defined" Error**
- Check if Clerk SDK is loaded properly
- Verify publishable key is correct
- Check browser console for loading errors

**2. JWT Verification Fails**
- Verify secret key is correct
- Check if token is being sent properly
- Ensure allowed origins are configured

**3. Trial Signup Fails**
- Check Clerk API key permissions
- Verify required fields are provided
- Check Supabase connection

**4. Webhook Not Working**
- Verify webhook URL is accessible
- Check webhook secret configuration
- Review webhook payload format

### Debug Mode
Enable debug logging by setting:
```bash
FLASK_DEBUG=True
FLASK_ENV=development
```

## 📞 Support

For issues with:
- **Clerk Integration**: Check [Clerk Documentation](https://clerk.com/docs)
- **Platform Issues**: Contact DrM Hope support
- **Trial Management**: Review trial_middleware.py

## 🎉 Success!

Once everything is set up, your trial visitors can:
1. Click "Start Free Trial" on landing page
2. Sign up using Clerk's secure authentication
3. Get immediate access to trial features
4. Use the platform with appropriate limitations
5. Upgrade to full access when ready

The integration provides a seamless trial experience while maintaining security and proper usage controls.
