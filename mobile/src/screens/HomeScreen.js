import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Icon from '../components/Icon';

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
        // Match campus by id (e.g., "copper_coast")
        const userCampus = campuses.campuses?.find(c => 
          c.id === userObj.campus || 
          c.id.toLowerCase() === userObj.campus?.toLowerCase() ||
          c.name?.toLowerCase().replace(/\s+/g, '_') === userObj.campus?.toLowerCase()
        );
        if (userCampus) {
          setCampus(userCampus);
        } else if (userObj.campus && userObj.campus !== 'all_campuses') {
          // If campus not found but user has one set, create a fallback
          setCampus({
            id: userObj.campus,
            name: userObj.campus.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
          });
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
      <View style={styles.gradient}>
        {/* Personalized Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text style={styles.greeting}>{getGreeting()}, {getFirstName()}</Text>
            <Text style={styles.campusName}>{campus?.name || 'Futures Church'}</Text>
          </View>
        </View>

        {/* Your Pathway Card */}
        <TouchableOpacity
          style={styles.journeySection}
          onPress={() => navigation.navigate('Pathway')}
          activeOpacity={0.7}
        >
          <View style={styles.journeyCard}>
            <View style={styles.journeyHeader}>
              <View style={styles.journeyTitleRow}>
                <Icon name="pathway" size={24} color={Colors.primary} style={styles.journeyIcon} />
                <Text style={styles.journeyTitle}>Your Pathway</Text>
              </View>
              <Icon name="arrowRight" size={20} color={Colors.textMuted} />
            </View>
            <Text style={styles.journeySubtitle}>Track your spiritual growth</Text>
          </View>
        </TouchableOpacity>

        {/* Campus Section - What's Coming Up */}
        <View style={styles.campusSection}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Icon name="calendar" size={20} color={Colors.textSecondary} style={styles.sectionIcon} />
              <Text style={styles.sectionTitle}>{campus?.name && campus.name !== 'All Campuses' ? campus.name : 'All Campuses'}</Text>
            </View>
            <TouchableOpacity onPress={() => navigation.navigate('Events')}>
              <Text style={styles.seeAllText}>See all</Text>
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
                  <View style={styles.eventGradient}>
                    <View style={styles.eventContent}>
                      <Text style={styles.eventTitle}>{event.title || 'Event'}</Text>
                      <View style={styles.eventInfoRow}>
                        <Icon name="calendar" size={14} color={Colors.textMuted} />
                        <Text style={styles.eventDate}>
                          {new Date(event.start_time || event.start_datetime).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                        </Text>
                      </View>
                      {event.location && (
                        <View style={styles.eventInfoRow}>
                          <Icon name="location" size={14} color={Colors.textMuted} />
                          <Text style={styles.eventLocation}>{event.location}</Text>
                        </View>
                      )}
                    </View>
                  </View>
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
              activeOpacity={0.7}
            >
              <View style={styles.actionContent}>
                <View style={[styles.actionIconContainer, { backgroundColor: Colors.primary + '20' }]}>
                  <Icon name="sunday" size={24} color={Colors.primary} />
                </View>
                <Text style={styles.actionText}>Sunday</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Give')}
              activeOpacity={0.7}
            >
              <View style={styles.actionContent}>
                <View style={[styles.actionIconContainer, { backgroundColor: Colors.success + '20' }]}>
                  <Icon name="give" size={24} color={Colors.success} />
                </View>
                <Text style={styles.actionText}>Give</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Groups')}
              activeOpacity={0.7}
            >
              <View style={styles.actionContent}>
                <View style={[styles.actionIconContainer, { backgroundColor: Colors.accent + '20' }]}>
                  <Icon name="groups" size={24} color={Colors.accent} />
                </View>
                <Text style={styles.actionText}>Groups</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('TVHome')}
              activeOpacity={0.7}
            >
              <View style={styles.actionContent}>
                <View style={[styles.actionIconContainer, { backgroundColor: Colors.primary + '20' }]}>
                  <Icon name="tv" size={24} color={Colors.primary} />
                </View>
                <Text style={styles.actionText}>Pulse TV</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Prayer')}
              activeOpacity={0.7}
            >
              <View style={styles.actionContent}>
                <View style={[styles.actionIconContainer, { backgroundColor: Colors.error + '20' }]}>
                  <Icon name="prayer" size={24} color={Colors.error} />
                </View>
                <Text style={styles.actionText}>Prayer</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Explore')}
              activeOpacity={0.7}
            >
              <View style={styles.actionContent}>
                <View style={[styles.actionIconContainer, { backgroundColor: Colors.info + '20' }]}>
                  <Icon name="explore" size={24} color={Colors.info} />
                </View>
                <Text style={styles.actionText}>Explore</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* Bottom Spacing */}
        <View style={styles.bottomSpacing} />
      </View>
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
    padding: Spacing.screenPadding,
    backgroundColor: Colors.background,
  },
  header: {
    marginBottom: Spacing.sectionSpacing,
    marginTop: Spacing.md,
  },
  headerContent: {
    paddingVertical: Spacing.lg,
  },
  greeting: {
    fontSize: FontSizes.xxxl,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
    letterSpacing: -0.5,
  },
  campusName: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  journeySection: {
    marginBottom: Spacing.sectionSpacing,
  },
  journeyCard: {
    padding: Spacing.cardPadding,
    borderRadius: 20,
    backgroundColor: Colors.surface,
    borderWidth: 0,
  },
  journeyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  journeyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  journeyIcon: {
    marginRight: Spacing.sm,
  },
  journeyTitle: {
    fontSize: FontSizes.xl,
    fontWeight: '600',
    color: Colors.text,
  },
  journeySubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
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
    marginBottom: Spacing.sectionSpacing,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sectionIcon: {
    marginRight: Spacing.sm,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
  },
  seeAllText: {
    fontSize: FontSizes.sm,
    color: Colors.primary,
    fontWeight: '600',
  },
  eventCard: {
    marginBottom: Spacing.md,
    borderRadius: 20,
    overflow: 'hidden',
  },
  eventGradient: {
    padding: Spacing.cardPadding,
    backgroundColor: Colors.surface,
    borderRadius: 20,
    borderWidth: 0,
  },
  eventContent: {
    flex: 1,
  },
  eventTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  eventInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  eventDate: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginLeft: Spacing.xs,
  },
  eventLocation: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginLeft: Spacing.xs,
  },
  emptyState: {
    padding: Spacing.xl,
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 20,
    borderWidth: 0,
  },
  emptyStateText: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  exploreButton: {
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: 12,
    backgroundColor: Colors.primary,
  },
  exploreButtonText: {
    fontSize: FontSizes.sm,
    color: Colors.text,
    fontWeight: '600',
  },
  actionsSection: {
    marginBottom: Spacing.sectionSpacing,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    marginBottom: Spacing.md,
    borderRadius: 20,
    backgroundColor: Colors.surface,
    borderWidth: 0,
  },
  actionContent: {
    padding: Spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 100,
  },
  actionIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  actionText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
  },
  bottomSpacing: {
    height: Spacing.xl,
  },
});
