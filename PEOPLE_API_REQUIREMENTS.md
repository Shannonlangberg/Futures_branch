# People Section API Requirements

## Overview
This document lists all API endpoints needed for the comprehensive People section with 8 sub-pages.

## Existing Endpoints ✅

### Persons/People
- `GET /api/persons` - Get all persons (with filters: campus, pulse_status, department, search, include_archived)
- `POST /api/persons` - Create new person
- `GET /api/persons/<person_id>` - Get person detail
- `GET /api/persons/email/<email>` - Get person by email
- `PUT /api/persons/<person_id>` - Update person
- `POST /api/persons/<person_id>/archive` - Archive person
- `POST /api/persons/<person_id>/restore` - Restore archived person
- `DELETE /api/persons/<person_id>` - Delete person
- `GET /api/persons/export` - Export persons CSV
- `POST /api/persons/import_pco` - Import from PCO CSV

### Heartbeat
- `GET /api/persons/<person_id>/pulse` - Get pulse status (exists as `get_pulse_status`)

---

## Required New Endpoints 🔨

### 1. People Main Directory (`/people`)

#### ✅ Already Exists
- `GET /api/persons` - Can filter by status, search, etc.

#### 🔨 Needs Enhancement
- Add `group_by_family` parameter to group results
- Add `connect_group_name` to response (join with connect_groups table)
- Add heartbeat score calculation in response

---

### 2. Families (`/people/families`)

#### 🔨 New Endpoints Needed

**GET /api/people/families**
- Group persons by household/family
- Calculate household heartbeat (average)
- Calculate attendance together percentage
- Detect attendance drifting
- Return family structure with members

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
          "role": "dad",
          "heartbeat": 85
        }
      ],
      "household_heartbeat": 82,
      "attendance_together": 75,
      "attendance_drifting": false,
      "parent_giving": true,
      "care_needs": [],
      "next_steps": []
    }
  ]
}
```

---

### 3. Heartbeat Dashboard (`/people/heartbeat`)

#### 🔨 New Endpoints Needed

**GET /api/heartbeat/dashboard**
- Health overview counts (healthy, watch, at_risk, critical, new_people, new_christians)
- AI analysis (positive shifts, health drops, attendance drops, giving changes, serving burnout, youth disengagement, leadership ready)
- Weekly Pastor Focus List (people to check on, encourage, celebrate, follow-up)
- Trends by campus/ministry

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
    "families_drifting": 4
  },
  "ai_analysis": {
    "positive_shifts": "5 people showing increased engagement...",
    "health_drops": "3 people showing declining attendance...",
    "attendance_drops": "8 people missed 3+ weeks...",
    "giving_rhythm_changes": "2 families changed giving patterns...",
    "serving_burnout": "1 person reduced serving frequency...",
    "youth_disengagement": "3 youth showing decreased engagement...",
    "leadership_ready": "2 people ready for leadership roles..."
  },
  "pastor_focus_list": [
    {
      "name": "John Smith",
      "reason": "Missed 4 weeks",
      "action": "Check on - may need encouragement",
      "priority": "high"
    }
  ],
  "trends": {
    "by_campus": {...},
    "by_ministry": {...}
  }
}
```

---

### 4. Pastoral Care (`/people/pastoral-care`)

#### 🔨 New Endpoints Needed

**GET /api/pastoral-care/cases**
- Get all open care cases
- Filter by priority, assigned leader, status
- Include AI summaries

**POST /api/pastoral-care/cases**
- Create new care case

**PUT /api/pastoral-care/cases/<case_id>**
- Update care case

**POST /api/pastoral-care/cases/<case_id>/resolve**
- Resolve care case (affects heartbeat)

