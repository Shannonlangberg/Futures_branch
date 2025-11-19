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

        // Load profile (this includes engagement data)
        try {
          const profileData = await ApiService.getPersonProfile(userObj.email);
          if (profileData) {
            setProfile(profileData);
            // Pathway data might be included in profile
            if (profileData.pathway) {
              setPathway(profileData.pathway);
            }
          }
        } catch (profileError) {
          console.warn('Error loading profile, trying pathway separately:', profileError);
          // Fallback: try pathway endpoint if it exists
          try {
            const pathwayData = await ApiService.getMyPathway(userObj.email);
            if (pathwayData?.pathway) {
              setPathway(pathwayData.pathway);
            }
          } catch (pathwayError) {
            console.warn('Error loading pathway:', pathwayError);
            // Continue without pathway data - app won't crash
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

            {/* All Steps */}
            {pathway.pathway?.steps && pathway.pathway.steps.length > 0 && (
              <View style={styles.stepsSection}>
                <Text style={styles.stepsTitle}>All Steps:</Text>
                {pathway.pathway.steps.map((step, index) => {
                  const isCompleted = step.is_completed;
                  const isCurrent = pathway.current_step_id === step.id && !isCompleted;
                  // Check both milestone_type and step name to identify connect group step
                  const isConnectGroup = step.milestone_type === 'group_join' || 
                                         (step.step_name && step.step_name.toLowerCase().includes('connect group'));
                  // Show Assign button for connect group step if not completed, even if not current
                  const showAssignButton = isConnectGroup && !isCompleted;
                  
                  // Debug logging
                  if (step.step_name && step.step_name.toLowerCase().includes('connect')) {
                    console.log('Connect Group Step Debug:', {
                      step_name: step.step_name,
                      milestone_type: step.milestone_type,
                      isConnectGroup,
                      isCompleted,
                      showAssignButton,
                      isCurrent
                    });
                  }
                  
                  return (
                    <View
                      key={step.id || index}
                      style={[
                        styles.stepCard,
                        isCurrent && styles.currentStepCard,
                        isCompleted && styles.completedStepCard,
                      ]}
                    >
                      <View style={styles.stepLeft}>
                        {isCompleted ? (
                          <View style={styles.completedIcon}>
                            <Text style={styles.checkmark}>✓</Text>
                          </View>
                        ) : (
                          <View style={styles.stepNumber}>
                            <Text style={styles.stepNumberText}>{step.step_order}</Text>
                          </View>
                        )}
                        <View style={styles.stepContent}>
                          <Text style={[styles.stepName, isCompleted && styles.completedStepName]}>
                            {step.step_name}
                          </Text>
                          {step.step_description && (
                            <Text style={styles.stepDescription}>{step.step_description}</Text>
                          )}
                          {isCompleted && step.completed_at && (
                            <Text style={styles.completedDate}>
                              Completed: {formatDate(step.completed_at)}
                            </Text>
                          )}
                        </View>
                      </View>
                      {!isCompleted && (
                        <View style={styles.stepActions}>
                          {isCurrent && !showAssignButton && (
                            <Text style={styles.currentBadge}>Current</Text>
                          )}
                          {showAssignButton ? (
                            <TouchableOpacity
                              style={styles.assignButton}
                              onPress={() => {
                                loadConnectGroups();
                                setShowConnectModal(true);
                              }}
                            >
                              <Text style={styles.assignButtonText}>Assign</Text>
                            </TouchableOpacity>
                          ) : !isConnectGroup ? (
                            <TouchableOpacity
                              style={styles.completeButton}
                              onPress={() => handleCompleteStep(step)}
                            >
                              <Text style={styles.completeButtonText}>Complete</Text>
                            </TouchableOpacity>
                          ) : isCurrent ? (
                            <Text style={styles.currentBadge}>Current</Text>
                          ) : null}
                        </View>
                      )}
                      {/* Debug: Show step info if it's connect group related */}
                      {step.step_name && step.step_name.toLowerCase().includes('connect') && __DEV__ && (
                        <Text style={{color: 'red', fontSize: 10}}>
                          Debug: milestone_type={step.milestone_type}, isConnectGroup={isConnectGroup ? 'true' : 'false'}, isCompleted={isCompleted ? 'true' : 'false'}
                        </Text>
                      )}
                    </View>
                  );
                })}
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
});

