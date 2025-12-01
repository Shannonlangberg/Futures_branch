# New People & New Christians System Analysis

## Overview

The system has two dedicated pages for tracking new people and new Christians:
- **New People** (`/people/new-people`) - Tracks visitors/newcomers
- **New Christians** (`/people/new-christians`) - Tracks people who made a decision for Christ

---

## How They Work

### 1. New People Page

**Location:** `frontend/src/pages/people/NewPeople.jsx`

**How People Are Identified:**
- People are considered "new" if they were **created in the last 30 days** (`created_at >= 30 days ago`)
- The page calls: `GET /api/persons?new_people=true`
- Backend filters persons where `created_at >= (now - 30 days)`

**What's Displayed:**
- Name (preferred or full)
- Visit Date (from `created_at` or `date_added`)
- Campus
- Service Attended (`service_attended` field)
- Follow-up Status (`follow_up_status` field - can be: 'contacted', 'connected', 'joined_events', 'needed')
- Next Steps (placeholder: 'Connect to group')
- AI Follow-up Message (if available)

**Current Limitations:**
- No assignment functionality visible
- Follow-up status is just displayed, not actionable
- No way to assign someone to follow up
- No workflow to move people through stages
- AI follow-up message field exists but may not be populated

---

### 2. New Christians Page

**Location:** `frontend/src/pages/people/NewChristians.jsx`

**How People Are Identified:**
- People are considered "new Christians" if they meet ANY of these criteria:
  1. `new_christian_date` exists and is within the last 2 years
  2. `is_new_christian` flag is `True`
  3. `baptised_on` date exists and is within the last 2 years

**What's Displayed:**
- Name
- Decision Date (`new_christian_date` or `baptised_on`)
- **Foundations Progress** (currently hardcoded as '50%' - TODO)
- **Pathway Progress** (calculated from `PersonPathwayProgress` and `PersonPathwayStepCompletion`)
- **Group Attendance** (percentage calculated from engagement profile attendance log)
- **Pulse TV Usage** (currently hardcoded as 'Medium' - TODO)
- **AI Analysis** (basic analysis with suggested next steps)

**Current Limitations:**
- Foundations progress is hardcoded
- Pulse TV usage is hardcoded
- No assignment functionality
- No way to track who's responsible for follow-up
- AI analysis is basic

---

## Current Follow-Up System

### Database Fields Available

From `models.py`, the Person model has:
- `follow_up_status` (TEXT): Can be 'contacted', 'connected', 'joined_events', 'needed'
- `service_attended` (TEXT): Service time they attended
- `is_new_christian` (BOOLEAN): Flag for new Christian
- `new_christian_date` (DATE): Date of decision
- `assigned_leader` (in PastoralCareCase): For pastoral care assignments

### What's Missing

1. **No Assignment System for New People/Christians**
   - No field to assign a leader/staff member to follow up
   - No way to track who's responsible
   - No notification system when someone is assigned

2. **No Workflow/Status Progression**
   - Follow-up status exists but no clear workflow
   - No way to move people through stages (e.g., Initial Contact → Connected → In Group → Serving)
   - No timeline or history of follow-up actions

3. **No Automated Follow-Up**
   - No reminders for follow-up
   - No scheduled tasks
   - No integration with communication system for automated messages

4. **Limited Context**
   - No notes/history of interactions
   - No way to see what's been done
   - No connection to other systems (events, groups, serving)

---

## Recommended Improvements

### 1. Assignment System

**Add to Person Model:**
```python
assigned_follow_up_leader = db.Column(db.String(200))  # User ID or name
assigned_follow_up_date = db.Column(db.DateTime)  # When assigned
follow_up_priority = db.Column(db.String(20))  # 'high', 'medium', 'low'
```

**Features:**
- Dropdown to assign a staff member/leader
- Show who's assigned on the card
- Filter by "My Assignments"
- Notification when assigned

### 2. Enhanced Follow-Up Workflow

**Status Progression:**
```
Needed → Contacted → Connected → In Group → Serving → Complete
```

**Add Actions:**
- "Mark as Contacted" button
- "Connect to Group" button (links to connect groups)
- "Start Pathway" button (for new Christians)
- "Schedule Follow-up" button (creates calendar event)

### 3. Follow-Up History & Notes

**Add Follow-Up Log:**
```python
class FollowUpLog(db.Model):
    person_id = db.Column(db.String(50), db.ForeignKey('persons.id'))
    action = db.Column(db.String(50))  # 'contacted', 'assigned', 'connected', etc.
    notes = db.Column(db.Text)
    performed_by = db.Column(db.String(200))
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Display:**
- Timeline of follow-up actions
- Who did what and when
- Notes from each interaction

### 4. Smart Suggestions & Automation

**For New People:**
- Suggest connect groups based on campus/department
- Suggest events they might be interested in
- Auto-generate welcome message
- Remind if no contact after 48 hours

**For New Christians:**
- Auto-suggest starting Foundations pathway
- Suggest next discipleship steps based on progress
- Alert if no group attendance after 2 weeks
- Suggest serving opportunities when ready

### 5. Integration Points

**Connect to Existing Systems:**
- **Connect Groups:** One-click "Add to Group" from new people page
- **Pathways:** Auto-enroll new Christians in Foundations
- **Events:** Suggest relevant events
- **Serving:** Suggest serving opportunities when ready
- **Communication:** Send welcome emails/SMS automatically
- **Heartbeat:** Track engagement automatically

### 6. Dashboard & Metrics

**Add Metrics:**
- Total new people this week/month
- Follow-up completion rate
- Average time to first contact
- Conversion rate (new people → new Christians)
- New Christian retention rate

**Filters:**
- By campus
- By assigned leader
- By follow-up status
- By time period

---

## Recommended Journey Forward

### For New People (Visitors)

```
Week 1: First Visit
├─ Auto-assign to campus pastor/staff
├─ Send welcome email/SMS
├─ Log service attended
└─ Status: "Needed" → "Contacted"

