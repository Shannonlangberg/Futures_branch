# Fix Missing Users on Beta Branch - Volume Configuration

## Problem
All users are missing on the beta branch deployment because the database volume isn't configured correctly.

## Root Cause
Railway volumes are configured per-service. If your beta branch is a separate service or doesn't have a volume mounted, it creates a new database that doesn't persist between deployments.

## Solution: Add Volume to Beta Service

### Step 1: Check Current Volume Status

1. Go to Railway Dashboard: https://railway.app
2. Find your **beta branch service** (might be named "Beta-Branch" or similar)
3. Click on the service
4. Go to **Settings** tab
5. Scroll to **Volumes** section

### Step 2: Add Volume to Beta Service

If no volume exists:

1. Click **"New Volume"** or **"Add Volume"**
2. Set mount path to: `/data`
3. Click **"Add"** or **"Create"**
4. Railway will automatically redeploy

### Step 3: Verify Volume is Working

After deployment, check the logs:

1. Go to Railway → Beta Service → **Deployments** → Latest deployment → **View Logs**
2. Look for this line: `✅ Using persistent volume database: /data/futures_link.db`
3. If you see this, the volume is working!

### Step 4: Seed Users (If Database is Empty)

If the volume is new and empty, you need to seed users:

**Option A: Via Railway CLI**
```bash
railway link  # Link to beta service
railway run python backend/seed_users.py
```

**Option B: Via Railway Dashboard**
1. Go to your beta service
2. Click **"Deployments"** → **"New Deployment"**
3. In the command, run: `python backend/seed_users.py`
4. Or use Railway's shell/terminal feature if available

**Option C: Copy Database from Main**

If main has the users and beta should have the same data:

1. Export database from main service
2. Import to beta service volume

## Alternative: Use PostgreSQL (Recommended for Production)

PostgreSQL is shared across services and more reliable:

1. **Add PostgreSQL Service** in Railway
   - Railway Dashboard → **New** → **Database** → **Add PostgreSQL**
   
2. **Connect Beta Service to PostgreSQL**
   - Railway automatically sets `DATABASE_URL` environment variable
   - Your app will automatically use PostgreSQL

3. **Run Migrations**
   - Connect to PostgreSQL
   - Run all migrations from `backend/migrations/`

4. **Seed Users**
   - Run `python backend/seed_users.py` (it will use PostgreSQL automatically)

## Verify Both Services Have Volumes

### Main Service
- Check: Railway → Main Service → Settings → Volumes
- Should have: Volume mounted at `/data`

### Beta Service  
- Check: Railway → Beta Service → Settings → Volumes
- Should have: Volume mounted at `/data`

## Important Notes

- **Separate Services = Separate Volumes**: If main and beta are different Railway services, they have separate volumes. Users in main won't appear in beta unless you copy the database.

- **Same Service, Different Branches**: If they're the same service with different branch deployments, they should share the volume automatically.

- **Volume Path**: The app checks for volumes at:
  - `/data` (primary - recommended)
  - `/app/backend/instance` (fallback)
  - `/app/data` (fallback)

## Quick Check Commands

To verify which database path is being used, check the deployment logs for:
- `✅ Using persistent volume database: /data/futures_link.db` (GOOD - volume working)
- `⚠️  No persistent volume detected!` (BAD - no volume, data will be lost)

## Next Steps After Fixing

1. ✅ Add volume to beta service at `/data`
2. ✅ Verify volume is detected in logs
3. ✅ Seed users: `python backend/seed_users.py`
4. ✅ Test login with seeded users
5. ✅ Verify users persist after redeployment

