# Expo Go Setup - Working Solutions

## ✅ Current Status
- Expo is running on port 8081 (LAN mode)
- Backend is running on port 5002
- Mobile app configured to use: http://192.168.20.12:5002

## 🚀 Option 1: Use Mac Hotspot (RECOMMENDED - Most Reliable)

1. **Enable Internet Sharing on Mac:**
   - System Settings → General → Sharing → Internet Sharing
   - Turn it ON
   - Share from: WiFi
   - Create a WiFi network name and password

2. **Connect your phone to Mac's WiFi hotspot**

3. **Get the hotspot IP:**
   ```bash
   ipconfig getifaddr bridge100
   ```
   (This will give you an IP like 192.168.2.1)

4. **Expo is already running!** Just use in Expo Go:
   ```
   exp://[HOTSPOT_IP]:8081
   ```
   Example: `exp://192.168.2.1:8081`

---

## 🌐 Option 2: Tunnel Mode (Works from Anywhere)

**IMPORTANT:** This requires running in an interactive terminal (where you can type 'y')

1. Stop current Expo (if running):
   ```bash
   pkill -f "expo start"
   ```

2. Run tunnel mode:
   ```bash
   cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/mobile
   npx expo start --tunnel
   ```

3. When it asks to install ngrok, type: `y` and press Enter

4. Wait 30-60 seconds for tunnel URL

5. Look for URL like: `exp://xxx-xxx.tunnel.exp.direct:80`

6. Copy and paste that URL into Expo Go

---

## 📱 Quick Start Commands

**Start Expo (LAN mode):**
```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/mobile
npx expo start --host lan
```

**Start Expo (Tunnel mode):**
```bash
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/mobile
npx expo start --tunnel
```

**Check if Expo is running:**
```bash
curl http://localhost:8081/status
```

**Get your Mac's IP:**
```bash
ipconfig getifaddr en0
```

---

## ❓ Troubleshooting

**If phone can't connect:**
- Make sure both devices are on the same WiFi network
- Or use Mac hotspot (Option 1)
- Or use tunnel mode (Option 2)

**If Expo won't start:**
```bash
pkill -9 -f expo
pkill -9 -f metro
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/mobile
npx expo start --host lan --clear
```

