import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StyleSheet, View, ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { StripeProvider } from '@stripe/stripe-react-native';
import { STRIPE_PUBLISHABLE_KEY } from './src/constants/config';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import SundayScreen from './src/screens/SundayScreen';
import GroupsScreen from './src/screens/GroupsScreen';
import GivingScreen from './src/screens/GivingScreen';
import PassportScreen from './src/screens/PassportScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import EditProfileScreen from './src/screens/EditProfileScreen';
import EventsScreen from './src/screens/EventsScreen';
import PrayerScreen from './src/screens/PrayerScreen';
import SermonNotesScreen from './src/screens/SermonNotesScreen';
import TVHomeScreen from './src/screens/TVHomeScreen';
import TVSeriesScreen from './src/screens/TVSeriesScreen';
import TVWatchScreen from './src/screens/TVWatchScreen';
import ExploreScreen from './src/screens/ExploreScreen';
import GroupChatScreen from './src/screens/GroupChatScreen';
import GroupLeaderPortalScreen from './src/screens/GroupLeaderPortalScreen';
import PrayerSubmitScreen from './src/screens/PrayerSubmitScreen';

// Services
import { AuthService } from './src/services/AuthService';
import { NotificationService } from './src/services/NotificationService';
import ApiService from './src/services/ApiService';
import { Platform } from 'react-native';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Helper function to create header options
const createHeaderOptions = (title) => ({
  presentation: 'card',
  animation: 'slide_from_right',
  headerShown: true,
  headerStyle: {
    backgroundColor: '#1e293b',
  },
  headerTintColor: '#ffffff',
  headerTitleStyle: {
    fontWeight: '600',
  },
  headerTitle: title,
  headerBackTitleVisible: false,
});

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

