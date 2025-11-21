# New Heartbeat Data Sources Implementation

## ✅ PHASE 1: FOUNDATION (COMPLETE)

### Models Created (backend/models.py)
- ✅ `AppSession` - Track app opens
- ✅ `PrayerSubmission` - Track prayer/praise submissions
- ✅ Existing: `TVUserEpisodeProgress` - Already tracking video completion
- ✅ Existing: `EventRegistration` - Already tracking event attendance

### API Endpoints Created (backend/engagement_api.py)
- ✅ `POST /api/engagement/log-app-open` - Log app opens (+1 engagement)
- ✅ `POST /api/engagement/submit-prayer` - Submit prayers (+5 care/spiritual)
- ✅ `POST /api/engagement/mark-event-attended` - Mark event attendance (+10 engagement)

### Database Migration
- ✅ `migrations/027_new_heartbeat_sources.sql` - Creates app_sessions and prayer_submissions tables

---

## 🔨 PHASE 2: HEARTBEAT ENGINE INTEGRATION (TODO)

### Update heartbeat_engine.py

#### 1. _load_person_data() - Add new data sources
```python
# Add to _load_person_data():

# App opens (last 12 weeks)
app_opens = AppSession.query.filter(
    AppSession.person_id == person_id,
    AppSession.session_start >= start_datetime
).all()

# Event attendance
event_attendance = EventRegistration.query.filter(
    EventRegistration.person_id == person_id,
    EventRegistration.status == 'attended',
    EventRegistration.created_at >= start_datetime
).all()

# TV episode completions
tv_completions = TVUserEpisodeProgress.query.filter(
    TVUserEpisodeProgress.person_id == person_id,
    TVUserEpisodeProgress.completed == True,
    TVUserEpisodeProgress.completed_at >= start_datetime
).all()

# Prayer submissions
prayer_submissions = PrayerSubmission.query.filter(
    PrayerSubmission.person_id == person_id,
    PrayerSubmission.created_at >= start_datetime
).all()

# Add to returned dict:
return {
    ...(existing fields)...
    'app_opens': app_opens,
    'event_attendance': event_attendance,
    'tv_completions': tv_completions,
    'prayer_submissions': prayer_submissions
}
```

#### 2. _calculate_engagement_score() - Add points

```python
def _calculate_engagement_score(self, data, start_date, end_date):
    ...(existing code)...
    
    # 4. App Opens (5% of engagement) - 1 point per open, max 5 points
    app_opens = data.get('app_opens', [])
    app_open_score = min(len(app_opens) * 1, 5.0)
    
    # 5. Event Attendance (10% of engagement) - 10 points per event
    event_attendance = data.get('event_attendance', [])
    event_score = min(len(event_attendance) * 10, 10.0)
    
    # Rebalance weights:
    # Connect Groups: 35%
    # Serving: 25%
    # Giving: 25%
    # App Opens: 5%
    # Events: 10%
    
    total_score = (
        connect_score * 0.35 +
        serving_score * 0.25 +
        giving_score * 0.25 +
        app_open_score * 0.05 +
        event_score * 0.10
    )
```

#### 3. _calculate_spiritual_score() - Add TV and Prayer

```python
def _calculate_spiritual_score(self, data, start_date, end_date):
    ...(existing code)...
    
    # 3. Pulse TV Completions (20% of spiritual)
    tv_completions = data.get('tv_completions', [])
    if tv_completions:
        # 5 points per video, max 20 points
        tv_score = min(len(tv_completions) * 5, 20.0)
    else:
        tv_score = 0.0
    
    # Rebalance weights:
    # Discipleship milestones: 60%
    # Pathway progress: 20%
    # TV Completions: 20%
```

#### 4. _calculate_care_score() - Add Prayer

```python
def _calculate_care_score(self, data):
    ...(existing code)...
    
    # 3. Prayer Submissions (20% of care)
    prayer_submissions = data.get('prayer_submissions', [])
    if prayer_submissions:
        # 5 points per submission, max 20 points
        prayer_score = min(len(prayer_submissions) * 5, 20.0)
    else:
        prayer_score = 0.0
    
    # Rebalance weights:
    # Open care cases: 60%
    # Recent touchpoints: 20%
    # Prayer submissions: 20%
```

---

## 🔨 PHASE 3: HEARTBEAT API INTEGRATION (TODO)

### Update heartbeat_api.py - get_person_heartbeat()

Add new data to `recent_activity`:

