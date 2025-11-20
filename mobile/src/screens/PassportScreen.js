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
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [connectGroups, setConnectGroups] = useState([]);
  const [loadingGroups, setLoadingGroups] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        // Load profile (this includes pathway data)
        try {
          const profileData = await ApiService.getPersonProfile(userObj.email);
          console.log('Profile Data:', JSON.stringify(profileData, null, 2));
          
          if (profileData && profileData.profile) {
            setProfile(profileData.profile);
            
            // Pathway data is included in profile response
            if (profileData.profile.pathway) {
              console.log('Pathway found in profile:', profileData.profile.pathway);
              setPathway(profileData.profile.pathway);
            } else {
              console.warn('No pathway data in profile response');
            }
          }
        } catch (profileError) {
          console.error('Error loading profile:', profileError);
          // Fallback: try pathway endpoint
          try {
            const pathwayData = await ApiService.getMyPathway(userObj.email);
            if (pathwayData?.pathway) {
              setPathway(pathwayData.pathway);
            }
          } catch (pathwayError) {
            console.warn('Error loading pathway:', pathwayError);
          }
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

  const loadConnectGroups = async () => {
    try {
      setLoadingGroups(true);
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        const profileData = await ApiService.getPersonProfile(userObj.email);
        if (profileData?.profile?.campus) {
          const groupsData = await ApiService.getConnectGroups(profileData.profile.campus);
          setConnectGroups(groupsData?.groups || []);
        }
      }
    } catch (error) {
      console.error('Error loading connect groups:', error);
      Alert.alert('Error', 'Failed to load connect groups');
    } finally {
      setLoadingGroups(false);
    }
  };

  const handleAssignConnectGroup = async (group) => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        await ApiService.joinGroup(userObj.email, group.id);
        Alert.alert('Success', `You've been assigned to ${group.name}`);
        setShowConnectModal(false);
        loadData(); // Reload pathway to show updated step
      }
    } catch (error) {
      console.error('Error assigning connect group:', error);
      Alert.alert('Error', 'Failed to assign connect group');
    }
  };

  const handleCompleteStep = async (step) => {
    if (!pathway?.id) return;
    
    try {
      await ApiService.completePathwayStep(pathway.id, step.id);
      Alert.alert('Success', `${step.step_name} marked as complete!`);
      loadData(); // Reload pathway
    } catch (error) {
      console.error('Error completing step:', error);
      Alert.alert('Error', 'Failed to complete step');
    }
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
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>My Pathway</Text>
          <Text style={styles.headerSubtitle}>Your discipleship journey</Text>
        </View>

        {/* Progress Summary */}
        {pathway && (
          <View style={styles.section}>
            <View style={styles.progressSummary}>
              <Text style={styles.progressPercent}>{pathway.progress_percentage || 0}%</Text>
              <Text style={styles.progressLabel}>Journey Complete</Text>
              <Text style={styles.progressSteps}>
                {pathway.completed_steps || 0} of {pathway.total_steps || 0} steps
              </Text>
            </View>

            {/* Visual Journey Path */}
            {pathway.steps && pathway.steps.length > 0 && (
              <View style={styles.journeyPath}>
                <Text style={styles.journeyPathTitle}>🗺️ Your Discipleship Journey</Text>
                
                {pathway.steps.map((step, index) => {
                  const isCompleted = step.is_completed;
                  const isCurrent = pathway.current_step_id === step.id && !isCompleted;
                  const isNextStep = isCurrent;
                  const isLast = index === pathway.steps.length - 1;
                  
                  return (
                    <View key={step.id || index}>
                      {/* Step Node */}
                      <View style={[
                        styles.stepNode,
                        index % 2 === 0 ? styles.stepNodeLeft : styles.stepNodeRight
                      ]}>
                        {/* Connector Line (except for last step) */}
                        {!isLast && (
                          <View style={[
                            styles.connector,
                            isCompleted ? styles.connectorCompleted : styles.connectorIncomplete,
                            index % 2 === 0 ? styles.connectorCurveRight : styles.connectorCurveLeft
                          ]} />
                        )}
                        
                        {/* Circle */}
                        <View style={[
                          styles.stepCircle,
                          isCompleted && styles.stepCircleCompleted,
                          isNextStep && styles.stepCircleNext,
                        ]}>
                          {isCompleted ? (
                            <Text style={styles.stepCircleCheck}>✓</Text>
                          ) : (
                            <Text style={styles.stepCircleNumber}>{step.step_order}</Text>
                          )}
                        </View>
                        
                        {/* Step Info Card */}
                        <View style={[
                          styles.stepInfoCard,
                          isNextStep && styles.stepInfoCardNext,
                          isCompleted && styles.stepInfoCardCompleted,
                        ]}>
                          <Text style={[
                            styles.stepInfoName,
                            isCompleted && styles.stepInfoNameCompleted
                          ]}>
                            {step.step_name}
                          </Text>
                          
                          {isCompleted && step.completed_at && (
                            <Text style={styles.stepInfoDate}>
                              ✓ {formatDate(step.completed_at)}
                            </Text>
                          )}
                          
                          {isNextStep && (
                            <View style={styles.nextStepBadge}>
                              <Text style={styles.nextStepText}>NEXT STEP →</Text>
                            </View>
                          )}
                        </View>
                      </View>
                    </View>
                  );
                })}
              </View>
            )}
          </View>
        )}

        {/* Empty state if no pathway */}
        {!pathway && !loading && (
          <View style={styles.section}>
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateEmoji}>🗺️</Text>
              <Text style={styles.emptyStateTitle}>No Pathway Data</Text>
              <Text style={styles.emptyStateText}>
                Your pathway information will appear here once it's available.
              </Text>
            </View>
          </View>
        )}
        
        {/* Bottom Spacing */}
        <View style={{ height: 100 }} />
      </LinearGradient>

      {/* Connect Group Assignment Modal */}
      <Modal
        visible={showConnectModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowConnectModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Assign Connect Group</Text>
              <TouchableOpacity
                onPress={() => setShowConnectModal(false)}
                style={styles.modalCloseButton}
              >
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>
            
            {loadingGroups ? (
              <ActivityIndicator size="large" color={Colors.primary} style={styles.modalLoading} />
            ) : connectGroups.length === 0 ? (
              <Text style={styles.modalEmptyText}>No connect groups available</Text>
            ) : (
              <ScrollView style={styles.modalScrollView}>
                {connectGroups.map((group) => (
                  <TouchableOpacity
                    key={group.id}
                    style={styles.groupItem}
                    onPress={() => handleAssignConnectGroup(group)}
                  >
                    <Text style={styles.groupName}>{group.name}</Text>
                    {group.description && (
                      <Text style={styles.groupDescription}>{group.description}</Text>
                    )}
                    {group.campus && (
                      <Text style={styles.groupCampus}>{group.campus}</Text>
                    )}
                  </TouchableOpacity>
                ))}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
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
  progressSummary: {
    alignItems: 'center',
    padding: Spacing.lg,
    backgroundColor: Colors.surface,
    borderRadius: 16,
    marginBottom: Spacing.xl,
  },
  progressPercent: {
    fontSize: 56,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: Spacing.xs,
  },
  progressLabel: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  progressSteps: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  journeyPath: {
    paddingVertical: Spacing.md,
  },
  journeyPathTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xl,
    textAlign: 'center',
  },
  stepNode: {
    position: 'relative',
    marginBottom: Spacing.xl,
    paddingHorizontal: Spacing.md,
  },
  stepNodeLeft: {
    alignItems: 'flex-start',
  },
  stepNodeRight: {
    alignItems: 'flex-end',
  },
  connector: {
    position: 'absolute',
    top: 60,
    width: 4,
    height: 80,
    left: '50%',
    marginLeft: -2,
  },
  connectorCompleted: {
    backgroundColor: Colors.success,
  },
  connectorIncomplete: {
    backgroundColor: Colors.border,
  },
  connectorCurveRight: {
    transform: [{ rotate: '10deg' }],
  },
  connectorCurveLeft: {
    transform: [{ rotate: '-10deg' }],
  },
  stepCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.surface,
    borderWidth: 3,
    borderColor: Colors.border,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.sm,
    zIndex: 10,
  },
  stepCircleCompleted: {
    backgroundColor: Colors.success,
    borderColor: Colors.success,
  },
  stepCircleNext: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  stepCircleCheck: {
    fontSize: 32,
    color: '#fff',
    fontWeight: 'bold',
  },
  stepCircleNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.text,
  },
  stepInfoCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    maxWidth: '75%',
  },
  stepInfoCardCompleted: {
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
    borderColor: Colors.success,
  },
  stepInfoCardNext: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 6,
  },
  stepInfoName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  stepInfoNameCompleted: {
    color: Colors.success,
  },
  stepInfoDate: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  nextStepBadge: {
    marginTop: Spacing.sm,
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  nextStepText: {
    fontSize: FontSizes.sm,
    fontWeight: '600',
    color: '#fff',
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
  stepsSection: {
    marginTop: Spacing.md,
  },
  stepsTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  stepCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  currentStepCard: {
    backgroundColor: Colors.primary + '20',
    borderColor: Colors.primary,
    borderWidth: 2,
  },
  completedStepCard: {
    opacity: 0.8,
  },
  stepLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  stepNumberText: {
    fontSize: FontSizes.md,
    fontWeight: 'bold',
    color: Colors.text,
  },
  completedIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#10B981',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  checkmark: {
    fontSize: FontSizes.md,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  stepContent: {
    flex: 1,
  },
  stepName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  completedStepName: {
    color: '#10B981',
  },
  stepDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  completedDate: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  stepActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  currentBadge: {
    fontSize: FontSizes.xs,
    fontWeight: '600',
    color: Colors.primary,
    backgroundColor: Colors.primary + '20',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
  },
  assignButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 8,
  },
  assignButtonText: {
    color: Colors.text,
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
  completeButton: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  completeButtonText: {
    color: Colors.text,
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
    paddingBottom: Spacing.xl,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
  },
  modalCloseButton: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseText: {
    fontSize: FontSizes.xl,
    color: Colors.textSecondary,
  },
  modalScrollView: {
    maxHeight: 400,
  },
  modalLoading: {
    padding: Spacing.xl,
  },
  modalEmptyText: {
    padding: Spacing.xl,
    textAlign: 'center',
    color: Colors.textSecondary,
  },
  groupItem: {
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  groupName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  groupDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  groupCampus: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
  },
  emptyState: {
    alignItems: 'center',
    padding: Spacing.xl,
    backgroundColor: Colors.surface,
    borderRadius: 16,
  },
  emptyStateEmoji: {
    fontSize: 48,
    marginBottom: Spacing.md,
  },
  emptyStateTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  emptyStateText: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
});

