# Vercel Deployment Guide for bhashai.com

## Prerequisites
1. GitHub account with your code repository
2. Vercel account (free tier available)
3. GoDaddy domain: bhashai.com
4. Supabase account for database
5. Local authentication system (already configured)

## Step 1: Prepare Your Repository

1. **Push all code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

## Step 2: Deploy to Vercel

1. **Go to Vercel Dashboard:**
   - Visit: https://vercel.com/dashboard
   - Sign in with GitHub

2. **Import Project:**
   - Click "New Project"
   - Import your GitHub repository: `DrMHopeSoftwares/bashai.com`
   - Select the repository

3. **Configure Build Settings:**
   - Framework Preset: `Other`
   - Root Directory: `./` (leave default)
   - Build Command: `pip install -r requirements.txt`
   - Output Directory: `./` (leave default)

## Step 3: Environment Variables

In Vercel dashboard, go to Settings > Environment Variables and add:

### Required Variables:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key
# Clerk environment variables removed - using local auth system
FLASK_ENV=production
FLASK_DEBUG=False
```

### Optional Variables (for full functionality):
```
BOLNA_API_KEY=your_bolna_api_key
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

## Step 4: Custom Domain Setup

1. **In Vercel Dashboard:**
   - Go to your project
   - Click "Settings" > "Domains"
   - Add custom domain: `bhashai.com`
   - Add www subdomain: `www.bhashai.com`

2. **In GoDaddy DNS Settings:**
   - Go to GoDaddy DNS Management
   - Add these records:

   **A Record:**
   ```
   Type: A
   Name: @
   Value: 76.76.19.61
   TTL: 1 Hour
   ```

   **CNAME Record:**
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   TTL: 1 Hour
   ```

## Step 5: SSL Certificate

Vercel automatically provides SSL certificates for custom domains.
Wait 24-48 hours for DNS propagation.

## Step 6: Test Deployment

1. **Check these URLs:**
   - https://bhashai.com (Landing page)
   - https://bhashai.com/dashboard.html (Dashboard)
   - https://bhashai.com/api/dev/voice-agents (API test)

## Step 7: Production Setup

1. **Setup Supabase Production Database**
2. **Configure Clerk for Production**
3. **Setup payment gateway (Razorpay)**
4. **Configure phone providers (Bolna, Twilio, etc.)**

## Troubleshooting

### Common Issues:

1. **Build Failures:**
   - Check requirements.txt
   - Verify Python version in runtime.txt

2. **Environment Variables:**
   - Ensure all required variables are set
   - Check for typos in variable names

3. **Domain Issues:**
   - Wait for DNS propagation (24-48 hours)
   - Verify DNS records in GoDaddy

4. **API Errors:**
   - Check Supabase connection
   - Verify Clerk configuration

## Support

For deployment issues, contact: support@bhashai.com
