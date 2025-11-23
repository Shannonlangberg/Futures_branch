# 📧 SendGrid Email Service Module

Standalone SendGrid service for professional email campaigns with engagement tracking.

## 📦 What's Included

- `backend/sendgrid_service.py` - Complete SendGridService class
- `config/.env.example` - Environment variable template
- `docs/API.md` - Usage documentation

## 🚀 Quick Start

### 1. Copy Files
```bash
cp modules/sendgrid-service/backend/sendgrid_service.py your-project/backend/
```

### 2. Install Dependencies
```bash
pip install sendgrid
```

### 3. Set Environment Variables
```bash
# .env file
SENDGRID_API_KEY=your_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourchurch.com
SENDGRID_FROM_NAME=Your Church Name
SENDGRID_UNSUBSCRIBE_GROUP_ID=12345
```

### 4. Use It
```python
from sendgrid_service import SendGridService

service = SendGridService()

# Send campaign email
result = service.send_campaign_email(
    campaign_data={
        "subject_line": "Weekly Update",
        "content": "<html>...</html>",
        "content_text": "Plain text version"
    },
    recipients=[
        {"email": "user@example.com", "name": "John Doe"}
    ]
)
```

## 📋 Features

- ✅ Email campaign sending
- ✅ Template management
- ✅ Engagement tracking (opens, clicks)
- ✅ Personalization
- ✅ Unsubscribe management
- ✅ HTML and plain text support

## 🔧 Configuration

See `config/.env.example` for all configuration options.

## 📚 Documentation

See `docs/API.md` for complete API reference.


