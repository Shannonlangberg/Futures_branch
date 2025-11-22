import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Modal,
  Alert,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Linking } from 'react-native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function PathwayScreen() {
  const navigation = useNavigation();
  const [pathway, setPathway] = useState(null);
  const [streaks, setStreaks] = useState([]);
  const [nextSteps, setNextSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStep, setSelectedStep] = useState(null);
  const [showStepModal, setShowStepModal] = useState(false);
  const [completingStep, setCompletingStep] = useState(false);
  const [celebrationAnim] = useState(new Animated.Value(0));
  const [pulseAnim] = useState(new Animated.Value(1));

  useEffect(() => {
    loadData();
  }, []);

  // Golden pulsing animation for current step
  useEffect(() => {
    const pulseAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.15,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    );
    pulseAnimation.start();
    return () => pulseAnimation.stop();
  }, [pulseAnim]);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        const profileData = await ApiService.getPersonProfile(userObj.email);
        
        if (profileData && profileData.profile) {
          // Try journey first, fall back to pathway for backward compatibility
          const journeyData = profileData.profile.journey || profileData.profile.pathway;
          if (journeyData) {
            setPathway(journeyData);
          }
          if (profileData.profile.streaks) {
            setStreaks(profileData.profile.streaks);
          }
          if (profileData.profile.next_steps) {
            setNextSteps(profileData.profile.next_steps);
          }
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

  const handleNextStepAction = (step) => {
    if (step.action === 'pathway') {
      // Already on pathway screen
      return;
    } else if (step.action === 'groups') {
      navigation.navigate('Groups');
    } else if (step.action === 'tv') {
      navigation.navigate('TVHome');
    } else if (step.action === 'contact') {
      // Could open contact form or phone
      console.log('Contact action:', step);
    }
  };

  const handleStepPress = (step) => {
    setSelectedStep(step);
    setShowStepModal(true);
  };

  const handleCompleteStep = async () => {
    if (!selectedStep || completingStep) return;
    
    Alert.alert(
      'Complete Step',
      `Mark "${selectedStep.step_name}" as complete?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Complete',
          onPress: async () => {
            try {
              setCompletingStep(true);
              const userData = await AsyncStorage.getItem('userData');
              if (!userData) {
                Alert.alert('Error', 'Please log in again');
                return;
              }
              
              const userObj = JSON.parse(userData);
              const result = await ApiService.completePathwayStep(
                userObj.email,
                selectedStep.id
              );
              
              if (result.pathway) {
                setPathway(result.pathway);
                // Trigger celebration animation
                Animated.sequence([
                  Animated.timing(celebrationAnim, {
                    toValue: 1,
                    duration: 300,
                    useNativeDriver: true,
                  }),
                  Animated.delay(1500),
                  Animated.timing(celebrationAnim, {
                    toValue: 0,
                    duration: 300,
                    useNativeDriver: true,
                  }),
                ]).start();
                
                setShowStepModal(false);
                setSelectedStep(null);
                
                // Reload data to get updated streaks/next steps
                setTimeout(() => {
                  loadData();
                }, 500);
              }
            } catch (error) {
              console.error('Error completing step:', error);
              Alert.alert('Error', error.response?.data?.error || 'Failed to complete step');
            } finally {
              setCompletingStep(false);
            }
          },
        },
      ]
    );
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

        {/* Growth Streaks */}
        {streaks && streaks.length > 0 && (
          <View style={styles.streaksSection}>
            <Text style={styles.sectionTitle}>Growth Streaks</Text>
            <View style={styles.streaksGrid}>
              {streaks.map((streak, index) => (
                <View key={index} style={styles.streakCard}>
                  <LinearGradient
                    colors={['rgba(99, 102, 241, 0.2)', 'rgba(139, 92, 246, 0.2)']}
                    style={styles.streakGradient}
                  >
                    <Text style={styles.streakEmoji}>{streak.emoji}</Text>
                    <Text style={styles.streakCount}>{streak.count}</Text>
                    <Text style={styles.streakLabel}>{streak.label}</Text>
                    {streak.message && (
                      <Text style={styles.streakMessage}>{streak.message}</Text>
                    )}
                  </LinearGradient>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Next Steps */}
        {nextSteps && nextSteps.length > 0 && (
          <View style={styles.nextStepsSection}>
            <Text style={styles.sectionTitle}>Next Steps</Text>
            {nextSteps.map((step, index) => (
              <TouchableOpacity
                key={index}
                style={styles.nextStepCard}
                onPress={() => handleNextStepAction(step)}
              >
                <View style={styles.nextStepContent}>
                  <View style={styles.nextStepHeader}>
                    <Text style={styles.nextStepTitle}>{step.title}</Text>
                    {step.priority === 'high' && (
                      <View style={styles.priorityBadge}>
                        <Text style={styles.priorityText}>Recommended</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.nextStepDescription}>{step.description}</Text>
                </View>
                <Text style={styles.nextStepArrow}>→</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

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
                    <Text style={styles.progressPercent}>{Math.round(pathway.progress_percentage || 0)}%</Text>
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
              {pathway.pathway && pathway.pathway.steps && pathway.pathway.steps.map((step, index) => {
                const isCompleted = step.is_completed;
                const isNext = pathway.current_step_id === step.id && !isCompleted;
                const isLast = index === pathway.pathway.steps.length - 1;
                
                return (
                  <View key={step.id || index} style={styles.stepContainer}>
                    {/* Left Column: Circle + Connector */}
                    <View style={styles.stepLeftColumn}>
                      {/* Step Circle */}
                      {isCompleted ? (
                        <LinearGradient
                          colors={['#10b981', '#059669']}
                          style={styles.stepCircle}
                        >
                          <Text style={styles.stepCheckmark}>✓</Text>
                        </LinearGradient>
                      ) : isNext ? (
                        <Animated.View
                          style={[
                            {
                              transform: [{ scale: pulseAnim }],
                            },
                          ]}
                        >
                          {/* Golden glow rings for pulsing effect */}
                          <Animated.View
                            style={[
                              styles.goldenGlow,
                              {
                                opacity: pulseAnim.interpolate({
                                  inputRange: [1, 1.15],
                                  outputRange: [0.3, 0.6],
                                }),
                                transform: [{ scale: pulseAnim }],
                              },
                            ]}
                          />
                          <Animated.View
                            style={[
                              styles.goldenGlowInner,
                              {
                                opacity: pulseAnim.interpolate({
                                  inputRange: [1, 1.15],
                                  outputRange: [0.5, 0.8],
                                }),
                                transform: [{ scale: pulseAnim }],
                              },
                            ]}
                          />
                          <LinearGradient
                            colors={['#fbbf24', '#f59e0b', '#d97706']}
                            style={[styles.stepCircle, styles.stepCircleNext]}
                          >
                            <Text style={styles.stepNumber}>{step.step_order}</Text>
                          </LinearGradient>
                        </Animated.View>
                      ) : (
                        <View style={[styles.stepCircle, styles.stepCircleInactive]}>
                          <Text style={[styles.stepNumber, styles.stepNumberInactive]}>{step.step_order}</Text>
                        </View>
                      )}
                      
                      {/* Connecting Line (below circle) */}
                      {!isLast && (
                        <View style={[
                          styles.connector,
                          isCompleted ? styles.connectorActive : styles.connectorInactive
                        ]} />
                      )}
                    </View>
                    
                    {/* Right Column: Step Card */}
                    <View style={styles.stepRightColumn}>
                      <TouchableOpacity
                        style={[
                          styles.stepCard,
                          isCompleted && styles.stepCardCompleted,
                          isNext && styles.stepCardNext,
                        ]}
                        onPress={() => handleStepPress(step)}
                        activeOpacity={0.7}
                      >
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
                        
                        {step.step_description && (
                          <Text style={styles.stepDescription} numberOfLines={2}>
                            {step.step_description}
                          </Text>
                        )}
                        
                        {isCompleted && step.completed_at && (
                          <View style={styles.completedInfo}>
                            <Text style={styles.completedIcon}>✓</Text>
                            <Text style={styles.completedDate}>
                              Completed {formatDate(step.completed_at)}
                            </Text>
                          </View>
                        )}
                        
                        {!isCompleted && (
                          <View style={styles.stepActions}>
                            <View style={styles.tapHint}>
                              <Text style={styles.tapHintText}>Tap to view details →</Text>
                            </View>
                            {isNext && (
                              <TouchableOpacity
                                style={styles.quickCompleteButton}
                                onPress={(e) => {
                                  e.stopPropagation();
                                  // Set selected step and complete it directly
                                  setSelectedStep(step);
                                  // Small delay to ensure state is set
                                  setTimeout(() => {
                                    Alert.alert(
                                      'Complete Step',
                                      `Mark "${step.step_name}" as complete?`,
                                      [
                                        { text: 'Cancel', style: 'cancel' },
                                        {
                                          text: 'Complete',
                                          onPress: async () => {
                                            try {
                                              setCompletingStep(true);
                                              const userData = await AsyncStorage.getItem('userData');
                                              if (!userData) {
                                                Alert.alert('Error', 'Please log in again');
                                                setCompletingStep(false);
                                                return;
                                              }
                                              
                                              const userObj = JSON.parse(userData);
                                              const result = await ApiService.completePathwayStep(
                                                userObj.email,
                                                step.id
                                              );
                                              
                                              if (result.pathway) {
                                                setPathway(result.pathway);
                                                // Trigger celebration animation
                                                Animated.sequence([
                                                  Animated.timing(celebrationAnim, {
                                                    toValue: 1,
                                                    duration: 300,
                                                    useNativeDriver: true,
                                                  }),
                                                  Animated.delay(1500),
                                                  Animated.timing(celebrationAnim, {
                                                    toValue: 0,
                                                    duration: 300,
                                                    useNativeDriver: true,
                                                  }),
                                                ]).start();
                                                
                                                setSelectedStep(null);
                                                
                                                // Reload data to get updated streaks/next steps
                                                setTimeout(() => {
                                                  loadData();
                                                }, 500);
                                              }
                                            } catch (error) {
                                              console.error('Error completing step:', error);
                                              Alert.alert('Error', error.response?.data?.error || 'Failed to complete step');
                                            } finally {
                                              setCompletingStep(false);
                                            }
                                          },
                                        },
                                      ]
                                    );
                                  }, 50);
                                }}
                                activeOpacity={0.7}
                              >
                                <LinearGradient
                                  colors={['#10b981', '#059669']}
                                  style={styles.quickCompleteGradient}
                                >
                                  <Text style={styles.quickCompleteText}>✓ Complete</Text>
                                </LinearGradient>
                              </TouchableOpacity>
                            )}
                          </View>
                        )}
                      </TouchableOpacity>
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

      {/* Step Detail Modal */}
      <Modal
        visible={showStepModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => {
          setShowStepModal(false);
          setSelectedStep(null);
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {selectedStep && (
              <>
                <View style={styles.modalHeader}>
                  <View style={styles.modalStepNumber}>
                    <Text style={styles.modalStepNumberText}>{selectedStep.step_order}</Text>
                  </View>
                  <View style={styles.modalHeaderText}>
                    <Text style={styles.modalTitle}>{selectedStep.step_name}</Text>
                    {selectedStep.is_completed && selectedStep.completed_at && (
                      <Text style={styles.modalCompletedDate}>
                        Completed {formatDate(selectedStep.completed_at)}
                      </Text>
                    )}
                  </View>
                  <TouchableOpacity
                    onPress={() => {
                      setShowStepModal(false);
                      setSelectedStep(null);
                    }}
                    style={styles.modalCloseButton}
                  >
                    <Text style={styles.modalCloseText}>✕</Text>
                  </TouchableOpacity>
                </View>

                <ScrollView style={styles.modalBody}>
                  {selectedStep.step_description && (
                    <View style={styles.modalDescription}>
                      <Text style={styles.modalDescriptionText}>
                        {selectedStep.step_description}
                      </Text>
                    </View>
                  )}

                  {selectedStep.milestone_type && (
                    <View style={styles.modalMilestone}>
                      <Text style={styles.modalMilestoneLabel}>Milestone Type:</Text>
                      <Text style={styles.modalMilestoneValue}>
                        {selectedStep.milestone_type.replace('_', ' ').toUpperCase()}
                      </Text>
                    </View>
                  )}

                  {/* Step Actions */}
                  {selectedStep.step_actions && selectedStep.step_actions.length > 0 && (
                    <View style={styles.modalActions}>
                      <Text style={styles.modalActionsTitle}>Actions to Complete:</Text>
                      {selectedStep.step_actions.map((action, index) => {
                        const getActionIcon = () => {
                          if (action.type === 'watch_video') return '▶️';
                          if (action.type === 'read_content') return '📖';
                          if (action.type === 'complete_task') return '✓';
                          return action.icon || '🔗';
                        };
                        
                        return (
                          <TouchableOpacity
                            key={index}
                            style={styles.actionCard}
                            onPress={() => {
                              if (action.url) {
                                Linking.openURL(action.url).catch(err => {
                                  Alert.alert('Error', 'Could not open link');
                                });
                              }
                            }}
                            activeOpacity={0.7}
                          >
                            <View style={styles.actionIcon}>
                              <Text style={styles.actionIconText}>{getActionIcon()}</Text>
                            </View>
                            <View style={styles.actionContent}>
                              <Text style={styles.actionTitle}>{action.title}</Text>
                              {action.url && (
                                <Text style={styles.actionLink} numberOfLines={1}>
                                  {action.url.length > 40 ? action.url.substring(0, 40) + '...' : action.url}
                                </Text>
                              )}
                            </View>
                            {action.url && (
                              <View style={styles.actionArrow}>
                                <Text style={styles.actionArrowText}>→</Text>
                              </View>
                            )}
                          </TouchableOpacity>
                        );
                      })}
                    </View>
                  )}

                  {selectedStep.is_completed ? (
                    <View style={styles.completedBadge}>
                      <Text style={styles.completedBadgeText}>✓ Step Completed</Text>
                    </View>
                  ) : (
                    <TouchableOpacity
                      style={[styles.completeButton, completingStep && styles.completeButtonDisabled]}
                      onPress={handleCompleteStep}
                      disabled={completingStep}
                    >
                      {completingStep ? (
                        <ActivityIndicator color="#ffffff" />
                      ) : (
                        <LinearGradient
                          colors={['#10b981', '#059669']}
                          style={styles.completeButtonGradient}
                        >
                          <Text style={styles.completeButtonText}>Mark as Complete</Text>
                        </LinearGradient>
                      )}
                    </TouchableOpacity>
                  )}
                </ScrollView>
              </>
            )}
          </View>
        </View>
      </Modal>

      {/* Celebration Animation */}
      {celebrationAnim._value > 0 && (
        <Animated.View
          style={[
            styles.celebration,
            {
              opacity: celebrationAnim,
              transform: [
                {
                  scale: celebrationAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.8, 1.2],
                  }),
                },
              ],
            },
          ]}
          pointerEvents="none"
        >
          <LinearGradient
            colors={['#10b981', '#059669']}
            style={styles.celebrationGradient}
          >
            <Text style={styles.celebrationEmoji}>🎉</Text>
            <Text style={styles.celebrationText}>Step Completed!</Text>
          </LinearGradient>
        </Animated.View>
      )}
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
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.md,
    marginTop: Spacing.lg,
  },
  // Growth Streaks Styles
  streaksSection: {
    marginBottom: Spacing.xl,
  },
  streaksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.md,
  },
  streakCard: {
    width: '48%',
    aspectRatio: 1,
    borderRadius: 16,
    overflow: 'hidden',
  },
  streakGradient: {
    flex: 1,
    padding: Spacing.md,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.3)',
    borderRadius: 16,
  },
  streakEmoji: {
    fontSize: 48,
    marginBottom: Spacing.sm,
  },
  streakCount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  streakLabel: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    marginBottom: Spacing.xs,
  },
  streakMessage: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
  },
  // Next Steps Styles
  nextStepsSection: {
    marginBottom: Spacing.xl,
  },
  nextStepCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: Spacing.lg,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    flexDirection: 'row',
    alignItems: 'center',
  },
  nextStepContent: {
    flex: 1,
  },
  nextStepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  nextStepTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    flex: 1,
  },
  priorityBadge: {
    backgroundColor: 'rgba(99, 102, 241, 0.3)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
  },
  priorityText: {
    fontSize: FontSizes.xs,
    fontWeight: '600',
    color: '#a5b4fc',
  },
  nextStepDescription: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: 20,
  },
  nextStepArrow: {
    fontSize: 24,
    color: 'rgba(255, 255, 255, 0.5)',
    marginLeft: Spacing.md,
  },
  // Pathway Styles
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
    flexDirection: 'row',
    marginBottom: Spacing.lg,
  },
  stepLeftColumn: {
    alignItems: 'center',
    width: 60,
    marginRight: Spacing.md,
  },
  stepRightColumn: {
    flex: 1,
    paddingTop: 10,
  },
  connector: {
    width: 3,
    flex: 1,
    marginTop: Spacing.xs,
    minHeight: 40,
  },
  connectorActive: {
    backgroundColor: '#10b981',
  },
  connectorInactive: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
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
    shadowColor: '#fbbf24',
    shadowOpacity: 0.8,
    shadowRadius: 12,
    elevation: 12,
  },
  goldenGlow: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fbbf24',
    opacity: 0.3,
    top: -10,
    left: -10,
  },
  goldenGlowInner: {
    position: 'absolute',
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#f59e0b',
    opacity: 0.5,
    top: -5,
    left: -5,
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
  stepDescription: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: Spacing.xs,
    lineHeight: 18,
  },
  tapHint: {
    marginTop: Spacing.sm,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  tapHintText: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.4)',
    fontStyle: 'italic',
  },
  stepActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: Spacing.sm,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  quickCompleteButton: {
    borderRadius: 8,
    overflow: 'hidden',
  },
  quickCompleteGradient: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  quickCompleteText: {
    fontSize: FontSizes.xs,
    fontWeight: '700',
    color: '#ffffff',
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1e293b',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    paddingBottom: 40,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  modalStepNumber: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(99, 102, 241, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  modalStepNumberText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#a5b4fc',
  },
  modalHeaderText: {
    flex: 1,
  },
  modalTitle: {
    fontSize: FontSizes.xl,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  modalCompletedDate: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.5)',
  },
  modalCloseButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseText: {
    fontSize: 20,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: 'bold',
  },
  modalBody: {
    padding: Spacing.lg,
  },
  modalDescription: {
    marginBottom: Spacing.lg,
  },
  modalDescriptionText: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 24,
  },
  modalMilestone: {
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    padding: Spacing.md,
    borderRadius: 12,
    marginBottom: Spacing.lg,
  },
  modalMilestoneLabel: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.5)',
    marginBottom: Spacing.xs,
  },
  modalMilestoneValue: {
    fontSize: FontSizes.sm,
    color: '#a5b4fc',
    fontWeight: '600',
  },
  completedBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    padding: Spacing.md,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  completedBadgeText: {
    fontSize: FontSizes.md,
    color: '#10b981',
    fontWeight: '600',
  },
  completeButton: {
    marginTop: Spacing.md,
    borderRadius: 16,
    overflow: 'hidden',
  },
  completeButtonDisabled: {
    opacity: 0.6,
  },
  completeButtonGradient: {
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  completeButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: '#ffffff',
  },
  // Actions Styles
  modalActions: {
    marginTop: Spacing.md,
    marginBottom: Spacing.md,
  },
  modalActionsTitle: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.md,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.2)',
  },
  actionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(99, 102, 241, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  actionIconText: {
    fontSize: 20,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  actionLink: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.5)',
  },
  actionArrow: {
    marginLeft: Spacing.sm,
  },
  actionArrowText: {
    fontSize: 20,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  // Celebration Styles
  celebration: {
    position: 'absolute',
    top: '30%',
    left: '50%',
    marginLeft: -100,
    width: 200,
    zIndex: 1000,
  },
  celebrationGradient: {
    padding: Spacing.lg,
    borderRadius: 20,
    alignItems: 'center',
    shadowColor: '#10b981',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 12,
  },
  celebrationEmoji: {
    fontSize: 48,
    marginBottom: Spacing.xs,
  },
  celebrationText: {
    fontSize: FontSizes.lg,
    fontWeight: '700',
    color: '#ffffff',
  },
});
