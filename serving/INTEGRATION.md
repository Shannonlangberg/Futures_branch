# 🔌 Serving Block - Integration Guide

## Step 1: Backend Setup

### 1.1 Copy Files
```bash
# Copy backend files
cp blocks/serving/backend/serving_api.py your-backend/
cp blocks/serving/backend/serving_models.py your-backend/
```

### 1.2 Install Dependencies
Add to `requirements.txt`:
```
Flask>=2.0.0
Flask-Login>=0.6.0
Flask-SQLAlchemy>=3.0.0
SQLAlchemy>=2.0.0
```

### 1.3 Run Migration
```bash
sqlite3 your_database.db < blocks/serving/migrations/004_serving_module.sql
```

### 1.4 Register Blueprint
In `app.py`:
```python
from serving_api import serving_bp
app.register_blueprint(serving_bp)
```

### 1.5 Update Models Import
In `serving_models.py`, ensure:
```python
from models import db  # Or your db location
```

## Step 2: Frontend Setup

### 2.1 Copy Components
```bash
cp -r blocks/serving/frontend/components/* src/components/serving/
cp blocks/serving/frontend/pages/ServingDashboard.jsx src/pages/
```

### 2.2 Add Route
```jsx
import ServingDashboard from './pages/ServingDashboard';

<Route path="/serving" element interpretations={<ServingDashboard />} />
```

## Step 3: Dependencies

The serving module requires:
- Person model (for user/member tracking)
- Campus data
- Permission system (optional but recommended)

## Step 4: Configuration

Ensure your app provides:
- User authentication
- Campus information
- Person/member database

See [README.md](./README.md) for full feature list.


