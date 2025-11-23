# 📧 Email Service Module (SMTP)

Standalone SMTP email service for event confirmations and notifications.

## 📦 What's Included

- `backend/email_service.py` - Complete EmailService class
- `config/.env.example` - Environment variable template
- `docs/API.md` - Usage documentation

## 🚀 Quick Start

### 1. Copy Files
```bash
cp modules/email-service/backend/email_service.py your-project/backend/
```

### 2. Install Dependencies
```bash
# No external dependencies - uses Python standard library
```

### 3. Set Environment Variables
```bash
# .env file
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=events@yourchurch.com
SENDER_PASSWORD=your_app_password
SENDER_NAME=Your Church Events
```

### 4. Use It
```python
from email_service import EmailService

service = EmailService()

# Send registration confirmation
service.send_registration_confirmation(registration, event)

# Send reminder
service.send_event_reminder(registration, event)
```

## 📋 Features

- ✅ Registration confirmations
- ✅ Event reminders
- ✅ Waitlist notifications
- ✅ HTML email templates
- ✅ Plain text fallback

## 🔧 Configuration

See `config/.env.example` for all configuration options.

## 📚 Documentation

See `docs/API.md` for complete API reference.


