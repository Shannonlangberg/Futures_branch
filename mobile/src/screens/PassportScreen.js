import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function PathwayScreen() {
  const [pathway, setPathway] = useState(null);
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
        const profileData = await ApiService.getPersonProfile(userObj.email);
        
        if (profileData && profileData.profile && profileData.profile.pathway) {
          setPathway(profileData.profile.pathway);
        }
      }
    } catch (error) {
      console.error('Error loading pathway:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
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
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Pathway</Text>
          <Text style={styles.headerSubtitle}>Your discipleship journey</Text>
        </View>

        {pathway && (
          <>
            {/* Progress Circle */}
            <View style={styles.progressSection}>
              <View style={styles.progressCircle}>
                <LinearGradient
                  colors={['#6366f1', '#8b5cf6']}
                  style={styles.progressGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <View style={styles.progressInner}>
                    <Text style={styles.progressPercent}>{pathway.progress_percentage || 0}%</Text>
                    <Text style={styles.progressLabel}>Complete</Text>
                  </View>
                </LinearGradient>
              </View>
              <Text style={styles.pathwayName}>{pathway.pathway_name || 'Your Journey'}</Text>
              <Text style={styles.progressSteps}>
                {pathway.completed_steps || 0} of {pathway.total_steps || 0} steps completed
              </Text>
            </View>

            {/* Journey Path */}
            <View style={styles.journeyPath}>
              {pathway.steps && pathway.steps.map((step, index) => {
                const isCompleted = step.is_completed;
                const isNext = pathway.current_step_id === step.id && !isCompleted;
                const isLast = index === pathway.steps.length - 1;
                
                return (
                  <View key={step.id || index} style={styles.stepContainer}>
                    {/* Connecting Line */}
                    {!isLast && (
                      <View style={[
                        styles.connector,
                        isCompleted ? styles.connectorActive : styles.connectorInactive
                      ]} />
                    )}
                    
                    {/* Step Circle */}
                    <View style={styles.stepCircleContainer}>
                      {isCompleted ? (
                        <LinearGradient
                          colors={['#10b981', '#059669']}
                          style={styles.stepCircle}
                        >
                          <Text style={styles.stepCheckmark}>✓</Text>
                        </LinearGradient>
                      ) : isNext ? (
                        <LinearGradient
                          colors={['#6366f1', '#8b5cf6']}
                          style={[styles.stepCircle, styles.stepCircleNext]}
                        >
                          <Text style={styles.stepNumber}>{step.step_order}</Text>
                        </LinearGradient>
                      ) : (
                        <View style={[styles.stepCircle, styles.stepCircleInactive]}>
                          <Text style={[styles.stepNumber, styles.stepNumberInactive]}>{step.step_order}</Text>
                        </View>
                      )}
                    </View>
                    
                    {/* Step Card */}
                    <View style={[
                      styles.stepCard,
                      isCompleted && styles.stepCardCompleted,
                      isNext && styles.stepCardNext,
                    ]}>
                      {isNext && (
                        <View style={styles.nextBadge}>
                          <Text style={styles.nextBadgeText}>NEXT STEP</Text>
                        </View>
                      )}
                      
                      <Text style={[
                        styles.stepName,
                        isCompleted && styles.stepNameCompleted,
                        isNext && styles.stepNameNext,
                      ]}>
                        {step.step_name}
                      </Text>
                      
                      {isCompleted && step.completed_at && (
                        <View style={styles.completedInfo}>
                          <Text style={styles.completedIcon}>✓</Text>
                          <Text style={styles.completedDate}>
                            Completed {formatDate(step.completed_at)}
                          </Text>
                        </View>
                      )}
                    </View>
                  </View>
                );
              })}
            </View>
          </>
        )}

        {!pathway && !loading && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>🗺️</Text>
            <Text style={styles.emptyTitle}>No Pathway Data</Text>
            <Text style={styles.emptyText}>
              Your pathway information will appear here once it's available.
            </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
  },
  gradient: {
    flex: 1,
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.xl,
  },
  header: {
    marginBottom: Spacing.xl,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  headerSubtitle: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  progressSection: {
    alignItems: 'center',
    marginBottom: Spacing.xxl,
  },
  progressCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    marginBottom: Spacing.lg,
  },
  progressGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 80,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 8,
  },
  progressInner: {
    width: '100%',
    height: '100%',
    borderRadius: 72,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressPercent: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  progressLabel: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  pathwayName: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  progressSteps: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.5)',
  },
  journeyPath: {
    paddingVertical: Spacing.md,
  },
  stepContainer: {
    marginBottom: Spacing.xl,
    position: 'relative',
  },
  connector: {
    position: 'absolute',
    left: 30,
    top: 60,
    width: 3,
    height: 60,
    zIndex: 0,
  },
  connectorActive: {
    backgroundColor: '#10b981',
  },
  connectorInactive: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  stepCircleContainer: {
    marginBottom: Spacing.md,
    zIndex: 10,
  },
  stepCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  stepCircleNext: {
    shadowColor: '#6366f1',
    shadowOpacity: 0.5,
  },
  stepCircleInactive: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  stepCheckmark: {
    fontSize: 32,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  stepNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  stepNumberInactive: {
    color: 'rgba(255, 255, 255, 0.4)',
  },
  stepCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: Spacing.lg,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  stepCardCompleted: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  stepCardNext: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    borderColor: 'rgba(99, 102, 241, 0.4)',
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  nextBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(99, 102, 241, 0.3)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: Spacing.sm,
  },
  nextBadgeText: {
    fontSize: FontSizes.xs,
    fontWeight: '700',
    color: '#a5b4fc',
    letterSpacing: 0.5,
  },
  stepName: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  stepNameCompleted: {
    color: '#10b981',
  },
  stepNameNext: {
    color: '#ffffff',
  },
  completedInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  completedIcon: {
    fontSize: 16,
    color: '#10b981',
    marginRight: Spacing.xs,
  },
  completedDate: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.5)',
  },
  emptyState: {
    alignItems: 'center',
    padding: Spacing.xxl,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    marginTop: Spacing.xxl,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: Spacing.lg,
  },
  emptyTitle: {
    fontSize: FontSizes.xl,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.sm,
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
    lineHeight: 22,
  },
});

