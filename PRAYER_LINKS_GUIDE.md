# Prayer & Praise Link System Guide

## Overview

The Prayer & Praise Link System allows you to create shareable links, QR codes, and NFC tap points for easy prayer request and praise report submissions. This is perfect for:

- **Physical tap points** around campus (NFC tags, QR codes)
- **Social media** links (Instagram, Facebook, etc.)
- **Website** integration
- **Event-specific** prayer walls
- **Department-filtered** submissions (Kids, Youth, Adults, etc.)

## Features

✅ **No login required** - Anyone can submit via public links
✅ **Campus filtering** - Pre-select campus for submissions
✅ **Department filtering** - Route to specific departments
✅ **Tracking** - Monitor scan count and submission count
✅ **Flexible types** - Prayer only, Praise only, or Both
✅ **Auto-routing** - Submissions route to campus pastors via Heartbeat
✅ **Multiple formats** - QR codes, NFC tags, or simple web links

## How It Works

### 1. Create a Prayer Link

**Via API (requires admin/pastor login):**

```bash
POST /api/prayer/links
Authorization: Bearer <token>

{
  "link_type": "both",           // 'prayer', 'praise', or 'both'
  "campus": "paradise",          // Optional: pre-filter to campus
  "department": "Youth",         // Optional: pre-filter to department
  "location": "Main Entrance",   // Description of physical location
  "description": "Youth Prayer Wall",
  "code_type": "qr",            // 'qr', 'nfc', or 'link'
  "count": 1                     // Generate multiple links at once
}
```

**Response:**

```json
{
  "success": true,
  "message": "Created 1 prayer link(s)",
  "links": [
    {
      "id": 1,
      "link_id": "prayer_abc123xyz",
      "link_type": "both",
      "campus": "paradise",
      "department": "Youth",
      "location": "Main Entrance",
      "code_type": "qr",
      "is_active": true,
      "scan_count": 0,
      "submission_count": 0,
      "url": "/prayer/link/prayer_abc123xyz",
      "full_url": "https://pulse.futuresbranch.org/prayer/link/prayer_abc123xyz"
    }
  ]
}
```

### 2. Share the Link

**Web URL:**
```
https://pulse.futuresbranch.org/prayer/link/prayer_abc123xyz
```

**QR Code:**
Generate a QR code pointing to the above URL using any QR code generator.

**NFC Tag:**
Program an NFC tag with the URL.

### 3. Public Submission

When someone scans/clicks the link:

1. **Beautiful submission page** opens
2. User fills out:
   - Name
   - Email
   - Phone (optional)
   - Campus (pre-filled if link has campus filter)
   - Prayer/Praise text
3. **Automatic routing** - submission creates a CareCase in Heartbeat
4. **Campus pastor notified** - routed to appropriate campus pastor

## API Endpoints

### Management (Requires Authentication)

#### Get All Links
```bash
GET /api/prayer/links?campus=paradise&is_active=true
Authorization: Bearer <token>
```

#### Create Link
```bash
POST /api/prayer/links
Authorization: Bearer <token>
```

#### Update Link
```bash
PUT /api/prayer/links/<link_id>
Authorization: Bearer <token>

{
  "location": "Updated location",
  "is_active": false
}
```

#### Delete Link (Deactivate)
```bash
DELETE /api/prayer/links/<link_id>
Authorization: Bearer <token>
```

### Public Endpoints (No Auth Required)

#### Get Link Info
```bash
GET /api/prayer/link/<link_id>
```

Returns link configuration (type, campus, department, location).

#### Submit via Link
```bash
POST /api/prayer/link/<link_id>/submit

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "0400000000",  // optional
  "type": "prayer",       // 'prayer' or 'praise'
  "text": "Please pray for...",
  "campus": "paradise",   // optional if link has campus
  "department": "Youth"   // optional if link has department
}
```

## Use Cases

### 1. Campus Prayer Tap Points

Create NFC tags around campus:

```bash
POST /api/prayer/links
{
  "link_type": "both",
  "campus": "paradise",
  "location": "Main Entrance - Left Wall",
  "description": "Main campus prayer point",
  "code_type": "nfc",
  "count": 10  // Create 10 tags at once
}
```

Stick NFC tags on walls with signage: "Tap your phone here to submit a prayer request"

### 2. Social Media Link

Create a general link for Instagram bio:

```bash
POST /api/prayer/links
{
  "link_type": "both",
  "location": "Instagram Bio",
  "description": "Social media prayer link",
  "code_type": "link"
}
```