**Response:**
```json
{
  "cases": [
    {
      "id": "case_123",
      "person_id": "person_456",
      "person_name": "John Smith",
      "priority": "high",
      "status": "open",
      "notes": "Family crisis - needs support",
      "assigned_leader": "Pastor Jane",
      "follow_up_date": "2024-01-15",
      "ai_summary": "High priority case requiring immediate pastoral response...",
      "suggested_responses": ["Phone call", "Home visit"],
      "family_dependencies": ["Spouse: Jane Smith"]
    }
  ]
}
```

---

### 5. New People (`/people/new-people`)

#### ✅ Partially Exists
- `GET /api/persons` can filter by date, but needs enhancement

#### 🔨 Needs Enhancement
- Add `new_people=true` filter (last 30 days)
- Add `follow_up_status` field
- Add `ai_follow_up_message` field
- Add `next_steps` field
- Add `service_attended` field

**GET /api/people/new-people**
- Filter persons created in last 30 days
- Include follow-up status and AI messages

---

### 6. New Christians (`/people/new-christians`)

#### 🔨 New Endpoints Needed

**GET /api/people/new-christians**
- Filter persons with `is_new_christian=true` or `new_christian_date`
- Include discipleship progress (foundations, pathway)
- Include attendance since decision
- Include group attendance percentage
- Include Pulse TV usage
- Include AI analysis and suggested next steps

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
      "pulse_tv_usage": "High",
      "ai_analysis": "This person is progressing well...",
      "suggested_next_step": "Baptism / Group / Serving / Meet pastor"
    }
  ]
}
```

---

### 7. Attendance (`/people/attendance`)

#### 🔨 New Endpoints Needed

**GET /api/attendance/patterns**
- Sunday attendance patterns
- Kids attendance
- Youth attendance
- Missing streaks (people who haven't attended in X days)
- Engagement patterns
- First-time visitors
- Families missing
- Serving attendance
- Event attendance

**Response:**
```json
{
  "sunday_avg": 450,
  "sunday_month": 1800,
  "sunday_trend": 5.2,
  "kids_attendance": {...},
  "youth_attendance": {...},
  "missing_streaks": [
    {
      "person_id": "person_123",
      "name": "John Smith",
      "days": 21,
      "last_attended": "2023-12-15"
    }
  ],
  "first_time_visitors": 12,
  "families_missing": [...],
  "serving_attendance": {...},
  "event_attendance": {...}
}
```

---

### 8. Groups (`/connect-groups`)

#### ✅ Already Exists
- `GET /api/connect-groups` - Get all groups
- Group management endpoints exist

---

## Database Schema Updates Needed

### Person Model Additions
- `family_id` or `household` field (for family grouping)
- `is_new_christian` boolean
- `new_christian_date` date
- `follow_up_status` string
- `service_attended` string
- `foundations_progress` string
- `pathway_progress` string
- `group_attendance` integer (percentage)
- `pulse_tv_usage` string

### New Tables Needed

**pastoral_care_cases**
- id
- person_id
- priority (high/medium/low)
- status (open/resolved)
- notes
- assigned_leader
- follow_up_date
- ai_summary
- suggested_responses
- created_at
- updated_at

**attendance_records**
- id
- person_id
- attendance_date
- attendance_type (sunday/kids/youth/serving/event)
- campus
- service_time
- created_at

---

## Implementation Priority

### Phase 1 (Critical - Core Functionality)
1. ✅ Enhance `GET /api/persons` with family grouping
2. 🔨 `GET /api/people/families`
3. 🔨 `GET /api/heartbeat/dashboard`
4. 🔨 `GET /api/people/new-people` (enhance existing)

### Phase 2 (Important - Care & Discipleship)
5. 🔨 `GET /api/pastoral-care/cases`
6. 🔨 `POST /api/pastoral-care/cases`
7. 🔨 `GET /api/people/new-christians`

### Phase 3 (Nice to Have - Analytics)
8. 🔨 `GET /api/attendance/patterns`

---

## Notes
- All endpoints should respect user permissions (campus scoping, role-based access)
- AI features can use existing Anthropic integration
- Heartbeat calculations should use existing engagement profile system
- Family grouping may need household/family relationship table

