# PostgreSQL Setup Guide - Persistent Database for Events

## Why PostgreSQL?
- ✅ **Persistent by default** - Data survives deployments
- ✅ **Available on all Railway plans** (including free)
- ✅ **Better performance** than SQLite
- ✅ **Production-ready** database

## Step-by-Step: Add PostgreSQL to Railway

### 1. Add PostgreSQL Service
1. Go to your Railway project dashboard
2. Click **"New"** button (top right)
3. Select **"Database"**
4. Click **"Add PostgreSQL"**
5. Railway will automatically create the database

### 2. Connect Your App (Automatic!)
- Railway automatically sets the `DATABASE_URL` environment variable
- Your app will automatically detect and use PostgreSQL
- **No code changes needed!**

### 3. Run the Migration
After PostgreSQL is added, you need to run the migration to create the new tables:

#### Option A: Using Railway's Database Tab
1. In Railway, click on your **PostgreSQL service**
2. Go to the **"Data"** or **"Query"** tab
3. Copy and paste the contents of `backend/migrations/028_enhanced_events_module_postgres.sql`
4. Click **"Run"** or **"Execute"**

#### Option B: Using psql (Command Line)
1. In Railway PostgreSQL service, go to **"Connect"** tab
2. Copy the connection string
3. Connect using psql:
   ```bash
   psql "your-connection-string"
   ```
4. Run the migration:
   ```sql
   \i backend/migrations/028_enhanced_events_module_postgres.sql
   ```

#### Option C: Using Railway CLI
```bash
railway connect postgres
# Then run the SQL migration file
```

### 4. Verify It's Working
Check your app logs after deployment. You should see:
- No SQLite warnings
- Database connection successful
- Tables created successfully

## Migration Files
- **SQLite**: `backend/migrations/028_enhanced_events_module.sql`
- **PostgreSQL**: `backend/migrations/028_enhanced_events_module_postgres.sql`

## What Happens to Existing Data?
- If you have existing events in SQLite, they won't automatically transfer
- You'll need to export from SQLite and import to PostgreSQL (if needed)
- For a fresh start, just run the migration and start creating events

## Benefits
✅ Events persist between deployments  
✅ Better performance for large datasets  
✅ Supports concurrent connections  
✅ Production-ready database  
✅ No volume setup needed  

## Troubleshooting

**Can't find "Add PostgreSQL" option?**
- Make sure you're in the Railway project dashboard
- Try refreshing the page
- Check if you're on the correct Railway plan

**Migration fails?**
- Make sure you're using the PostgreSQL version of the migration
- Check that the `events` table already exists
- Verify you have the correct permissions

**App still using SQLite?**
- Check that `DATABASE_URL` environment variable is set in Railway
- Verify the connection string starts with `postgresql://`
- Check app logs to see which database is being used

