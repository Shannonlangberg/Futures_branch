# Deployment Guide - Railway

## Prerequisites

1. Railway account
2. Google Sheets API credentials
3. GitHub repository (optional)

## Step 1: Prepare Files

Ensure these files are in your root:
- `backend/app.py`
- `backend/requirements.txt`
- `backend/users.json`
- `frontend/` (built static files)

## Step 2: Build Frontend

```bash
cd frontend
npm run build
```

This creates `frontend/dist/` which will be served by Flask.

## Step 3: Railway Configuration

Create `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && python app.py",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300
  }
}
```

## Step 4: Environment Variables

Add to Railway:
```
GOOGLE_CREDENTIALS_PATH=/app/backend/credentials.json
SHEET_ID=your_google_sheet_id
SECRET_KEY=generate_random_secret_key
PORT=5002
FLASK_ENV=production
```

## Step 5: Deploy

### Option A: GitHub Integration
1. Push code to GitHub
2. Connect Railway to repository
3. Railway auto-deploys

### Option B: Railway CLI
```bash
railway login
railway init
railway up
```

## Step 6: Post-Deployment

1. Test login: `https://your-app.railway.app`
2. Verify Google Sheets connection
3. Test each user role
4. Check finance submissions

## Troubleshooting

### Static files not loading
- Ensure `frontend/dist` is copied to backend/static
- Check Flask route: `@app.route('/')`

### Database errors
- Run migrations: `python migrate_regions.py`
- Check `instance/church_voice.db` exists

### Google Sheets API errors
- Verify credentials JSON is uploaded
- Check Sheet ID is correct
- Ensure service account has access to sheet

## Monitoring

Railway provides:
- Logs: Real-time application logs
- Metrics: CPU, memory, network usage
- Deployments: History and rollback

## Scaling

For high traffic:
1. Upgrade Railway plan
2. Enable auto-scaling
3. Consider Redis for session storage
4. Implement caching for Google Sheets API

---

**Production URL**: TBD
**Status**: Ready for deployment ✅
