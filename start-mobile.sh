#!/bin/bash

# Start Expo with QR code visible
cd /Users/shannonlangberg/Documents/Futures_PulseV1.1/mobile

echo "═══════════════════════════════════════════════"
echo "   Starting Futures Mobile App..."
echo "═══════════════════════════════════════════════"
echo ""
echo "This will show the QR code you can scan with your iPhone"
echo ""
echo "Make sure:"
echo "  ✓ Expo Go is installed on your iPhone"
echo "  ✓ Your iPhone and Mac are on the same Wi-Fi"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "═══════════════════════════════════════════════"
echo ""

# Start Expo
npx expo start --clear

