# Roles & Permissions Reference Table

## Complete Role Permissions Matrix

| Role | Description | Users | Campuses | Settings | Devotions | Connect Groups | Beacons | Serving | Communications | Prayer | Events | Finance | Heartbeat | Passport |
|------|-------------|-------|----------|----------|-----------|----------------|---------|---------|-----------------|--------|--------|---------|-----------|----------|
| **admin** | Administrator - Full system access | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **senior_leadership** | Senior Leadership - Same as admin | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **senior_pastor** | Senior Pastor - Full access | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **lead_pastor** | Lead Pastor - Full access | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **campus_pastor** | Campus-specific leadership | 👁️ View/Edit | 👁️ View/Edit | ❌ None | 👁️ View/Edit/Publish | ✅ All | ❌ None | ✅ All | ✅ All | ✅ All | ✅ All | 👁️ View | ✅ All | ✅ All |
| **staff** | Staff Member - Limited admin | 👁️ View | 👁️ View | ❌ None | 👁️ View/Edit | 👁️ View/Edit | ❌ None | 👁️ View/Edit | 👁️ View/Edit | 👁️ View/Edit | 👁️ View/Edit | ❌ None | 👁️ View | 👁️ View |
| **dream_team_leader** | Volunteer team leadership | ❌ None | 👁️ View | ❌ None | 👁️ View | 👁️ View | ❌ None | 👁️ View/Edit | ❌ None | 👁️ View | 👁️ View | ❌ None | 👁️ View | 👁️ View |
| **member** | Regular church member | ❌ None | ❌ None | ❌ None | ❌ None | 👁️ Own Groups | ❌ None | 👁️ Own Only | ❌ None | 👁️ Own/Create | 👁️ View | ❌ None | 👁️ Own | 👁️ Own/Edit |
| **connect_group_leader** | Connect group leader | ❌ None | 👁️ View | ❌ None | ❌ None | 👁️ Own Groups/Edit | ❌ None | ❌ None | ❌ None | ❌ None | 👁️ View | ❌ None | 👁️ Own/Edit | ❌ None |

**Legend:**
- ✅ All = Full access (can view, edit, create, delete)
- 👁️ View = Can view only
- 👁️ View/Edit = Can view and edit
- 👁️ Own/Edit = Can view and edit own data only
- 👁️ Own Groups = Can view own connect groups only
- ❌ None = No access

---

## Detailed Role Breakdown

### 1. Administrator (admin)
**Access Level:** Full system access - can see all campuses and regions

**Can Do:**
- ✅ Manage all users (create, edit, delete)
- ✅ Manage all campuses
- ✅ System settings and configuration
- ✅ Manage devotions (create, edit, publish, delete)
- ✅ Manage all connect groups
- ✅ Manage beacons (Bluetooth zone management)
- ✅ Full serving management
- ✅ Full communications access
- ✅ Manage all prayer requests
- ✅ Manage all events
- ✅ Full finance access
- ✅ Full heartbeat/engagement dashboard access
- ✅ Full passport access

**Campus Scope:** All campuses (cross-campus access)
**Region Scope:** All regions (global access)

---

### 2. Senior Leadership (senior_leadership)
**Access Level:** Full system access - same as admin

**Can Do:**
- ✅ Everything that admin can do
- ✅ All system functions
- ✅ Cross-campus and cross-region access

**Campus Scope:** All campuses (cross-campus access)
**Region Scope:** All regions (global access)

---

### 3. Senior Pastor (senior_pastor)
**Access Level:** Full system access

**Can Do:**
- ✅ Everything that admin can do
- ✅ All system functions
- ✅ Cross-campus and cross-region access

**Campus Scope:** All campuses (cross-campus access)
**Region Scope:** All regions (global access)

---

### 4. Lead Pastor (lead_pastor)
**Access Level:** Full system access

**Can Do:**
- ✅ Everything that admin can do
- ✅ All system functions
- ✅ Cross-campus and cross-region access

**Campus Scope:** All campuses (cross-campus access)
**Region Scope:** All regions (global access)

---

### 5. Campus Pastor (campus_pastor)
**Access Level:** Campus-specific leadership and management

**Can Do:**
- ✅ View and edit users (within campus scope)
- ✅ View and edit campuses
- ✅ Manage devotions (view, edit, publish) for their campus
- ✅ Full access to connect groups (within campus)
- ❌ No beacon management
- ✅ Full serving management (within campus)
- ✅ Full communications (within campus)
- ✅ Manage prayer requests (within campus)
- ✅ Manage events (within campus)
- ✅ View finance data only (cannot edit)
- ✅ Full heartbeat access (within campus)
- ✅ Full passport access (within campus)

**Campus Scope:** Own campus only
**Region Scope:** Own region only

---

### 6. Staff Member (staff)
**Access Level:** Limited administrative access

**Can Do:**
- ✅ View users only (cannot edit)
- ✅ View campuses only
- ❌ No system settings access
- ✅ Manage devotions (view, edit) - cannot publish or delete
- ✅ View and edit connect groups
- ❌ No beacon access
- ✅ View and edit serving assignments
- ✅ View and edit communications
- ✅ View and edit prayer requests
- ✅ View and edit events
- ❌ No finance access
- ✅ View heartbeat dashboards only
- ✅ View passport only

**Campus Scope:** Own campus only
**Region Scope:** Own region only

---

