# Service Times Update Flow

## Current Status: ⚠️ **PARTIALLY AUTOMATIC**

When a campus service time is added or changed (e.g., Salisbury adds a 9:30 AM service), here's what happens:

---

## ✅ **What Updates Automatically**

### 1. **Input Form (Log Stats Page)**
- ✅ **YES** - Updates automatically
- The form calls `/api/campuses` which returns campus data including `service_times`
- The `getCampusServiceTimes()` function dynamically loads service times for the selected campus
- **When it updates**: Immediately when you refresh the page or select the campus
- **No restart needed**: The frontend fetches fresh data from the API

### 2. **Campus Management Page**
- ✅ **YES** - Updates when you save changes
- Service times are stored in the database (SQLite `campuses_new` table)
- When you update a campus via the Campus Management page, it saves to the database
- The `/api/v2/campuses/<campus_id>` PUT endpoint updates `service_times` in the database

### 3. **Mobile App (Futures App)**
- ✅ **YES** - Updates automatically
- The mobile app calls `/api/campuses/public` which returns campus data including `service_times`
- **When it updates**: On app refresh or when it fetches campus data
- **No restart needed**: The API returns current data from the database

---

## ⚠️ **What Needs Manual Updates**

### 1. **Google Sheets**
- ⚠️ **PARTIAL** - Needs column to exist first
- **Current Issue**: The backend hardcodes specific service time columns:
  - `9:00 AM`, `10:00 AM`, `11:00 AM`, `5:00 PM`, `5:30 PM`
  - `Kids 9:00 AM`, `Kids 10:00 AM`, `Kids 11:00 AM`, `Kids 5:00 PM`, `Kids 5:30 PM`
- **What happens**: If you add a new service time like "9:30 AM":
  - The input form will show it ✅
  - But the backend won't save it to Google Sheets ❌ (unless the column exists)
- **Solution**: 
  1. **Manual**: Add the column to Google Sheets first (e.g., add "9:30 AM" column)
  2. **Better**: Update the backend to dynamically handle any service time

### 2. **Dashboard**
- ⚠️ **PARTIAL** - Will show data if column exists
- The dashboard reads from Google Sheets
- If the Google Sheets column exists, the dashboard will show the data
- If the column doesn't exist, the data won't be saved, so nothing to display

---

## 🔧 **How It Currently Works**

### When You Update a Campus Service Time:

1. **Campus Management Page** → Updates database via `/api/v2/campuses/<campus_id>` PUT
2. **Database** → Stores `service_times` as JSON array in `campuses_new` table
3. **Input Form** → Fetches from `/api/campuses` → Gets updated `service_times` → Shows new fields ✅
4. **Backend Quick Input** → Tries to save to Google Sheets → Only saves if column exists ⚠️
5. **Dashboard** → Reads from Google Sheets → Shows data if column exists ⚠️
6. **Mobile App** → Fetches from `/api/campuses/public` → Gets updated `service_times` ✅

---

## 🐛 **Current Limitation**

The backend `quick_input` endpoint has **hardcoded service time columns**:

```python
row_data = {
    '9:00 AM': safe_value('9:00 AM'),
    '10:00 AM': safe_value('10:00 AM'),
    '11:00 AM': safe_value('11:00 AM'),
    '5:00 PM': safe_value('5:00 PM'),
    '5:30 PM': safe_value('5:30 PM'),
    # ... hardcoded list
}
```

**Problem**: If Salisbury adds "9:30 AM", the backend won't include it in `row_data`, so it won't be saved to Google Sheets.

**Workaround**: 
1. Manually add "9:30 AM" and "Kids 9:30 AM" columns to Google Sheets
2. The backend will then save data to those columns (because it uses the existing headers from the sheet)

---

## ✅ **Recommended Solution**

Update the backend to **dynamically handle service times**:

1. Get service times from the campus data (already available)
2. Dynamically build `row_data` dictionary with all service times
3. Include both adult and kids service times dynamically
4. This way, any new service time will automatically work

**Example fix**:
```python
# Get service times for the campus
campus_service_times = get_campus_service_times(campus)

# Build row_data dynamically
row_data = {
    'Timestamp': ...,
    'Date': ...,
    'Campus': campus,
    # ... other fixed fields
}

# Add service times dynamically
for service_time in campus_service_times:
    row_data[service_time] = safe_value(service_time)
    row_data[f'Kids {service_time}'] = safe_value(f'Kids {service_time}')
```

---

## 📋 **Summary**

| Component | Updates Automatically? | Notes |
|-----------|----------------------|-------|
| **Input Form** | ✅ Yes | Fetches from API, shows immediately |
| **Campus Management** | ✅ Yes | Saves to database |
| **Mobile App** | ✅ Yes | Fetches from public API |
| **Google Sheets** | ⚠️ Partial | Needs column to exist first |
| **Dashboard** | ⚠️ Partial | Depends on Google Sheets having the column |

---

## 🎯 **Action Items**

1. **Short-term**: When adding a new service time:
   - Update campus in Campus Management ✅
   - Manually add column to Google Sheets ⚠️
   - Input form will work ✅
   - Dashboard will work once column exists ✅

2. **Long-term**: Update backend to handle dynamic service times automatically

---

## 📝 **Example: Adding 9:30 AM to Salisbury**

1. **Update Campus** (Campus Management):
   - Edit Salisbury
   - Add "9:30 AM" to service times
   - Save ✅

2. **Input Form**:
   - Select Salisbury
   - See "9:30 AM" field appear ✅
   - Enter attendance ✅

3. **Google Sheets**:
   - Manually add "9:30 AM" column (if not exists) ⚠️
   - Manually add "Kids 9:30 AM" column (if not exists) ⚠️
   - Backend will save data to these columns ✅

4. **Dashboard**:
   - Will show 9:30 AM data once column exists ✅

5. **Mobile App**:
   - Will show 9:30 AM in campus info immediately ✅

