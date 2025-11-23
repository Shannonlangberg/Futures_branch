# 🔌 Devotions Block - Integration Guide

## Step 1: Backend Setup

### 1.1 Copy Files
```bash
cp blocks/devotions/backend/devotions_api.py your-backend/
cp blocks/devotions/backend/devotions_admin_api.py your-backend/
```

### 1.2 Run Migration
```bash
sqlite3 your_database.db < blocks/devotions/migrations/001_devotions_module.sql
```

### 1.3 Register Blueprints
In `app.py`:
```python
from devotions_api import devotions_bp
from devotions_admin_api import devotions_admin_bp

app.register_blueprint(devotions_bp)
app.register_blueprint(devotions_admin_bp)
```

## Step 2: Frontend Setup

### 2.1 Copy Components
```bash
cp blocks/devotions/frontend/components/* src/components/
cp blocks/devotions/frontend/pages/* src/pages/
```

### 2.2 Add Routes
```jsx
import DevotionsAdmin from './pages/DevotionsAdmin';
import DevotionPlanManager from './pages/DevotionPlanManager';

<Route path="/devotions" element={<DevotionsAdmin />} />
<Route path="/devotions/plans" element={<DevotionPlanManager />} />
```

## Step 3: Privacy Configuration

The devotions block enforces positive-only responses. Ensure:
- No attendance tracking
- No streak counting  
- Row-level security enabled
- Positive language guard active

## Step 4: Customization

- Add custom devotion plans
- Customize reading themes
- Configure note tags
- Set up sharing permissions

See [README.md](./README.md) for full feature list.


