import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function PrayerScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('prayer'); // 'prayer' or 'praise'
  const [request, setRequest] = useState('');
  const [praise, setPraise] = useState('');
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    const userData = await AsyncStorage.getItem('userData');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  };

  const handleSubmitPrayer = async () => {
    if (!request.trim()) {
      Alert.alert('Error', 'Please enter your prayer request.');
      return;
    }

    if (!user) {
      Alert.alert('Error', 'User not found.');
      return;
    }

    setSubmitting(true);

    try {
      console.log('🙏 Submitting prayer request:');
      console.log('   - Email:', user.email);
      console.log('   - Person ID:', user.person_id);
      console.log('   - Campus:', user.campus);
      
      if (!user.person_id) {
        console.error('❌ WARNING: No person_id in user object!', user);
        Alert.alert('Error', 'User profile not loaded correctly. Please log out and log back in.');
        setSubmitting(false);
        return;
      }
      
      const result = await ApiService.submitPrayerRequest(user.email, {
        request: request.trim(),
        campus: user.campus, // Pass the user's campus
        person_id: user.person_id, // NEW: Pass person_id to link to correct profile
        created_at: new Date().toISOString(),
      });
      
      console.log('✅ Prayer request response:', result);

      if (result.success || result.message) {
        Alert.alert(
          'Prayer Request Submitted 🙏',
          'Your prayer request has been received. Our team will be praying for you.',
          [{ text: 'OK', onPress: () => setRequest('') }]
        );
      } else {
        Alert.alert('Error', result.error || 'Failed to submit prayer request.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to submit prayer request. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitPraise = async () => {
    if (!praise.trim()) {
      Alert.alert('Error', 'Please enter your praise report.');
      return;
    }

    if (!user) {
      Alert.alert('Error', 'User not found.');
      return;
    }

    setSubmitting(true);

    try {
      console.log('🎉 Submitting praise report:');
      console.log('   - Email:', user.email);
      console.log('   - Person ID:', user.person_id);
      console.log('   - Campus:', user.campus);
      
      if (!user.person_id) {
        console.error('❌ WARNING: No person_id in user object!', user);
        Alert.alert('Error', 'User profile not loaded correctly. Please log out and log back in.');
        setSubmitting(false);
        return;
      }
      
      const result = await ApiService.submitPraiseReport(user.email, {
        report: praise.trim(),
        campus: user.campus, // Pass the user's campus
        person_id: user.person_id, // NEW: Pass person_id to link to correct profile
        created_at: new Date().toISOString(),
      });
      
      console.log('✅ Praise report response:', result);

      if (result.success || result.message) {
        Alert.alert(
          'Praise Report Submitted 🎉',
          'Thank you for sharing! Your praise report has been received.',
          [{ text: 'OK', onPress: () => setPraise('') }]
        );
      } else {
        Alert.alert('Error', result.error || 'Failed to submit praise report.');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to submit praise report. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Prayer & Praise</Text>
          <Text style={styles.headerSubtitle}>
            Share your prayer needs and praise reports
          </Text>
        </View>

        {/* Tabs */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'prayer' && styles.tabActive]}
            onPress={() => setActiveTab('prayer')}
          >
            <Text
              style={[styles.tabText, activeTab === 'prayer' && styles.tabTextActive]}
            >
              🙏 Prayer Request
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'praise' && styles.tabActive]}
            onPress={() => setActiveTab('praise')}
          >
            <Text
              style={[styles.tabText, activeTab === 'praise' && styles.tabTextActive]}
            >
              🎉 Praise Report
            </Text>
          </TouchableOpacity>
        </View>

        {/* Prayer Request Form */}
        {activeTab === 'prayer' ? (
          <View style={styles.form}>
            <Text style={styles.formTitle}>Share Your Prayer Request</Text>
            <Text style={styles.formDescription}>
              Your prayer request will be received by our prayer team and logged in Heartbeat care signals.
            </Text>
            <TextInput
              style={styles.textInput}
              placeholder="What would you like us to pray for?"
              placeholderTextColor={Colors.textMuted}
              value={request}
              onChangeText={setRequest}
              multiline
              numberOfLines={8}
              textAlignVertical="top"
            />
            <TouchableOpacity
              style={styles.submitButton}
              onPress={handleSubmitPrayer}
              disabled={submitting || !request.trim()}
            >
              <LinearGradient
                colors={[Colors.primary, Colors.accent]}
                style={styles.submitButtonGradient}
              >
                {submitting ? (
                  <ActivityIndicator color={Colors.text} />
                ) : (
                  <Text style={styles.submitButtonText}>Submit Prayer Request</Text>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.form}>
            <Text style={styles.formTitle}>Share Your Praise Report</Text>
            <Text style={styles.formDescription}>
              We'd love to hear what God is doing in your life!
            </Text>
            <TextInput
              style={styles.textInput}
              placeholder="What are you praising God for?"
              placeholderTextColor={Colors.textMuted}
              value={praise}
              onChangeText={setPraise}
              multiline
              numberOfLines={8}
              textAlignVertical="top"
            />
            <TouchableOpacity
              style={styles.submitButton}
              onPress={handleSubmitPraise}
              disabled={submitting || !praise.trim()}
            >
              <LinearGradient
                colors={[Colors.success, Colors.primary]}
                style={styles.submitButtonGradient}
              >
                {submitting ? (
                  <ActivityIndicator color={Colors.text} />
                ) : (
                  <Text style={styles.submitButtonText}>Submit Praise Report</Text>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        )}
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
    marginBottom: Spacing.xl,
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
  form: {
    flex: 1,
  },
  formTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  formDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  textInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    color: Colors.text,
    fontSize: FontSizes.md,
    minHeight: 150,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  submitButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  submitButtonGradient: {
    padding: Spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButtonText: {
    color: Colors.text,
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
});


