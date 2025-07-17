# RelevanceAI Integration Guide for BhashAI Platform

## Overview

This guide explains how RelevanceAI has been integrated into the BhashAI platform, providing multi-agent AI capabilities alongside the existing Bolna and OpenAI Realtime providers.

## 🚀 Features Added

### 1. **Multi-Provider Support**
- **Bolna AI**: Voice-optimized for Hindi/Hinglish calls
- **RelevanceAI**: Multi-agent workflows and automation
- **OpenAI Realtime**: GPT-4 powered conversations

### 2. **RelevanceAI Capabilities**
- Multi-agent teams for complex workflows
- Custom tools and integrations
- Advanced analytics and monitoring
- Webhook-based real-time updates
- Business automation workflows

### 3. **Enhanced UI**
- Provider selection in agent creation
- RelevanceAI-specific configuration options
- Tool and integration management
- Multi-agent team setup

## 📁 Files Added/Modified

### New Files Created:
1. **`relevance_ai_integration.py`** - Core integration module
2. **`relevance_ai_schema_update.sql`** - Database schema updates
3. **`apply_relevance_ai_schema.py`** - Schema application script
4. **`static/create-agent-enhanced.html`** - Enhanced UI with provider selection
5. **`test_relevance_ai_integration.py`** - Comprehensive test suite
6. **`RELEVANCE_AI_INTEGRATION_GUIDE.md`** - This documentation

### Modified Files:
1. **`.env`** - Added RelevanceAI configuration
2. **`main.py`** - Added RelevanceAI endpoints and webhook handlers

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file:

```env
# RelevanceAI Configuration
RELEVANCE_AI_API_KEY=sk-OTM3Mjg1ZDUtZGViZi00MjA3LWI2ZjctMGM3ZThjMTdjMTk4
RELEVANCE_AI_REGION=f1db6c
RELEVANCE_AI_PROJECT_ID=2b2b02320797-4190-b55a-33eeb1d625c0
RELEVANCE_AI_BASE_URL=https://api-f1db6c.stack.tryrelevance.com/latest
```

### Database Setup

1. **Apply schema updates:**
   ```bash
   python apply_relevance_ai_schema.py
   ```

2. **Verify schema:**
   ```bash
   python test_relevance_ai_integration.py
   ```

## 🔧 API Endpoints

### Voice Agent Management (Enhanced)

#### Create Agent with Provider Selection
```http
POST /api/voice-agents
Content-Type: application/json

{
  "name": "Customer Support Agent",
  "description": "AI agent for customer support",
  "language": "english",
  "use_case": "workflow",
  "provider": "relevance_ai",
  "provider_config": {
    "agent_type": "multi",
    "tools": ["knowledge_base", "email_automation"],
    "integrations": ["slack", "sheets"]
  }
}
```

### RelevanceAI Specific Endpoints

#### List RelevanceAI Agents
```http
GET /api/relevance-ai/agents
Authorization: Bearer <token>
```

#### Create Session
```http
POST /api/relevance-ai/agents/{agent_id}/sessions
Content-Type: application/json

{
  "config": {
    "language": "english",
    "context": "customer_support"
  }
}
```

#### Send Message
```http
POST /api/relevance-ai/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "How can I help you today?",
  "context": {
    "user_id": "user123",
    "channel": "web"
  }
}
```

#### Get Session History
```http
GET /api/relevance-ai/sessions/{session_id}/history
Authorization: Bearer <token>
```

#### Get Analytics
```http
GET /api/relevance-ai/agents/{agent_id}/analytics
Authorization: Bearer <token>
```

#### Tools Management
```http
GET /api/relevance-ai/tools
POST /api/relevance-ai/tools
```

### Webhook Endpoints

#### RelevanceAI Webhooks
```http
POST /api/webhooks/relevance-ai
Content-Type: application/json

{
  "event_type": "session.started",
  "session_id": "session_123",
  "agent_id": "agent_456",
  "context": {}
}
```

**Supported webhook events:**
- `session.started`
- `session.completed`
- `message.received`
- `agent.response`
- `workflow.triggered`
- `tool.executed`

## 💾 Database Schema

### New Tables Created:

1. **`relevance_ai_sessions`** - Tracks conversation sessions
2. **`relevance_ai_messages`** - Stores conversation messages
3. **`relevance_ai_tools`** - Custom tools for agents
4. **`relevance_ai_workflows`** - Workflow configurations
5. **`relevance_ai_integrations`** - Third-party integrations

### Enhanced Tables:

1. **`voice_agents`** - Added provider support:
   - `provider_type` (bolna, relevance_ai, openai_realtime)
   - `relevance_ai_agent_id`
   - `relevance_ai_config`
   - `provider_config`

## 🖥️ User Interface

### Enhanced Agent Creation

1. **Provider Selection Step:**
   - Choose between Bolna, RelevanceAI, or OpenAI
   - View provider comparison table
   - Understand capabilities and costs

2. **RelevanceAI Configuration:**
   - Single vs Multi-agent setup
   - Tool selection (Slack, Sheets, Email, etc.)
   - API key configuration
   - Region selection

3. **Use Case Templates:**
   - Workflow Automation
   - Data Processing
   - System Integration
   - Customer Support

### Access the Enhanced UI:
```
http://localhost:8000/create-agent-enhanced.html
```

## 🔌 Integration Patterns

### 1. Voice Agent Creation
```python
from relevance_ai_integration import RelevanceAIAgentManager

manager = RelevanceAIAgentManager()

# Create voice-optimized agent
agent = manager.create_voice_agent({
    'name': 'Support Agent',
    'language': 'hindi',
    'use_case': 'customer_support'
})

# Create workflow agent
workflow_agent = manager.create_workflow_agent({
    'name': 'Data Processor',
    'workflow_type': 'data_processing'
})
```