### 7. Dream Team Leader (dream_team_leader)
**Access Level:** Volunteer team leadership

**Can Do:**
- ❌ Cannot manage users
- ✅ View campuses
- ❌ No system access
- ✅ View devotions only
- ✅ View connect groups only
- ❌ No beacon access
- ✅ View and edit serving assignments (for their team)
- ❌ No communications access
- ✅ View prayer requests
- ✅ View events
- ❌ No finance access
- ✅ View heartbeat dashboards
- ✅ View passport

**Campus Scope:** Own campus only
**Region Scope:** Own region only

---

### 8. Member (member)
**Access Level:** Regular church member

**Can Do:**
- ❌ No user management
- ❌ No campus management
- ❌ No system access
- ❌ No devotions management
- ✅ View own connect groups only
- ❌ No beacon access
- ✅ View own serving assignments only
- ❌ No communications access
- ✅ View own prayer requests and create new ones
- ✅ View events
- ❌ No finance access
- ✅ View own heartbeat/engagement profile
- ✅ View and edit own passport

**Campus Scope:** Own data only
**Region Scope:** Own region only

---

### 9. Connect Group Leader (connect_group_leader)
**Access Level:** Connect group leader with group management and attendance marking

**Can Do:**
- ❌ No user management
- ✅ View campuses
- ❌ No system access
- ❌ No devotions management
- ✅ View and edit own connect groups
- ❌ No beacon access
- ❌ No serving access
- ❌ No communications access
- ❌ No prayer request access
- ✅ View events
- ❌ No finance access
- ✅ View and edit own heartbeat (can mark attendance which feeds heartbeat)
- ❌ No passport access

**Campus Scope:** Own groups only
**Region Scope:** Own region only

**Special Notes:**
- Can mark attendance for their connect group members
- Attendance marking feeds into heartbeat/engagement profiles

---

## Campus & Region Scoping Rules

### Cross-Campus Access
The following roles can see data from **all campuses**:
- admin
- senior_leadership
- senior_pastor
- lead_pastor
- finance (if this role exists)

### Regional Access
The following roles can see data from **all regions** (global access):
- admin
- senior_leadership
- senior_pastor
- lead_pastor

### Campus-Scoped Resources
These resources are automatically filtered by campus for non-cross-campus roles:
- Connect Groups
- Devotions Admin
- Serving
- Events
- Prayer Requests
- Heartbeat

### Region-Scoped Resources
These resources respect region boundaries:
- Campuses
- Connect Groups
- Devotions Admin
- Serving
- Events
- Prayer Requests
- Finance
- Heartbeat

---

## Permission Action Definitions

- **view** = Can see/read the resource
- **edit** = Can modify existing resources
- **create** = Can create new resources
- **delete** = Can remove resources
- **manage** = Can perform all management actions
- **publish** = Can publish content (e.g., devotions)
- **view_own** = Can only see own data
- **edit_own** = Can only edit own data
- **view_self_groups** = Can see own connect groups
- **view_own_groups** = Can see groups they lead
- **edit_own_groups** = Can edit groups they lead
- **\*** = Wildcard - full access to all actions for that resource
- **[]** = Empty array means no access

---

## Quick Reference: What Each Role Can See

| Role | Dashboard Access | Stats Logging | User Management | Campus Management | Finance | Groups | Events |
|------|------------------|---------------|-----------------|-------------------|---------|--------|--------|
| admin | ✅ All Campuses | ✅ All Campuses | ✅ Yes | ✅ Yes | ✅ Full | ✅ All | ✅ All |
| senior_leadership | ✅ All Campuses | ✅ All Campuses | ✅ Yes | ✅ Yes | ✅ Full | ✅ All | ✅ All |
| senior_pastor | ✅ All Campuses | ✅ All Campuses | ✅ Yes | ✅ Yes | ✅ Full | ✅ All | ✅ All |
| lead_pastor | ✅ All Campuses | ✅ All Campuses | ✅ Yes | ✅ Yes | ✅ Full | ✅ All | ✅ All |
| campus_pastor | ✅ Own Campus | ✅ Own Campus | 👁️ View Only | 👁️ View Only | 👁️ View | ✅ Own Campus | ✅ Own Campus |
| staff | ✅ Own Campus | ✅ Own Campus | 👁️ View Only | 👁️ View Only | ❌ None | ✅ Own Campus | ✅ Own Campus |
| dream_team_leader | ✅ Own Campus | ❌ None | ❌ None | ❌ None | ❌ None | ✅ Own Campus | ✅ Own Campus |
| member | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | 👁️ Own Only | ✅ View |
| connect_group_leader | ❌ None | ❌ None | ❌ None | ❌ None | ❌ None | ✅ Own Groups | ✅ View |

---

## Notes

1. **Cross-Campus Roles**: admin, senior_leadership, senior_pastor, and lead_pastor can see data from all campuses and regions.

2. **Campus-Scoped Roles**: campus_pastor, staff, dream_team_leader, member, and connect_group_leader are restricted to their assigned campus.

3. **Finance Role**: While mentioned in cross-campus roles, finance role may have limited access - only to finance-specific features.

4. **Special Permissions**: 
   - Connect Group Leaders can mark attendance which feeds into Heartbeat/engagement profiles
   - Members can create their own prayer requests
   - Members can view and edit their own Passport profile

5. **Resource Hierarchy**: Full access (`*`) includes all actions (view, edit, create, delete, manage, etc.)

