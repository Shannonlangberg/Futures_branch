# Railway Volume Setup Guide - Keep Events Data Between Deployments

## Why You Need This
Without a persistent volume, your database (and all events data) gets wiped every time Railway redeploys your app.

## Step-by-Step: Adding a Volume in Railway

### Method 1: Using Railway Web Dashboard

1. **Go to Railway Dashboard**
   - Open https://railway.app
   - Log in and select your project

2. **Select Your Service**
   - Click on the service that runs your app (usually named something like "Futures_branch" or "futuresbranch")

3. **Open Settings Tab**
   - Click on the **"Settings"** tab at the top

4. **Find Volumes Section**
   - Scroll down to find the **"Volumes"** section
   - If you don't see it, Railway might not support volumes for your plan, or you need to upgrade

5. **Create New Volume**
   - Click **"New Volume"** or **"Add Volume"** button
   - In the mount path field, enter: `/data`
   - Click **"Add"** or **"Create"**

6. **Redeploy**
   - Railway will automatically redeploy your service
   - The volume will persist your database between deployments

### Method 2: Using Railway CLI (Alternative)

If you have Railway CLI installed:

```bash
railway volume create --mount /data
```

### Method 3: Use Railway PostgreSQL (Recommended for Production)

Instead of SQLite with volumes, use Railway's PostgreSQL service:

1. **Add PostgreSQL Service**
   - In Railway dashboard, click **"New"**
   - Select **"Database"** → **"Add PostgreSQL"**
   - Railway automatically creates the database

2. **Connect Your App**
   - Railway automatically sets `DATABASE_URL` environment variable
   - Your app will automatically use PostgreSQL (no code changes needed!)

3. **Run Migrations**
   - Connect to your PostgreSQL database
   - Run the migration: `backend/migrations/028_enhanced_events_module.sql`

## Verify It's Working

After setting up the volume, check your logs:

1. Go to Railway → Your Service → **"Deployments"** → Click latest deployment → **"View Logs"**
2. Look for a line like: `Using persistent volume database: /data/futures_link.db`
3. If you see this, the volume is working!

## Troubleshooting

**Can't find Volumes section?**
- You might be on a plan that doesn't support volumes
- Consider upgrading or using PostgreSQL instead

**Volume not persisting?**
- Make sure the mount path is exactly `/data`
- Check that the volume was created successfully in Settings
- Verify in logs that it's using the volume path

**Still losing data?**
- Check Railway logs to see which database path is being used
- Make sure you're not accidentally using a different database file
- Consider switching to PostgreSQL for guaranteed persistence

## Current Status

The code now automatically checks for volumes at:
- `/data` (primary - recommended)
- `/app/backend/instance` (fallback)
- `/app/data` (fallback)

If no volume is found, it falls back to the default SQLite location (which won't persist).

