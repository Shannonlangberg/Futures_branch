# User Roles & Permissions Guide

## All Available Roles

### 1. **Admin**
**Full System Access** - Can do everything
- ✅ Log Stats (all campuses)
- ✅ View Dashboards (all campuses)
- ✅ View/Edit Finance Data
- ✅ Manage Users (add/edit/delete)
- ✅ Manage Campuses
- ✅ Query/Export Data
- ✅ All Settings

### 2. **Senior Leadership** (Josh)
**Full System Access** - Same as Admin
- ✅ Log Stats (all campuses)
- ✅ View Dashboards (all campuses)
- ✅ View/Edit Finance Data
- ✅ Manage Users (add/edit/delete)
- ✅ Manage Campuses
- ✅ Query/Export Data
- ✅ All Settings

### 3. **Campus Pastor**
**Campus-Specific Management**
- ✅ Log Stats (own campus only)
- ✅ View Dashboards (own campus only)
- ❌ No Finance Access
- ❌ Cannot Manage Users
- ❌ Cannot Manage Campuses
- ✅ Query Data (own campus)

### 4. **Pastor**
**Basic Pastor Access**
- ✅ Log Stats (own campus)
- ✅ View Dashboards (own campus only)
- ❌ No Finance Access
- ❌ Cannot Manage Users
- ❌ Cannot Manage Campuses
- ✅ Query Data (own campus)

### 5. **Finance**
**Finance-Only Access**
- ❌ Cannot Log Stats
- ❌ Cannot View Dashboards
- ✅ Finance Data ONLY (submit tithe)
- ❌ Cannot Manage Users
- ❌ Cannot Manage Campuses
- ❌ No Query Access

## Current Users

| Name | Username | Role | What They Can Do |
|------|----------|------|------------------|
| Shannon Langberg | admin | Admin | Everything |
| Josh Greenwood | Josh Greenwood | Senior Leadership | Everything (same as admin) |
| Ashley Evans | Ashley Evans | Senior Leadership | Everything (same as admin) |
| Shannon Langberg | Shannon Langberg | Senior Pastor | Log stats, view all dashboards |
| Finance | Finance | Finance | Submit tithe only |

## Permission Matrix

| Permission | Admin | Senior Leadership | Campus Pastor | Pastor | Finance |
|------------|-------|-------------------|---------------|--------|---------|
| Log Stats | ✅ All | ✅ All | ✅ Own | ✅ Own | ❌ |
| View Dashboards | ✅ All | ✅ All | ✅ Own | ✅ Own | ❌ |
| Finance Data | ✅ | ✅ | ❌ | ❌ | ✅ |
| Manage Users | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Campuses | ✅ | ✅ | ❌ | ❌ | ❌ |
| Query/Export | ✅ All | ✅ All | ✅ Own | ✅ Own | ❌ |

## Notes
- **Senior Leadership** = Same as Admin (updated today)
- **Campus Pastor** / **Pastor** only see their assigned campus data
- **Finance** role is restricted to tithe submission only
- Use "All Campuses" when creating users who should see all locations

## UI Refresh Issue
**Issue**: When updating a user's role, the table doesn't refresh automatically.
**Status**: Fixed - the user list now reloads before closing the modal.
**Deployed**: Yes (in latest deployment)

