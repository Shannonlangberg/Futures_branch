# 📱 Twilio SMS Service Module

Standalone Twilio SMS service for sending SMS campaigns and two-way messaging.

## 📦 What's Included

- `backend/twilio_service.py` - Complete TwilioService class
- `config/.env.example` - Environment variable template
- `docs/API.md` - Usage documentation

## 🚀 Quick Start

### 1. Copy Files
```bash
cp modules/twilio-service/backend/twilio_service.py your-project/backend/
```

### 2. Install Dependencies
```bash
pip install twilio
```

### 3. Set Environment Variables
```bash
# .env file
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/api/webhooks/twilio
```

### 4. Use It
```python
from twilio_service import TwilioService

service = TwilioService()

# Send SMS
result = service.send_sms(
    to_number="+1234567890",
    message="Hello from church!",
    sender_id="FUTURES"
)

# Send bulk SMS
result = service.send_bulk_sms(
    recipients=[{"phone": "+1234567890", "name": "John"}],
    message="Campaign message",
    sender_id="FUTURES"
)
```

## 📋 Features

- ✅ Send individual SMS
- ✅ Bulk SMS campaigns
- ✅ Two-way messaging
- ✅ Phone number validation
- ✅ Delivery tracking
- ✅ Sender ID management
- ✅ Webhook handling

## 🔧 Configuration

See `config/.env.example` for all configuration options.

## 📚 Documentation

See `docs/API.md` for complete API reference.


