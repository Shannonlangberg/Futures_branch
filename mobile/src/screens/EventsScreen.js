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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function EventsScreen({ route }) {
  const [user, setUser] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        const eventsData = await ApiService.getEvents(userObj.campus);
        if (eventsData.events) {
          // Sort by date
          const sorted = eventsData.events.sort(
            (a, b) => new Date(a.start_time) - new Date(b.start_time)
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

  const formatEventDate = (dateString) => {
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
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Events</Text>
          <Text style={styles.headerSubtitle}>Upcoming church events</Text>
        </View>

        {events.length > 0 ? (
          events.map((event) => {
            const dateInfo = formatEventDate(event.start_time);
            return (
              <View key={event.id} style={styles.eventCard}>
                <View style={styles.eventHeader}>
                  <View style={styles.eventDateBox}>
                    <Text style={styles.eventDate}>{dateInfo.date}</Text>
                    <Text style={styles.eventWeekday}>{dateInfo.weekday}</Text>
                  </View>
                  <View style={styles.eventContent}>
                    <Text style={styles.eventTitle}>{event.title}</Text>
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
                  <TouchableOpacity
                    style={[styles.rsvpButton, styles.rsvpYes]}
                    onPress={() => handleRSVP(event.id, 'yes')}
                  >
                    <Text style={styles.rsvpButtonText}>Going ✓</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.rsvpButton, styles.rsvpMaybe]}
                    onPress={() => handleRSVP(event.id, 'maybe')}
                  >
                    <Text style={styles.rsvpButtonText}>Maybe</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.rsvpButton, styles.rsvpNo]}
                    onPress={() => handleRSVP(event.id, 'no')}
                  >
                    <Text style={styles.rsvpButtonText}>Can't Go</Text>
                  </TouchableOpacity>
                </View>
              </View>
            );
          })
        ) : (
          <Text style={styles.emptyText}>No upcoming events</Text>
        )}
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
    marginBottom: Spacing.xs,
  },
  headerSubtitle: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  eventCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
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
    color: Colors.primary,
  },
  eventWeekday: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    textTransform: 'uppercase',
  },
  eventContent: {
    flex: 1,
  },
  eventTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  eventTime: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  eventLocation: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  eventDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
  },
  eventActions: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  rsvpButton: {
    flex: 1,
    padding: Spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
  },
  rsvpYes: {
    backgroundColor: Colors.success,
  },
  rsvpMaybe: {
    backgroundColor: Colors.warning,
  },
  rsvpNo: {
    backgroundColor: Colors.error,
  },
  rsvpButtonText: {
    color: Colors.text,
    fontSize: FontSizes.sm,
    fontWeight: '500',
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: Colors.textMuted,
    textAlign: 'center',
    padding: Spacing.xxl,
  },
});