```python
# After existing queries...

# App opens (last 20)
recent_app_opens = AppSession.query.filter(
    AppSession.person_id == person_id,
    AppSession.session_start >= datetime.combine(twelve_weeks_ago, datetime.min.time())
).order_by(AppSession.session_start.desc()).limit(20).all()

# Event attendance
recent_events = EventRegistration.query.filter(
    EventRegistration.person_id == person_id,
    EventRegistration.status == 'attended',
    EventRegistration.created_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
).order_by(EventRegistration.created_at.desc()).limit(10).all()

# TV completions
recent_tv = TVUserEpisodeProgress.query.filter(
    TVUserEpisodeProgress.person_id == person_id,
    TVUserEpisodeProgress.completed == True,
    TVUserEpisodeProgress.completed_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
).order_by(TVUserEpisodeProgress.completed_at.desc()).limit(10).all()

# Prayer submissions
recent_prayers = PrayerSubmission.query.filter(
    PrayerSubmission.person_id == person_id,
    PrayerSubmission.created_at >= datetime.combine(twelve_weeks_ago, datetime.min.time())
).order_by(PrayerSubmission.created_at.desc()).limit(10).all()

# Add to response:
'recent_activity': {
    ...(existing fields)...
    'app_opens': [a.to_dict() for a in recent_app_opens],
    'event_attendance': [e.to_dict() for e in recent_events],
    'tv_completions': [t.to_dict() for t in recent_tv],
    'prayer_submissions': [p.to_dict() for p in recent_prayers]
}
```

---

## 📱 PHASE 4: MOBILE APP INTEGRATION (TODO)

### 1. App Opens (mobile/src/App.js or index.js)

```javascript
// In main app entry point, on mount:
useEffect(() => {
  const logAppOpen = async () => {
    const userData = await AsyncStorage.getItem('userData');
    if (userData) {
      const user = JSON.parse(userData);
      try {
        await ApiService.logAppOpen(user.email, 'ios'); // or 'android'
        console.log('✅ App open logged');
      } catch (error) {
        console.log('Failed to log app open:', error);
      }
    }
  };
  
  logAppOpen();
}, []);
```

### 2. Prayer Submission UI (new screen)

Create `mobile/src/screens/PrayerSubmissionScreen.js`:
- Form with prayer/praise toggle
- Text area for content
- Category selector
- Anonymous option
- Submit button calls ApiService.submitPrayer()

### 3. Event Check-In

Update event detail screen to include check-in button that calls:
```javascript
await ApiService.markEventAttended(user.email, event.id);
```

---

## 🌐 PHASE 5: WEB APP INTEGRATION (TODO)

### 1. Prayer Submission Page (frontend/src/pages/PrayerSubmit.jsx)
- Public form for submitting prayers/praises
- Works with QR codes
- Submit via `/api/engagement/submit-prayer`

### 2. Event Check-In  
- Add check-in button to event registration confirmations
- Staff can mark attendance from event management

---

## 📊 EXPECTED IMPACT

### Engagement Score (out of 100)
- **Before:** Connect Groups (40%), Serving (30%), Giving (30%)
- **After:** Connect Groups (35%), Serving (25%), Giving (25%), App Opens (5%), Events (10%)

### Spiritual Score (out of 100)
- **Before:** Discipleship milestones (80%), Pathway (20%)
- **After:** Milestones (60%), Pathway (20%), TV Completions (20%)

### Care Score (out of 100)
- **Before:** Care cases (70%), Touchpoints (30%)
- **After:** Care cases (60%), Touchpoints (20%), Prayers (20%)

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Run migration 027 on Railway database
- [ ] Deploy backend changes
- [ ] Test each endpoint individually
- [ ] Update mobile app with app open tracking
- [ ] Build prayer submission UI
- [ ] Test end-to-end heartbeat recalculation
- [ ] Verify all scores updating correctly
- [ ] Monitor for 1 week with real data

---

## 📝 TESTING PLAN

1. **App Opens:** Open app 5 times, verify +5 engagement
2. **Events:** Attend event, verify +10 engagement
3. **TV:** Complete video, verify +5 spiritual
4. **Prayer:** Submit prayer, verify +5 care
5. **Combined:** Do all 4, verify total score increase

---

## ⚡ QUICK START (Next Steps)

1. Run migration on dev database
2. Test API endpoints with Postman/curl
3. Update heartbeat_engine.py (Phase 2)
4. Update heartbeat_api.py (Phase 3)
5. Add mobile app open tracking (Phase 4.1)
6. Test with your own account!