function MainTabs() {
  const insets = useSafeAreaInsets();
  
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#6366f1',
        tabBarInactiveTintColor: '#64748b',
        tabBarStyle: {
          backgroundColor: '#1e293b',
          borderTopColor: '#334155',
          borderTopWidth: 1,
          paddingBottom: Math.max(insets.bottom, 8), // Use safe area bottom inset
          paddingTop: 8,
          height: 60 + Math.max(insets.bottom - 8, 0), // Adjust height for safe area
          elevation: 10,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 2,
          marginBottom: 0,
        },
        tabBarIconStyle: {
          marginTop: 2,
        },
      }}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>🏠</Text>
          ),
        }}
      />
      <Tab.Screen 
        name="Pathway" 
        component={PassportScreen}
        options={{
          tabBarLabel: 'Pathway',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>🗺️</Text>
          ),
        }}
      />
      <Tab.Screen 
        name="Give" 
        component={GivingScreen}
        options={{
          tabBarLabel: 'Give',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>💰</Text>
          ),
        }}
      />
      <Tab.Screen 
        name="Groups" 
        component={GroupsScreen}
        options={{
          tabBarLabel: 'Groups',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>👥</Text>
          ),
        }}
      />
      <Tab.Screen 
        name="Prayer" 
        component={PrayerScreen}
        options={{
          tabBarLabel: 'Prayer',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>🙏</Text>
          ),
        }}
      />
      <Tab.Screen 
        name="Settings" 
        component={ProfileScreen}
        options={{
          tabBarLabel: 'Settings',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>⚙️</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    checkAuth();
    setupNotifications();
  }, []);

  // NEW: Log app open for engagement tracking (+1 point)
  useEffect(() => {
    const logAppOpen = async () => {
      if (user && user.email) {
        try {
          const platform = Platform.OS; // 'ios' or 'android'
          const appVersion = Constants?.expoConfig?.version || '1.0.0';
          
          await ApiService.logAppOpen(user.email, platform, appVersion);
          console.log('✅ App open logged for engagement tracking');
        } catch (error) {
          // Fail silently - don't break the app if tracking fails
          console.log('App open tracking failed (non-critical):', error.message);
        }
      }
    };
    
    if (isAuthenticated && user) {
      logAppOpen();
    }
  }, [isAuthenticated, user]); // Fire when authentication state changes

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const userData = await AsyncStorage.getItem('userData');
      
      if (token && userData) {
        // Verify token is still valid
        const isValid = await AuthService.verifyToken(token);
        if (isValid) {
          setUser(JSON.parse(userData));
          setIsAuthenticated(true);
        } else {
          await AsyncStorage.removeItem('authToken');
          await AsyncStorage.removeItem('userData');
        }
      }
    } catch (error) {
      console.error('Auth check error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const setupNotifications = async () => {
    try {
      // Only setup notifications if we have a valid Expo project ID
      const projectId = Constants?.expoConfig?.extra?.eas?.projectId;
      if (!projectId || projectId === 'your-project-id' || projectId === null) {
        // Silently skip notifications if no project ID configured
        return;
      }
      
      await NotificationService.registerForPushNotifications();
      const token = await NotificationService.getPushToken();
      if (token && user) {
        await NotificationService.savePushToken(user.email, token);
      }
    } catch (error) {
      // Fail gracefully - don't break the app if notifications can't be set up
      // This happens when projectId is invalid or missing
      if (error.message?.includes('projectId') || error.message?.includes('Invalid uuid')) {
        // Silently ignore invalid project ID errors
        return;
      }
      console.warn('Notification setup failed (app will continue):', error.message);
    }
  };

  const handleLogin = async (email, password) => {
    try {
      const result = await AuthService.login(email, password);
      if (result.success) {
        await AsyncStorage.setItem('authToken', result.token);
        await AsyncStorage.setItem('userData', JSON.stringify(result.user));
        setUser(result.user);
        setIsAuthenticated(true);
        
        // Setup notifications with user email
        const pushToken = await NotificationService.getPushToken();
        if (pushToken) {
          await NotificationService.savePushToken(result.user.email, pushToken);
        }
        
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('userData');
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StripeProvider publishableKey={STRIPE_PUBLISHABLE_KEY}>
        <NavigationContainer>
          <StatusBar style="light" />
          <Stack.Navigator screenOptions={{ headerShown: false }}>
          {isAuthenticated ? (
            <>
              <Stack.Screen name="Main" component={MainTabs} />
              {/* Screens accessible from navigation (not in tab bar) */}
              <Stack.Screen 
                name="Sunday" 
                component={SundayScreen}
                options={createHeaderOptions('Sunday Service')}
              />
              <Stack.Screen 
                name="Events" 
                component={EventsScreen}
                options={createHeaderOptions('Events')}
              />
              <Stack.Screen 
                name="SermonNotes" 
                component={SermonNotesScreen}
                options={{ 
                  presentation: 'card',
                  animation: 'slide_from_right',
                  headerShown: false, // Custom header in component
                }}
              />
              <Stack.Screen 
                name="TVHome" 
                component={TVHomeScreen}
                options={createHeaderOptions('Pulse TV')}
              />
              <Stack.Screen 
                name="TVSeries" 
                component={TVSeriesScreen}
                options={createHeaderOptions('TV Series')}
              />
              <Stack.Screen 
                name="TVWatch" 
                component={TVWatchScreen}
                options={{ 
                  presentation: 'fullScreenModal',
                  animation: 'slide_from_bottom',
                  headerShown: false, // Full screen video
                  headerBackTitleVisible: false,
                }}
              />
              {/* Profile accessible from Journey tab */}
              <Stack.Screen 
                name="Profile" 
                component={ProfileScreen}
                options={createHeaderOptions('Profile')}
              />
              <Stack.Screen 
                name="EditProfile" 
                component={EditProfileScreen}
                options={createHeaderOptions('Edit Profile')}
              />
              <Stack.Screen 
                name="Explore" 
                component={ExploreScreen}
                options={createHeaderOptions('Explore')}
              />
              <Stack.Screen 
                name="PrayerSubmit" 
                component={PrayerSubmitScreen}
                options={{
                  ...createHeaderOptions('Prayer & Praise'),
                  presentation: 'card',
                  animation: 'slide_from_bottom',
                }}
              />
              <Stack.Screen 
                name="GroupChat" 
                component={GroupChatScreen}
                options={{ 
                  presentation: 'card',
                  animation: 'slide_from_right',
                  headerShown: false,
                }}
              />
              <Stack.Screen 
                name="GroupLeaderPortal" 
                component={GroupLeaderPortalScreen}
                options={{ 
                  presentation: 'card',
                  animation: 'slide_from_right',
                  headerShown: false,
                }}
              />
            </>
          ) : (
            <Stack.Screen name="Login">
              {(props) => <LoginScreen {...props} onLogin={handleLogin} />}
            </Stack.Screen>
          )}
          </Stack.Navigator>
        </NavigationContainer>
      </StripeProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
  },
});

