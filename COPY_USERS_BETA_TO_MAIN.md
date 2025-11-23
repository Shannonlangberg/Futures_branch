# Copy Users from Beta to Main

This guide shows how to copy all users from the beta database to the main database.

## Prerequisites

- Railway CLI installed (`npm i -g @railway/cli`)
- Access to both beta and main services

## Method 1: Using Railway CLI (Recommended)

### Step 1: Export Users from Beta

1. Link to your beta service:
   ```bash
   railway link
   # Select your beta service when prompted
   ```

2. Run the export script:
   ```bash
   railway run python backend/copy_users_beta_to_main.py export
   ```

   This will:
   - Export all users from beta database
   - Save them to `backend/users_export_from_beta.json`

3. Download the export file:
   ```bash
   railway run cat backend/users_export_from_beta.json > users_export_from_beta.json
   ```
   
   Or use Railway dashboard to download the file from the service.

### Step 2: Import Users to Main

1. Link to your main service:
   ```bash
   railway link
   # Select your main service when prompted
   ```

2. Upload the export file (if you downloaded it):
   ```bash
   # Copy the file to the service
   railway run --service main -- sh -c "cat > backend/users_export_from_beta.json" < users_export_from_beta.json
   ```

   Or upload via Railway dashboard.

3. Run the import script:
   ```bash
   railway run python backend/copy_users_beta_to_main.py import
   ```

   This will:
   - Load users from the export file
   - Import new users to main
   - Update existing users in main (if they already exist)

## Method 2: Using Railway Dashboard

### Step 1: Export from Beta

1. Go to Railway Dashboard → Beta Service
2. Go to **Deployments** → Latest deployment
3. Use the terminal/shell feature (if available) or create a new deployment with:
   ```bash
   python backend/copy_users_beta_to_main.py export
   ```
4. Download the `users_export_from_beta.json` file from the service

### Step 2: Import to Main

1. Go to Railway Dashboard → Main Service
2. Upload `users_export_from_beta.json` to the service
3. Use terminal/shell or create a deployment with:
   ```bash
   python backend/copy_users_beta_to_main.py import
   ```

## What Gets Copied

The script copies:
- ✅ Username
- ✅ Password hash (users keep their passwords)
- ✅ Full name
- ✅ Email
- ✅ Role
- ✅ Campus assignment
- ✅ Active status
- ✅ Last login timestamp

## Important Notes

- **Existing users**: If a user with the same username already exists in main, their data will be **updated** (not duplicated)
- **New users**: Users that don't exist in main will be **created**
- **Passwords**: Users keep their existing passwords from beta
- **IDs**: User IDs may change (they're auto-incremented), but usernames are preserved

## Verification

After importing, verify users are in main:

1. Check the logs for: `✅ Successfully imported X new users and updated Y existing users`
2. Log into main service and verify users can log in
3. Check user list in the admin panel

## Troubleshooting

**"Beta database not found"**
- Make sure you're running export on the beta service
- Check that the volume is mounted at `/data`

**"Main database not found"**
- Make sure you're running import on the main service
- Check that the volume is mounted at `/data`

**"users table does not exist"**
- Run migrations first: The database needs to have migrations applied
- Check that migrations have run on both services

**"Export file not found"**
- Make sure you ran the export step first
- Check the file path: `backend/users_export_from_beta.json`

