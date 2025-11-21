# Deploy Prayer & Praise Fix - URGENT

## Issue
Mobile app getting **502 errors** when submitting prayer requests to production.

Error: `❌ API Error: 502 - /api/prayer/requests`

## Root Cause
The prayer/praise endpoints are either:
1. Not deployed to production (Railway)
2. Missing the `heartbeat_care_cases` table in production DB
3. Backend server needs restart

## Quick Fix Steps

### Option 1: Deploy to Railway (RECOMMENDED)

```bash
# 1. Commit the changes
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1
git add backend/prayer_api.py backend/models.py backend/migrations/024_create_prayer_links.sql backend/app.py
git commit -m "Fix: Add prayer & praise endpoints with better error logging"

# 2. Push to Beta-Branch (Railway will auto-deploy)
git push origin Beta-Branch

# 3. Wait 2-3 minutes for deployment
# 4. Check logs in Railway dashboard
```

### Option 2: Manual Database Migration on Production

If the issue is a missing table, you need to run the migrations on production:

**Via Railway CLI:**
```bash
# Connect to production database
railway run --service futuresbranch-production

# Then in the Railway shell:
sqlite3 /app/backend/futures_link.db < /app/backend/migrations/024_create_prayer_links.sql
```

**Or via Railway Dashboard:**
- Go to your Railway project
- Click on the service
- Go to "Database" or "Volumes"
- Connect and run the migration SQL

### Option 3: Quick Restart

Sometimes just restarting the service helps:

1. Go to Railway Dashboard
2. Click on your service
3. Click "Restart"
4. Wait for it to come back online

## Verify Fix

### Test from Mobile App
1. Open mobile app
2. Go to Prayer tab (🙏)
3. Submit a test prayer request
4. Should see success message

### Test from API
```bash
curl -X POST https://futuresbranch-production.up.railway.app/api/prayer/requests \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "request": "Test prayer request"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Prayer request received",
  "id": 123
}
```

### Check Logs
Look for these in Railway logs:
- ✅ `Prayer request endpoint called`
- ✅ `Looking up person: email@example.com`
- ✅ `✅ Prayer request created`

OR errors:
- ❌ `Person not found`
- ❌ `Error creating care case`
- ❌ `no such table: heartbeat_care_cases`

## Changes Made

### 1. Added Detailed Logging
- Every step now logs to help debug issues
- Errors include full tracebacks
- Shows exactly where failures occur

### 2. Files Modified
- ✅ `backend/prayer_api.py` - Added extensive logging
- ✅ `backend/models.py` - Added PrayerLink model
- ✅ `backend/migrations/024_create_prayer_links.sql` - New table
- ✅ `backend/app.py` - Added prayer link route
- ✅ `mobile/App.js` - Added Prayer to navigation

### 3. Database Changes
- New table: `prayer_links`
- Existing table used: `heartbeat_care_cases`
- Existing table used: `persons`

## Common Issues & Solutions

### "Person not found"
**Problem:** User email doesn't exist in the `persons` table
**Solution:** 
- User needs to be created first
- Or modify code to auto-create person (see `giving_api.py` for example)

### "no such table: heartbeat_care_cases"
**Problem:** Heartbeat migrations haven't run in production
**Solution:** 
- Run Heartbeat migrations first
- Or create the table manually in production DB

### "502 Bad Gateway"
**Problem:** Backend server crashed
**Solution:**
- Check Railway logs for Python errors
- Restart the service
- Check all dependencies are installed

### "Connection refused"
**Problem:** Backend not running
**Solution:**
- Check Railway service status
- Verify environment variables are set
- Check if service is sleeping (free tier)

## Migration SQL

If you need to manually create tables in production:

```sql
-- Prayer Links Table
CREATE TABLE IF NOT EXISTS prayer_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id TEXT UNIQUE NOT NULL,
    link_type TEXT NOT NULL DEFAULT 'both',
    campus TEXT,
    department TEXT,
    location TEXT,
    description TEXT,
    code_type TEXT DEFAULT 'qr',
    is_active INTEGER DEFAULT 1,
    scan_count INTEGER DEFAULT 0,
    submission_count INTEGER DEFAULT 0,
    last_scan_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_prayer_links_link_id ON prayer_links(link_id);
CREATE INDEX IF NOT EXISTS idx_prayer_links_campus ON prayer_links(campus);
CREATE INDEX IF NOT EXISTS idx_prayer_links_active ON prayer_links(is_active);
```

## Emergency Rollback

If prayer endpoints cause issues:

1. Comment out prayer_bp registration in app.py:
```python
# from prayer_api import prayer_bp
# app.register_blueprint(prayer_bp)
```

2. Redeploy to Railway

3. Users will see 404 instead of 502

## Next Steps

After deploying:

1. ✅ Test prayer submission from mobile app
2. ✅ Test praise submission from mobile app
3. ✅ Verify CareCases are created in Heartbeat
4. ✅ Check campus pastor routing works
5. ✅ Test web link: `/prayer/link/prayer_test123abc`
6. ✅ Add Prayer page to frontend web app (already created!)

## Support

If still having issues:

1. Check Railway logs: `railway logs --service futuresbranch-production`
2. Test locally first: `./start.sh`
3. Compare local vs production database schemas
4. Verify all environment variables are set in Railway
5. Check if database volume is mounted correctly

## Status

- ✅ Code fixed locally
- ⏳ Awaiting deployment to production
- ⏳ Need to test on production
- ⏳ Need to add Prayer page to frontend

---

**Deploy NOW to fix the mobile app!** 🚀

