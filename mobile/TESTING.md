# Testing the Futures Mobile App

## Quick Start

1. **Install dependencies** (if not done):
   ```bash
   cd mobile
   npm install
   ```

2. **Start the Expo development server**:
   ```bash
   npm start
   ```
   or
   ```bash
   npx expo start
   ```

3. **Test the app**:
   - **iOS Simulator**: Press `i` in the terminal, or scan the QR code with Camera app
   - **Android Emulator**: Press `a` in the terminal, or scan the QR code with Expo Go app
   - **Physical Device**: 
     - Install **Expo Go** app from App Store (iOS) or Google Play (Android)
     - Scan the QR code that appears in the terminal
     - Make sure your phone and computer are on the same WiFi network

## Important: Backend Connection

Before testing, make sure your backend is running:

1. **Start your Pulse backend** (in a separate terminal):
   ```bash
   cd /Users/shannonlangberg/Documents/Futures_PulseV1.1
   python backend/app.py
   # or however you normally start your backend
   ```

2. **Update API URL** (if testing on physical device):
   - Get your local IP address:
     ```bash
     ipconfig getifaddr en0  # Mac WiFi
     # or
     ifconfig | grep "inet " | grep -v 127.0.0.1
     ```
   - Update `mobile/src/constants/config.js`:
     ```javascript
     export const API_BASE_URL = 'http://YOUR_IP_ADDRESS:5000';
     ```
   - Example: `http://192.168.1.100:5000`

## Testing Features

### 1. Login Screen
- The app will show the login screen first
- Use email/password that exists in your backend database

### 2. Bottom Navigation
- Test all 5 tabs: Home, Sunday, Give, Groups, Journey
- Verify 2-click rule: everything should be accessible within 2 clicks

### 3. Home Screen
- Quick action cards should navigate to different screens
- Upcoming events section
- Journey progress link

### 4. Sunday Screen
- Service times display
- Manual check-in button
- Campus information
- Prayer & Praise quick access

### 5. Give Screen
- Giving type selection
- Amount input
- Quick amount buttons
- **Note**: Stripe will need to be configured with real keys for payment testing

### 6. Groups Screen
- Browse groups tab
- My groups tab
- Join group functionality
- Attendance buttons

### 7. Journey Screen
- Pathway progress
- Milestones display
- Achievements
- Profile access link

### 8. Events Screen
- Events list
- RSVP buttons (Going, Maybe, Can't Go)

### 9. Prayer Screen
- Prayer request submission
- Praise report submission

### 10. Profile Screen
- User info display
- Quick access links
- Sign out button

## Troubleshooting

### "Network request failed"
- Make sure backend is running
- Update `API_BASE_URL` in `config.js` if using physical device
- Check firewall settings

### "Module not found" errors
- Delete `node_modules` and reinstall:
  ```bash
  rm -rf node_modules
  npm install
  ```

### Expo Go not connecting
- Make sure phone and computer are on same WiFi
- Try restarting Expo server: `npx expo start --clear`
- Check that your router allows device-to-device communication

### Build errors
- Clear Expo cache: `npx expo start --clear`
- Reset Metro bundler: Press `r` in terminal, or stop and restart

## Next Steps

Once testing is successful:
1. Configure Stripe with real publishable key
2. Set up push notifications (Expo project ID needed)
3. Configure beacons (when ready)
4. Build for App Store / Google Play using EAS Build

## Development Tips

- **Hot Reload**: Changes automatically refresh in the app
- **Debug Menu**: Shake device or press `Cmd+D` (iOS) / `Cmd+M` (Android)
- **Reload**: Press `r` in terminal or shake device and tap "Reload"
- **Dev Tools**: Press `j` in terminal to open React DevTools


