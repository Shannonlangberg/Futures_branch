# Heartbeat Activation Guide

## Current Status ✅
- ✅ Database schema created
- ✅ People imported from Copper Coast
- ✅ Heartbeat calculation engine working
- ✅ Dashboard displaying scores
- ⚠️ **No engagement data yet** (attendance, serving, connect groups, etc.)

## What You Need to Activate Heartbeat

### 1. **Attendance Data** (Gather Score - 35% weight)
**What you need:**
- Record when people attend Sunday services
- Track last 12 weeks of attendance

**How to add data:**
```sql
-- Create a service
INSERT INTO heartbeat_services (id, campus_id, type, starts_at, ends_at)
VALUES ('service_001', 'copper_coast', 'sunday', '2024-01-07 10:00:00', '2024-01-07 11:30:00');

-- Record attendance
INSERT INTO heartbeat_attendance_events (id, person_id, service_id, source, created_at)
VALUES ('att_001', 'person_id_here', 'service_001', 'manual', NOW());
```

**Options:**
- **Manual entry**: Create admin interface to record attendance
- **Import from existing system**: If you have attendance data elsewhere
- **Check-in system integration**: Connect to your check-in system
- **Beacon integration**: Use existing beacon data if available

### 2. **Connect Group Data** (Engagement Score - 25% weight)
**What you need:**
- Create connect groups
- Record group membership
- Track weekly attendance at groups

**How to add data:**
```sql
-- Create a connect group
INSERT INTO heartbeat_connect_groups (id, campus_id, name, leader_person_id, type, day_of_week, is_active)
VALUES ('group_001', 'copper_coast', 'Home Group Alpha', 'leader_person_id', 'home', 'Tuesday', true);

-- Record group attendance
INSERT INTO heartbeat_connect_attendance (id, person_id, connect_group_id, date, status)
VALUES ('ca_001', 'person_id', 'group_001', '2024-01-09', 'present');
```

**Options:**
- **Manual entry**: Admin interface for group leaders
- **Import from existing groups**: If you have group data
- **Self-service**: Let group leaders record attendance

### 3. **Serving Data** (Engagement Score - 25% weight)
**What you need:**
- Create teams (e.g., "Worship Team", "Kids Team")
- Assign people to teams
- Record when they serve

**How to add data:**
```sql
-- Create a team
INSERT INTO heartbeat_teams (id, campus_id, name)
VALUES ('team_001', 'copper_coast', 'Worship Team');

-- Create serving assignment
INSERT INTO heartbeat_serving_assignments (id, person_id, team_id, service_id, role, status)
VALUES ('serving_001', 'person_id', 'team_001', 'service_001', 'Musician', 'served');
```

**Options:**
- **Manual entry**: Admin interface
- **Import from scheduling system**: If you use Planning Center or similar
- **Self-service**: Let team leaders record serving

### 4. **Giving Data** (Engagement Score - 25% weight)
**What you need:**
- Track giving frequency and patterns
- Monthly/weekly summaries

**How to add data:**
```sql
INSERT INTO heartbeat_giving_summaries (id, person_id, period_start, period_end, frequency, pattern_score, last_gift_at)
VALUES ('giving_001', 'person_id', '2024-01-01', '2024-01-31', 'monthly', 0.85, '2024-01-15');
```

**Options:**
- **Import from giving system**: Connect to your giving platform
- **Manual entry**: If giving is tracked elsewhere
- **API integration**: Connect to PushPay, Tithe.ly, etc.

### 5. **Discipleship Data** (Spiritual Score - 25% weight)
**What you need:**
- Track milestones: salvation, baptism, Holy Spirit, next steps
- Record when people complete discipleship steps

**How to add data:**
```sql
INSERT INTO heartbeat_discipleship_steps (id, person_id, type, description, date, created_by_person_id)
VALUES ('step_001', 'person_id', 'salvation', 'Made decision for Christ', '2024-01-10', 'pastor_id');
```

**Options:**
- **Manual entry**: Pastors/leaders record milestones
- **Import from existing records**: If you track this elsewhere
- **Self-service**: People can record their own milestones (with approval)

### 6. **Care Cases** (Care Score - 15% weight)
**What you need:**
- Track when people need pastoral care
- Record touchpoints (visits, calls, etc.)

**How to add data:**
```sql
-- Create care case
INSERT INTO heartbeat_care_cases (id, person_id, type, status, priority, summary, created_by_person_id)
VALUES ('care_001', 'person_id', 'bereavement', 'open', 'high', 'Loss of family member', 'pastor_id');

-- Record touchpoint
INSERT INTO heartbeat_care_touchpoints (id, care_case_id, person_id, contacted_by_person_id, method, notes)
VALUES ('touch_001', 'care_001', 'person_id', 'pastor_id', 'phone', 'Called to check in');
```

**Options:**
- **Manual entry**: Pastoral care team
- **Integration**: Connect to care management system

## Implementation Priority

### Phase 1: Quick Wins (Get Basic Scores)
1. **Create Services** - Set up Sunday services for the next 12 weeks
2. **Record Attendance** - Start manually recording attendance (or import historical data)
3. **Create Connect Groups** - Set up your existing groups
4. **Record Group Attendance** - Start tracking weekly attendance

**Result**: Gather and Engagement scores will start showing real data

### Phase 2: Full Activation
1. **Serving Assignments** - Set up teams and record serving
2. **Giving Integration** - Connect to giving platform or import data
3. **Discipleship Tracking** - Start recording milestones
4. **Care Cases** - Set up care tracking workflow

**Result**: All scores will reflect real engagement

## Data Import Options

### Option A: Manual Entry Interface
Create admin forms to:
- Record attendance after each service
- Let group leaders record group attendance
- Let team leaders record serving
- Pastors record discipleship milestones

### Option B: Bulk Import Scripts
Create Python scripts to:
- Import historical attendance data
- Import connect group data
- Import serving schedules
- Import giving summaries

### Option C: API Integration
Connect to:
- Planning Center Online (attendance, groups, serving)
- PushPay/Tithe.ly (giving)
- Your existing database (if data exists elsewhere)

## Next Steps

1. **Decide on data collection method** (manual, import, API)
2. **Start with attendance** - This has the biggest impact (35% weight)
3. **Set up connect groups** - Second biggest impact (25% weight)
4. **Create recurring services** - Set up services for the next 12 weeks
5. **Run recalculation** - After adding data, recalculate to see new scores

## Quick Start Commands

```bash
# Create sample services (run once)
cd backend
python seed_heartbeat.py

# Recalculate all people in a campus
# (Use the "Recalculate Campus" button in the dashboard, or:)
curl -X POST http://localhost:5000/api/heartbeat/recalculate/copper_coast
```

## Questions to Answer

1. **Do you have existing attendance data?** (Where is it stored?)
2. **Do you have connect group data?** (Who's in which groups?)
3. **Do you have serving schedules?** (Who serves when?)
4. **Do you have giving data?** (What platform do you use?)
5. **Do you track discipleship milestones?** (Where is this data?)

Once you answer these, we can build the import/integration tools you need!


