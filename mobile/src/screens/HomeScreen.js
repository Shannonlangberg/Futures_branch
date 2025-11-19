import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function HomeScreen() {
  const navigation = useNavigation();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [campus, setCampus] = useState(null);
  const [upcomingEvents, setUpcomingEvents] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        // Load campus info
        const campuses = await ApiService.getCampuses();
        const userCampus = campuses.campuses?.find(c => c.id === userObj.campus);
        if (userCampus) {
          setCampus(userCampus);
        }

        // Load upcoming events
        const events = await ApiService.getEvents(userObj.campus);
        if (events.events) {
          const upcoming = events.events
            .filter(e => new Date(e.start_time) > new Date())
            .slice(0, 3);
          setUpcomingEvents(upcoming);
        }
      }
    } catch (error) {
      console.error('Error loading home data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <LinearGradient
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}!</Text>
            <Text style={styles.subtitle}>{campus?.name || 'Futures Church'}</Text>
          </View>
        </View>

        {/* Quick Actions - Everything accessible within 1 click from Home */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Sunday')}
            >
              <LinearGradient
                colors={[Colors.primary, Colors.accent]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>⛪</Text>
                <Text style={styles.actionText}>Sunday</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Give')}
            >
              <LinearGradient
                colors={[Colors.success, Colors.primary]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>💰</Text>
                <Text style={styles.actionText}>Give</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Groups')}
            >
              <LinearGradient
                colors={[Colors.accent, Colors.primary]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>👥</Text>
                <Text style={styles.actionText}>Groups</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Prayer')}
            >
              <LinearGradient
                colors={[Colors.warning, Colors.error]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>🙏</Text>
                <Text style={styles.actionText}>Prayer</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Journey')}
            >
              <LinearGradient
                colors={[Colors.primary, Colors.accent]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>🎫</Text>
                <Text style={styles.actionText}>Journey</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Events')}
            >
              <LinearGradient
                colors={[Colors.accent, Colors.primary]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>📅</Text>
                <Text style={styles.actionText}>Events</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>

        {/* Upcoming Events */}
        {upcomingEvents.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Upcoming Events</Text>
            {upcomingEvents.map((event) => (
              <TouchableOpacity
                key={event.id}
                style={styles.eventCard}
                onPress={() => navigation.navigate('Events', { eventId: event.id })}
              >
                <View style={styles.eventContent}>
                  <Text style={styles.eventTitle}>{event.title}</Text>
                  <Text style={styles.eventDate}>
                    {new Date(event.start_time).toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </Text>
                  {event.location && (
                    <Text style={styles.eventLocation}>📍 {event.location}</Text>
                  )}
                </View>
              </TouchableOpacity>
            ))}
            <TouchableOpacity
              style={styles.viewAllButton}
              onPress={() => navigation.navigate('Events')}
            >
              <Text style={styles.viewAllText}>View All Events →</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Journey Progress */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Journey</Text>
          <TouchableOpacity
            style={styles.journeyCard}
            onPress={() => navigation.navigate('Journey')}
          >
            <LinearGradient
              colors={[Colors.surface, Colors.surfaceLight]}
              style={styles.journeyGradient}
            >
              <Text style={styles.journeyText}>View your spiritual journey</Text>
              <Text style={styles.journeyArrow}>→</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
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
  header: {
    marginBottom: Spacing.xl,
    marginTop: Spacing.lg,
  },
  greeting: {
    fontSize: FontSizes.xxl,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  subtitle: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  section: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: Spacing.md,
  },
  actionCard: {
    width: '48%',
    marginBottom: Spacing.md,
    borderRadius: 16,
    overflow: 'hidden',
  },
  actionGradient: {
    padding: Spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 100,
  },
  actionEmoji: {
    fontSize: 32,
    marginBottom: Spacing.sm,
  },
  actionText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
  },
  eventCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
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
  eventDate: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  eventLocation: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
  },
  viewAllButton: {
    marginTop: Spacing.sm,
    alignItems: 'center',
  },
  viewAllText: {
    color: Colors.primary,
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
  journeyCard: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  journeyGradient: {
    padding: Spacing.lg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  journeyText: {
    fontSize: FontSizes.md,
    color: Colors.text,
    fontWeight: '500',
  },
  journeyArrow: {
    fontSize: FontSizes.xl,
    color: Colors.primary,
  },
});

