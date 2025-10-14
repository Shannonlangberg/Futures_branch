# Google Sheets Setup Guide

This guide will help you connect your Futures LINK app to Google Sheets.

## 📋 Quick Overview

Your app needs:
1. A Google Cloud Service Account (free)
2. A Google Sheet named "Stats" with specific structure
3. Credentials file or environment variable

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a Project"** → **"New Project"**
3. Name it: `futures-church` (or anything you prefer)
4. Click **"Create"**

---

## Step 2: Enable Required APIs

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for and enable these APIs:
   - **Google Sheets API** (click Enable)
   - **Google Drive API** (click Enable)

---

## Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in details:
   - **Name**: `futures-link-service`
   - **Description**: `Service account for Futures LINK app`
4. Click **"Create and Continue"**
5. **Grant this service account access to project**:
   - Role: **Editor**
   - Click **"Continue"** → **"Done"**

---

## Step 4: Generate JSON Key

1. On the Credentials page, find your new service account
2. Click on the service account email
3. Go to **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Choose **JSON** format
6. Click **"Create"**
7. A file will download automatically (e.g., `futures-church-xxxxx.json`)

---

## Step 5: Save Credentials

**Option A: Use credentials.json file (Recommended for local development)**

1. Rename the downloaded file to `credentials.json`
2. Copy it to: `/Users/shannonlangberg/Documents/futures-link/backend/credentials.json`

**Option B: Use environment variable (For production)**

1. Open the downloaded JSON file
2. Copy the entire contents (it's one long JSON object)
3. Add to your `.env` file:
   ```bash
   GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"...entire JSON here..."}
   ```

---

## Step 6: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a **New Blank Spreadsheet**
3. **Important**: Name it exactly **"Stats"** (case-sensitive)

### Tab 1: Stats

1. Keep the first sheet, rename it to **"Stats"**
2. Add these column headers in Row 1:

```
A: Timestamp
B: Date
C: Campus
D: Total People in Campus
E: Total Attendance
F: First Time
G: Visitors
H: Info Gathered
I: First Time Christians
J: Rededications
K: Youth Attendance
L: Youth Salvations
M: Youth New People
N: Kids Total
O: Kids Leaders
P: New Kids
Q: New Kids Salvations
R: Connect Groups
S: Dream Team
T: Tithe
U: Baptisms
V: Child Dedications
```

### Tab 2: Tithe

1. Click **+** at the bottom to add a new sheet
2. Name it **"Tithe"**
3. Add these column headers in Row 1:

```
A: Timestamp
B: Date
C: Campus
D: General
E: Trust
F: Online Giving
G: Building Fund
H: Total
```

---

## Step 7: Share Sheet with Service Account

**This is CRITICAL - don't skip this step!**

1. Open your `credentials.json` file (or the downloaded JSON)
2. Find the **`client_email`** value (looks like: `futures-link-service@futures-church.iam.gserviceaccount.com`)
3. In your Google Sheet, click **"Share"** button (top right)
4. Paste the service account email
5. Give it **"Editor"** access
6. **Uncheck** "Notify people" (it's a robot, not a person!)
7. Click **"Share"**

---

## Step 8: Add Sample Data (Optional)

Add a test row to verify everything works:

**Stats sheet (Row 2):**
```
2025-10-14 10:00:00 | 2025-10-14 | Paradise | 450 | 450 | 12 | 8 | 15 | 3 | 2 | 85 | 1 | 5 | 120 | 15 | 8 | 2 | 25 | 35 | 5000 | 0 | 0
```

---

## Step 9: Configure Your App

1. Create `.env` file in `/Users/shannonlangberg/Documents/futures-link/backend/`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials

3. Restart your backend server

---

## Step 10: Test Connection

1. Restart your backend:
   ```bash
   cd /Users/shannonlangberg/Documents/futures-link/backend
   pkill -f "python app.py"
   python app.py
   ```

2. Check the logs - you should see:
   ```
   [DEBUG] Google Sheets initialized successfully via Local credentials.json
   ```

3. Log in to your app and check the Dashboard - you should see data!

---

## 🎯 Campus Names (Must Match Exactly)

Your app expects these exact campus names:
- `Paradise`
- `South`
- `Salisbury`
- `Adelaide City`
- `Mount Barker`
- `Copper Coast`
- `Clare Valley`
- `Victor Harbour`

---

## 🔧 Troubleshooting

### "Google Sheets initialized via Fallback"
- Credentials file not found or invalid
- Check file location: `backend/credentials.json`
- Verify JSON is valid (use JSONLint.com)

### "Permission denied" errors
- Sheet not shared with service account email
- Double-check the `client_email` in credentials
- Share the sheet with Editor access

### "Spreadsheet not found"
- Sheet must be named exactly **"Stats"** (case-sensitive)
- Check you're logged in with the correct Google account

### No data showing in Dashboard
- Add at least one row of data to the Stats sheet
- Make sure Campus name matches exactly
- Check browser console for errors

---

## 🔒 Security Notes

- **Never commit** `credentials.json` to git
- **Never commit** `.env` file to git  
- The `.gitignore` should already exclude these files
- For production, use Railway environment variables

---

## ✅ Verification Checklist

- [ ] Google Cloud Project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service Account created with Editor role
- [ ] JSON key downloaded
- [ ] Credentials saved as `backend/credentials.json` OR in `.env`
- [ ] Google Sheet created named "Stats"
- [ ] "Stats" worksheet created with headers
- [ ] "Tithe" worksheet created with headers
- [ ] Sheet shared with service account email (Editor access)
- [ ] Sample data added to test
- [ ] Backend restarted
- [ ] Dashboard showing data

---

Need help? The logs at `/tmp/backend.log` will show detailed error messages.

