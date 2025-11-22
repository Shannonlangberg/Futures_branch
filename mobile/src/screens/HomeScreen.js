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
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={[Colors.primary, Colors.accent]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.journeyCard}
          >
            <View style={styles.journeyHeader}>
              <View style={styles.journeyTitleRow}>
                <View style={styles.journeyIconContainer}>
                  <Icon name="pathway" size={24} color="#ffffff" style={styles.journeyIcon} />
                </View>
                <Text style={styles.journeyTitleWhite}>Your Journey</Text>
              </View>
              <Icon name="arrowRight" size={20} color="rgba(255, 255, 255, 0.9)" />
            </View>
            <Text style={styles.journeySubtitleWhite}>Track your spiritual growth</Text>
          </LinearGradient>
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
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#6366f1', '#8b5cf6']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.actionGradient}
              >
                <View style={styles.actionContent}>
                  <View style={styles.actionIconContainerWhite}>
                    <Icon name="sunday" size={28} color="#ffffff" />
                  </View>
                  <Text style={styles.actionTextWhite}>Sunday</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Give')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#10b981', '#34d399']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.actionGradient}
              >
                <View style={styles.actionContent}>
                  <View style={styles.actionIconContainerWhite}>
                    <Icon name="give" size={28} color="#ffffff" />
                  </View>
                  <Text style={styles.actionTextWhite}>Give</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Groups')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#8b5cf6', '#a78bfa']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.actionGradient}
              >
                <View style={styles.actionContent}>
                  <View style={styles.actionIconContainerWhite}>
                    <Icon name="groups" size={28} color="#ffffff" />
                  </View>
                  <Text style={styles.actionTextWhite}>Groups</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('TVHome')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#3b82f6', '#60a5fa']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.actionGradient}
              >
                <View style={styles.actionContent}>
                  <View style={styles.actionIconContainerWhite}>
                    <Icon name="tv" size={28} color="#ffffff" />
                  </View>
                  <Text style={styles.actionTextWhite}>Pulse TV</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Prayer')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#ef4444', '#f87171']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.actionGradient}
              >
                <View style={styles.actionContent}>
                  <View style={styles.actionIconContainerWhite}>
                    <Icon name="prayer" size={28} color="#ffffff" />
                  </View>
                  <Text style={styles.actionTextWhite}>Prayer</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Explore')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#06b6d4', '#22d3ee']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.actionGradient}
              >
                <View style={styles.actionContent}>
                  <View style={styles.actionIconContainerWhite}>
                    <Icon name="explore" size={28} color="#ffffff" />
                  </View>
                  <Text style={styles.actionTextWhite}>Explore</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>
          </View>
          {/* Spacing below Quick Actions */}
          <View style={styles.actionsBottomSpacing} />
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
    marginBottom: Spacing.xl,
    marginTop: Spacing.lg,
    paddingBottom: Spacing.xs,
  },
  headerContent: {
    paddingVertical: Spacing.sm,
  },
  greeting: {
    fontSize: FontSizes.xxxl,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: Spacing.xs,
    letterSpacing: -0.5,
    lineHeight: 40,
  },
  campusName: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  journeySection: {
    marginBottom: Spacing.xl,
  },
  journeyCard: {
    padding: Spacing.cardPadding,
    borderRadius: 20,
    marginBottom: 0,
  },
  journeyIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.sm,
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
  journeyTitleWhite: {
    fontSize: FontSizes.xl,
    fontWeight: '700',
    color: '#ffffff',
  },
  journeySubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  journeySubtitleWhite: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 20,
    marginTop: Spacing.xs,
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
    marginBottom: Spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
    paddingVertical: Spacing.xs,
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
    marginBottom: Spacing.cardGap,
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
    marginBottom: Spacing.xl,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    marginBottom: Spacing.cardGap,
    borderRadius: 20,
    overflow: 'hidden',
  },
  actionGradient: {
    borderRadius: 20,
    padding: Spacing.cardPadding,
    minHeight: 130,
    justifyContent: 'center',
  },
  actionContent: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  actionIconContainerWhite: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  actionText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
  },
  actionTextWhite: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: '#ffffff',
  },
  actionsBottomSpacing: {
    height: Spacing.lg,
  },
  bottomSpacing: {
    height: Spacing.xxl,
  },
});
