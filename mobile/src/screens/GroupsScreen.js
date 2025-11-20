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
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function GroupsScreen() {
  const navigation = useNavigation();
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [myGroups, setMyGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('browse'); // 'browse' or 'my'

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        // Load all groups
        const allGroups = await ApiService.getConnectGroups(userObj.campus);
        if (allGroups.groups) {
          setGroups(allGroups.groups);
        }

        // Load my groups
        const myGroupsData = await ApiService.getMyGroups(userObj.email);
        if (myGroupsData.groups) {
          setMyGroups(myGroupsData.groups);
        }
      }
    } catch (error) {
      console.error('Error loading groups:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  // Join functionality removed - groups are assigned by leaders only

  const handleAttendance = async (groupId, meetingDate, status) => {
    if (!user) {
      Alert.alert('Error', 'User not found.');
      return;
    }

    try {
      const result = await ApiService.submitGroupAttendance(
        user.email,
        groupId,
        meetingDate,
        status
      );
      
      if (result.success) {
        Alert.alert('Success', `Attendance recorded: ${status}`);
      } else {
        Alert.alert('Error', result.error || 'Failed to record attendance.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to record attendance. Please try again.');
    }
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
          <Text style={styles.headerTitle}>Connect Groups</Text>
          <Text style={styles.headerSubtitle}>Find your community</Text>
        </View>

        {/* Tabs */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'browse' && styles.tabActive]}
            onPress={() => setActiveTab('browse')}
          >
            <Text
              style={[styles.tabText, activeTab === 'browse' && styles.tabTextActive]}
            >
              Browse Groups
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'my' && styles.tabActive]}
            onPress={() => setActiveTab('my')}
          >
            <Text
              style={[styles.tabText, activeTab === 'my' && styles.tabTextActive]}
            >
              My Groups ({myGroups.length})
            </Text>
          </TouchableOpacity>
        </View>

        {/* Groups List */}
        {activeTab === 'browse' ? (
          groups.length > 0 ? (
            groups.map((group) => (
              <TouchableOpacity
                key={group.id}
                style={styles.groupCard}
                onPress={() => {
                  Alert.alert(
                    group.name,
                    `Leader: ${group.leader_name || 'N/A'}\nTime: ${group.meeting_day} ${group.meeting_time}\nLocation: ${group.location || 'TBA'}\n\nGroups are assigned by leaders. Contact your campus pastor to join a group.`
                  );
                }}
              >
                <View style={styles.groupContent}>
                  <Text style={styles.groupName}>{group.name}</Text>
                  <Text style={styles.groupDetails}>
                    {group.meeting_day} {group.meeting_time}
                  </Text>
                  {group.location && (
                    <Text style={styles.groupLocation}>📍 {group.location}</Text>
                  )}
                  <Text style={styles.groupMembers}>
                    👥 {group.member_count || 0} members
                  </Text>
                </View>
              </TouchableOpacity>
            ))
          ) : (
            <Text style={styles.emptyText}>No groups available</Text>
          )
        ) : (
          myGroups.length > 0 ? (
            myGroups.map((group) => {
              // Check if user is a leader
              const isLeader = user && (
                user.email?.toLowerCase() === group.leader_email?.toLowerCase() ||
                user.email?.toLowerCase() === group.co_leader_email?.toLowerCase() ||
                (group.leader_emails && group.leader_emails.includes(user.email?.toLowerCase()))
              );
              
              return (
                <View key={group.id} style={styles.groupCard}>
                  <View style={styles.groupContent}>
                    <View style={styles.groupHeader}>
                      <View style={styles.groupHeaderLeft}>
                        <Text style={styles.groupName}>{group.name}</Text>
                        <Text style={styles.groupDetails}>
                          {group.meeting_day} {group.meeting_time}
                        </Text>
                        {group.location && (
                          <Text style={styles.groupLocation}>📍 {group.location}</Text>
                        )}
                      </View>
                      {isLeader && (
                        <TouchableOpacity
                          style={styles.leaderBadge}
                          onPress={() => navigation.navigate('GroupLeaderPortal', { group })}
                        >
                          <Text style={styles.leaderBadgeText}>👑 Leader</Text>
                        </TouchableOpacity>
                      )}
                    </View>
                    
                    {/* Action Buttons */}
                    <View style={styles.groupActions}>
                      <TouchableOpacity
                        style={styles.actionButton}
                        onPress={() => navigation.navigate('GroupChat', { group })}
                      >
                        <Text style={styles.actionButtonText}>💬 Chat</Text>
                      </TouchableOpacity>
                      
                      {/* Attendance Buttons */}
                      <View style={styles.attendanceButtons}>
                        <TouchableOpacity
                          style={[styles.attendanceButton, styles.attendanceYes]}
                          onPress={() =>
                            handleAttendance(group.id, new Date().toISOString().split('T')[0], 'present')
                          }
                        >
                          <Text style={styles.attendanceButtonText}>I'm Coming ✓</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={[styles.attendanceButton, styles.attendanceNo]}
                          onPress={() =>
                            handleAttendance(group.id, new Date().toISOString().split('T')[0], 'absent')
                          }
                        >
                          <Text style={styles.attendanceButtonText}>Can't Make It</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  </View>
                </View>
              );
            })
          ) : (
            <Text style={styles.emptyText}>You're not in any groups yet</Text>
          )
        )}

        {/* Quick Access to Events */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.eventsButton}
            onPress={() => navigation.navigate('Events')}
          >
            <LinearGradient
              colors={[Colors.accent, Colors.primary]}
              style={styles.eventsButtonGradient}
            >
              <Text style={styles.eventsButtonEmoji}>📅</Text>
              <View style={styles.eventsButtonContent}>
                <Text style={styles.eventsButtonTitle}>Upcoming Events</Text>
                <Text style={styles.eventsButtonSubtitle}>RSVP for church events</Text>
              </View>
              <Text style={styles.eventsButtonArrow}>→</Text>
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
  tabs: {
    flexDirection: 'row',
    marginBottom: Spacing.lg,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.xs,
  },
  tab: {
    flex: 1,
    padding: Spacing.sm,
    alignItems: 'center',
    borderRadius: 8,
  },
  tabActive: {
    backgroundColor: Colors.primary,
  },
  tabText: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  tabTextActive: {
    color: Colors.text,
    fontWeight: '600',
  },
  groupCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  groupContent: {
    flex: 1,
  },
  groupName: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  groupDetails: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  groupLocation: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
    marginBottom: Spacing.sm,
  },
  groupMembers: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
  },
  attendanceButtons: {
    flexDirection: 'row',
    marginTop: Spacing.md,
    gap: Spacing.sm,
  },
  attendanceButton: {
    flex: 1,
    padding: Spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
  },
  attendanceYes: {
    backgroundColor: Colors.success,
  },
  attendanceNo: {
    backgroundColor: Colors.error,
  },
  attendanceButtonText: {
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
  eventsButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: Spacing.md,
  },
  eventsButtonGradient: {
    padding: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
  },
  eventsButtonEmoji: {
    fontSize: 32,
    marginRight: Spacing.md,
  },
  eventsButtonContent: {
    flex: 1,
  },
  eventsButtonTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  eventsButtonSubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.text,
    opacity: 0.9,
  },
  eventsButtonArrow: {
    fontSize: FontSizes.lg,
    color: Colors.text,
    marginLeft: Spacing.sm,
  },
  groupHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: Spacing.md,
  },
  groupHeaderLeft: {
    flex: 1,
  },
  leaderBadge: {
    backgroundColor: Colors.warning,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
  },
  leaderBadgeText: {
    fontSize: FontSizes.xs,
    fontWeight: '700',
    color: Colors.text,
  },
  groupActions: {
    marginTop: Spacing.md,
  },
  actionButton: {
    backgroundColor: Colors.primary,
    padding: Spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  actionButtonText: {
    color: Colors.text,
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
});

