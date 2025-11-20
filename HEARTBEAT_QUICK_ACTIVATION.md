# Heartbeat Quick Activation Checklist

## 🎯 Goal: Get Real Scores (Not Just 15!)

Currently everyone has a score of 15 because:
- ✅ Care score = 100 (no care cases = good!)
- ❌ Gather = 0 (no attendance data)
- ❌ Engagement = 0 (no groups/serving/giving)
- ❌ Spiritual = 0 (no milestones)

## 📋 Action Items (In Priority Order)

### 1. **Create Services** (5 minutes)
Services are needed before you can record attendance.

```bash
cd backend
python seed_heartbeat.py
```

This creates:
- Heartbeat campuses (if missing)
- Sunday services for the last 12 weeks

### 2. **Record Attendance** (Biggest Impact - 35% weight)
Choose one method:

**Option A: Manual Entry (Start Here)**
- After each service, record who attended
- Use the API or create a simple form

**Option B: Import Historical Data**
- If you have attendance records elsewhere
- Create an import script

**Option C: Connect to Check-in System**
- If you use Planning Center, Church Online, etc.
- Build an integration

### 3. **Set Up Connect Groups** (25% weight)
- Create groups in the database
- Record weekly attendance
- This will boost Engagement scores

### 4. **Record Serving** (25% weight)
- Create teams (Worship, Kids, etc.)
- Record when people serve
- This also boosts Engagement scores

### 5. **Add Discipleship Milestones** (25% weight)
- Record salvation, baptism, etc.
- This boosts Spiritual scores

## 🚀 Quick Start (Today)

1. **Run seed script:**
   ```bash
   cd backend
   python seed_heartbeat.py
   ```

2. **Record some test attendance:**
   - Pick 5-10 people
   - Record them attending the last 2-3 services
   - Use SQL or create a simple API call

3. **Recalculate:**
   - Click "Recalculate Campus" in dashboard
   - Or: `POST /api/heartbeat/recalculate/copper_coast`

4. **Check results:**
   - Scores should start increasing!
   - Gather score will go up first

## 📊 What Data Do You Have?

Answer these to determine next steps:

- [ ] **Attendance data?** Where? (Planning Center, spreadsheet, database?)
- [ ] **Connect groups?** Who's in which groups?
- [ ] **Serving schedules?** Who serves when?
- [ ] **Giving data?** What platform? (PushPay, Tithe.ly, etc.)
- [ ] **Discipleship milestones?** Where are these tracked?

## 🔧 Need Help?

Once you tell me what data you have, I can:
1. Create import scripts
2. Build API integrations
3. Create admin forms for manual entry
4. Set up automated data collection

## 💡 Pro Tip

**Start with attendance** - it has the biggest impact (35% of total score). Even recording just the last 4-6 weeks will make a huge difference!



