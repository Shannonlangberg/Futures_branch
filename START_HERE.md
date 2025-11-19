# 🚀 How to Start & Test the Futures Mobile App

## Option 1: Quick Start (Recommended)

### Step 1: Open Terminal on Your Mac
1. Press `Cmd + Space` (Command + Spacebar)
2. Type "Terminal"
3. Press Enter

### Step 2: Run This Command
In the Terminal, type:
```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1
./start-mobile.sh
```

### Step 3: Wait for the QR Code
You'll see:
- A QR code appear in the terminal
- Connection info like `exp://192.168.20.12:8081`

### Step 4: Scan with Your iPhone
1. Open the **Camera app** on your iPhone
2. Point it at the QR code in your terminal
3. Tap the notification that appears
4. It will open in Expo Go

---

## Option 2: Manual URL (No QR Code Needed)

1. Install **Expo Go** from the App Store
2. Open **Expo Go** on your iPhone
3. Tap **"Enter URL manually"**
4. Type: `exp://192.168.20.12:8081`
5. Tap **"Connect"**

---

## Important Notes

⚠️ **Make sure your iPhone and Mac are on the same Wi-Fi network!**

✅ Backend is already running on port 5000  
✅ The app will connect to: http://192.168.20.12:5000

---

## Troubleshooting

**Can't see QR code?**
- Scroll up in the terminal - it might be above
- Wait a few seconds for it to render
- Use Option 2 (manual URL) instead

**App won't connect?**
- Check both devices are on the same Wi-Fi
- Make sure Expo Go is installed on your iPhone
- Try restarting Expo Go on your phone

**Backend not working?**
- Check if it's running: Open http://192.168.20.12:5000/api/health in a browser
- If it says connection refused, the backend isn't running

---

## That's It! 🎉

Once connected, you'll see the Futures app load in Expo Go on your iPhone!
