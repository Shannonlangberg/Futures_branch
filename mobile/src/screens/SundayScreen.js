import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import { BeaconService } from '../services/BeaconService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function SundayScreen() {
  const navigation = useNavigation();
  const [user, setUser] = useState(null);
  const [campus, setCampus] = useState(null);
  const [serviceTimes, setServiceTimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [beaconEnabled, setBeaconEnabled] = useState(false);
  
  useEffect(() => {
    loadData();
    checkBeaconPermission();
  }, []);

  const loadData = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        setUser(userObj);

        // Load campus with detailed info
        const campuses = await ApiService.getCampuses();
        const userCampus = campuses.campuses?.find(c => c.id === userObj.campus);
        if (userCampus) {
          setCampus(userCampus);
          
          // Load service times
          try {
            const times = await ApiService.getServiceTimes(userCampus.id);
            if (times.services) {
              setServiceTimes(times.services);
            }
          } catch (e) {
            console.warn('Service times not available:', e);
          }
        }
      }
    } catch (error) {
      console.error('Error loading Sunday data:', error);
    } finally {
      setLoading(false);
    }
  };


  const checkBeaconPermission = async () => {
    const result = await BeaconService.requestPermissions();
    setBeaconEnabled(result.success);
  };

  const handleManualCheckIn = async () => {
    if (!user || !campus) {
      Alert.alert('Error', 'Unable to check in. Please try again.');
      return;
    }

    setCheckingIn(true);
    
    try {
      // Log attendance to heartbeat (this is the "gather" metric!)
      const result = await ApiService.logAttendance(user.email, {
        campus: campus.id
      });
      
      if (result.success || result.message) {
        Alert.alert(
          'Checked In! ✅',
          'You\'ve been checked in to today\'s service. See you there!',
          [{ text: 'OK' }]
        );
      } else {
        throw new Error('Check-in failed');
      }
    } catch (error) {
      console.error('Check-in error:', error);
      Alert.alert('Error', error.response?.data?.error || 'Check-in failed. Please try again.');
    } finally {
      setCheckingIn(false);
    }
  };

  const handleBeaconToggle = async () => {
    if (!beaconEnabled) {
      const result = await BeaconService.requestPermissions();
      if (result.success) {
        setBeaconEnabled(true);
        Alert.alert(
          'Beacon Check-In Enabled',
          'You\'ll be automatically checked in when you arrive at service.',
        );
      } else {
        Alert.alert('Permission Required', result.error || 'Location permission is required for beacon check-in.');
      }
    } else {
      setBeaconEnabled(false);
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
    <ScrollView style={styles.container}>
        <LinearGradient
          colors={['#0f172a', '#1e293b', '#0f172a']}
          style={styles.gradient}
        >
          {/* Campus Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Sunday Service</Text>
            <Text style={styles.headerSubtitle}>{campus?.name || 'All Campuses'}</Text>
          </View>

          {/* Check-In Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Check In</Text>
            
            {/* Beacon Toggle */}
            <TouchableOpacity
              style={styles.optionCard}
              onPress={handleBeaconToggle}
            >
              <View style={styles.optionContent}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.optionTitle}>Automatic Beacon Check-In</Text>
                  <Text style={styles.optionDescription}>
                    Get checked in automatically when you arrive
                  </Text>
                </View>
                <View style={[
                  styles.toggle,
                  beaconEnabled && styles.toggleActive
                ]}>
                  <Text style={styles.toggleText}>
                    {beaconEnabled ? 'ON' : 'OFF'}
                  </Text>
                </View>
              </View>
            </TouchableOpacity>

            {/* Manual Check-In */}
            <TouchableOpacity
              style={styles.checkInButton}
              onPress={handleManualCheckIn}
              disabled={checkingIn}
            >
              <LinearGradient
                colors={['#6366f1', '#8b5cf6']}
                style={styles.checkInGradient}
              >
                {checkingIn ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <>
                    <Text style={styles.checkInEmoji}>✓</Text>
                    <Text style={styles.checkInText}>I'm Here</Text>
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>

          {/* Campus Information */}
          {campus && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Campus Information</Text>
              <View style={styles.infoCard}>
                {campus.description && (
                  <Text style={styles.campusDescription}>{campus.description}</Text>
                )}
                {campus.location && (
                  <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>📍 Location:</Text>
                    <Text style={styles.infoValue}>{campus.location}</Text>
                  </View>
                )}
                {campus.parking && (
                  <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>🚗 Parking:</Text>
                    <Text style={styles.infoValue}>{campus.parking}</Text>
                  </View>
                )}
                {campus.kids_info && (
                  <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>👶 Kids:</Text>
                    <Text style={styles.infoValue}>{campus.kids_info}</Text>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* Service Times */}
          {serviceTimes.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Service Times</Text>
              {serviceTimes.map((service, index) => (
                <View key={index} style={styles.serviceCard}>
                  <Text style={styles.serviceTime}>
                    ⏰ {new Date(service.start_time).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </Text>
                  <Text style={styles.serviceType}>{service.type || 'Sunday Service'}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Sermon Notes */}
          <View style={styles.section}>
            <TouchableOpacity
              style={styles.notesCard}
              onPress={() => navigation.navigate('SermonNotes')}
            >
              <LinearGradient
                colors={['rgba(99, 102, 241, 0.2)', 'rgba(139, 92, 246, 0.2)']}
                style={styles.notesCardGradient}
              >
                <View style={styles.notesCardContent}>
                  <Text style={styles.notesCardEmoji}>📝</Text>
                  <View style={styles.notesCardText}>
                    <Text style={styles.notesCardTitle}>Sermon Notes</Text>
                    <Text style={styles.notesCardSubtitle}>
                      Take notes during service • Auto-saved locally
                    </Text>
                  </View>
                  <Text style={styles.notesCardArrow}>→</Text>
                </View>
              </LinearGradient>
            </TouchableOpacity>
          </View>

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
  gradient: {
    flex: 1,
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.xl,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    alignItems: 'center',
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
  section: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.md,
  },
  serviceCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  serviceTime: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#6366f1',
    marginBottom: Spacing.xs,
  },
  serviceType: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  optionCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  optionContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  optionTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  optionDescription: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  toggle: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  toggleActive: {
    backgroundColor: '#6366f1',
  },
  toggleText: {
    color: '#ffffff',
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
  checkInButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: Spacing.md,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  checkInGradient: {
    padding: Spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  checkInEmoji: {
    fontSize: 24,
    marginRight: Spacing.sm,
  },
  checkInText: {
    color: '#ffffff',
    fontSize: FontSizes.lg,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  campusDescription: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 22,
    marginBottom: Spacing.md,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: Spacing.sm,
  },
  infoLabel: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
    marginRight: Spacing.sm,
    fontWeight: '500',
    minWidth: 100,
  },
  infoValue: {
    fontSize: FontSizes.sm,
    color: '#ffffff',
    flex: 1,
  },
  notesCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: Spacing.md,
  },
  notesCardGradient: {
    padding: Spacing.lg,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.3)',
  },
  notesCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  notesCardEmoji: {
    fontSize: 32,
    marginRight: Spacing.md,
  },
  notesCardText: {
    flex: 1,
  },
  notesCardTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  notesCardSubtitle: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  notesCardArrow: {
    fontSize: 24,
    color: Colors.primary,
    marginLeft: Spacing.sm,
  },
});
