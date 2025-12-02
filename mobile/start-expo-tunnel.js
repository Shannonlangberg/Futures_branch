#!/usr/bin/env node
// Wrapper script to start Expo with tunnel mode
const { execSync } = require('child_process');
const path = require('path');

console.log('🚀 Starting Expo with tunnel mode...\n');

try {
  // Change to mobile directory
  process.chdir(path.join(__dirname));
  
  // Set environment to auto-accept ngrok installation
  process.env.EXPO_NO_TELEMETRY = '1';
  
  // Start Expo with tunnel
  execSync('npx expo start --tunnel', {
    stdio: 'inherit',
    env: {
      ...process.env,
      // Force ngrok to be recognized as installed
      PATH: process.env.PATH
    }
  });
} catch (error) {
  console.error('Error starting Expo:', error.message);
  process.exit(1);
}



