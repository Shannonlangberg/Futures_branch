# Futures LINK - Setup Guide

## 🎯 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Sheets API credentials

### Step 1: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create `backend/.env` (or copy `ENV_TEMPLATE.txt` and adjust values):

```env
# Flask
SECRET_KEY=your_random_secret_key_here
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173

# Google Sheets (paste full JSON from Google Cloud)
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"your-project","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"service-account@your-project.iam.gserviceaccount.com"}
GOOGLE_SHEET_NAME=Stats

# Database (SQLite default)
DATABASE_URL=sqlite:///futures_link.db
# Optional: switch to Postgres
# DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/futures_pulse
```

### Step 3: Google Sheets Setup

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com
   - Create new project

2. **Enable Google Sheets API**
   - In API Library, search "Google Sheets API"
   - Click Enable

3. **Create Service Account**
   - Go to "Credentials"
   - Create Service Account
   - Download JSON key file
   - Save as `backend/credentials.json`

4. **Share Google Sheet**
   - Open your Google Sheet
   - Click Share
   - Add service account email (from JSON)
   - Give "Editor" permission

5. **Get Sheet ID**
   - From URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Copy SHEET_ID_HERE

### Step 4: Database Setup

1. SQLite (default – nothing extra required)  
   - The app will create `instance/church_voice.db` (regions, campuses)  
   - And `futures_link.db` for SQLAlchemy tables on first run

2. Postgres (recommended for multi-campus scaling)  
   - Install Postgres locally (e.g. `brew install postgresql` on macOS)  
   - Create a database: `createdb futures_pulse`  
   - Update `DATABASE_URL` in `.env`, e.g. `postgresql+psycopg2://postgres:password@localhost:5432/futures_pulse`  
   - Optional tuning: set `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, etc. as needed

On first run the backend will create any missing SQLAlchemy tables automatically.  
To populate the legacy `church_voice.db` tables (regions, campuses) you can still run:

```bash
cd backend
python migrate_regions.py
```

### Step 5: Start Backend

```bash
cd backend
python app.py
```

Backend runs on: http://localhost:5002

### Step 6: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: http://localhost:5173

### Step 7: Login

Default credentials:
- **Username**: admin
- **Password**: futures2025

⚠️ **Change password after first login!**

---

## 🚀 Railway Deployment

### Step 1: Prepare Project

```bash
cd futures-link

# Build frontend for production
cd frontend
npm install
npm run build

# This creates frontend/dist/
# Flask will serve these static files
```

### Step 2: Create Railway Project

1. Go to https://railway.app
2. Create new project
3. Choose "Deploy from GitHub repo" or "Empty Project"

### Step 3: Configure Environment Variables

Add these in Railway dashboard:

```env
# Google Sheets
GOOGLE_CREDENTIALS_PATH=/app/backend/credentials.json
SHEET_ID=your_sheet_id

# Flask
SECRET_KEY=generate_strong_random_key
FLASK_ENV=production
PORT=5002