Week 1-2: Initial Follow-Up
├─ Personal contact (call/text)
├─ Invite to connect group
├─ Invite to next service
└─ Status: "Contacted" → "Connected"

Week 2-4: Integration
├─ Attend connect group
├─ Attend events
├─ Get to know people
└─ Status: "Connected" → "In Group"

Month 2+: Engagement
├─ Regular attendance
├─ Consider serving
├─ Consider Foundations (if not Christian)
└─ Status: "In Group" → "Engaged"
```

### For New Christians

```
Week 1: Decision & Celebration
├─ Log decision date
├─ Assign discipleship leader
├─ Send congratulations message
├─ Invite to baptism class
└─ Status: "New Christian - Initial"

Week 1-2: Foundations
├─ Enroll in Foundations pathway
├─ Start DNA course
├─ Connect to mentor/leader
└─ Status: "In Foundations"

Week 2-4: Community
├─ Join connect group
├─ Attend Rise (if applicable)
├─ Regular attendance
└─ Status: "Connected to Community"

Month 2-3: Growth
├─ Complete Foundations
├─ Get baptized
├─ Fill with Holy Spirit
└─ Status: "Growing in Faith"

Month 3+: Serving
├─ Start serving
├─ Mentor others
├─ Lead connect group (if called)
└─ Status: "Serving & Leading"
```

---

## Implementation Priority

### Phase 1: Core Functionality (High Priority)
1. ✅ Assignment system (assign leader to follow up)
2. ✅ Action buttons (Mark as Contacted, Connect to Group, etc.)
3. ✅ Follow-up status workflow
4. ✅ Basic notes/history

### Phase 2: Integration (Medium Priority)
1. ✅ Connect to Connect Groups API
2. ✅ Connect to Pathways API
3. ✅ Connect to Communication API (send messages)
4. ✅ Connect to Events API (suggest events)

### Phase 3: Automation (Lower Priority)
1. ✅ Auto-assignment rules
2. ✅ Automated reminders
3. ✅ Smart suggestions (AI-powered)
4. ✅ Metrics dashboard

---

## Technical Implementation Notes

### Backend Changes Needed

1. **Add Assignment Fields to Person Model:**
   - Migration to add `assigned_follow_up_leader`, `assigned_follow_up_date`, `follow_up_priority`

2. **Create Follow-Up Log Table:**
   - New model: `FollowUpLog`
   - Track all follow-up actions

3. **API Endpoints:**
   - `POST /api/persons/<id>/assign` - Assign follow-up leader
   - `POST /api/persons/<id>/follow-up` - Log follow-up action
   - `GET /api/persons/<id>/follow-up-history` - Get follow-up history
   - `POST /api/persons/<id>/update-status` - Update follow-up status

4. **Enhance Existing Endpoints:**
   - `GET /api/people/new-people` - Add assignment info
   - `GET /api/people/new-christians` - Add assignment info, better progress calculation

### Frontend Changes Needed

1. **New People Page:**
   - Add assignment dropdown
   - Add action buttons (Contact, Connect to Group, etc.)
   - Add follow-up history timeline
   - Add notes section

2. **New Christians Page:**
   - Add assignment dropdown
   - Add action buttons (Start Pathway, Connect to Group, etc.)
   - Better progress visualization
   - Add follow-up history

3. **Shared Components:**
   - Assignment selector component
   - Follow-up action buttons
   - Status workflow component
   - Follow-up history timeline

---

## Questions to Consider

1. **Who should be assignable?**
   - All staff?
   - Campus pastors only?
   - Connect group leaders?
   - Volunteers?

2. **What's the SLA for follow-up?**
   - How quickly should new people be contacted?
   - What's the priority system?

3. **What triggers "New People"?**
   - Currently: created in last 30 days
   - Should it be based on first attendance?
   - Should it be manually flagged?

4. **What triggers "New Christian"?**
   - Currently: decision date, baptism, or flag
   - Should it be manually set?
   - Should it auto-detect from other systems?

5. **Integration with other systems:**
   - Should new people auto-create in other systems?
   - Should new Christians auto-enroll in pathways?
   - Should assignments sync with calendar?

---

## Next Steps

1. **Review this analysis** with stakeholders
2. **Prioritize features** based on needs
3. **Design UI/UX** for assignment and actions
4. **Create database migrations** for new fields
5. **Implement backend APIs** for assignments and follow-up
6. **Update frontend pages** with new functionality
7. **Test workflow** end-to-end
8. **Train staff** on new system

