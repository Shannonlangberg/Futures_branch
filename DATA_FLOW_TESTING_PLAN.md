# Data Flow Testing & Verification Plan

## Current Status
✅ Legacy discipleship data cleared  
✅ Person record verified: Shannon Langberg (pco_33559749)  
✅ Engagement profile exists (but empty)  
⚠️ All engagement data is currently empty (0 records)

---

## Data Flows to Test & Fix

### 1. ✅ Attendance ("I'm Here" Button)
**Flow:** Mobile App → `/api/attendance/log` → `engagement_profiles.attendance_log` → Heartbeat

**Test Steps:**
1. Open mobile app
2. Tap "I'm Here" button
3. Check Railway logs for: `✅ Attendance logged successfully`
4. Run diagnostic to verify attendance_log has entries
5. Verify heartbeat recalculates (GATHER score increases)

**Expected Result:**
- `attendance_log` should have 1+ entries
- GATHER score should be > 0
- Last seen date should update

---

### 2. ✅ Connect Group Attendance
**Flow:** Leader Portal → `/api/connect-groups/{id}/leader-portal/attendance` → `connect_attendance` table → Heartbeat

**Test Steps:**
1. Open Connect Group Leader Portal
2. Mark Shannon as present for a meeting
3. Check Railway logs for success
4. Run diagnostic to verify connect_attendance table has records
5. Verify heartbeat recalculates (ENGAGEMENT score increases)

**Expected Result:**
- `connect_attendance` table should have 1+ records
- ENGAGEMENT score should increase
- "No Connect Group" risk factor should disappear

---

### 3. ✅ Giving (App/QR/NFC)
**Flow:** Mobile App/Web → `/api/giving/create-intent` → Stripe → Webhook → `GivingTransaction` → Heartbeat

**Test Steps:**
1. Make a test payment ($1) via mobile app
2. Check Stripe webhook fires: `payment_intent.succeeded`
3. Check Railway logs for: `[WEBHOOK] ✅ Payment processed`
4. Run diagnostic to verify:
   - `giving_transactions` table has record
   - `engagement_profiles.serving_log` has giving entry (type: 'giving')
5. Verify heartbeat recalculates (ENGAGEMENT score increases)

**Expected Result:**
- Transaction recorded in database
- `serving_log` (milestones) has giving entry
- ENGAGEMENT score increases
- "No Giving" risk factor disappears

---

### 4. ✅ Pathway Completions
**Flow:** Pathway Manager → Complete Step → `person_pathway_step_completion` → Heartbeat

**Test Steps:**
1. Start a pathway for Shannon (e.g., General Discipleship Pathway)
2. Mark a step as complete
3. Run diagnostic to verify:
   - `person_pathway_progress` table has record
   - `person_pathway_step_completion` table has records
4. Verify heartbeat recalculates (SPIRITUAL score increases)

**Expected Result:**
- Pathway progress tracked
- SPIRITUAL score > 0
- "No Salvation Milestone" risk factor disappears

---

### 5. ✅ Serving (Dream Team)
**Flow:** Serving API → `/api/serving/log` → `serving_assignments` → Heartbeat

**Test Steps:**
1. Log a serving assignment for Shannon
2. Verify it records in `serving_assignments` table
3. Verify heartbeat recalculates (ENGAGEMENT score increases)

**Expected Result:**
- Serving tracked
- ENGAGEMENT score increases
- "No Serving" risk factor disappears

---

## Testing Order

1. **Test "I'm Here" attendance first** (easiest to test)
2. **Test Giving** (already built, just needs verification)
3. **Test Connect Group attendance** (via leader portal)
4. **Test Pathway completion** (requires pathway manager)
5. **Test Serving** (if API exists)

---

## Success Criteria

After all tests pass:
- ✅ GATHER score > 0 (attendance working)
- ✅ ENGAGEMENT score > 0 (groups, giving, serving working)
- ✅ SPIRITUAL score > 0 (pathways working)
- ✅ CARE score = 100 (no open care cases)
- ✅ Total Heartbeat Score > 17 (should be 40-60+)
- ✅ No false risk factors
- ✅ All data visible in Person Health Report

---

## Next Step: Test "I'm Here" Button

**Action Required from Shannon:**
1. Open mobile app
2. Navigate to home/dashboard
3. Find and tap "I'm Here" button
4. Report back if you see success message or any errors

**I'll monitor Railway logs to verify the data flow works.**

