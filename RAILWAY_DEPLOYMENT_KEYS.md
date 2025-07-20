# 🚀 Railway Deployment - Actual API Keys

## 🚨 **CRITICAL: Server Crash Fix**

Your Railway server crashed because these environment variables are missing. Add them to fix the crash:

### **✅ WORKING API KEYS (Add to Railway)**

```bash
# ElevenLabs Configuration (VERIFIED WORKING)
ELEVENLABS_API_KEY=sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c
ELEVENLABS_API_URL=https://api.elevenlabs.io/v1
ELEVENLABS_WEBSOCKET_URL=wss://api.elevenlabs.io/v1/text-to-speech
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL_ID=eleven_multilingual_v2

# Twilio Configuration (PARTIAL - Account SID working)
TWILIO_ACCOUNT_SID=ACb4f43ae70f647972a12b7c27ef1c0c0f
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### **❌ REQUIRED TO PREVENT CRASH (Get these API keys)**

```bash
# These are causing the server crash - get from respective dashboards
BOLNA_API_KEY=your_bolna_api_key_here
RELEVANCE_AI_API_KEY=your_relevance_ai_key_here  
OPENAI_API_KEY=your_openai_api_key_here
```

### **⚙️ SYSTEM CONFIGURATION**

```bash
# System settings for Railway
FLASK_ENV=production
PORT=8080
USE_MOCK_MODE=true
PYTHONPATH=/app
```

## 🔧 **How to Add to Railway**

### **Step 1: Go to Railway Dashboard**
1. Visit: https://railway.app/dashboard
2. Select your `bashai.com` project
3. Click on the service
4. Go to **Variables** tab

### **Step 2: Add Environment Variables**
Copy and paste each variable from above:

**CRITICAL FIRST (to fix crash):**
- `ELEVENLABS_API_KEY` = `sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c`
- `BOLNA_API_KEY` = `get_from_bolna_dashboard`
- `RELEVANCE_AI_API_KEY` = `get_from_relevance_dashboard`
- `OPENAI_API_KEY` = `get_from_openai_dashboard`

**TWILIO (for phone calls):**
- `TWILIO_ACCOUNT_SID` = `ACb4f43ae70f647972a12b7c27ef1c0c0f`
- `TWILIO_AUTH_TOKEN` = `get_from_twilio_console`

### **Step 3: Deploy**
After adding variables, Railway will automatically redeploy.

## 🔑 **Where to Get Missing API Keys**

### **Bolna API Key**
- Go to: https://app.bolna.dev/
- Sign up/Login
- Navigate to API Keys section
- Generate new API key
- Copy and add to Railway as `BOLNA_API_KEY`

### **RelevanceAI API Key**
- Go to: https://relevanceai.com/
- Create account
- Go to Dashboard → API Keys
- Generate API key
- Copy and add to Railway as `RELEVANCE_AI_API_KEY`

### **OpenAI API Key**
- Go to: https://platform.openai.com/
- Login to your account
- Go to API Keys section
- Create new secret key
- Copy and add to Railway as `OPENAI_API_KEY`

### **Twilio Auth Token (Optional - for real calls)**
- Go to: https://console.twilio.com/
- Login to your account
- Find Auth Token in Account Info
- Copy and add to Railway as `TWILIO_AUTH_TOKEN`

## 🎯 **Immediate Action Plan**

### **Priority 1: Fix Server Crash**
1. Add `ELEVENLABS_API_KEY` to Railway (already have this)
2. Get and add `BOLNA_API_KEY`
3. Get and add `RELEVANCE_AI_API_KEY`
4. Get and add `OPENAI_API_KEY`
5. Redeploy

### **Priority 2: Enable Full Functionality**
1. Add `TWILIO_AUTH_TOKEN` for real phone calls
2. Add other optional keys for full features

## ✅ **Expected Results**

After adding the API keys:

### **Immediate (Server Fixed)**
- ✅ Server will start successfully
- ✅ No more crashes on startup
- ✅ ElevenLabs integration fully working
- ✅ Other integrations work in mock mode

### **Full Functionality (All Keys Added)**
- ✅ Real phone calls to +919373111709
- ✅ Professional AI voice conversations
- ✅ Multi-provider agent creation
- ✅ Complete BhashAI platform functionality

## 🚨 **Security Note**

This file contains actual API keys for deployment purposes. 
- **DO NOT** commit this file to public repositories
- **USE ONLY** for Railway environment variable setup
- **DELETE** this file after deployment setup

## 📞 **Test After Deployment**

Once deployed with API keys:

1. **Check Server Status**: Visit your Railway URL
2. **Test ElevenLabs**: Go to `/test-elevenlabs-call.html`
3. **Make Test Call**: Try calling +919373111709
4. **Verify Logs**: Check Railway deployment logs

## 🎉 **Success Indicators**

You'll know it's working when:
- ✅ Railway deployment shows "Running"
- ✅ No error logs about missing API keys
- ✅ ElevenLabs voice synthesis working
- ✅ Can create and test AI agents
- ✅ Phone calls connect successfully

**Your BhashAI platform will be fully operational! 🚀📞🎙️**
