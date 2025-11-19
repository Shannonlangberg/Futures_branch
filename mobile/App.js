import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StyleSheet, View, ActivityIndicator } from 'react-native';
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
import EventsScreen from './src/screens/EventsScreen';
import PrayerScreen from './src/screens/PrayerScreen';

// Services
import { AuthService } from './src/services/AuthService';
import { NotificationService } from './src/services/NotificationService';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

function MainTabs() {
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
          paddingBottom: 8,
          paddingTop: 8,
          height: 65,
          elevation: 10,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 4,
        },
        tabBarIconStyle: {
          marginTop: 4,
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
        name="Sunday" 
        component={SundayScreen}
        options={{
          tabBarLabel: 'Sunday',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>⛪</Text>
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
        name="Journey" 
        component={PassportScreen}
        options={{
          tabBarLabel: 'Journey',
          tabBarIcon: ({ color, size }) => (
            <Text style={{ fontSize: 24 }}>🎫</Text>
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
      await NotificationService.registerForPushNotifications();
      const token = await NotificationService.getPushToken();
      if (token && user) {
        await NotificationService.savePushToken(user.email, token);
      }
    } catch (error) {
      console.error('Notification setup error:', error);
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
    <StripeProvider publishableKey={STRIPE_PUBLISHABLE_KEY}>
      <NavigationContainer>
        <StatusBar style="light" />
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {isAuthenticated ? (
            <>
              <Stack.Screen name="Main" component={MainTabs} />
              {/* Events and Prayer accessible within 1 click from Home/other screens */}
              <Stack.Screen 
                name="Events" 
                component={EventsScreen}
                options={{ 
                  presentation: 'card',
                  animation: 'slide_from_right'
                }}
              />
              <Stack.Screen 
                name="Prayer" 
                component={PrayerScreen}
                options={{ 
                  presentation: 'card',
                  animation: 'slide_from_right'
                }}
              />
              {/* Profile accessible from Journey tab */}
              <Stack.Screen 
                name="Profile" 
                component={ProfileScreen}
                options={{ 
                  presentation: 'card',
                  animation: 'slide_from_right'
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

