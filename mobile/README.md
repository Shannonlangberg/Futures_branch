# Futures Mobile App

The official Futures Church mobile app - "One place for church life, discipleship, connection, and growth."

## Features

### ✅ Implemented

1. **Sunday Experience**
   - Service times & locations
   - Automatic beacon check-in
   - Manual check-in fallback
   - Campus information

2. **Prayer & Praise**
   - Submit prayer requests
   - Submit praise reports
   - Logs to Heartbeat care signals

3. **Connect Groups**
   - Browse all groups
   - Join groups
   - Attendance tracking (I'm coming / can't make it)

4. **Giving** (Stripe Integration)
   - Tithe, Offerings, Missions, Events
   - Secure Stripe payments
   - Giving history (pattern view, not amounts)
   - Links to Heartbeat for frequency tracking

5. **Events**
   - View all church events
   - RSVP (Going / Maybe / Can't Go)
   - Event details and locations

6. **Passport (Journey)**
   - Personal spiritual journey timeline
   - Pathway progress tracking
   - Milestones (Baptism, DNA, Serving, etc.)
   - Achievement badges

7. **Profile**
   - User profile management
   - Quick access to all features

### 🚧 Coming Soon

- **Pulse TV** (Video Hub) - Phase 2
- **Dream Team** (Serving) - Phase 2
- **Push Notifications** - Phase 2
- **AI Integration** - Phase 3

## Setup

### Prerequisites

- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- iOS Simulator (Mac) or Android Emulator

### Installation

```bash
cd mobile
npm install
```

### Configuration

1. Update `src/constants/config.js`:
   - Set `API_BASE_URL` to your backend URL
   - Set `STRIPE_PUBLISHABLE_KEY` to your Stripe publishable key
   - Update `BEACON_UUID` if using beacons

2. Update `app.json`:
   - Set your Expo project ID
   - Update bundle identifiers (iOS/Android)

### Running the App

```bash
# Start Expo
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## Building for Production

### iOS (App Store)

```bash
# Build iOS app
eas build --platform ios

# Submit to App Store
eas submit --platform ios
```

### Android (Google Play)

```bash
# Build Android app
eas build --platform android

# Submit to Google Play
eas submit --platform android
```

## API Endpoints

The app connects to the Pulse backend. Key endpoints:

- `/api/login` - Authentication
- `/api/campuses/public` - Get campuses
- `/api/service-times` - Get service times
- `/api/beacons/detect` - Beacon check-in
- `/api/prayer/requests` - Submit prayer request
- `/api/prayer/praise` - Submit praise report
- `/api/connect-groups` - Get/join groups
- `/api/connect-groups/attendance` - Submit attendance
- `/api/giving/create-intent` - Create payment intent
- `/api/giving/confirm-payment` - Confirm payment
- `/api/giving/history` - Get giving history
- `/api/events` - Get events
- `/api/events/rsvp` - RSVP to event
- `/api/pathways/my-pathway` - Get pathway progress
- `/api/people/profile` - Get/update profile

## Environment Variables

Required environment variables (backend):

- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret

## Design

The app matches the Pulse design system:
- Dark theme (slate-900 background)
- Purple/blue gradient accents
- Modern, ergonomic UI
- Smooth animations and transitions

## Support

For issues or questions, contact the development team.


