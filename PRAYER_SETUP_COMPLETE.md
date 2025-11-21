# Prayer & Praise System - Setup Complete! ✅

## What's Been Built

I've created a complete **Prayer & Praise Link System** similar to your Giving system, allowing people to submit prayer requests and praise reports through:

- 🔗 **Shareable Links** (social media, websites)
- 📱 **QR Codes** (print and place around campus)
- 📡 **NFC Tap Points** (tap-to-pray stations)
- 📲 **Mobile App** (already working!)

## Key Features

### ✅ Link Creation & Management
- Create prayer/praise links filtered by campus and department
- Generate multiple links at once (e.g., 10 NFC tags for different locations)
- Track scan counts and submission counts
- Activate/deactivate links as needed

### ✅ Public Submissions (No Login Required)
- Beautiful, mobile-friendly submission page
- Pre-fill campus from link (tap at Paradise campus = auto-selects Paradise)
- Support for both prayer requests AND praise reports
- Creates person record if they don't exist

### ✅ Automatic Routing via Heartbeat
- All submissions create CareCases in Heartbeat
- Auto-routes to campus pastor based on person's campus
- Includes link context (location, description)
- Tagged with source information

### ✅ Mobile App Ready
- Existing PrayerScreen already works for logged-in users
- New ApiService methods added for link-based submissions
- Can scan QR/NFC and submit via links

## Files Created/Modified

### Backend Files

1. **`backend/models.py`** - Added `PrayerLink` model
   - Stores link configuration, campus filters, tracking data

2. **`backend/prayer_api.py`** - Enhanced with new endpoints
   - `/api/prayer/links` - CRUD operations (requires auth)
   - `/api/prayer/link/<id>` - Public link info
   - `/api/prayer/link/<id>/submit` - Public submission

3. **`backend/migrations/024_create_prayer_links.sql`** - Database migration
   - Creates `prayer_links` table with indexes
   - ✅ Already run successfully!

4. **`backend/app.py`** - Added route to serve submission page
   - `/prayer/link/<link_id>` serves the public HTML page

5. **`backend/static/prayer-submit.html`** - Beautiful public submission page
   - Mobile-friendly design
   - Auto-loads link configuration
   - Switches between prayer/praise tabs
   - Validates and submits to API

### Mobile App Files

6. **`mobile/src/services/ApiService.js`** - Added prayer link methods
   - `getPrayerLinkInfo(linkId)`
   - `submitViaLink(linkId, data)`

### Documentation

7. **`PRAYER_LINKS_GUIDE.md`** - Complete usage guide
8. **`PRAYER_SETUP_COMPLETE.md`** - This file!

## How to Use

### 1. Create Your First Prayer Link

Using the API (requires admin login):

```bash
curl -X POST https://pulse.futuresbranch.org/api/prayer/links \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "link_type": "both",
    "campus": "paradise",
    "location": "Main Entrance Prayer Wall",
    "description": "Paradise Campus Main Prayer Point",
    "code_type": "qr"
  }'
```

Response will include:
```json
{
  "links": [{
    "link_id": "prayer_abc123xyz",
    "url": "/prayer/link/prayer_abc123xyz",
    "full_url": "https://pulse.futuresbranch.org/prayer/link/prayer_abc123xyz"
  }]
}
```

### 2. Generate QR Code

Take the `full_url` and create a QR code:
- Go to https://qr.io or https://www.qr-code-generator.com
- Paste: `https://pulse.futuresbranch.org/prayer/link/prayer_abc123xyz`
- Download and print

### 3. Create NFC Tags

For tap-to-pray points:
- Buy NFC tags (NTAG213 or NTAG216)
- Use NFC Tools app to program URL
- Stick near entrance, youth room, etc.
- Add signage: "Tap here to share prayer requests"

### 4. Share on Social Media

- Instagram bio: "Submit prayer requests: [link]"
- Facebook: Pin a post with the link
- Website: Add a "Prayer Request" button

## Test Link Created

I've created a test link for you:
```
Link ID: prayer_test123abc
URL: https://pulse.futuresbranch.org/prayer/link/prayer_test123abc
Campus: Paradise
Department: Youth
Location: Test Location - Main Entrance
```

You can test it by:
1. Going to the URL in a browser
2. Filling out the form
3. Checking Heartbeat for the CareCase

## Use Cases You Mentioned

### ✅ Prayer Tap Points Around Campus

Create 10 NFC tags for different locations:

```bash
POST /api/prayer/links
{
  "link_type": "both",
  "campus": "paradise",
  "location": "Main Auditorium",
  "code_type": "nfc",
  "count": 10
}
```

Stick tags on walls with signage.

### ✅ Link on Socials

Create a general link:

