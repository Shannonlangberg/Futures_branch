# Railway Setup for Passport (Separate from Stats App)

This is a **NEW Railway project** for testing Passport - your existing stats app won't be touched.

## Setup Steps:

### Option 1: Deploy from GitHub (Recommended)

If you have your code on GitHub:

1. **Push your code to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Add Passport integration"
   git push origin main
   ```

2. **Create New Railway Project**:
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repo
   - Name it: `futures-pulse-passport-test` (or whatever you want)

3. **Configure Build Settings**:
   
   In Railway dashboard, go to your service settings:
   
   **Build Command:**
   ```bash
   cd frontend && npm install && npm run build && cp -r dist/* ../backend/static/
   ```
   
   **Start Command:**
   ```bash
   cd backend && python app.py
   ```
   
   **Root Directory:**
   Leave empty (or set to project root)

4. **Set Environment Variables**:
   
   Add these in Railway (Settings > Variables):
   
   ```
   PORT=5002
   DATABASE_URL=sqlite:///./dev.db
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=production
   ```

### Option 2: Deploy from Local (No GitHub Needed)

If you don't have GitHub or want to deploy directly:

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Create New Project**:
   ```bash
   cd /Users/shannonlangberg/Documents/Futures_PulseV1.1
   railway init
   railway link  # Link to a new project
   ```

3. **Set Build Command**:
   ```bash
   railway variables set BUILD_COMMAND="cd frontend && npm install && npm run build && cp -r dist/* ../backend/static/"
   railway variables set START_COMMAND="cd backend && python app.py"
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

## What This Does:

- ✅ Builds frontend with Passport included
- ✅ Runs backend with Passport API routes
- ✅ Completely separate from your stats app
- ✅ Safe to test without affecting production

## If You Want to Use This Setup Later:

Once you've tested and it works, you can:
1. Merge Passport into your main stats app
2. Or keep them separate

## Notes:

- This uses the same codebase but deploys as a separate project
- Your existing stats app on Railway is untouched
- You can delete this test project anytime
