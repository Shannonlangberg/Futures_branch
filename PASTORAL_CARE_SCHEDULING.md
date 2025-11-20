# Pastoral Care Scheduling System

## Overview

A comprehensive system for scheduling catch-ups, appointments, and pastoral care sessions with role-based access control and notification support.

## Features

✅ **Role-Based Access Control**
- Pastors/Leaders can schedule appointments for anyone
- Members can view their own appointments
- Admins have full access

✅ **Appointment Management**
- Create, view, update, and cancel appointments
- Link appointments to care cases
- Track appointment status (scheduled, confirmed, completed, cancelled, no_show)

✅ **Flexible Scheduling**
- Multiple appointment types (catch_up, counseling, prayer, follow_up, other)
- Customizable duration (default 30 minutes)
- Multiple location options (office, coffee_shop, home, church, online, other)
- Detailed location information

✅ **Notification Support** (Ready for implementation)
- Email notifications for person and pastor
- In-app notifications
- Reminder system

## API Endpoints

### Get Appointments
```
GET /api/pastoral-care/appointments
Query Parameters:
  - person_id: Filter by person
  - pastor_id: Filter by pastor
  - status: Filter by status (scheduled, confirmed, completed, cancelled)
  - start_date: Filter by start date
  - end_date: Filter by end date
  - upcoming_only: true/false - Only show upcoming appointments
```

### Create Appointment
```
POST /api/pastoral-care/appointments
Body:
{
  "person_id": "required",
  "pastor_id": "optional (defaults to current user)",
  "care_case_id": "optional",
  "title": "Pastoral Care Catch-Up",
  "description": "optional",
  "appointment_type": "catch_up | counseling | prayer | follow_up | other",
  "scheduled_date": "2025-01-20T14:00:00Z",
  "duration_minutes": 30,
  "location": "office | coffee_shop | home | church | online | other",
  "location_details": "optional specific address or meeting link"
}
```

### Get Single Appointment
```
GET /api/pastoral-care/appointments/<appointment_id>
```

### Update Appointment
```
PUT /api/pastoral-care/appointments/<appointment_id>
Body: (any fields to update)
{
  "title": "Updated title",
  "status": "confirmed",
  "notes": "Private notes for pastor",
  ...
}
```

### Confirm Appointment
```
POST /api/pastoral-care/appointments/<appointment_id>/confirm
```

### Cancel Appointment
```
DELETE /api/pastoral-care/appointments/<appointment_id>
```

### Get Available Pastors
```
GET /api/pastoral-care/available-pastors
```

## Role Permissions

| Action | Admin/Pastor/Leader | Member |
|--------|-------------------|--------|
| View all appointments | ✅ | ❌ |
| View own appointments | ✅ | ✅ |
| Create appointment | ✅ | ❌ |
| Update appointment | ✅ | ✅ (own only) |
| Cancel appointment | ✅ | ❌ |
| View pastor notes | ✅ | ❌ |

## Database Schema

The `pastoral_care_appointments` table includes:
- Person and pastor relationships
- Optional link to care cases
- Appointment details (title, description, type, date, duration, location)
- Status tracking
- Notification flags
- Timestamps (created, updated, completed, cancelled)
- Notes (private for pastor, follow-up notes)

## Next Steps

1. **Frontend Implementation**
   - Create appointment scheduling form
   - Calendar view for appointments
   - List view with filters
   - Appointment detail modal

2. **Notification System**
   - Email notifications on appointment creation
   - Email reminders (24 hours before)
   - In-app notification center
   - Push notifications (for mobile app)

3. **Integration**
   - Link with existing CareCase system
   - Add to person profile page
   - Dashboard widget for upcoming appointments
   - Calendar integration (Google Calendar, Outlook)

4. **Mobile App**
   - Schedule catch-up button on person profile
   - Notification handling
   - Calendar view

## Usage Example

### Scheduling a Catch-Up (Pastor/Leader)

```javascript
// From a person's profile page
const scheduleCatchUp = async (personId) => {
  const response = await fetch('/api/pastoral-care/appointments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      person_id: personId,
      title: 'Pastoral Care Catch-Up',
      appointment_type: 'catch_up',
      scheduled_date: '2025-01-20T14:00:00Z',
      duration_minutes: 30,
      location: 'office',
      description: 'Regular check-in'
    })
  });
  
  const result = await response.json();
  // Appointment created, notifications sent
};
```

### Viewing Upcoming Appointments

```javascript
const getUpcomingAppointments = async () => {
  const response = await fetch('/api/pastoral-care/appointments?upcoming_only=true', {
    credentials: 'include'
  });
  
  const { appointments } = await response.json();
  // Display appointments in calendar or list
};
```

## Migration

Run the migration to create the database table:
```bash
# The migration file is at:
backend/migrations/019_pastoral_care_appointments.sql
```

The table will be created automatically when the app starts if using SQLite migrations.


