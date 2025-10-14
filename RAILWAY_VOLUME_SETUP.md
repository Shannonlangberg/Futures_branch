# Railway Volume Setup Required

## Problem
The database is being wiped on every deployment because it's stored inside the ephemeral container.

## Solution
Create a persistent volume in Railway:

### Steps:
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add a new variable: `RAILWAY_VOLUME_MOUNT_PATH` = `/app/backend/instance`
5. Go to "Settings" tab
6. Scroll to "Volumes" section
7. Click "New Volume"
8. Mount path: `/app/backend/instance`
9. Save and redeploy

### Alternative: Use Railway PostgreSQL
If volumes don't work, switch to Railway's PostgreSQL addon for persistent storage.

### Current Status
- Migration 014 deletes all users
- Seed script inserts 5 users
- But without a persistent volume, they're lost on each deployment