# Database
DATABASE_URL=sqlite:///instance/church_voice.db
```

### Step 4: Upload Google Credentials

In Railway:
1. Go to "Variables"
2. Click "Raw Editor"
3. Add entire JSON credentials as multi-line string
4. Or upload `credentials.json` to backend folder

### Step 5: Deploy

**Option A: GitHub**
```bash
git init
git add .
git commit -m "Initial Futures LINK deployment"
git remote add origin your_github_repo
git push -u origin main
```

Then connect Railway to GitHub repo.

**Option B: Railway CLI**
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Step 6: Verify Deployment

1. Wait for build to complete
2. Railway provides public URL
3. Test login
4. Test each feature:
   - Dashboard (all campuses)
   - Input stats
   - Finance submission
   - Campus management

---

## 🔐 User Management

### Default Users

**Admin** (Full Access)
- Username: `admin`
- Password: `futures2025`
- Role: `admin`
- Campus: `all_campuses`

**Finance**
- Username: `Finance`
- Password: `futures2025`
- Role: `finance`
- Campus: `all_campuses`

### Adding Campus Pastors

Edit `backend/users.json`:

```json
{
  "users": {
    "ps_tony": {
      "id": "ps_tony",
      "username": "Tony Paradise",
      "password_hash": "placeholder",
      "email": "tony@futures.church",
      "full_name": "Tony Pastor",
      "role": "campus_pastor",
      "campus": "paradise",  ← Assign their campus
      "active": true,
      "created_date": "2025-10-09"
    }
  }
}
```

Campus pastor will:
- ✅ See ONLY their campus dashboard
- ✅ Log stats for their campus
- ❌ Cannot see other campuses
- ❌ Cannot see Australia overview

---

## 📊 Google Sheet Structure

### Tab 1: Stats

Headers (Columns A-AD):
```
Timestamp | Date | Campus | 9:00 AM | 10:00 AM | 11:00 AM | 5:00 PM | 5:30 PM | 
Youth Attendance | First Time Christians | Just Visiting | Rededications | 
New Kids | New Kids Salvations | Youth Salvations | Connect Groups | 
Info Gathered | Dream Team | Baptisms | Child Dedications | Kids 9:00 AM | 
Kids 10:00 AM | Kids 11:00 AM | Kids 5:00 PM | Kids 5:30 PM | Kids Leaders | 
Total People in Campus
```

### Tab 2: Tithe

Headers (Columns A-H):
```
Timestamp | Date | Campus | General | Trust | Online Giving | Building Fund | Total
```

---

## 🏗️ Project Structure

```
futures-link/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── users.json                # User accounts & roles
│   ├── requirements.txt          # Python dependencies
│   ├── config/
│   │   ├── feature_flags.py      # Feature toggles
│   │   └── roles.yaml            # Role definitions
│   ├── utils/
│   │   ├── rbac.py               # Role-based access control
│   │   └── campus_scope.py       # Campus filtering
│   ├── migrations/
│   │   └── 011_regions_support.sql
│   ├── instance/
│   │   ├── church_voice.db       # Main database
│   │   └── futures_link.db       # SQLAlchemy database
│   └── static/                   # Frontend build output
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Main app & routing
│   │   ├── components/
│   │   │   └── MainLayout.jsx    # Navigation & layout
│   │   └── pages/
│   │       ├── Login.jsx         # Login page
│   │       ├── Dashboard.jsx     # Main dashboard
│   │       ├── CampusSelector.jsx
│   │       ├── CampusDashboard.jsx
│   │       ├── LogStats.jsx      # Input page
│   │       ├── Finance.jsx       # Finance dashboard
│   │       └── CampusManagement.jsx
│   ├── package.json
│   └── vite.config.js
│
├── README.md
├── DEPLOYMENT.md
├── railway.json
└── Procfile
```

---

## 🧪 Testing

### Test User Roles

1. **Admin Login**
   - Should see all navigation
   - Should see campus selector
   - Should see all campuses + Australia

2. **Finance Login**
   - Should ONLY see Finance in navigation
   - Should see all campuses for tithe input
   - Should NOT see Dashboard

3. **Campus Pastor** (create test user)
   - Should auto-load their campus
   - Should NOT see campus selector
   - Should NOT see other campuses

### Test Features

✅ Dashboard
- [ ] Campus selector shows all regions
- [ ] Campus cards clickable
- [ ] Modals show detailed breakdowns
- [ ] Charts display YTD data
- [ ] Previous year comparison works

✅ Input Page
- [ ] Service times match campus config
- [ ] Kids attendance by service
- [ ] Stats submit to Google Sheets
- [ ] Auto-calculates totals

✅ Finance
- [ ] All campuses visible
- [ ] Breakdown: General, Trust, Online, Building
- [ ] Submits to "Tithe" tab
- [ ] Shows in dashboard modal

✅ Settings
- [ ] Campus management
- [ ] Add/edit/delete campuses
- [ ] Service times configurable
- [ ] Pastor assignments

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check port 5002 is free
lsof -ti:5002 | xargs kill -9

# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend build fails
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Google Sheets API errors
- Verify credentials.json is valid
- Check service account has Sheet access
- Ensure Sheet ID is correct
- Check API is enabled in Google Cloud

### Database errors
```bash
# Delete and recreate
rm -rf backend/instance/*.db
python backend/migrate_regions.py
```

### Authentication issues
- Clear browser cookies
- Check session secret key is set
- Verify users.json is valid JSON

---

## 📞 Support

**Technical Issues**
- Check logs: `backend/logs/`
- Review Railway deployment logs
- Check browser console (F12)

**Contact**
- Email: shannon.langberg@futures.church
- Repository: [Your GitHub URL]

---

## 🔄 Updates & Maintenance

### Updating Code
```bash
# Pull latest
git pull origin main

# Update backend
cd backend
pip install -r requirements.txt --upgrade

# Update frontend
cd frontend
npm install
npm run build

# Restart servers
```

### Database Migrations
When schema changes:
```bash
cd backend
python migrate_regions.py
```

### Backup
```bash
# Backup databases
cp backend/instance/*.db backups/

# Backup users
cp backend/users.json backups/

# Backup Google Sheet (manually export)
```

---

**Version**: 5.1  
**Last Updated**: October 9, 2025  
**Status**: ✅ Production Ready


