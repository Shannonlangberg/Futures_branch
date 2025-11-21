# Prayer & Praise - Quick Test Guide

## ✅ FIXES APPLIED

### 1. Mobile App Navigation - FIXED ✅
**Problem:** Prayer wasn't visible in the bottom navigation
**Solution:** Added Prayer tab to the main navigation bar

The mobile app now has:
- 🏠 Home
- 🗺️ Pathway
- 💰 Give
- 👥 Groups
- 🙏 **Prayer** (NEW!)
- ⚙️ Settings

### 2. Prayer Link Route - FIXED ✅
**Problem:** Link route wasn't registered
**Solution:** Added route to serve the public submission page

## 🔄 RESTART REQUIRED

**You need to restart the backend server for the prayer link route to work!**

```bash
# Stop current backend (Ctrl+C)
# Then restart:
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1
./start.sh
```

## 🧪 TEST THE FIXES

### Test 1: Mobile App Navigation

1. **Restart the mobile app** (close and reopen)
2. You should see **🙏 Prayer** in the bottom navigation
3. Tap it to open the Prayer & Praise screen
4. Try submitting a prayer request or praise report

### Test 2: Prayer Link (Web)

After restarting the backend, test the link:

**Test Link ID:** `prayer_test123abc`

**Test URLs:**

1. **Public Submission Page:**
   ```
   http://localhost:5000/prayer/link/prayer_test123abc
   ```
   or
   ```
   https://pulse.futuresbranch.org/prayer/link/prayer_test123abc
   ```

2. **API - Get Link Info:**
   ```bash
   curl http://localhost:5000/api/prayer/link/prayer_test123abc
   ```

3. **API - Submit via Link:**
   ```bash
   curl -X POST http://localhost:5000/api/prayer/link/prayer_test123abc/submit \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User",
       "email": "test@example.com",
       "type": "prayer",
       "text": "This is a test prayer request"
     }'
   ```

### Expected Results

**Public Page:**
- Opens a beautiful purple/blue gradient page
- Shows "🙏 Prayer & Praise"
- Shows "Test Location - Main Entrance"
- Has two tabs: Prayer Request and Praise Report
- Form fields: Name, Email, Phone (optional), Campus (Paradise pre-selected)
- Submit button

**API Response:**
```json
{
  "success": true,
  "link_type": "both",
  "campus": "paradise",
  "department": "Youth",
  "location": "Test Location - Main Entrance"
}
```

## 📱 Mobile App Changes

**File Modified:** `mobile/App.js`

**Changes:**
1. Added Prayer to the `MainTabs` component (bottom navigation)
2. Removed duplicate Prayer from Stack.Navigator
3. Added 🙏 emoji icon for Prayer tab

**You'll need to:**
- Restart the mobile app (Expo Go or dev build)
- Or reload: Shake device → "Reload"

## 🔧 Backend Changes

**File Modified:** `backend/app.py`

**Changes:**
1. Added route: `/prayer/link/<link_id>`
2. Serves: `backend/static/prayer-submit.html`

**You'll need to:**
- Stop backend server (Ctrl+C)
- Restart backend server (`./start.sh`)

## 🎯 What Should Work Now

### Mobile App (After Restart)
✅ Prayer tab visible in bottom navigation
✅ Tap to open Prayer & Praise screen
✅ Submit prayer requests
✅ Submit praise reports
✅ Automatically routes to campus pastor via Heartbeat

### Web Links (After Backend Restart)
✅ Open `/prayer/link/<link_id>` in browser
✅ Beautiful submission page loads
✅ Form pre-fills campus from link
✅ Submit prayer/praise without login
✅ Creates person if doesn't exist
✅ Creates CareCase in Heartbeat
✅ Routes to campus pastor

## 🐛 Troubleshooting

### "Prayer tab not showing in app"
- **Solution:** Restart the mobile app completely (close and reopen)
- Or: Shake device → Reload

### "Link shows 404 Not Found"
- **Solution:** Restart the backend server
- Check: `grep -n "prayer_submission_page" backend/app.py`
- Should show the route on line ~17191

### "Link loads but shows blank page"
- **Solution:** Check file exists:
  ```bash
  ls backend/static/prayer-submit.html
  ```
- Should show: 12K file size

### "Submission fails with 404"
- Check API endpoint is registered:
  ```bash
  curl http://localhost:5000/api/prayer/links
  ```
- If 404, check prayer_bp is registered in app.py

### "Person not found error"
- **Solution:** The link creates persons automatically
- Check database:
  ```bash
  sqlite3 backend/futures_link.db "SELECT * FROM persons WHERE email='test@example.com';"
  ```

## 📊 Check Backend Logs

After testing, check if submission worked:

```bash
# Check app logs
tail -f backend/app.log

# Check prayer links
sqlite3 backend/futures_link.db "SELECT * FROM prayer_links;"

# Check if CareCase was created
sqlite3 backend/futures_link.db "SELECT * FROM care_cases ORDER BY created_at DESC LIMIT 5;"

# Check scan/submission counts
sqlite3 backend/futures_link.db "SELECT link_id, scan_count, submission_count FROM prayer_links;"
```

## 🎉 Success Checklist

- [ ] Mobile app shows Prayer tab in navigation
- [ ] Can tap Prayer tab and open screen
- [ ] Can submit prayer request from app
- [ ] Backend server restarted
- [ ] Can open `/prayer/link/prayer_test123abc` in browser
- [ ] Submission page loads with beautiful design
- [ ] Can submit prayer via web form
- [ ] Check Heartbeat - CareCase created
- [ ] Check prayer_links - scan_count increased
- [ ] Check prayer_links - submission_count increased

## 🚀 Next Steps (After Testing)

Once everything works:

1. **Create real prayer links** for each campus
2. **Generate QR codes** for physical locations
3. **Order NFC tags** for tap points
4. **Share links** on social media
5. **Train staff** on the system

## 📚 Full Documentation

For complete documentation, see:
- `PRAYER_LINKS_GUIDE.md` - Complete usage guide
- `PRAYER_SETUP_COMPLETE.md` - Full setup documentation

## 💬 Questions?

If something isn't working:
1. Check this troubleshooting guide
2. Verify backend and app are restarted
3. Check backend logs
4. Test with curl commands first
5. Then test in browser
6. Finally test in mobile app

**Most common issue:** Forgetting to restart backend/app after changes! 🔄

