import * as Location from 'expo-location';
import { BEACON_UUID } from '../constants/config';
import { ApiService } from './ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const BeaconService = {
  async requestPermissions() {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        return { success: false, error: 'Location permission denied' };
      }

      const { status: backgroundStatus } = await Location.requestBackgroundPermissionsAsync();
      if (backgroundStatus !== 'granted') {
        console.warn('Background location permission not granted');
      }

      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  async startBeaconScanning(onBeaconDetected) {
    try {
      // Note: Expo doesn't have native beacon support
      // For production, you'll need to use react-native-beacons-manager or similar
      // This is a placeholder implementation

      // For now, we'll use a polling mechanism to check for beacons
      // In production, you'd use actual BLE beacon scanning
      
      const scanInterval = setInterval(async () => {
        // Simulate beacon detection (replace with actual beacon scanning)
        // This would typically use react-native-beacons-manager or similar library
        
        // Example: Check if user is near a known beacon location
        const location = await Location.getCurrentPositionAsync({});
        
        // In production, you'd compare location with known beacon zones
        // For now, we'll skip actual beacon scanning
      }, 10000); // Check every 10 seconds

      return { success: true, scanInterval };
    } catch (error) {
      console.error('Beacon scanning error:', error);
      return { success: false, error: error.message };
    }
  },

  async stopBeaconScanning(scanInterval) {
    if (scanInterval) {
      clearInterval(scanInterval);
    }
    return { success: true };
  },

  async reportBeaconDetection(beaconData) {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (!userData) {
        return { success: false, error: 'Not authenticated' };
      }

      const user = JSON.parse(userData);
      const result = await ApiService.detectBeacon(user.email, beaconData);

      return { success: true, data: result };
    } catch (error) {
      console.error('Beacon detection error:', error);
      return { success: false, error: error.message };
    }
  },

  async manualCheckIn(campus, zones = []) {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (!userData) {
        return { success: false, error: 'Not authenticated' };
      }

      const user = JSON.parse(userData);
      
      // Simulate beacon detection for manual check-in
      const beaconData = {
        beacon_uuid: BEACON_UUID,
        beacon_major: 0,
        beacon_minor: 0,
        timestamp: new Date().toISOString(),
        manual: true,
      };

      const result = await ApiService.detectBeacon(user.email, beaconData);

      return { success: true, data: result };
    } catch (error) {
      console.error('Manual check-in error:', error);
      return { success: false, error: error.message };
    }
  },
};


