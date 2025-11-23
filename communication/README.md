# 💬 Communication Platform Module

Complete communication platform with email and SMS campaigns, targeting, and engagement tracking.

## 📦 What's Included

- `backend/communication_api.py` - Flask Blueprint with API routes
- `backend/communication_models.py` - Database models
- `backend/campaign_manager.py` - Campaign orchestration
- `migrations/002_communication_tables.sql` - Database migration
- `docs/API.md` - API documentation

## 🚀 Quick Start

### 1. Copy Files
```bash
cp modules/communication/backend/* your-project/backend/
cp modules/communication/migrations/* your-project/migrations/
```

### 2. Install Dependencies
```bash
pip install sendgrid twilio flask flask-login sqlalchemy
```

### 3. Set Environment Variables
```bash
# SendGrid
SENDGRID_API_KEY=your_key
SENDGRID_FROM_EMAIL=noreply@church.com

# Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890
```

### 4. Run Migration
```bash
sqlite3 your_db.db < migrations/002_communication_tables.sql
```

### 5. Register Blueprint
```python
from communication_api import communication_bp
app.register_blueprint(communication_bp)
```

## 📋 Features

- ✅ Email campaigns (SendGrid)
- ✅ SMS campaigns (Twilio)
- ✅ Smart targeting (campus, department, tags, engagement)
- ✅ Engagement tracking
- ✅ Analytics and reporting
- ✅ Template management
- ✅ Scheduling

## 🔧 Dependencies

- SendGrid Service (included in this module)
- Twilio Service (included in this module)
- Person/User model for targeting
- Flask-Login for authentication

## 📚 Documentation

See `docs/API.md` for complete API reference.


