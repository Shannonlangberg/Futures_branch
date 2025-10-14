# 🚀 Deploy Futures Link to Railway - Complete Guide

## ✅ What's Already Done

- ✅ Frontend built (production-ready)
- ✅ Git repository initialized
- ✅ All code committed
- ✅ `.gitignore` configured
- ✅ Railway config (`railway.json`) ready
- ✅ GitHub CLI installed

---

## 📦 Option 1: Deploy via GitHub (Recommended)

### Step 1: Authenticate with GitHub (Required once)

Run this command:
```bash
cd /Users/shannonlangberg/Documents/futures-link
gh auth login --web
```

**When prompted:**
1. Copy the one-time code shown
2. Press Enter to open browser
3. Paste the code at https://github.com/login/device
4. Authorize GitHub CLI

### Step 2: Create GitHub Repository

```bash
gh repo create futures-link --private --source=. --remote=origin --push
```

This will:
- Create a private repo named `futures-link`
- Add it as remote origin
- Push all code automatically

### Step 3: Connect Railway to GitHub

1. Go to https://railway.app
2. Open your **Futures_LINK** project
3. Click **"New Service"** → **"GitHub Repo"**
4. Select `futures-link`
5. Railway will auto-deploy! 🎉

---

## 📦 Option 2: Deploy via Railway CLI (Alternative)

### Step 1: Login to Railway

```bash
railway login
```

This opens your browser for authentication.

### Step 2: Link to Your Project

```bash
cd /Users/shannonlangberg/Documents/futures-link
railway link
```

Select **"Futures_LINK"** from the list.

### Step 3: Deploy

```bash
railway up
```

---

## 🔑 Required Environment Variables

After deployment starts, add these in Railway Dashboard:

Go to: **Project** → **Variables** → **Add Variable**

### Required Variables:

```bash
# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS=<paste entire contents of backend/credentials.json>
GOOGLE_SHEET_NAME=<your Google Sheet name>

# Flask Configuration
SECRET_KEY=<generate a random secret - use: python -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=production

# CORS (update with your Railway URL after first deploy)
CORS_ORIGINS=https://your-app-name.up.railway.app

# Optional
LOG_LEVEL=INFO
```

### To Get Your credentials.json Content:

```bash
cat /Users/shannonlangberg/Documents/futures-link/backend/credentials.json
```

Copy the entire output and paste as the value for `GOOGLE_SHEETS_CREDENTIALS`.

---

## 🎯 Quick Deploy Commands (Copy & Paste)

### For GitHub Method:
```bash
cd /Users/shannonlangberg/Documents/futures-link
gh auth login --web
gh repo create futures-link --private --source=. --remote=origin --push
```

Then connect Railway to GitHub repo via dashboard.

### For Railway CLI Method:
```bash
cd /Users/shannonlangberg/Documents/futures-link
railway login
railway link
railway up
```

---

## 📋 Post-Deployment Checklist

After deployment completes:

1. ✅ Get your Railway URL (shown in dashboard)
2. ✅ Update `CORS_ORIGINS` environment variable with Railway URL
3. ✅ Test login at your Railway URL
4. ✅ Verify dashboard loads with Google Sheets data
5. ✅ Test adding finance data
6. ✅ Test user management (admin role)
7. ✅ Test data export
8. ✅ Test profile settings

---

## 🐛 Troubleshooting

### Build Fails

**Issue:** Frontend build fails
```bash
cd frontend && npm install && npm run build
```

**Issue:** Python packages fail
```bash
cd backend && pip install -r requirements.txt
```

### Google Sheets Not Working

1. Verify `GOOGLE_SHEETS_CREDENTIALS` is set correctly
2. Check service account email has Editor access to sheet
3. Verify sheet name matches `GOOGLE_SHEET_NAME` variable

### Static Files Not Loading

Railway should serve from `backend/static/` automatically. If issues:
- Check `backend/app.py` has `@app.route('/')` serving `index.html`
- Verify `frontend/dist/` contents were copied to `backend/static/`

### CORS Errors

Update `CORS_ORIGINS` with exact Railway URL (no trailing slash):
```
https://futures-link-production.up.railway.app
```

---

## 🎉 You're Ready!

**Current Status:** 
- Code: ✅ Ready
- Build: ✅ Complete  
- Config: ✅ Set

**Next:** Choose Option 1 or 2 above and run the commands!

**Railway Project:** Futures_LINK  
**Local Path:** `/Users/shannonlangberg/Documents/futures-link`

---

*Generated: October 14, 2025*

