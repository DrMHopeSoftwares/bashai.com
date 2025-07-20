# 🚀 Production Setup Guide - ElevenLabs Integration

## 🔐 **SECURE CONFIGURATION**

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