Add to Instagram: "Share your prayer requests or praise reports: [link]"

### 3. Youth-Specific Prayer Wall

Create a link filtered to youth department:

```bash
POST /api/prayer/links
{
  "link_type": "both",
  "campus": "paradise",
  "department": "Youth",
  "location": "Youth Room",
  "description": "Youth prayer wall",
  "code_type": "qr"
}
```

### 4. Event-Specific

Create links for specific events:

```bash
POST /api/prayer/links
{
  "link_type": "prayer",
  "location": "Easter Service 2024",
  "description": "Easter prayer requests",
  "code_type": "link"
}
```

Deactivate after the event:

```bash
PUT /api/prayer/links/<id>
{ "is_active": false }
```

## Mobile App Integration

The mobile app already has prayer/praise submission built in. To add link support:

```javascript
// When scanning a QR/NFC tag:
const linkId = scannedCode; // e.g., "prayer_abc123xyz"

// Get link info
const linkInfo = await ApiService.getPrayerLinkInfo(linkId);

// Submit via link
const result = await ApiService.submitViaLink(linkId, {
  name: user.name,
  email: user.email,
  type: 'prayer',
  text: prayerText
});
```

## Heartbeat Integration

All submissions are automatically:

1. **Logged as CareCases** in Heartbeat
2. **Routed to campus pastors** based on submitter's campus
3. **Tagged with link context** - includes location and link description
4. **Tracked** - scan count and submission count are monitored

## Analytics

Track link performance:

```bash
GET /api/prayer/links
```

Response includes:
- `scan_count` - How many times link was accessed
- `submission_count` - How many submissions were completed
- `last_scan_at` - Last time link was accessed

## Security & Privacy

- ✅ **Public submission** - No login required
- ✅ **Email verification** - Validates email format
- ✅ **Spam prevention** - Rate limiting on submission endpoint
- ✅ **Campus pastor routing** - Auto-routes to appropriate pastor
- ✅ **Admin control** - Links can be deactivated anytime
- ✅ **No sensitive data in URLs** - Link IDs are random identifiers

## Frontend Integration

The public submission page is hosted at:
```
/static/prayer-submit.html
```

It automatically:
- Extracts `link_id` from URL
- Loads link configuration
- Pre-fills campus if specified
- Adapts UI based on link type
- Handles submission to API

## Database Schema

```sql
CREATE TABLE prayer_links (
    id INTEGER PRIMARY KEY,
    link_id TEXT UNIQUE NOT NULL,
    link_type TEXT NOT NULL,      -- 'prayer', 'praise', 'both'
    campus TEXT,
    department TEXT,
    location TEXT,
    description TEXT,
    code_type TEXT,               -- 'qr', 'nfc', 'link'
    is_active INTEGER,
    scan_count INTEGER,
    submission_count INTEGER,
    last_scan_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    created_by TEXT
);
```

## Best Practices

1. **Use descriptive locations** - Makes tracking easier
2. **Set campus filters** - Ensures proper routing
3. **Monitor analytics** - Check scan vs submission rates
4. **Deactivate old links** - Keep link list clean
5. **Create batches** - Use `count` parameter for multiple similar links
6. **Test before deploying** - Scan QR codes yourself first
7. **Add signage** - Clear instructions near physical tap points

## Troubleshooting

**Q: Link not working?**
- Check if link is active: `GET /api/prayer/links`
- Verify link_id in URL is correct
- Check server logs for errors

**Q: Submissions not routing to campus pastor?**
- Ensure person has campus assigned
- Verify campus pastor exists in users table
- Check CareCase was created in Heartbeat

**Q: QR code not scanning?**
- Ensure URL is correct format
- Try different QR code generator
- Test with multiple phones

**Q: NFC tag not working?**
- Verify tag is formatted as URL/URI
- Check phone has NFC enabled
- Try different tag type (NTAG213/215/216)

## Future Enhancements

Potential additions:
- [ ] Link expiration dates
- [ ] Custom redirect after submission
- [ ] Anonymous submissions (no email required)
- [ ] Multi-language support
- [ ] Custom branding per link
- [ ] Email notifications to submitter
- [ ] SMS integration
- [ ] Prayer team assignment

## Support

For questions or issues with the Prayer Link system:
- Check logs: `backend/app.log`
- Review CareCases in Heartbeat
- Contact system administrator

