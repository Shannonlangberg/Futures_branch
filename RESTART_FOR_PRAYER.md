# RESTART BACKEND TO SEE PRAYER

## The Issue
The new frontend files are built and ready, but your backend server is still serving the OLD cached version.

## Fix: Restart Backend Server

### Step 1: Stop Current Server
In your terminal where the backend is running:
```
Press: Ctrl+C
```

### Step 2: Restart Server
```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1
./start.sh
```

### Step 3: Clear Browser & Reload
1. Open browser
2. Go to: http://localhost:5000
3. Press: Cmd+Shift+R (or Ctrl+Shift+R)
4. Login again

### Step 4: Check Navigation
You should now see:
- Connect Groups
- **Prayer & Praise** ← HERE!
- Resources

## If STILL Not Showing

### Check Your Role
Prayer & Praise is visible to these roles:
- admin
- senior_leadership
- senior_leader
- senior_pastor
- lead_pastor
- campus_pastor
- pastor
- staff

**NOT visible to:**
- user
- connect_group_leader (unless also staff)

### Check Your Role
In browser console (F12):
```javascript
// Check session
fetch('/api/session', { credentials: 'include' })
  .then(r => r.json())
  .then(d => console.log('Your role:', d.role))
```

### Verify Files Were Copied
```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/backend/static
ls -lh index.html
# Should show: Nov 21 13:45

# Check if Prayer.jsx is in the bundle
grep -l "Prayer.*Praise" assets/*.js
```

## Alternative: Force Rebuild & Restart

```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1

# Rebuild frontend
cd frontend
npm run build

# Copy to backend
cd ..
cp -r frontend/dist/* backend/static/

# Restart backend
./start.sh
```

## Still Nothing?

Try accessing directly:
```
http://localhost:5000/prayer
```

If you get:
- **404** = Route not registered (check app.py)
- **403** = You don't have permission (check your role)
- **Prayer page loads** = Navigation filter issue

## Debug Navigation

The navigation filter is in `MainLayout.jsx`:
```javascript
roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 
        'lead_pastor', 'campus_pastor', 'pastor', 'staff']
```

If your role is NOT in this list, you won't see it!

**Most likely: You just need to RESTART the backend!** 🔄

