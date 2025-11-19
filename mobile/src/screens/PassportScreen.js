import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function PassportScreen() {
  const navigation = useNavigation();
  const [user, setUser] = useState(null);
  const [pathway, setPathway] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        // Load pathway
        const pathwayData = await ApiService.getMyPathway(userObj.email);
        if (pathwayData.pathway) {
          setPathway(pathwayData.pathway);
        }

        // Load profile
        const profileData = await ApiService.getPersonProfile(userObj.email);
        if (profileData.profile) {
          setProfile(profileData.profile);
        }
      }
    } catch (error) {
      console.error('Error loading passport data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
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
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Journey</Text>
          <Text style={styles.headerSubtitle}>Your spiritual growth timeline</Text>
        </View>

        {/* Progress Card */}
        {pathway && (
          <View style={styles.section}>
            <View style={styles.progressCard}>
              <LinearGradient
                colors={[Colors.primary, Colors.accent]}
                style={styles.progressGradient}
              >
                <Text style={styles.progressTitle}>{pathway.pathway_name || 'Pathway'}</Text>
                <Text style={styles.progressPercent}>
                  {pathway.progress_percentage || 0}% Complete
                </Text>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${pathway.progress_percentage || 0}%` },
                    ]}
                  />
                </View>
                <Text style={styles.progressSteps}>
                  {pathway.completed_steps || 0} of {pathway.total_steps || 0} steps
                </Text>
              </LinearGradient>
            </View>

            {/* Next Step */}
            {pathway.next_step && (
              <View style={styles.nextStepCard}>
                <Text style={styles.nextStepLabel}>Next Step:</Text>
                <Text style={styles.nextStepName}>
                  {pathway.next_step.step_name}
                </Text>
                {pathway.next_step.step_description && (
                  <Text style={styles.nextStepDescription}>
                    {pathway.next_step.step_description}
                  </Text>
                )}
              </View>
            )}
          </View>
        )}

        {/* Milestones */}
        {profile && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Milestones</Text>
            <View style={styles.milestonesList}>
              {profile.baptised_on && (
                <View style={styles.milestoneCard}>
                  <Text style={styles.milestoneEmoji}>💧</Text>
                  <View style={styles.milestoneContent}>
                    <Text style={styles.milestoneTitle}>Baptized</Text>
                    <Text style={styles.milestoneDate}>
                      {new Date(profile.baptised_on).toLocaleDateString('en-US', {
                        month: 'long',
                        year: 'numeric',
                      })}
                    </Text>
                  </View>
                </View>
              )}

              {profile.dna_completed && (
                <View style={styles.milestoneCard}>
                  <Text style={styles.milestoneEmoji}>📖</Text>
                  <View style={styles.milestoneContent}>
                    <Text style={styles.milestoneTitle}>DNA Completed</Text>
                    <Text style={styles.milestoneDate}>
                      {new Date(profile.dna_completed).toLocaleDateString('en-US', {
                        month: 'long',
                        year: 'numeric',
                      })}
                    </Text>
                  </View>
                </View>
              )}

              {profile.first_served_on && (
                <View style={styles.milestoneCard}>
                  <Text style={styles.milestoneEmoji}>🤝</Text>
                  <View style={styles.milestoneContent}>
                    <Text style={styles.milestoneTitle}>First Time Serving</Text>
                    <Text style={styles.milestoneDate}>
                      {new Date(profile.first_served_on).toLocaleDateString('en-US', {
                        month: 'long',
                        year: 'numeric',
                      })}
                    </Text>
                  </View>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Achievements */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Achievements</Text>
          <View style={styles.achievementsGrid}>
            {/* Example achievements - in production these would come from backend */}
            <View style={styles.achievementCard}>
              <Text style={styles.achievementEmoji}>🔥</Text>
              <Text style={styles.achievementLabel}>7-Week Streak</Text>
            </View>
            <View style={styles.achievementCard}>
              <Text style={styles.achievementEmoji}>📚</Text>
              <Text style={styles.achievementLabel}>Foundations</Text>
            </View>
            <View style={styles.achievementCard}>
              <Text style={styles.achievementEmoji}>🤝</Text>
              <Text style={styles.achievementLabel}>Team Member</Text>
            </View>
          </View>
        </View>

        {/* Profile Access */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.profileButton}
            onPress={() => navigation.navigate('Profile')}
          >
            <LinearGradient
              colors={[Colors.surface, Colors.surfaceLight]}
              style={styles.profileButtonGradient}
            >
              <Text style={styles.profileButtonEmoji}>👤</Text>
              <View style={styles.profileButtonContent}>
                <Text style={styles.profileButtonTitle}>Profile & Settings</Text>
                <Text style={styles.profileButtonSubtitle}>Manage your account</Text>
              </View>
              <Text style={styles.profileButtonArrow}>→</Text>
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
  section: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  progressCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  progressGradient: {
    padding: Spacing.lg,
    alignItems: 'center',
  },
  progressTitle: {
    fontSize: FontSizes.xl,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  progressPercent: {
    fontSize: FontSizes.xxxl,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  progressBar: {
    width: '100%',
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 4,
    marginBottom: Spacing.sm,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.text,
    borderRadius: 4,
  },
  progressSteps: {
    fontSize: FontSizes.sm,
    color: Colors.text,
    opacity: 0.9,
  },
  nextStepCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  nextStepLabel: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  nextStepName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  nextStepDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  milestonesList: {
    gap: Spacing.md,
  },
  milestoneCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  milestoneEmoji: {
    fontSize: 32,
    marginRight: Spacing.md,
  },
  milestoneContent: {
    flex: 1,
  },
  milestoneTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  milestoneDate: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  achievementsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  achievementCard: {
    width: '31%',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    alignItems: 'center',
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  achievementEmoji: {
    fontSize: 32,
    marginBottom: Spacing.xs,
  },
  achievementLabel: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  profileButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: Spacing.md,
  },
  profileButtonGradient: {
    padding: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileButtonEmoji: {
    fontSize: 32,
    marginRight: Spacing.md,
  },
  profileButtonContent: {
    flex: 1,
  },
  profileButtonTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  profileButtonSubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  profileButtonArrow: {
    fontSize: FontSizes.lg,
    color: Colors.primary,
    marginLeft: Spacing.sm,
  },
});

