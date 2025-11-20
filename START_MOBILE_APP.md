# How to Test the Futures Mobile App

## ✅ Everything is Running!

**Backend:** Running on port 5000 (http://192.168.20.12:5000)  
**Expo:** Running on port 8081  
**Your Mac IP:** 192.168.20.12

---

## Quick Start - Test on Your iPhone

### Step 1: Install Expo Go
1. Open the **App Store** on your iPhone
2. Search for **"Expo Go"**
3. Install it (it's free)

### Step 2: Connect to the App
**Option A: Scan QR Code (Easiest)**
1. Open the **Camera app** on your iPhone
2. Point it at the QR code in your terminal (where Expo is running)
3. Tap the notification that appears
4. It will open in Expo Go

**Option B: Enter URL Manually**
1. Open **Expo Go** on your iPhone
2. Tap **"Enter URL manually"**
3. Type: `exp://192.168.20.12:8081`
4. Tap **"Connect"**

### Step 3: Make Sure You're on the Same Wi-Fi
- Your iPhone and Mac **must** be on the same Wi-Fi network

---

## If You Don't See the QR Code

The QR code should appear in the terminal where Expo is running. If you don't see it:

1. **Check your terminal** - Look for the terminal window where you started Expo
2. **Scroll up** - The QR code might be above the current view
3. **Wait a few seconds** - Sometimes it takes a moment to render
4. **Use the manual URL** - Option B above works without a QR code

---

## To See Expo Output (QR Code)

If you want to see the QR code in a visible terminal, open a **new terminal window** and run:

```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/mobile
npx expo start --clear
```

This will show the QR code in that terminal window.

---

## Troubleshooting

**App won't connect?**
- Make sure both devices are on the same Wi-Fi network
- Try the manual URL instead: `exp://192.168.20.12:8081`
- Restart Expo Go on your phone

**Backend connection errors?**
- Backend is running on: http://192.168.20.12:5000
- Check if backend is running: Open http://192.168.20.12:5000/api/health in a browser

**Can't see the QR code?**
- Use the manual URL entry in Expo Go
- Check that port 8081 isn't blocked by a firewall

---

## Current Status

✅ Backend: Running on port 5000  
✅ Expo: Running on port 8081  
✅ Config: IP set to 192.168.20.12

**Ready to test!** 🚀


