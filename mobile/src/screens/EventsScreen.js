import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Linking,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Calendar from 'expo-calendar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useStripe } from '@stripe/stripe-react-native';
import * as ExpoLinking from 'expo-linking';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function EventsScreen({ route }) {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { initPaymentSheet, presentPaymentSheet } = useStripe();
  const [user, setUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [calendarPermission, setCalendarPermission] = useState(null);
  const [processingPayment, setProcessingPayment] = useState(false);

  useEffect(() => {
    loadEvents();
    requestCalendarPermission();
  }, []);

  const requestCalendarPermission = async () => {
    try {
      const { status } = await Calendar.requestCalendarPermissionsAsync();
      setCalendarPermission(status === 'granted');
    } catch (error) {
      console.error('Error requesting calendar permission:', error);
      setCalendarPermission(false);
    }
  };

  const loadEvents = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        const eventsData = await ApiService.getEvents(userObj.campus);
        if (eventsData.events) {
          // Sort by date - use start_datetime if available, otherwise start_time
          const sorted = eventsData.events.sort(
            (a, b) => new Date(a.start_datetime || a.start_time) - new Date(b.start_datetime || b.start_time)
          );
          setEvents(sorted);
        }
      }
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadEvents();
  };

  const handleRSVP = async (eventId, rsvp) => {
    if (!user) {
      Alert.alert('Error', 'User not found.');
      return;
    }

    try {
      const result = await ApiService.rsvpEvent(user.email, eventId, rsvp);
      if (result.success) {
        Alert.alert('Success', `RSVP recorded: ${rsvp}`);
        loadEvents();
      } else {
        Alert.alert('Error', result.error || 'Failed to record RSVP.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to record RSVP. Please try again.');
    }
  };

  const handleAddToCalendar = async (event) => {
    if (!calendarPermission) {
      Alert.alert(
        'Calendar Permission Required',
        'Please grant calendar access in Settings to add events to your calendar.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Open Settings', onPress: () => Linking.openSettings() },
        ]
      );
      return;
    }

    try {
      const calendars = await Calendar.getCalendarsAsync(Calendar.EntityTypes.EVENT);
      if (calendars.length === 0) {
        Alert.alert('No Calendars', 'Please create a calendar first in your calendar app.');
        return;
      }

      // Use default calendar (first one)
      const defaultCalendar = calendars.find(cal => cal.allowsModifications) || calendars[0];
      
      const startDate = new Date(event.start_datetime || event.start_time);
      const endDate = event.end_time 
        ? new Date(event.end_time) 
        : new Date(startDate.getTime() + 60 * 60 * 1000); // Default 1 hour

      const eventId = await Calendar.createEventAsync(defaultCalendar.id, {
        title: event.title,
        startDate: startDate,
        endDate: endDate,
        location: event.location || '',
        notes: event.description || '',
        timeZone: 'Australia/Adelaide',
        alarms: [{ relativeOffset: -15, method: Calendar.AlarmMethod.ALERT }], // 15 min before
      });

      Alert.alert('Success', 'Event added to your calendar!');
    } catch (error) {
      console.error('Error adding to calendar:', error);
      Alert.alert('Error', 'Failed to add event to calendar. Please try again.');
    }
  };

  const getReturnURL = () => {
    return ExpoLinking.createURL('/');
  };

  const handlePaidEventRegistration = async (event) => {
    if (!user || !user.email) {
      Alert.alert('Error', 'User email not found. Please log in.');
      return;
    }

    setProcessingPayment(true);

    try {
      // Step 1: Create payment intent
      const paymentData = await ApiService.createEventPaymentIntent(
        event.id,
        user.email,
        0 // guest_count - can be added later
      );

      if (!paymentData.client_secret) {
        throw new Error('Failed to create payment intent');
      }

      // Step 2: Initialize payment sheet
      const { error: initError } = await initPaymentSheet({
        paymentIntentClientSecret: paymentData.client_secret,
        merchantDisplayName: 'Futures Church',
        returnURL: getReturnURL(),
      });

      if (initError) {
        throw new Error(initError.message || 'Failed to initialize payment');
      }

      // Step 3: Present payment sheet
      const { error: paymentError } = await presentPaymentSheet();

      if (paymentError) {
        if (paymentError.code !== 'Canceled') {
          Alert.alert('Payment Error', paymentError.message || 'Payment failed. Please try again.');
        }
        setProcessingPayment(false);
        return;
      }

      // Step 4: Payment succeeded - register user
      const registrationData = await ApiService.registerForEvent(
        event.id,
        user.email,
        user.full_name || user.name || '',
        user.phone || '',
        0,
        paymentData.payment_intent_id
      );

      Alert.alert(
        'Registration Successful!',
        `You're registered for ${event.title}!\n\n` +
        `Amount paid: $${paymentData.amount.toFixed(2)}\n\n` +
        `A confirmation email has been sent.`,
        [{ text: 'OK', onPress: () => loadEvents() }]
      );
    } catch (error) {
      console.error('Registration error:', error);
      Alert.alert(
        'Registration Error',
        error.message || 'Failed to register. Please try again or contact the church office.'
      );
    } finally {
      setProcessingPayment(false);
    }
  };

  const formatEventDate = (dateString) => {
    if (!dateString) return { date: '', time: '', weekday: '' };
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      weekday: date.toLocaleDateString('en-US', { weekday: 'short' }),
    };
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <LinearGradient
        colors={['#0f172a', '#1e293b', '#0f172a']}
        style={styles.gradient}
      >
        <View style={[styles.header, { paddingTop: insets.top > 0 ? 0 : Spacing.md }]}>
          <Text style={styles.headerTitle}>Upcoming Events</Text>
          <Text style={styles.headerSubtitle}>Join us for these upcoming events</Text>
        </View>

        {events.length > 0 ? (
          events.map((event) => {
            const dateInfo = formatEventDate(event.start_datetime || event.start_time);
            const requiresPayment = event.requires_payment && event.price > 0;
            
            return (
              <View key={event.id} style={styles.eventCard}>
                <View style={styles.eventHeader}>
                  <View style={styles.eventDateBox}>
                    <Text style={styles.eventDate}>{dateInfo.date}</Text>
                    <Text style={styles.eventWeekday}>{dateInfo.weekday}</Text>
                  </View>
                  <View style={styles.eventContent}>
                    <View style={styles.eventTitleRow}>
                      <Text style={styles.eventTitle}>{event.title}</Text>
                      {requiresPayment && (
                        <View style={styles.priceBadge}>
                          <Text style={styles.priceText}>${event.price}</Text>
                        </View>
                      )}
                    </View>
                    <Text style={styles.eventTime}>🕐 {dateInfo.time}</Text>
                    {event.location && (
                      <Text style={styles.eventLocation}>📍 {event.location}</Text>
                    )}
                    {event.description && (
                      <Text style={styles.eventDescription} numberOfLines={2}>
                        {event.description}
                      </Text>
                    )}
                  </View>
                </View>

                <View style={styles.eventActions}>
                  {requiresPayment ? (
                    <TouchableOpacity
                      style={[styles.actionButton, styles.registerButton, processingPayment && styles.disabledButton]}
                      onPress={() => handlePaidEventRegistration(event)}
                      disabled={processingPayment}
                    >
                      {processingPayment ? (
                        <ActivityIndicator size="small" color="#ffffff" />
                      ) : (
                        <Text style={styles.actionButtonText}>Register & Pay ${event.price}</Text>
                      )}
                    </TouchableOpacity>
                  ) : (
                    <>
                      <TouchableOpacity
                        style={[styles.actionButton, styles.rsvpYes]}
                        onPress={() => handleRSVP(event.id, 'yes')}
                      >
                        <Text style={styles.actionButtonText}>Going</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.actionButton, styles.rsvpMaybe]}
                        onPress={() => handleRSVP(event.id, 'maybe')}
                      >
                        <Text style={styles.actionButtonText}>Maybe</Text>
                      </TouchableOpacity>
                    </>
                  )}
                  
                  <TouchableOpacity
                    style={[styles.actionButton, styles.calendarButton]}
                    onPress={() => handleAddToCalendar(event)}
                  >
                    <Text style={styles.actionButtonText}>
                      {Platform.OS === 'ios' ? '📅 Add to Calendar' : '📅 Add'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            );
          })
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>📅</Text>
            <Text style={styles.emptyText}>No upcoming events</Text>
            <Text style={styles.emptySubtext}>Check back soon for new events!</Text>
          </View>
        )}

        <View style={{ height: 100 }} />
      </LinearGradient>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  gradient: {
    flex: 1,
    padding: Spacing.md,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: Spacing.xl,
    marginTop: Spacing.sm,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  headerSubtitle: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  eventCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  eventHeader: {
    flexDirection: 'row',
    marginBottom: Spacing.md,
  },
  eventDateBox: {
    width: 60,
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  eventDate: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#6366f1',
  },
  eventWeekday: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.5)',
    textTransform: 'uppercase',
  },
  eventContent: {
    flex: 1,
  },
  eventTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  eventTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    flex: 1,
  },
  priceBadge: {
    backgroundColor: 'rgba(99, 102, 241, 0.3)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
    marginLeft: Spacing.xs,
  },
  priceText: {
    fontSize: FontSizes.sm,
    fontWeight: '600',
    color: '#a5b4fc',
  },
  eventTime: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: Spacing.xs,
  },
  eventLocation: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: Spacing.xs,
  },
  eventDescription: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.5)',
    lineHeight: 18,
  },
  eventActions: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: Spacing.sm,
  },
  actionButton: {
    flex: 1,
    padding: Spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 40,
  },
  rsvpYes: {
    backgroundColor: 'rgba(16, 185, 129, 0.3)',
  },
  rsvpMaybe: {
    backgroundColor: 'rgba(251, 191, 36, 0.3)',
  },
  registerButton: {
    backgroundColor: 'rgba(99, 102, 241, 0.3)',
    flex: 2,
  },
  calendarButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    flex: 1,
  },
  disabledButton: {
    opacity: 0.5,
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    padding: Spacing.xxl,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: Spacing.lg,
  },
  emptyText: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  emptySubtext: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
  },
});