### 2. Session Management
```python
# Handle voice call
session = manager.handle_voice_call(agent_id, {
    'phone_number': '+91XXXXXXXXXX',
    'call_id': 'call_123'
})

# Process conversation
response = manager.process_conversation_turn(
    agent_id=agent_id,
    session_id=session['session_id'],
    user_input="I need help with my order",
    context={'user_id': 'user123'}
)
```

### 3. Custom Tools
```python
provider = RelevanceAIProvider()

# Create custom tool
tool = provider.create_tool({
    'name': 'Order Lookup',
    'description': 'Look up customer orders',
    'type': 'api',
    'config': {
        'endpoint': 'https://api.example.com/orders',
        'auth_type': 'bearer'
    }
})
```

## 🧪 Testing

### Run Integration Tests
```bash
python test_relevance_ai_integration.py
```

### Test Scenarios Covered:
1. Environment setup verification
2. Module import testing
3. RelevanceAI API connection
4. Database schema validation
5. Server startup verification
6. Authentication testing
7. Agent creation via API
8. Agent listing functionality
9. Webhook endpoint testing
10. UI file verification

### Manual Testing Steps:

1. **Start the server:**
   ```bash
   python main.py
   ```

2. **Create a RelevanceAI agent:**
   - Go to `/create-agent-enhanced.html`
   - Select "Relevance AI" provider
   - Configure agent settings
   - Deploy the agent

3. **Test agent functionality:**
   - Create a session via API
   - Send messages to the agent
   - View conversation history
   - Check analytics

## 🚨 Troubleshooting

### Common Issues:

#### 1. RelevanceAI API Connection Failed
```
Error: RELEVANCE_AI_API_KEY environment variable is required
```
**Solution:** Check `.env` file has correct API key

#### 2. Database Schema Not Applied
```
Error: relation "relevance_ai_sessions" does not exist
```
**Solution:** Run `python apply_relevance_ai_schema.py`

#### 3. Agent Creation Fails
```
Error: Failed to create RelevanceAI agent
```
**Solution:** 
- Verify API key is valid
- Check RelevanceAI service status
- Ensure project ID is correct

#### 4. Webhook Not Receiving Events
```
No webhook events received from RelevanceAI
```
**Solution:**
- Configure webhook URL in RelevanceAI dashboard
- Ensure webhook endpoint is accessible
- Check webhook URL: `https://yourdomain.com/api/webhooks/relevance-ai`

### Debug Mode:
Set `FLASK_DEBUG=True` in `.env` for detailed error messages.

## 📊 Monitoring and Analytics

### Built-in Analytics:
- Session count and success rate
- Message volume and response times
- Tool usage statistics
- Integration performance metrics

### Custom Analytics:
Access via `/api/relevance-ai/agents/{agent_id}/analytics`

### Database Queries:
```sql
-- Session statistics
SELECT 
    va.name,
    COUNT(ras.id) as total_sessions,
    COUNT(CASE WHEN ras.status = 'completed' THEN 1 END) as completed_sessions
FROM voice_agents va
LEFT JOIN relevance_ai_sessions ras ON va.id = ras.voice_agent_id
WHERE va.provider_type = 'relevance_ai'
GROUP BY va.id, va.name;

-- Message volume by day
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as message_count,
    COUNT(CASE WHEN message_type = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN message_type = 'agent' THEN 1 END) as agent_messages
FROM relevance_ai_messages
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

## 🔄 Workflow Examples

### 1. Customer Support Workflow
```javascript
// Agent configuration
{
  "name": "Support Agent",
  "use_case": "customer_support",
  "tools": ["knowledge_base", "ticket_creation", "escalation"],
  "integrations": ["slack", "crm"],
  "workflow": {
    "greeting": "Hello! How can I help you today?",
    "fallback": "Let me transfer you to a human agent",
    "escalation_trigger": "complex_issue"
  }
}
```

### 2. Data Processing Workflow
```javascript
// Workflow agent configuration
{
  "name": "Data Processor",
  "use_case": "data_processing",
  "tools": ["data_extraction", "data_validation", "reporting"],
  "integrations": ["sheets", "database"],
  "schedule": "daily",
  "output_format": "excel"
}
```

## 🚀 Deployment

### Production Checklist:
- [ ] Environment variables configured
- [ ] Database schema applied
- [ ] RelevanceAI webhooks configured
- [ ] SSL certificates for webhook endpoints
- [ ] Monitoring and logging enabled
- [ ] Backup procedures in place

### Performance Optimization:
- Enable database connection pooling
- Implement Redis caching for session data
- Use CDN for static UI assets
- Monitor API rate limits

## 📚 Additional Resources

- [RelevanceAI Documentation](https://relevanceai.com/docs)
- [BhashAI API Reference](https://docs.bhashai.com)
- [Flask Application Structure](https://flask.palletsprojects.com/)
- [Supabase Database](https://supabase.com/docs)

## 🤝 Support

For issues with the integration:

1. **Check the test suite:** `python test_relevance_ai_integration.py`
2. **Review logs:** Check Flask application logs
3. **Database issues:** Verify schema with `apply_relevance_ai_schema.py`
4. **API issues:** Test RelevanceAI connection directly

## 📝 Changelog

### v1.0.0 (Initial Integration)
- ✅ Multi-provider support (Bolna, RelevanceAI, OpenAI)
- ✅ RelevanceAI agent creation and management
- ✅ Session and message handling
- ✅ Webhook integration
- ✅ Enhanced UI with provider selection
- ✅ Comprehensive test suite
- ✅ Database schema updates
- ✅ Analytics and monitoring

---

**🎉 RelevanceAI integration successfully added to BhashAI platform!**

For questions or support, contact the development team or refer to the troubleshooting section above.