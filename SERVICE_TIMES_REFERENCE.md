# Service Times Reference

## Current Configuration (from campuses.json)

| Campus | Service Times |
|--------|---------------|
| **Paradise** | 9:00 AM, 11:00 AM, 5:30 PM |
| **South** | 9:00 AM, 11:00 AM |
| **Salisbury** | 9:00 AM, 11:00 AM |
| **Adelaide City** | 9:00 AM, 11:00 AM, 5:00 PM |
| **Mount Barker** | 10:00 AM |
| **Copper Coast** | 10:00 AM |
| **Clare Valley** | 10:00 AM |
| **Victor Harbor** | 10:00 AM |

## How It Works

1. **Backend**: Reads service times from `/backend/campuses.json`
2. **Dashboard**: Shows service breakdown based on these times
3. **Stats Input**: Uses these times for data entry

## To Update Service Times

Edit `/backend/campuses.json` and update the `service_times` array for any campus:

```json
{
  "campuses": {
    "paradise": {
      "service_times": ["9:00 AM", "11:00 AM", "5:30 PM"]
    }
  }
}
```

Then restart the backend:
```bash
pkill -f "python app.py"
cd backend && python app.py
```

## Google Sheets Columns

The dashboard expects these columns in your Google Sheet:
- `9:00 AM` - Adult attendance at 9am service
- `10:00 AM` - Adult attendance at 10am service
- `11:00 AM` - Adult attendance at 11am service
- `5:00 PM` - Adult attendance at 5pm service
- `5:30 PM` - Adult attendance at 5:30pm service

And for kids:
- `Kids 9:00 AM`
- `Kids 10:00 AM`
- `Kids 11:00 AM`
- `Kids 5:00 PM`
- `Kids 5:30 PM`

The dashboard will automatically show only the services that each campus actually has.

