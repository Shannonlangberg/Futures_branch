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

        // Load campus
        const campuses = await ApiService.getCampuses();
        const userCampus = campuses.campuses?.find(c => c.id === userObj.campus);
        if (userCampus) {
          setCampus(userCampus);
          
          // Load service times
          const times = await ApiService.getServiceTimes(userCampus.id);
          if (times.services) {
            setServiceTimes(times.services);
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
      const result = await BeaconService.manualCheckIn(campus.id);
      
      if (result.success) {
        Alert.alert(
          'Checked In! ✅',
          'You\'ve been checked in to today\'s service.',
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert('Error', result.error || 'Check-in failed. Please try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'Check-in failed. Please try again.');
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
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Campus Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{campus?.name || 'Sunday Service'}</Text>
          {campus?.location && (
            <Text style={styles.headerSubtitle}>📍 {campus.location}</Text>
          )}
        </View>

        {/* Service Times */}
        {serviceTimes.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Service Times</Text>
            {serviceTimes.map((service, index) => (
              <View key={index} style={styles.serviceCard}>
                <View style={styles.serviceContent}>
                  <Text style={styles.serviceTime}>
                    {new Date(service.start_time).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </Text>
                  <Text style={styles.serviceType}>{service.type || 'Sunday Service'}</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Check-In Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Check In</Text>
          
          {/* Beacon Toggle */}
          <TouchableOpacity
            style={styles.optionCard}
            onPress={handleBeaconToggle}
          >
            <View style={styles.optionContent}>
              <View>
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
              colors={[Colors.primary, Colors.accent]}
              style={styles.checkInGradient}
            >
              {checkingIn ? (
                <ActivityIndicator color={Colors.text} />
              ) : (
                <>
                  <Text style={styles.checkInEmoji}>✓</Text>
                  <Text style={styles.checkInText}>I'm Here</Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Campus Info */}
        {campus && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Campus Information</Text>
            <View style={styles.infoCard}>
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

        {/* Quick Access to Prayer */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.prayerButton}
            onPress={() => navigation.navigate('Prayer')}
          >
            <LinearGradient
              colors={[Colors.warning, Colors.error]}
              style={styles.prayerButtonGradient}
            >
              <Text style={styles.prayerButtonEmoji}>🙏</Text>
              <View style={styles.prayerButtonContent}>
                <Text style={styles.prayerButtonTitle}>Prayer & Praise</Text>
                <Text style={styles.prayerButtonSubtitle}>Submit a prayer request or praise report</Text>
              </View>
              <Text style={styles.prayerButtonArrow}>→</Text>
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
  serviceCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  serviceContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  serviceTime: {
    fontSize: FontSizes.xl,
    fontWeight: '600',
    color: Colors.primary,
    marginRight: Spacing.md,
  },
  serviceType: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  optionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  optionContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  optionTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  optionDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  toggle: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 20,
    backgroundColor: Colors.border,
  },
  toggleActive: {
    backgroundColor: Colors.primary,
  },
  toggleText: {
    color: Colors.text,
    fontSize: FontSizes.sm,
    fontWeight: '600',
  },
  checkInButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: Spacing.md,
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
    color: Colors.text,
    fontSize: FontSizes.lg,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: Spacing.sm,
  },
  infoLabel: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginRight: Spacing.sm,
    fontWeight: '500',
  },
  infoValue: {
    fontSize: FontSizes.sm,
    color: Colors.text,
    flex: 1,
  },
  prayerButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginTop: Spacing.md,
  },
  prayerButtonGradient: {
    padding: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
  },
  prayerButtonEmoji: {
    fontSize: 32,
    marginRight: Spacing.md,
  },
  prayerButtonContent: {
    flex: 1,
  },
  prayerButtonTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  prayerButtonSubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.text,
    opacity: 0.9,
  },
  prayerButtonArrow: {
    fontSize: FontSizes.lg,
    color: Colors.text,
    marginLeft: Spacing.sm,
  },
});

