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
  const [journeyData, setJourneyData] = useState(null);

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

        // Load upcoming events for campus
        try {
          const events = await ApiService.getEvents(userObj.campus || 'all_campuses');
          if (events.events && Array.isArray(events.events)) {
            const upcoming = events.events
              .filter(e => {
                const eventDate = new Date(e.start_time || e.start_datetime);
                return eventDate > new Date();
              })
              .slice(0, 3);
            setUpcomingEvents(upcoming);
          }
        } catch (e) {
          console.warn('Error loading events:', e);
          setUpcomingEvents([]);
        }

        // Load journey/passport data
        try {
          const profileData = await ApiService.getPersonProfile(userObj.email);
          if (profileData.profile) {
            setJourneyData(profileData.profile);
          }
        } catch (e) {
          console.warn('Error loading journey data:', e);
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

  const getFirstName = () => {
    if (!user?.name) return '';
    return user.name.split(' ')[0];
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}
      showsVerticalScrollIndicator={false}
    >
      <LinearGradient
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Personalized Header */}
        <View style={styles.header}>
          <LinearGradient
            colors={[Colors.primary, Colors.accent]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.headerGradient}
          >
            <Text style={styles.greeting}>{getGreeting()}, {getFirstName()}! 👋</Text>
            <Text style={styles.campusName}>{campus?.name || 'Futures Church'}</Text>
          </LinearGradient>
        </View>

        {/* Your Pathway Card */}
        <TouchableOpacity
          style={styles.journeySection}
          onPress={() => navigation.navigate('Pathway')}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={[Colors.surface, Colors.surfaceLight]}
            style={styles.journeyCard}
          >
            <View style={styles.journeyHeader}>
              <Text style={styles.journeyTitle}>Your Pathway 🗺️</Text>
              <Text style={styles.journeyArrow}>→</Text>
            </View>
            <Text style={styles.journeySubtitle}>Track your spiritual growth</Text>
            {journeyData?.engagement?.pulse_status && (
              <View style={styles.journeyStatus}>
                <View style={[
                  styles.statusDot,
                  { backgroundColor: journeyData.engagement.pulse_status === 'green' ? Colors.success : 
                    journeyData.engagement.pulse_status === 'yellow' ? Colors.warning : Colors.error }
                ]} />
                <Text style={styles.journeyStatusText}>
                  Pulse: {journeyData.engagement.pulse_status.charAt(0).toUpperCase() + 
                  journeyData.engagement.pulse_status.slice(1)}
                </Text>
              </View>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Campus Section - What's Coming Up */}
        <View style={styles.campusSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>📅 {campus?.name || 'Your Campus'}</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Events')}>
              <Text style={styles.seeAllText}>See all →</Text>
            </TouchableOpacity>
          </View>

          {upcomingEvents.length > 0 ? (
            <>
              {upcomingEvents.map((event, index) => (
                <TouchableOpacity
                  key={event.id || index}
                  style={styles.eventCard}
                  onPress={() => navigation.navigate('Events', { eventId: event.id })}
                  activeOpacity={0.7}
                >
                  <LinearGradient
                    colors={[Colors.surface, Colors.surfaceLight]}
                    style={styles.eventGradient}
                  >
                    <View style={styles.eventContent}>
                      <Text style={styles.eventTitle}>{event.title || 'Event'}</Text>
                      <Text style={styles.eventDate}>
                        📆 {new Date(event.start_time || event.start_datetime).toLocaleDateString('en-US', {
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
                  </LinearGradient>
                </TouchableOpacity>
              ))}
            </>
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>No upcoming events</Text>
              <TouchableOpacity
                style={styles.exploreButton}
                onPress={() => navigation.navigate('Events')}
              >
                <Text style={styles.exploreButtonText}>Explore Events →</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Quick Actions */}
        <View style={styles.actionsSection}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Sunday')}
              activeOpacity={0.8}
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
              activeOpacity={0.8}
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
              activeOpacity={0.8}
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
              onPress={() => navigation.navigate('TVHome')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={[Colors.primary, Colors.accent]}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>📺</Text>
                <Text style={styles.actionText}>Pulse TV</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Prayer')}
              activeOpacity={0.8}
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
              onPress={() => navigation.navigate('Explore')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#06b6d4', '#0891b2']}
                style={styles.actionGradient}
              >
                <Text style={styles.actionEmoji}>🔍</Text>
                <Text style={styles.actionText}>Explore</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>

        {/* Bottom Spacing */}
        <View style={styles.bottomSpacing} />
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
    marginBottom: Spacing.lg,
    marginTop: Spacing.sm,
  },
  headerGradient: {
    padding: Spacing.lg,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  greeting: {
    fontSize: FontSizes.xxxl,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  campusName: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    opacity: 0.9,
  },
  journeySection: {
    marginBottom: Spacing.lg,
  },
  journeyCard: {
    padding: Spacing.lg,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  journeyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  journeyTitle: {
    fontSize: FontSizes.xl,
    fontWeight: '700',
    color: Colors.text,
  },
  journeyArrow: {
    fontSize: FontSizes.xl,
    color: Colors.primary,
    fontWeight: 'bold',
  },
  journeySubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  journeyStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: Spacing.xs,
  },
  journeyStatusText: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  campusSection: {
    marginBottom: Spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '700',
    color: Colors.text,
  },
  seeAllText: {
    fontSize: FontSizes.sm,
    color: Colors.primary,
    fontWeight: '600',
  },
  eventCard: {
    marginBottom: Spacing.md,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  eventGradient: {
    padding: Spacing.md,
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
  emptyState: {
    padding: Spacing.xl,
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  emptyStateText: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  exploreButton: {
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: 8,
    backgroundColor: Colors.primary,
  },
  exploreButtonText: {
    fontSize: FontSizes.sm,
    color: Colors.text,
    fontWeight: '600',
  },
  actionsSection: {
    marginBottom: Spacing.lg,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    marginBottom: Spacing.md,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  actionGradient: {
    padding: Spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 110,
  },
  actionEmoji: {
    fontSize: 36,
    marginBottom: Spacing.sm,
  },
  actionText: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: Colors.text,
  },
  bottomSpacing: {
    height: Spacing.xl,
  },
});
