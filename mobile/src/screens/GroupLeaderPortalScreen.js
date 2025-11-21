import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  TextInput,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRoute, useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function GroupLeaderPortalScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const { group } = route.params || {};
  
  const [members, setMembers] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [showMeetingModal, setShowMeetingModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [attendance, setAttendance] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);
        
        // Load leader portal data
        const portalData = await ApiService.getLeaderPortal(group.id, userObj.email, '');
        console.log('Leader Portal Data:', JSON.stringify(portalData, null, 2));
        
        if (portalData.members) {
          console.log(`Found ${portalData.members.length} members:`, portalData.members.map(m => ({ name: m.full_name, connect_group: m.connect_group })));
          setMembers(portalData.members);
        } else {
          console.warn('No members array in portal data');
        }
        if (portalData.recent_meetings) {
          setMeetings(portalData.recent_meetings);
        }
      }
    } catch (error) {
      console.error('Error loading leader portal:', error);
      console.error('Error details:', error.response?.data || error.message);
      Alert.alert('Error', error.response?.data?.error || 'Failed to load leader portal data');
    } finally {
      setLoading(false);
    }
  };

  const openMeetingModal = () => {
    // Initialize attendance - all members present by default
    const initialAttendance = {};
    members.forEach(member => {
      initialAttendance[member.id] = true;
    });
    setAttendance(initialAttendance);
    setShowMeetingModal(true);
  };

  const toggleAttendance = (personId) => {
    setAttendance(prev => ({
      ...prev,
      [personId]: !prev[personId]
    }));
  };

  const saveAttendance = async () => {
    if (!user || saving) return;
    
    try {
      setSaving(true);
      const attendanceList = members.map(member => ({
        person_id: member.id,
        present: attendance[member.id] !== false, // Default to true
      }));
      
      await ApiService.markLeaderAttendance(
        group.id,
        user.email,
        selectedDate,
        attendanceList
      );
      
      Alert.alert('Success', 'Attendance marked successfully!');
      setShowMeetingModal(false);
      loadData(); // Reload to show new meeting
    } catch (error) {
      console.error('Error saving attendance:', error);
      Alert.alert('Error', error.response?.data?.error || 'Failed to save attendance');
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backButton}
            activeOpacity={0.7}
          >
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>Leader Portal</Text>
            <Text style={styles.headerSubtitle}>{group?.name}</Text>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={openMeetingModal}
          >
            <LinearGradient
              colors={[Colors.primary, Colors.accent]}
              style={styles.primaryButtonGradient}
            >
              <Text style={styles.primaryButtonText}>✓ Mark Attendance</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Members */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Members ({members.length})</Text>
          {members.map((member) => (
            <View key={member.id} style={styles.memberCard}>
              <View style={styles.memberInfo}>
                <Text style={styles.memberName}>{member.full_name || member.preferred_name}</Text>
                {member.email && (
                  <Text style={styles.memberEmail}>{member.email}</Text>
                )}
              </View>
            </View>
          ))}
        </View>

        {/* Recent Meetings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Meetings</Text>
          {meetings.length > 0 ? (
            meetings.map((meeting) => {
              const presentCount = meeting.attendance?.filter(a => a.present).length || 0;
              const totalCount = meeting.attendance?.length || 0;
              return (
                <View key={meeting.id} style={styles.meetingCard}>
                  <View style={styles.meetingHeader}>
                    <Text style={styles.meetingDate}>{formatDate(meeting.meeting_date)}</Text>
                    <Text style={styles.meetingAttendance}>
                      {presentCount}/{totalCount} present
                    </Text>
                  </View>
                  {meeting.notes && (
                    <Text style={styles.meetingNotes}>{meeting.notes}</Text>
                  )}
                </View>
              );
            })
          ) : (
            <Text style={styles.emptyText}>No meetings recorded yet</Text>
          )}
        </View>
      </LinearGradient>

      {/* Mark Attendance Modal */}
      <Modal
        visible={showMeetingModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowMeetingModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Mark Attendance</Text>
              <TouchableOpacity
                onPress={() => setShowMeetingModal(false)}
                style={styles.modalCloseButton}
              >
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.dateInput}
              value={selectedDate}
              onChangeText={setSelectedDate}
              placeholder="YYYY-MM-DD"
            />

            <ScrollView style={styles.attendanceList}>
              {members.map((member) => (
                <TouchableOpacity
                  key={member.id}
                  style={[
                    styles.attendanceItem,
                    attendance[member.id] && styles.attendanceItemPresent,
                  ]}
                  onPress={() => toggleAttendance(member.id)}
                >
                  <Text style={styles.attendanceItemName}>
                    {member.full_name || member.preferred_name}
                  </Text>
                  <Text style={styles.attendanceItemStatus}>
                    {attendance[member.id] !== false ? '✓ Present' : '✗ Absent'}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.saveButton, saving && styles.saveButtonDisabled]}
                onPress={saveAttendance}
                disabled={saving}
              >
                {saving ? (
                  <ActivityIndicator color={Colors.text} />
                ) : (
                  <Text style={styles.saveButtonText}>Save Attendance</Text>
                )}
              </TouchableOpacity>
            </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  gradient: {
    flex: 1,
    padding: Spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xl,
    marginTop: Spacing.lg,
    paddingTop: Spacing.md,
  },
  backButton: {
    marginRight: Spacing.md,
    padding: Spacing.sm,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    fontSize: 24,
    color: Colors.text,
    fontWeight: 'bold',
    lineHeight: 28,
  },
  headerContent: {
    flex: 1,
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
    fontWeight: '700',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  primaryButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  primaryButtonGradient: {
    padding: Spacing.md,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: Colors.text,
  },
  memberCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  memberEmail: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  meetingCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  meetingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.xs,
  },
  meetingDate: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
  },
  meetingAttendance: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  meetingNotes: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: Colors.textMuted,
    textAlign: 'center',
    padding: Spacing.xl,
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    paddingBottom: 40,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: {
    fontSize: FontSizes.xl,
    fontWeight: '700',
    color: Colors.text,
  },
  modalCloseButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseText: {
    fontSize: 20,
    color: Colors.text,
    fontWeight: 'bold',
  },
  dateInput: {
    backgroundColor: Colors.background,
    borderRadius: 12,
    padding: Spacing.md,
    margin: Spacing.lg,
    fontSize: FontSizes.md,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  attendanceList: {
    maxHeight: 400,
    paddingHorizontal: Spacing.lg,
  },
  attendanceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    backgroundColor: Colors.background,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.border,
  },
  attendanceItemPresent: {
    borderColor: Colors.success,
    backgroundColor: Colors.success + '20',
  },
  attendanceItemName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
  },
  attendanceItemStatus: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  modalActions: {
    padding: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  saveButton: {
    backgroundColor: Colors.primary,
    padding: Spacing.md,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '700',
    color: Colors.text,
  },
});

