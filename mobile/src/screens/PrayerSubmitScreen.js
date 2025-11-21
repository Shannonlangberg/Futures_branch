import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Switch,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SafeAreaView } from 'react-native-safe-area-context';
import ApiService from '../services/ApiService';

export default function PrayerSubmitScreen({ navigation, route }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submissionType, setSubmissionType] = useState('prayer'); // 'prayer' or 'praise'
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('general');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isUrgent, setIsUrgent] = useState(false);
  const [isPublic, setIsPublic] = useState(true);

  // Get pre-filled type from route params (if coming from QR/NFC)
  useEffect(() => {
    loadUser();
    if (route.params?.type) {
      setSubmissionType(route.params.type);
    }
  }, []);

  const loadUser = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const categories = [
    { value: 'general', label: 'General', emoji: '📝' },
    { value: 'health', label: 'Health', emoji: '🏥' },
    { value: 'family', label: 'Family', emoji: '👨‍👩‍👧‍👦' },
    { value: 'work', label: 'Work/Study', emoji: '💼' },
    { value: 'spiritual', label: 'Spiritual Growth', emoji: '✝️' },
    { value: 'relationships', label: 'Relationships', emoji: '💑' },
    { value: 'financial', label: 'Financial', emoji: '💰' },
    { value: 'other', label: 'Other', emoji: '🙏' }
  ];

  const handleSubmit = async () => {
    if (!content.trim()) {
      Alert.alert('Required', `Please enter your ${submissionType} request.`);
      return;
    }

    if (!user && !isAnonymous) {
      Alert.alert('Login Required', 'Please login or submit anonymously.');
      return;
    }

    setLoading(true);

    try {
      await ApiService.submitPrayer({
        email: !isAnonymous && user ? user.email : null,
        type: submissionType,
        content: content.trim(),
        category,
        is_anonymous: isAnonymous,
        is_urgent: isUrgent,
        campus: user?.campus || 'all_campuses',
        is_public: isPublic
      });

      Alert.alert(
        '✅ Submitted!',
        `Your ${submissionType} has been received. Our team will be praying ${submissionType === 'prayer' ? 'for you' : 'with you'}!`,
        [
          {
            text: 'Done',
            onPress: () => {
              setContent('');
              setIsUrgent(false);
              if (navigation.canGoBack()) {
                navigation.goBack();
              }
            }
          }
        ]
      );
    } catch (error) {
      console.error('Submit error:', error);
      Alert.alert(
        'Submission Failed',
        error.response?.data?.error || 'Please try again later.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView style={styles.scrollView}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>🙏 Prayer & Praise</Text>
            <Text style={styles.subtitle}>
              Share your request with our prayer team
            </Text>
          </View>

          {/* Type Toggle */}
          <View style={styles.section}>
            <Text style={styles.label}>Type</Text>
            <View style={styles.typeToggle}>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  submissionType === 'prayer' && styles.typeButtonActive
                ]}
                onPress={() => setSubmissionType('prayer')}
              >
                <Text
                  style={[
                    styles.typeButtonText,
                    submissionType === 'prayer' && styles.typeButtonTextActive
                  ]}
                >
                  🙏 Prayer Request
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  submissionType === 'praise' && styles.typeButtonActive
                ]}
                onPress={() => setSubmissionType('praise')}
              >
                <Text
                  style={[
                    styles.typeButtonText,
                    submissionType === 'praise' && styles.typeButtonTextActive
                  ]}
                >
                  🎉 Praise Report
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Category */}
          <View style={styles.section}>
            <Text style={styles.label}>Category</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.categoryList}>
                {categories.map((cat) => (
                  <TouchableOpacity
                    key={cat.value}
                    style={[
                      styles.categoryButton,
                      category === cat.value && styles.categoryButtonActive
                    ]}
                    onPress={() => setCategory(cat.value)}
                  >
                    <Text style={styles.categoryEmoji}>{cat.emoji}</Text>
                    <Text
                      style={[
                        styles.categoryLabel,
                        category === cat.value && styles.categoryLabelActive
                      ]}
                    >
                      {cat.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </View>

          {/* Content */}
          <View style={styles.section}>
            <Text style={styles.label}>
              {submissionType === 'prayer' ? 'Prayer Request' : 'Praise Report'} *
            </Text>
            <TextInput
              style={styles.textArea}
              placeholder={
                submissionType === 'prayer'
                  ? 'Share what you would like us to pray for...'
                  : 'Share what you are praising God for...'
              }
              placeholderTextColor="#64748b"
              multiline
              numberOfLines={6}
              value={content}
              onChangeText={setContent}
              maxLength={1000}
            />
            <Text style={styles.charCount}>{content.length}/1000</Text>
          </View>

          {/* Options */}
          {user && (
            <View style={styles.section}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabel}>
                  <Text style={styles.switchTitle}>Submit Anonymously</Text>
                  <Text style={styles.switchSubtitle}>
                    Your name will not be shared
                  </Text>
                </View>
                <Switch
                  value={isAnonymous}
                  onValueChange={setIsAnonymous}
                  trackColor={{ false: '#334155', true: '#6366f1' }}
                  thumbColor="#fff"
                />
              </View>

              {submissionType === 'prayer' && (
                <View style={styles.switchRow}>
                  <View style={styles.switchLabel}>
                    <Text style={styles.switchTitle}>🔴 Urgent</Text>
                    <Text style={styles.switchSubtitle}>
                      Request immediate prayer attention
                    </Text>
                  </View>
                  <Switch
                    value={isUrgent}
                    onValueChange={setIsUrgent}
                    trackColor={{ false: '#334155', true: '#ef4444' }}
                    thumbColor="#fff"
                  />
                </View>
              )}

              <View style={styles.switchRow}>
                <View style={styles.switchLabel}>
                  <Text style={styles.switchTitle}>Share with Prayer Team</Text>
                  <Text style={styles.switchSubtitle}>
                    Allow prayer team to see this request
                  </Text>
                </View>
                <Switch
                  value={isPublic}
                  onValueChange={setIsPublic}
                  trackColor={{ false: '#334155', true: '#6366f1' }}
                  thumbColor="#fff"
                />
              </View>
            </View>
          )}

          {/* Submit Button */}
          <TouchableOpacity
            style={[styles.submitButton, loading && styles.submitButtonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitButtonText}>
                Submit {submissionType === 'prayer' ? 'Prayer' : 'Praise'}
              </Text>
            )}
          </TouchableOpacity>

          {/* Info Text */}
          <Text style={styles.infoText}>
            💜 Your submission will be received by our pastoral care team. 
            {isUrgent && ' Urgent requests are prioritized.'}
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  scrollView: {
    flex: 1,
    padding: 20,
  },
  header: {
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  typeToggle: {
    flexDirection: 'row',
    gap: 12,
  },
  typeButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    borderWidth: 2,
    borderColor: '#334155',
    alignItems: 'center',
  },
  typeButtonActive: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  typeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#94a3b8',
  },
  typeButtonTextActive: {
    color: '#fff',
  },
  categoryList: {
    flexDirection: 'row',
    gap: 12,
  },
  categoryButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    borderWidth: 2,
    borderColor: '#334155',
    alignItems: 'center',
  },
  categoryButtonActive: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  categoryEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  categoryLabel: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: '600',
  },
  categoryLabelActive: {
    color: '#fff',
  },
  textArea: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
    minHeight: 150,
    textAlignVertical: 'top',
    borderWidth: 2,
    borderColor: '#334155',
  },
  charCount: {
    textAlign: 'right',
    fontSize: 12,
    color: '#64748b',
    marginTop: 8,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  switchLabel: {
    flex: 1,
    marginRight: 16,
  },
  switchTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  switchSubtitle: {
    fontSize: 14,
    color: '#94a3b8',
  },
  submitButton: {
    backgroundColor: '#6366f1',
    paddingVertical: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoText: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 40,
    lineHeight: 20,
  },
});

