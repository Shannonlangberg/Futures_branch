# People Section API Implementation Summary

## ✅ Completed Endpoints

### 1. Enhanced GET /api/persons
**Status:** ✅ Enhanced

**New Features:**
- Added `heartbeat_score` calculation (0-100) based on pulse_status and overall_engagement
- Added `connect_group_name` field (joins with ConnectGroup table)
- Added `new_people=true` filter (last 30 days)
- Added `new_christians=true` filter (baptised in last 2 years)

**Response includes:**
```json
{
  "persons": [
    {
      "id": "...",
      "heartbeat_score": 85,
      "connect_group_name": "Young Adults Group",
      "pulse_status": "green",
      "overall_engagement": 90.5,
      ...
    }
  ]
}
```

---

### 2. GET /api/people/families
**Status:** ✅ Implemented

**Endpoint:** `GET /api/people/families`

**Features:**
- Groups persons by household (using email domain + last name)
- Calculates household heartbeat (average of all members)
- Tracks attendance together percentage
- Detects attendance drifting
- Identifies parent giving patterns

**Response:**
```json
{
  "families": [
    {
      "id": "family_123",
      "members": [
        {
          "id": "person_1",
          "name": "John Smith",
          "role": "parent",
          "heartbeat": 85
        }
      ],
      "household_heartbeat": 82,
      "attendance_together": 75,
      "attendance_drifting": false,
      "parent_giving": false
    }
  ],
  "total": 45
}
```

**Note:** Currently uses simple email/last name grouping. For production, add `family_id` field to Person model.

---

### 3. GET /api/heartbeat/dashboard
**Status:** ✅ Implemented

**Endpoint:** `GET /api/heartbeat/dashboard`

**Features:**
- Health overview counts (healthy, watch, at_risk, critical, new_people, new_christians, youth_at_risk)
- AI analysis (positive shifts, health drops, attendance drops, giving changes, serving burnout, youth disengagement, leadership ready)
- Weekly Pastor Focus List (people to check on, encourage, celebrate, follow-up)
- Trends by campus/ministry (placeholder structure)

**Response:**
```json
{
  "health_overview": {
    "healthy": 245,
    "watch": 32,
    "at_risk": 18,
    "critical": 5,
    "new_people": 12,
    "new_christians": 3,
    "youth_at_risk": 8,
    "families_drifting": 0
  },
  "ai_analysis": {
    "positive_shifts": "...",
    "health_drops": "...",
    "attendance_drops": "...",
    "giving_rhythm_changes": "...",
    "serving_burnout": "...",
    "youth_disengagement": "...",
    "leadership_ready": "..."
  },
  "pastor_focus_list": [
    {
      "name": "John Smith",
      "reason": "Critical status - last seen 25 days ago",
      "action": "Check on - may need immediate pastoral care",
      "priority": "high"
    }
  ],
  "trends": {
    "by_campus": {},
    "by_ministry": {}
  }
}
```

---

### 4. GET /api/pastoral-care/cases
**Status:** ✅ Implemented (Placeholder)

**Endpoint:** `GET /api/pastoral-care/cases`

**Current Status:**
- Returns empty array with message
- Structure ready for future implementation
- Requires `PastoralCareCase` model and table creation

**Future Implementation:**
- Create `pastoral_care_cases` table
- Link to Person model
- Track priority, status, assigned leader, follow-up dates
- Generate AI summaries

---

### 5. GET /api/people/new-christians
**Status:** ✅ Implemented

**Endpoint:** `GET /api/people/new-christians`

**Features:**
- Filters persons baptised in last 2 years
- Includes discipleship progress (foundations, pathway)
- Calculates group attendance percentage
- Generates AI analysis and suggested next steps

**Response:**
```json
{
  "new_christians": [
    {
      "id": "person_123",
      "name": "John Smith",
      "new_christian_date": "2024-01-01",
      "foundations_progress": "50%",
      "pathway_progress": "Step 3 of 8",
      "attendance_since_decision": 8,
      "group_attendance": 75,
      "pulse_tv_usage": "Medium",
      "ai_analysis": "This person is progressing well...",
      "suggested_next_step": "Start Foundations course"
    }
  ],
  "total": 12
}
```

---

### 6. GET /api/attendance/patterns
**Status:** ✅ Implemented

