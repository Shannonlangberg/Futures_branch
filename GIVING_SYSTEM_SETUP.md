# Giving System Setup Guide

## Overview

The giving system has been enhanced with:
- **Transaction tracking** with source attribution (app, QR code, web, manual)
- **Analytics dashboard** for campus breakdowns, source analysis, and trends
- **Tap to Give (QR Code) system** for chair backs
- **QR scan analytics** to track taps per Sunday/service

## Database Migration

Run the migration to create the new tables:

```bash
cd backend
sqlite3 instance/futures_link.db < migrations/021_giving_transactions.sql
```

Or manually run the SQL in `backend/migrations/021_giving_transactions.sql`

## Features

### 1. Transaction Tracking

Every giving transaction is now tracked with:
- Person ID
- Amount and currency
- Giving type (tithe, offering, missions, event)
- Campus
- **Source** (app, qr_code, tap_to_give, web, manual)
- QR code ID (if from QR)
- Service date (if from QR)
- Stripe payment intent ID
- Status

### 2. Analytics Dashboard

Access at `/giving-analytics` in Pulse:

**Overview Tab:**
- Total giving amount
- Transaction count
- Average transaction
- Breakdowns by:
  - Campus (bar chart)
  - Type (doughnut chart)
  - Source (detailed list with icons)
  - Daily trend (line chart)

**Tap to Give Tab:**
- Total scans
- Active QR codes
- Scans per service date
- QR codes list with scan counts

**Transactions Tab:**
- Recent transactions table
- Filtered by campus, type, source, date range

### 3. QR Code Management

**Generate QR Codes:**
- Navigate to `/giving-analytics`
- Click "Tap to Give" tab
- Click "Generate QR Codes"
- Enter:
  - Campus
  - Zone (optional, e.g., "Main Auditorium")
  - Seat number (optional, e.g., "Row 5, Seat 12")
  - Count (how many QR codes to generate)

**QR Code URL Format:**
```
https://your-domain.com/api/giving/qr/{qr_code_id}
```

**QR Code Behavior:**
- When scanned, tracks the scan
- Opens giving page with campus pre-filled
- Sets service date to today
- Records source as "tap_to_give"

### 4. Mobile App Integration

When users give through the mobile app:
- Set `source: 'app'` in the payment intent request
- Transaction is automatically tracked
- Appears in analytics with mobile app icon

### 5. Web Integration

For web giving:
- Set `source: 'web'` in the payment intent request
- Tracked separately from app/QR

## API Endpoints

### Analytics
- `GET /api/giving/analytics` - Get giving analytics (requires finance.view permission)
  - Query params: `campus`, `start_date`, `end_date`, `giving_type`, `source`

### QR Scans Analytics
- `GET /api/giving/analytics/qr-scans` - Get QR scan analytics (requires finance.view permission)
  - Query params: `campus`, `start_date`, `end_date`

### QR Code Management
- `GET /api/giving/qr-codes` - List QR codes (requires finance.view permission)
  - Query params: `campus`, `is_active`
- `POST /api/giving/qr-codes` - Create QR codes (requires finance.create permission)
  - Body: `{ campus, zone?, seat_number?, count }`
- `DELETE /api/giving/qr-codes/<id>` - Deactivate QR code (requires finance.delete permission)

### QR Redirect
- `GET /api/giving/qr/<qr_code_id>` - Public endpoint for QR code redirect
  - Returns QR code info and redirect instructions
  - Tracks scan count

## Usage Workflow

### Setting Up QR Codes for Chairs

1. **Generate QR Codes:**
   - Go to `/giving-analytics` → "Tap to Give" tab
   - Click "Generate QR Codes"
   - For each row/section, create QR codes:
     - Example: Campus="Adelaide", Zone="Main Auditorium", Seat="Row 1-10" (generate 10)

2. **Print QR Codes:**
   - Each QR code has a unique URL
   - Use a QR code generator service (e.g., qr-code-generator.com) with the URL
   - Format: `https://your-domain.com/api/giving/qr/{qr_code_id}`
   - Print and attach to chair backs

3. **Track Usage:**
   - View scans per service in the "Tap to Give" tab
   - See which QR codes are most used
   - Track conversion (scans vs. completed gifts)

### Monitoring Giving

1. **Daily Check:**
   - Go to `/giving-analytics`
   - Check "Daily Trend" chart
   - Review recent transactions

2. **Weekly Review:**
   - Filter by date range (last 7 days)
   - Review campus breakdowns
   - Check QR scan analytics per service

3. **Monthly Analysis:**
   - Review by campus
   - Compare sources (app vs. QR vs. web)
   - Analyze giving types

## Permissions

The following permissions are required:
- `finance.view` - View analytics and QR codes
- `finance.create` - Generate QR codes
- `finance.delete` - Deactivate QR codes

## Frontend Route

Add a link to the Giving Analytics page in your navigation:

```jsx
<Link to="/giving-analytics">Giving Analytics</Link>
```

Or add it to your MainLayout navigation menu.

## Testing

1. **Test QR Code Generation:**
   - Generate a test QR code
   - Check it appears in the QR codes list

2. **Test QR Scan:**
   - Use the QR code URL in a browser or QR scanner
   - Verify scan count increases
   - Check it redirects properly

3. **Test Giving Flow:**
   - Make a test donation through app/web
   - Verify transaction appears in analytics
   - Check source is correctly recorded

4. **Test Analytics:**
   - Filter by campus, type, source
   - Verify charts update correctly
   - Check date range filtering works

## Next Steps

1. Run the database migration
2. Generate QR codes for your campuses
3. Print and attach QR codes to chairs
4. Test the QR code scanning flow
5. Monitor analytics regularly

## Notes

- QR codes track scans even if the user doesn't complete a donation
- The system prevents duplicate transactions (same Stripe payment intent)
- Transactions sync with Heartbeat engagement profiles
- Giving frequency is tracked for spiritual health scores (amounts are private)


