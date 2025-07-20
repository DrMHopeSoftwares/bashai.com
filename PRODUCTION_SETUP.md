# 🚀 Production Setup Guide - ElevenLabs Integration

## ⚡ **AUTOMATIC SETUP (RECOMMENDED)**

### **One-Command Setup**

Run the automatic production setup script:

```bash
python3 setup_production.py
```

This will automatically:
- ✅ Configure ElevenLabs API key
- ✅ Set up Twilio Account SID
- ✅ Create production `.env` file
- ✅ Verify API connections
- ✅ Create quick test scripts
- ✅ Enable mock mode for development

**Ready to use immediately!** 🎉

### **What the Automatic Setup Does**

✅ **ElevenLabs Configuration**:
- API Key: `sk_97fa57d9766f4fee1b9632e8987595ba3de79f630ed2d14c` (Active)
- 22 voices available including Rachel (Professional Female)
- API connection verified and working

✅ **Twilio Configuration**:
- Account SID: `ACb4f43ae70f647972a12b7c27ef1c0c0f` (Configured)
- Mock mode enabled for development testing
- Ready for real calls when auth token is added

✅ **Production Files Created**:
- `.env` - Production environment variables
- `quick_production_test.py` - Quick testing script
- `.env.backup.timestamp` - Backup of previous configuration

✅ **Immediate Capabilities**:
- ElevenLabs voice synthesis ✅ **WORKING**
- Agent creation and management ✅ **WORKING**
- Call simulation and logging ✅ **WORKING**
- Web interface testing ✅ **WORKING**

---

## 🔐 **MANUAL CONFIGURATION (Alternative)**

### **Step 1: Configure Environment Variables**

Copy `.env.example` to `.env` and update with your actual credentials:

```bash
cp .env.example .env
```

### **Step 2: Add Your API Keys**

Update the following in your `.env` file:

#### **ElevenLabs Configuration**
```bash
# Get your API key from: https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY=sk_your_actual_elevenlabs_api_key_here
ELEVENLABS_API_URL=https://api.elevenlabs.io/v1
ELEVENLABS_WEBSOCKET_URL=wss://api.elevenlabs.io/v1/text-to-speech
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

#### **Twilio Configuration**
```bash
# Get from: https://console.twilio.com/
TWILIO_ACCOUNT_SID=ACyour_actual_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_actual_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1your_twilio_phone_number
```

### **Step 3: Test the Integration**

#### **Quick Test (Automatic Setup)**
```bash
python3 quick_production_test.py
```

#### **Method 1: Web Interface**
```bash
python3 main.py
# Open: http://localhost:8000/test-elevenlabs-call.html
```

#### **Method 2: Production Script**
```bash
python3 make_real_elevenlabs_call.py
```

#### **Method 3: API Call**
```bash
curl -X POST http://localhost:8000/api/twilio-elevenlabs/make-call \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919373111709",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "message": "नमस्ते! मैं BhashAI से एक AI असिस्टेंट हूं।",
    "language": "hi"
  }'
```

## 🎙️ **Voice Configuration**

### **Recommended Voices**
- **Rachel** (21m00Tcm4TlvDq8ikWAM): Professional female voice
- **Adam** (pNInz6obpgDQGcFmaJgB): Authoritative male voice
- **Domi** (AZnzlk1XvdvUeBnXmlld): Confident female voice

### **Voice Settings**
```javascript
{
  "stability": 0.85,        // High consistency
  "similarity_boost": 0.8,  // Natural quality
  "style": 0.15,           // Professional tone
  "use_speaker_boost": true
}
```

## 📞 **Phone Call Features**

### **Supported Languages**
- **Hindi**: Native support
- **English**: Full support
- **Hinglish**: Hindi + English mix

### **Call Capabilities**
- Real-time voice synthesis
- Natural conversation flow
- Professional greetings
- Call logging and analytics
- Webhook integration
- Session management

## 🔧 **Technical Architecture**

### **Components**
1. **ElevenLabs API**: Voice synthesis and conversational AI
2. **Twilio**: Phone call infrastructure
3. **Flask Backend**: API endpoints and webhook handling
4. **Web Interface**: User-friendly testing interface

### **API Endpoints**
- `POST /api/elevenlabs/make-test-call`: Test calls (mock mode)
- `POST /api/twilio-elevenlabs/make-call`: Real calls (production)
- `POST /api/elevenlabs/voice-webhook`: Twilio voice webhook
- `POST /api/elevenlabs/process-speech`: Speech processing

## 🛡️ **Security Best Practices**

### **Environment Variables**
- Never commit `.env` file to git
- Use different keys for development/production
- Rotate API keys regularly
- Monitor API usage and costs

### **Webhook Security**
- Use HTTPS for all webhook URLs
- Validate webhook signatures
- Implement rate limiting
- Log all webhook events

## 📊 **Monitoring & Analytics**

### **Call Logging**
All calls are logged with:
- Call ID and session ID
- Phone number and duration
- Voice settings used
- Success/failure status
- Timestamp and user info

### **API Monitoring**
- ElevenLabs API usage
- Twilio call costs
- Error rates and response times
- Voice synthesis quality metrics

## 🚨 **Troubleshooting**

### **Common Issues**

#### **API Key Invalid**
```bash
❌ ELEVENLABS_API_KEY not found - using mock mode
```
**Solution**: Add valid ElevenLabs API key to `.env`

#### **Twilio Authentication Failed**
```bash
❌ Twilio authentication failed
```
**Solution**: Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN

#### **Call Not Connecting**
```bash
❌ Call failed to initiate
```
**Solution**: Check phone number format and Twilio balance

### **Debug Mode**
Enable debug logging:
```bash
export FLASK_DEBUG=True
python3 main.py
```

## 🎯 **Production Checklist**

- [ ] ElevenLabs API key configured
- [ ] Twilio credentials configured
- [ ] Webhook URLs accessible via HTTPS
- [ ] Phone numbers in correct format
- [ ] API rate limits configured
- [ ] Error handling implemented
- [ ] Call logging enabled
- [ ] Security measures in place

## 📈 **Scaling Considerations**

### **High Volume Calls**
- Implement connection pooling
- Use async processing for webhooks
- Cache voice synthesis results
- Monitor API rate limits

### **Multi-tenant Support**
- Separate API keys per tenant
- Tenant-specific voice settings
- Isolated call logging
- Custom webhook endpoints

## 🎉 **Ready for Production!**

Once configured, the system supports:
- ✅ Real phone calls using ElevenLabs AI
- ✅ Professional voice quality
- ✅ Multi-language support
- ✅ Comprehensive logging
- ✅ Webhook integration
- ✅ Scalable architecture

**Start making AI-powered phone calls today!** 📞🎙️
