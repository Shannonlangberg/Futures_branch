# Heartbeat Module - Quick Start Checklist

## ✅ To Make It Live & Testable

### Step 1: Restart Application (Auto-creates tables)
```bash
# Tables will be created automatically via SQLAlchemy
# Just restart your app
./start.sh
# or
python backend/app.py
```

**What happens:** SQLAlchemy's `db.create_all()` automatically creates all Heartbeat tables.

### Step 2: Seed Initial Data
```bash
cd backend
python seed_heartbeat.py
```

**What this does:**
- Creates Heartbeat campus records from your existing Person.campus values
- Creates sample Sunday services for the last 12 weeks
- Sets up the basic structure

### Step 3: Verify Setup
Check that you can access:
- Dashboard: `http://your-app/heartbeat`
- API: `GET /api/heartbeat/campus/{campus_id}/people`

### Step 4: Add Real Data (Choose one)

#### Option A: Quick Test with Minimal Data
1. Pick a campus that has people
2. Go to `/heartbeat` dashboard
3. Select that campus
4. Click "Recalculate Campus" (will work even with minimal/no data)

#### Option B: Full Test with Sample Data
Create some test records via API or database:

**Create a Service:**
```sql
INSERT INTO heartbeat_services (campus_id, type, starts_at, ends_at)
VALUES ('paradise', 'sunday', '2025-01-19 09:00:00', '2025-01-19 11:00:00');
```

**Create Attendance Event:**
```sql
INSERT INTO heartbeat_attendance_events (person_id, service_id, source)
VALUES ('person-uuid-here', 1, 'manual');
```

**Then recalculate:**
- Use dashboard button, or
- `POST /api/heartbeat/recalculate/{campus_id}`

### Step 5: View Results
Navigate to `/heartbeat` and you should see:
- Campus overview
- People with heartbeat scores
- Status breakdowns

## 🚨 Common Issues

**No data showing?**
- Make sure you've selected a campus
- Check that people have `is_active = true` in persons table
- Run recalculation after adding data

**All scores are zero?**
- Need attendance data in last 12 weeks
- Need services created
- Run recalculation

**Tables not created?**
- Check app logs for errors
- Verify `init_db(app)` is called
- Check database permissions

## 📝 Minimal Test (5 minutes)

1. Restart app ✅
2. Run seed script ✅
3. Go to `/heartbeat` ✅
4. Select a campus ✅
5. Click "Recalculate" ✅
6. See results! 🎉

Even with no attendance data, you'll see people listed (with no scores yet). This confirms the system is working.

## 🔄 Next: Integrate Real Data

Once basic setup works, integrate with your existing systems:
- Connect attendance tracking → create AttendanceEvents
- Connect group system → create ConnectAttendance
- Serving system → create ServingAssignments
- Giving system → create GivingSummaries

Then scores will populate automatically!





