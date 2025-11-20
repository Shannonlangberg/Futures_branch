# Heartbeat Module Setup Guide

## Overview
The Heartbeat module tracks congregant health through comprehensive engagement scoring. This guide will help you get it up and running.

## What Happens Automatically

1. **Database Tables**: SQLAlchemy will automatically create all Heartbeat tables when the app starts (via `init_db()`)
2. **Migrations**: The migration file `018_heartbeat_module.sql` will run automatically on startup
3. **API Endpoints**: Already registered and available at `/api/heartbeat/*`

## Steps to Make It Live

### 1. Restart Your Application
The tables will be created automatically when the app starts. Just restart your Flask app:

```bash
# If running locally
python backend/app.py

# Or if using the start script
./start.sh
```

### 2. Verify Tables Were Created
Check your database to confirm tables exist:
- `heartbeat_campuses`
- `heartbeat_services`
- `heartbeat_attendance_events`
- `heartbeat_connect_groups`
- `heartbeat_connect_attendance`
- `heartbeat_teams`
- `heartbeat_serving_assignments`
- `heartbeat_giving_summaries`
- `heartbeat_discipleship_steps`
- `heartbeat_care_cases`
- `heartbeat_care_touchpoints`
- `heartbeat_snapshots`

### 3. Seed Initial Data (Optional but Recommended)

Run the seed script to create test data:

```bash
cd backend
python seed_heartbeat.py
```

This will:
- Create Heartbeat campus records from your existing campuses
- Create some sample services
- Optionally create test attendance/engagement data

### 4. Populate Real Data

To make Heartbeat useful, you need to populate it with real data:

#### A. Create Services
Services represent church services (Sunday, Youth, Kids, etc.). You can create them via API or directly in the database.

Example API call:
```bash
POST /api/heartbeat/services
{
  "campus_id": "paradise",
  "type": "sunday",
  "starts_at": "2025-01-19T09:00:00Z",
  "ends_at": "2025-01-19T11:00:00Z"
}
```

#### B. Record Attendance
When someone attends a service, create an AttendanceEvent:
```bash
POST /api/heartbeat/attendance
{
  "person_id": "person-uuid",
  "service_id": 1,
  "source": "beacon"  # or "manual", "checkin", "import"
}
```

#### C. Connect Groups
Create connect groups and record attendance:
```bash
POST /api/heartbeat/connect-groups
{
  "campus_id": "paradise",
  "name": "Young Adults Group",
  "leader_person_id": "leader-uuid",
  "type": "home",
  "day_of_week": "Tuesday"
}
```

#### D. Serving Assignments
Track when people serve:
```bash
POST /api/heartbeat/serving
{
  "person_id": "person-uuid",
  "team_id": 1,
  "service_id": 1,
  "role": "Worship Leader",
  "status": "served"
}
```

### 5. Run Initial Calculation

Once you have some data, trigger the first heartbeat calculation:

**Via Dashboard:**
1. Go to `/heartbeat`
2. Select a campus
3. Click "🔄 Recalculate Campus"

**Via API:**
```bash
POST /api/heartbeat/recalculate/{campus_id}
```

This will:
- Calculate scores for all active people in that campus
- Create HeartbeatSnapshot records
- Make data visible in the dashboard

### 6. View the Dashboard

Navigate to `/heartbeat` in your app to see:
- Campus overview with status counts
- Individual person cards with scores
- Risk factors and recommendations
- Filter by status or search by name

## Testing Without Real Data

If you want to test the dashboard without real data, you can:

1. **Use the seed script** to create sample data
2. **Manually create test records** in the database
3. **Use the API** to create test services, attendance, etc.

## API Endpoints Reference

- `GET /api/heartbeat/campus/{campus_id}/people` - List people with heartbeat data
- `GET /api/heartbeat/person/{person_id}` - Get detailed heartbeat for one person
- `POST /api/heartbeat/recalculate/{campus_id}` - Recalculate all people in campus
- `POST /api/heartbeat/recalculate/person/{person_id}` - Recalculate one person
- `GET /api/heartbeat/snapshots/{person_id}` - Get historical snapshots

## Troubleshooting

### Tables Not Created
- Check app logs for SQLAlchemy errors
- Verify `init_db(app)` is being called
- Check database permissions

### No Data Showing
- Ensure you've created services and attendance events
- Run recalculation after adding data
- Check that people have `is_active = true`

### Scores All Zero
- Verify you have attendance data in the last 12 weeks
- Check that services are marked as type "sunday"
- Ensure connect groups, serving, etc. have recent data

## Next Steps

1. **Integrate with existing systems**: Connect your attendance tracking, connect group system, etc. to automatically create Heartbeat records
2. **Set up scheduled recalculation**: Add a cron job or scheduled task to recalculate weekly
3. **Add notifications**: Alert pastors when someone moves to "at_risk" or "critical"
4. **Create reports**: Build reports showing trends over time




