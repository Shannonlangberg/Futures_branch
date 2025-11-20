# Profile Linking Guide: App ↔ Pulse

## How It Works

### Current Linking Mechanism

1. **User Login** (Mobile App)
   - User logs in with email/password
   - Credentials stored in `users` table (backend database)

2. **Profile Lookup** (Mobile App → Backend)
   - App calls: `GET /api/persons/email/{email}`
   - Backend finds Person record by email (case-insensitive)
   - Returns full Person profile + EngagementProfile data

3. **Data Flow**
   ```
   users table (login) → email → persons table (profile) → engagement_profiles (pulse data)
   ```

## Best Approach for Church Rollout

### ✅ **Option 1: Email-Based Auto-Linking (RECOMMENDED)**

**How it works:**
- When someone downloads the app and creates an account, they use their email
- Backend automatically matches email to existing Person record in Pulse
- If match found → instant link, all Pulse data available
- If no match → create Person record or flag for admin review

**Advantages:**
- ✅ No duplicate profiles
- ✅ Preserves all existing Pulse data
- ✅ Seamless user experience
- ✅ Works with existing church database

**Implementation:**
```python
# In login/registration endpoint:
1. User provides email
2. Check if Person exists with that email
3. If yes → link automatically
4. If no → create Person record or notify admin
```

### Option 2: Manual Admin Linking

**How it works:**
- Users create app accounts independently
- Admin manually links app users to Person records in Pulse dashboard
- More control but requires admin work

**Advantages:**
- ✅ Full admin control
- ✅ Can verify before linking

**Disadvantages:**
- ❌ Requires manual work
- ❌ Slower user experience
- ❌ Users wait for admin approval

## Current Status

✅ **Your Account:**
- Email: `shannon@futures.church` (or `shannon.langberg@futures.church`)
- User ID: 5 in `users` table
- Linked to Person record via email matching

## Database Structure

```
users table (authentication)
├── id
├── username
├── email ← Links to
├── password_hash
└── role

persons table (Pulse profiles)
├── id
├── email ← Matches users.email
├── full_name
├── campus
└── engagement_profile_id

engagement_profiles table (Pulse data)
├── id
├── person_id
├── pulse_status
├── attendance_frequency
└── ... (all Pulse metrics)
```

## API Endpoints

### Get Person by Email (Mobile App)
```
GET /api/persons/email/{email}
Response: {
  "id": "...",
  "email": "...",
  "full_name": "...",
  "engagement": {
    "pulse_status": "green",
    ...
  }
}
```

## Recommendations for Rollout

1. **Pre-populate Person records** with emails from your existing church database
2. **Use email as primary key** for linking
3. **Auto-create Person records** if email doesn't exist (with admin review flag)
4. **Sync emails** between users table and persons table regularly
5. **Add "Link Profile" feature** in admin dashboard for manual linking when needed