**Endpoint:** `GET /api/attendance/patterns`

**Features:**
- Calculates missing streaks (people who haven't attended in 2+ weeks)
- Counts first-time visitors (last 30 days)
- Tracks Sunday attendance averages
- Placeholder structure for kids/youth/serving/event attendance

**Response:**
```json
{
  "sunday_avg": 450,
  "sunday_month": 1800,
  "sunday_trend": 0,
  "missing_streaks": [
    {
      "person_id": "person_123",
      "name": "John Smith",
      "days": 21,
      "last_attended": "2023-12-15"
    }
  ],
  "first_time_visitors": 12,
  "families_missing": [],
  "serving_attendance": {},
  "event_attendance": {}
}
```

---

## Frontend Updates

### ✅ PeopleMain.jsx
- Updated to use backend `new_people` and `new_christians` filters
- Uses `heartbeat_score` from API response
- Uses `connect_group_name` from API response

### ✅ NewPeople.jsx
- Updated to use `/api/persons?new_people=true` endpoint

### ✅ NewChristians.jsx
- Updated to use `/api/people/new-christians` endpoint
- Displays all discipleship progress data

---

## Database Schema Notes

### Current Person Model
- ✅ Has `baptised_on` field (used for new Christians)
- ✅ Has `connect_group` field (ID reference)
- ❌ Missing `family_id` field (needed for proper family grouping)
- ❌ Missing `is_new_christian` boolean flag
- ❌ Missing `new_christian_date` field (separate from baptised_on)
- ❌ Missing `follow_up_status` field

### Future Additions Needed

**Person Model:**
```python
family_id = db.Column(db.String(50))  # For family grouping
is_new_christian = db.Column(db.Boolean, default=False)
new_christian_date = db.Column(db.Date)
follow_up_status = db.Column(db.String(50))  # 'contacted', 'connected', 'joined_events'
```

**New Table: pastoral_care_cases**
```python
class PastoralCareCase(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'))
    priority = db.Column(db.String(20))  # high, medium, low
    status = db.Column(db.String(20))  # open, resolved
    notes = db.Column(db.Text)
    assigned_leader = db.Column(db.String(200))
    follow_up_date = db.Column(db.Date)
    ai_summary = db.Column(db.Text)
    suggested_responses = db.Column(db.Text)  # JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Testing Checklist

- [ ] Test GET /api/persons with heartbeat_score and connect_group_name
- [ ] Test GET /api/persons?new_people=true filter
- [ ] Test GET /api/persons?new_christians=true filter
- [ ] Test GET /api/people/families endpoint
- [ ] Test GET /api/heartbeat/dashboard endpoint
- [ ] Test GET /api/people/new-christians endpoint
- [ ] Test GET /api/attendance/patterns endpoint
- [ ] Verify PeopleMain page displays heartbeat scores correctly
- [ ] Verify connect_group_name displays in table
- [ ] Test all filter buttons in PeopleMain

---

## Next Steps

1. **Add family_id to Person model** - Create migration to add family_id field
2. **Create PastoralCareCase model** - Full implementation of care cases
3. **Enhance AI analysis** - Integrate with Anthropic API for better insights
4. **Implement attendance trends** - Calculate actual trends from attendance logs
5. **Add campus/ministry trends** - Break down trends by campus and ministry
6. **Family attendance calculation** - Implement actual attendance together percentage

---

## API Endpoint Summary

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/persons` | GET | ✅ Enhanced | Get all persons with heartbeat_score, connect_group_name |
| `/api/persons?new_people=true` | GET | ✅ New | Filter persons created in last 30 days |
| `/api/persons?new_christians=true` | GET | ✅ New | Filter persons baptised in last 2 years |
| `/api/people/families` | GET | ✅ New | Get families grouped by household |
| `/api/heartbeat/dashboard` | GET | ✅ New | Get health overview and AI analysis |
| `/api/pastoral-care/cases` | GET | ✅ Placeholder | Get pastoral care cases (structure ready) |
| `/api/people/new-christians` | GET | ✅ New | Get new Christians with discipleship progress |
| `/api/attendance/patterns` | GET | ✅ New | Get attendance patterns and missing streaks |

---

**Implementation Date:** $(date)
**Status:** ✅ Core endpoints implemented and ready for testing

