# Bolna AI Voice Agent Integration Guide

## Overview

This integration replaces the make.com workflow with a direct Bolna API integration for triggering AI voice calls. The workflow allows users to select contacts and start bulk voice calls using Bolna AI agents.

## Workflow Architecture

```
User Dashboard → Select Contacts → Trigger Bulk Calls → Bolna API → Voice Calls
     ↓               ↓                    ↓              ↓           ↓
Contact Manager → JavaScript → Flask API → BolnaAPI → Call Logs
```

## Implementation Components

### 1. Backend Integration (`bolna_integration.py`)

**Key Features:**
- `BolnaAPI` class for Bolna platform communication
- Bulk call management with error handling
- Agent configuration mapping
- Call status tracking

**Agent Configuration:**
- Agent ID: `15554373-b8e1-4b00-8c25-c4742dc8e480`
- Sender Phone: `+918035743222`
- Support for multiple agent types (appointment booking, reminders, etc.)

### 2. API Endpoints (`main.py`)

**New Endpoints:**
- `POST /api/voice-agents/{id}/contacts/bulk-call` - Start bulk calls
- `GET /api/call-logs` - View call history  
- `GET /api/call-logs/{id}/status` - Check call status

**Request Format:**
```json
{
  "contact_ids": ["uuid1", "uuid2"],
  "campaign_name": "Campaign Name",
  "custom_variables": {
    "additional": "data"
  }
}
```

**Response Format:**
```json
{
  "message": "Bulk call campaign initiated",
  "summary": {
    "total_contacts": 5,
    "successful_calls": 4,
    "failed_calls": 1,
    "campaign_name": "Test Campaign"
  },
  "agent_config": {
    "bolna_agent_id": "15554373-b8e1-4b00-8c25-c4742dc8e480",
    "sender_phone": "+918035743222"
  }
}
```

### 3. Frontend Integration (`dashboard.html`)

**New Features:**
- "📞 Start Calls" button in Contact Manager
- Contact selection with checkboxes
- Bulk call confirmation dialogs
- Real-time results modal
- Call campaign naming

**User Flow:**
1. Open Contact Manager for any voice agent
2. Select contacts using checkboxes
3. Click "📞 Start Calls" button
4. Enter campaign name
5. Confirm bulk call action
6. View results in modal

## Configuration

### Environment Variables

Add to `.env` file:
```env
# Bolna AI Voice Agent Configuration
BOLNA_API_URL=https://api.bolna.dev
BOLNA_API_KEY=your-bolna-api-key-here
BOLNA_SENDER_PHONE=+918035743222
```

### Bolna Agent Setup

Based on the screenshots, configure:
- **Connection**: "My Bolna API connection"
- **Agent ID**: `15554373-b8e1-4b00-8c25-c4742dc8e480`
- **Recipient Phone**: Dynamic from contact selection
- **Sender Phone**: `+918035743222`
- **Variables**: Dynamic based on agent type and contact

## Agent Type Mapping

| Voice Agent Title | Bolna Configuration | Purpose |
|-------------------|-------------------|----------|
| Patient Appointment Booking | appointment_booking | Schedule patient appointments |
| Prescription Reminder Calls | prescription_reminder | Medication refill reminders |
| Lab Results Notification | prescription_reminder | Lab result notifications |
| Delivery Follow-up | delivery_followup | Logistics follow-up calls |

## Database Schema

### Call Logs Table
- Tracks all call attempts
- Stores Bolna call IDs
- Records campaign information
- Maintains call status and duration

### Activity Logs Table  
- Logs bulk call activities
- Tracks trial usage limits
- Records user actions

## Security & Permissions

### Row Level Security (RLS)
- Users can only access their enterprise data
- Call logs are enterprise-scoped
- Contact access is agent-specific

### Trial Limitations
- Integrated with existing trial middleware
- Configurable call limits
- Usage tracking and reporting

## Testing

Run the test suite:
```bash
python test_bolna_workflow.py
```

**Test Coverage:**
- Module imports and configuration
- Database schema validation
- API endpoint availability
- Agent configuration logic
- Mock API request/response

## Production Deployment

### Prerequisites
1. Valid Bolna API account and key
2. Configured Bolna agents
3. Phone number setup (+918035743222)
4. Database schema applied

### Setup Steps
1. Get Bolna API key from https://app.bolna.dev
2. Update `BOLNA_API_KEY` in `.env`
3. Configure Bolna agents in dashboard
4. Test with small contact groups
5. Monitor call logs for success rates

## Error Handling

### Common Issues
- **Missing API Key**: Configuration validation prevents startup
- **Invalid Phone Numbers**: E.164 format validation
- **Network Errors**: Retry logic and error logging
- **Rate Limits**: Handled by Bolna API

### Monitoring
- Call success/failure rates in database
- Error logs in Flask application  
- Bolna dashboard for call analytics

## Usage Example

1. **Select Contacts**: Choose contacts in dashboard
2. **Start Campaign**: Click "📞 Start Calls"
3. **Enter Details**: Campaign name and confirmation
4. **Monitor Results**: View real-time success/failure stats
5. **Track Calls**: Check call logs for detailed status

## Integration Benefits

- **No make.com dependency**: Direct API integration
- **Real-time results**: Immediate feedback on call status
- **Scalable**: Bulk operations with error handling
- **Trackable**: Complete audit trail in database
- **Flexible**: Configurable agent types and variables

## Next Steps

1. **Advanced Analytics**: Call duration and success metrics
2. **Scheduling**: Delayed call campaigns
3. **Templates**: Pre-defined campaign templates
4. **Webhooks**: Real-time call status updates from Bolna
5. **Mobile App**: Extend functionality to mobile interface