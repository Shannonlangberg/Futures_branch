# Futures LINK

**Modern Church Management Dashboard**

## Features

### ✅ Dashboard
- Campus-specific dashboards
- National overview for leadership
- Real-time statistics and charts
- YTD attendance and tithe tracking
- Previous year comparisons

### ✅ Input Page
- Quick stats logging
- Service-time breakdown
- Kids ministry tracking
- Automated data submission to Google Sheets

### ✅ Finance
- Tithe tracking by campus
- Breakdown: General, Trust, Online, Building Fund
- Separate finance dashboard
- Role-based access control

### ✅ Settings
- Campus management
- Multi-region support (AU, US, Brazil, Indonesia)
- Service time configuration
- Pastor assignments

## Tech Stack

**Backend:**
- Python 3.11+
- Flask
- SQLite
- Google Sheets API

**Frontend:**
- React 18
- Vite
- Tailwind CSS
- Chart.js
- Three.js (animations)

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create `.env` in backend directory:
```
GOOGLE_CREDENTIALS_PATH=path/to/credentials.json
SHEET_ID=your_sheet_id
SECRET_KEY=your_secret_key
```

## User Roles

- **Admin**: Full access
- **Senior Leader**: All campuses + finance
- **Campus Pastor**: Assigned campus only
- **Finance**: Finance page only
- **Pastor**: Input page only

## Deployment

See `DEPLOYMENT.md` for Railway deployment instructions.

## Support

Contact: shannon.langberg@futures.church
