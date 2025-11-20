import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { ApiService } from './ApiService';

export const NotificationService = {
  async registerForPushNotifications() {
    if (!Device.isDevice) {
      console.warn('Must use physical device for Push Notifications');
      return null;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.warn('Failed to get push token for push notification!');
      return null;
    }

    // Get projectId from Expo constants (set automatically by Expo)
    const projectId = Constants.expoConfig?.extra?.eas?.projectId || Constants.easConfig?.projectId;
    
    const token = await Notifications.getExpoPushTokenAsync(
      projectId ? { projectId } : undefined
    );

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#6366f1',
      });
    }

    return token.data;
  },

  async getPushToken() {
    try {
      // Get projectId from Expo constants (set automatically by Expo)
      const projectId = Constants.expoConfig?.extra?.eas?.projectId || Constants.easConfig?.projectId;
      
      // Only include projectId if it's set (not required in development)
      const token = await Notifications.getExpoPushTokenAsync(
        projectId ? { projectId } : undefined
      );
      return token.data;
    } catch (error) {
      console.error('Error getting push token:', error);
      // In development without a projectId, this is expected - just return null
      return null;
    }
  },

  async savePushToken(email, pushToken) {
    try {
      await ApiService.savePushToken(email, pushToken);
      return { success: true };
    } catch (error) {
      console.error('Error saving push token:', error);
      return { success: false, error: error.message };
    }
  },

  // Setup notification handlers
  setupNotificationHandlers() {
    // Foreground notifications
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });

    // Notification received listener
    Notifications.addNotificationReceivedListener((notification) => {
      console.log('Notification received:', notification);
    });

    // Notification response listener (when user taps notification)
    Notifications.addNotificationResponseReceivedListener((response) => {
      console.log('Notification tapped:', response);
      // Handle navigation based on notification data
    });
  },
};


