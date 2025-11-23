import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import { NotificationService } from '../services/NotificationService';

export default function ProfileScreen() {
  const navigation = useNavigation();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [checkingNotifications, setCheckingNotifications] = useState(false);
  const [pushToken, setPushToken] = useState(null);
  const [showTokenModal, setShowTokenModal] = useState(false);

  useEffect(() => {
    loadProfile();
    checkNotificationStatus();
  }, []);

  const checkNotificationStatus = async () => {
    try {
      const { status } = await Notifications.getPermissionsAsync();
      setNotificationsEnabled(status === 'granted');
      
      // If enabled, also get and display the token
      if (status === 'granted') {
        try {
          const projectId = Constants?.expoConfig?.extra?.eas?.projectId || Constants?.easConfig?.projectId;
          if (projectId && projectId !== 'your-project-id') {
            const token = await Notifications.getExpoPushTokenAsync(
              projectId ? { projectId } : undefined
            );
            setPushToken(token.data);
            console.log('📱 Push Token:', token.data); // Log for easy copying
          }
        } catch (error) {
          console.log('Could not get push token:', error.message);
        }
      }
    } catch (error) {
      console.error('Error checking notification status:', error);
    }
  };

  const handleNotificationToggle = async (value) => {
    if (!Device.isDevice) {
      Alert.alert('Notifications', 'Push notifications are only available on physical devices.');
      return;
    }

    setCheckingNotifications(true);
    try {
      if (value) {
        // Enable notifications
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;

        if (existingStatus !== 'granted') {
          const { status } = await Notifications.requestPermissionsAsync();
          finalStatus = status;
        }

        if (finalStatus === 'granted') {
          // Get push token and save it
          const projectId = Constants?.expoConfig?.extra?.eas?.projectId || Constants?.easConfig?.projectId;
          if (!projectId || projectId === 'your-project-id') {
            Alert.alert(
              'Notifications',
              'Push notifications are not configured for this app. Please contact support.'
            );
            setNotificationsEnabled(false);
            return;
          }

          const token = await Notifications.getExpoPushTokenAsync(
            projectId ? { projectId } : undefined
          );

          if (token && user) {
            const platform = Platform.OS;
            const appVersion = Constants?.expoConfig?.version || '1.0.0';
            await NotificationService.savePushToken(user.email, token.data, platform, null, appVersion);
            setNotificationsEnabled(true);
            Alert.alert('Success', 'Push notifications enabled! You will now receive notifications from Futures Church.');
          }
        } else {
          Alert.alert(
            'Permission Denied',
            'Push notifications require permission. Please enable them in your device settings.'
          );
          setNotificationsEnabled(false);
        }
      } else {
        // Disable notifications - just update local state
        setNotificationsEnabled(false);
        Alert.alert('Notifications Disabled', 'You will no longer receive push notifications.');
      }
    } catch (error) {
      console.error('Error toggling notifications:', error);
      Alert.alert('Error', 'Failed to update notification settings. Please try again.');
      setNotificationsEnabled(!value); // Revert toggle
    } finally {
      setCheckingNotifications(false);
    }
  };

  const loadProfile = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        const profileData = await ApiService.getPersonProfile(userObj.email);
        if (profileData.profile) {
          setProfile(profileData.profile);
        }
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('authToken');
            await AsyncStorage.removeItem('userData');
            // Navigation handled in App.js
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
        </View>

        {/* Profile Info */}
        <View style={styles.profileCard}>
          <View style={styles.profileHeader}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </Text>
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.profileName}>
                {profile?.full_name || user?.name || 'User'}
              </Text>
              <Text style={styles.profileEmail}>{user?.email || ''}</Text>
              {profile?.campus && (
                <Text style={styles.profileCampus}>📍 {profile.campus}</Text>
              )}
            </View>
          </View>
        </View>

        {/* Edit Profile Button */}
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => navigation.navigate('EditProfile')}
        >
          <LinearGradient
            colors={[Colors.primary, Colors.accent]}
            style={styles.editButtonGradient}
          >
            <Text style={styles.editButtonText}>✏️ Edit Profile</Text>
          </LinearGradient>
        </TouchableOpacity>

        {/* Settings */}
        <View style={styles.menu}>
          <Text style={styles.sectionTitle}>Settings</Text>
          
          {/* Push Notifications Toggle */}
          <View style={styles.menuItem}>
            <Text style={styles.menuIcon}>🔔</Text>
            <View style={styles.menuTextContainer}>
              <Text style={styles.menuText}>Push Notifications</Text>
              <Text style={styles.menuSubtext}>
                {notificationsEnabled ? (pushToken ? 'Enabled • Tap to view token' : 'Enabled') : 'Disabled'}
              </Text>
            </View>
            {checkingNotifications ? (
              <ActivityIndicator size="small" color={Colors.primary} />
            ) : (
              <Switch
                value={notificationsEnabled}
                onValueChange={handleNotificationToggle}
                trackColor={{ false: Colors.border, true: Colors.primary }}
                thumbColor={notificationsEnabled ? Colors.accent : Colors.textSecondary}
              />
            )}
          </View>
          
          {/* Show Token Button (if enabled) */}
          {notificationsEnabled && pushToken && (
            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => setShowTokenModal(true)}
            >
              <Text style={styles.menuIcon}>📋</Text>
              <View style={styles.menuTextContainer}>
                <Text style={styles.menuText}>View Push Token</Text>
                <Text style={styles.menuSubtext}>
                  Tap to copy for testing
                </Text>
              </View>
              <Text style={styles.menuArrow}>→</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Quick Access Links */}
        <View style={styles.menu}>
          <Text style={styles.sectionTitle}>Quick Access</Text>
          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => navigation.navigate('Events')}
          >
            <Text style={styles.menuIcon}>📅</Text>
            <Text style={styles.menuText}>Events</Text>
            <Text style={styles.menuArrow}>→</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => navigation.navigate('Prayer')}
          >
            <Text style={styles.menuIcon}>🙏</Text>
            <Text style={styles.menuText}>Prayer & Praise</Text>
            <Text style={styles.menuArrow}>→</Text>
          </TouchableOpacity>
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
      </LinearGradient>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  gradient: {
    flex: 1,
    padding: Spacing.md,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: Spacing.xl,
    marginTop: Spacing.lg,
  },
  headerTitle: {
    fontSize: FontSizes.xxl,
    fontWeight: 'bold',
    color: Colors.text,
  },
  profileCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: Spacing.lg,
    marginBottom: Spacing.xl,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  avatarText: {
    fontSize: FontSizes.xxl,
    fontWeight: 'bold',
    color: Colors.text,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  profileEmail: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  profileCampus: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
  },
  editButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: Spacing.lg,
  },
  editButtonGradient: {
    padding: Spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  editButtonText: {
    color: Colors.text,
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
  menu: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  menuItem: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  menuIcon: {
    fontSize: 24,
    marginRight: Spacing.md,
  },
  menuText: {
    flex: 1,
    fontSize: FontSizes.md,
    color: Colors.text,
    fontWeight: '500',
  },
  menuTextContainer: {
    flex: 1,
    marginLeft: Spacing.xs,
  },
  menuSubtext: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  menuArrow: {
    fontSize: FontSizes.lg,
    color: Colors.textSecondary,
  },
  logoutButton: {
    backgroundColor: Colors.error,
    borderRadius: 12,
    padding: Spacing.md,
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  logoutText: {
    color: Colors.text,
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
});