```bash
POST /api/prayer/links
{
  "link_type": "both",
  "location": "Instagram",
  "code_type": "link"
}
```

Add to Instagram bio/Facebook pinned post.

### ✅ App Integration

The mobile app **already works**! Users can:
- Open Prayer & Praise screen
- Submit prayer requests
- Submit praise reports

These go to the same backend and route to campus pastors.

### ✅ Backend Filtering

View all links:
```bash
GET /api/prayer/links?campus=paradise
```

Filter by department:
```bash
GET /api/prayer/links?department=Youth
```

Track analytics:
- `scan_count` - How many times link accessed
- `submission_count` - How many submissions completed

### ✅ Similar to Giving Links

Just like giving QR codes:
- Create campus-filtered links
- Generate multiple at once
- Track usage analytics
- Activate/deactivate as needed
- Public submission (no auth required)

## Backend Integration

All submissions:
1. Create a `Person` if they don't exist (or find existing by email)
2. Create a `CareCase` in Heartbeat with type `prayer_request` or `praise_report`
3. Route to campus pastor based on person's campus
4. Include link context in CareCase details
5. Update link `submission_count`

Campus pastors see these in their Heartbeat dashboard!

## Next Steps

### Immediate Actions

1. **Create real links** for your campuses
   ```bash
   # Paradise Main Entrance
   # South Youth Room
   # Adelaide City Foyer
   # etc.
   ```

2. **Generate QR codes** and print them

3. **Order NFC tags** (Amazon, eBay - search "NTAG213")

4. **Add to social media** (Instagram, Facebook)

5. **Train staff** on how the system works

### Optional Enhancements

- [ ] Add to website navigation
- [ ] Create department-specific links (Kids, Youth, Adults)
- [ ] Event-specific prayer walls
- [ ] Email notifications to submitters
- [ ] SMS integration
- [ ] Custom branding per link
- [ ] Link expiration dates

## API Reference

### Management Endpoints (Requires Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prayer/links` | List all links |
| POST | `/api/prayer/links` | Create new link(s) |
| PUT | `/api/prayer/links/<id>` | Update link |
| DELETE | `/api/prayer/links/<id>` | Deactivate link |

### Public Endpoints (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prayer/link/<link_id>` | Get link info |
| POST | `/api/prayer/link/<link_id>/submit` | Submit prayer/praise |
| GET | `/prayer/link/<link_id>` | Web submission page |

### Mobile App Methods

```javascript
// Get link info
const info = await ApiService.getPrayerLinkInfo(linkId);

// Submit via link
const result = await ApiService.submitViaLink(linkId, {
  name: "John Doe",
  email: "john@example.com",
  type: "prayer",
  text: "Please pray for..."
});
```

## Database

Migration **already run** ✅

Table created:
```sql
prayer_links (
  id, link_id, link_type, campus, department,
  location, description, code_type, is_active,
  scan_count, submission_count, last_scan_at,
  created_at, updated_at, created_by
)
```

Current status:
- ✅ 1 test link created
- ✅ Indexes created
- ✅ Ready for production use

## Troubleshooting

### Link not working?
```bash
# Check if link exists
sqlite3 backend/futures_link.db "SELECT * FROM prayer_links WHERE link_id='your_link_id';"

# Check if active
sqlite3 backend/futures_link.db "SELECT is_active FROM prayer_links WHERE link_id='your_link_id';"
```

### Submission not creating CareCase?
- Check person exists: `SELECT * FROM persons WHERE email='test@example.com';`
- Check CareCase created: `SELECT * FROM care_cases WHERE person_id='person_id';`
- Check campus pastor exists: `SELECT * FROM users WHERE role='campus_pastor' AND campus='paradise';`

### Mobile app not working?
- Verify PrayerScreen exists (it does!)
- Check ApiService methods imported
- Test with existing prayer submission first

## Support

For detailed documentation, see:
- **`PRAYER_LINKS_GUIDE.md`** - Complete usage guide

For questions:
- Check logs: `backend/app.log`
- Review database: `sqlite3 backend/futures_link.db`
- Test with curl: See examples above

## Summary

✅ **Prayer & Praise link system is fully built and ready!**

You can now:
- Create prayer tap points (QR/NFC)
- Share links on social media
- Let anyone submit prayer/praise (no login)
- Automatically route to campus pastors
- Track analytics (scans, submissions)
- Manage links (activate/deactivate)

The mobile app **already works** for logged-in users, and the new link system makes it accessible to **everyone** - perfect for visitors, guests, and tap points around campus!

Let me know if you want me to:
1. Create specific links for each campus
2. Add more features (email notifications, SMS, etc.)
3. Customize the submission page design
4. Create a video tutorial for staff training
5. Add to the admin dashboard UI

**The foundation is complete and ready to use!** 🎉

