import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  Modal,
  FlatList,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function SermonNotesScreen() {
  const navigation = useNavigation();
  const [sermonNotes, setSermonNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [availableDates, setAvailableDates] = useState([]);
  const [user, setUser] = useState(null);

  useEffect(() => {
    loadUser();
    loadSermonNotes();
    loadAvailableDates();
  }, [selectedDate]);

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

  const loadSermonNotes = async () => {
    try {
      const savedNotes = await AsyncStorage.getItem(`sermon_notes_${selectedDate}`);
      if (savedNotes) {
        setSermonNotes(savedNotes);
      } else {
        setSermonNotes('');
      }
    } catch (error) {
      console.error('Error loading sermon notes:', error);
    }
  };

  const loadAvailableDates = async () => {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const noteKeys = keys.filter(key => key.startsWith('sermon_notes_'));
      const dates = noteKeys.map(key => key.replace('sermon_notes_', '')).sort().reverse();
      setAvailableDates(dates);
    } catch (error) {
      console.error('Error loading dates:', error);
    }
  };

  const saveSermonNotes = async (text) => {
    try {
      setSavingNotes(true);
      await AsyncStorage.setItem(`sermon_notes_${selectedDate}`, text);
      setLastSaved(new Date());
      
      // Log engagement if notes are substantial (> 50 chars)
      if (text.length > 50 && user) {
        try {
          await ApiService.logEngagement(user.email, 'sermon_notes', {
            date: selectedDate,
            length: text.length,
            word_count: text.split(/\s+/).filter(Boolean).length
          });
        } catch (e) {
          console.warn('Could not log sermon notes engagement:', e);
        }
      }
      
      // Refresh available dates
      loadAvailableDates();
    } catch (error) {
      console.error('Error saving sermon notes:', error);
      Alert.alert('Error', 'Failed to save notes. Please try again.');
    } finally {
      setSavingNotes(false);
    }
  };

  let autoSaveTimeout = null;
  const handleNotesChange = (text) => {
    setSermonNotes(text);
    // Auto-save after 2 seconds of no typing
    if (autoSaveTimeout) clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
      saveSermonNotes(text);
    }, 2000);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (dateString === today.toISOString().split('T')[0]) {
      return 'Today';
    } else if (dateString === yesterday.toISOString().split('T')[0]) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'short',
        month: 'short', 
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
      });
    }
  };

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    setShowDatePicker(false);
  };

  const wordCount = sermonNotes.split(/\s+/).filter(Boolean).length;
  const charCount = sermonNotes.length;

  return (
    <KeyboardAvoidingView 
      style={{ flex: 1 }} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.container}>
        <LinearGradient
          colors={['#0f172a', '#1e293b']}
          style={styles.header}
        >
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          
          <View style={styles.headerContent}>
            <Text style={styles.headerTitle}>📝 Sermon Notes</Text>
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowDatePicker(true)}
            >
              <Text style={styles.dateButtonText}>
                {formatDate(selectedDate)}
              </Text>
              <Text style={styles.dateButtonArrow}>▼</Text>
            </TouchableOpacity>
          </View>
          
          {lastSaved && (
            <Text style={styles.savedText}>
              Saved {lastSaved.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
            </Text>
          )}
        </LinearGradient>

        <ScrollView style={styles.content}>
          <View style={styles.statsBar}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{wordCount}</Text>
              <Text style={styles.statLabel}>words</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{charCount}</Text>
              <Text style={styles.statLabel}>characters</Text>
            </View>
            {savingNotes && (
              <View style={styles.stat}>
                <ActivityIndicator size="small" color={Colors.primary} />
                <Text style={styles.statLabel}>Saving...</Text>
              </View>
            )}
          </View>

          <View style={styles.notesContainer}>
            <TextInput
              style={styles.notesInput}
              placeholder="Write your sermon notes here...

💡 Tips:
• Take notes during the service
• Capture key points, scriptures, and insights
• Your notes add to your engagement score!
• All notes are saved automatically and locally"
              placeholderTextColor="rgba(255, 255, 255, 0.3)"
              value={sermonNotes}
              onChangeText={handleNotesChange}
              multiline
              textAlignVertical="top"
            />
          </View>

          <View style={styles.hint}>
            <Text style={styles.hintText}>
              💡 Auto-saves every 2 seconds • Your notes contribute to your engagement score!
            </Text>
          </View>
        </ScrollView>

        {/* Date Picker Modal */}
        <Modal
          visible={showDatePicker}
          transparent={true}
          animationType="slide"
          onRequestClose={() => setShowDatePicker(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Select Date</Text>
                <TouchableOpacity
                  onPress={() => setShowDatePicker(false)}
                  style={styles.modalCloseButton}
                >
                  <Text style={styles.modalCloseText}>✕</Text>
                </TouchableOpacity>
              </View>
              
              <FlatList
                data={availableDates}
                keyExtractor={(item) => item}
                renderItem={({ item }) => (
                  <TouchableOpacity
                    style={[
                      styles.dateItem,
                      item === selectedDate && styles.dateItemSelected
                    ]}
                    onPress={() => handleDateSelect(item)}
                  >
                    <Text style={styles.dateItemText}>{formatDate(item)}</Text>
                    {item === selectedDate && (
                      <Text style={styles.dateItemCheck}>✓</Text>
                    )}
                  </TouchableOpacity>
                )}
                ListEmptyComponent={
                  <Text style={styles.emptyDates}>No saved notes yet</Text>
                }
              />
              
              <TouchableOpacity
                style={styles.newDateButton}
                onPress={() => {
                  const today = new Date().toISOString().split('T')[0];
                  handleDateSelect(today);
                }}
              >
                <Text style={styles.newDateButtonText}>+ Today's Notes</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  header: {
    paddingTop: Spacing.xl + 20,
    paddingBottom: Spacing.lg,
    paddingHorizontal: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  backButton: {
    marginBottom: Spacing.md,
  },
  backButtonText: {
    color: Colors.primary,
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 12,
  },
  dateButtonText: {
    color: '#ffffff',
    fontSize: FontSizes.md,
    fontWeight: '600',
    marginRight: Spacing.xs,
  },
  dateButtonArrow: {
    color: '#ffffff',
    fontSize: 12,
  },
  savedText: {
    fontSize: FontSizes.xs,
    color: '#10b981',
    marginTop: Spacing.sm,
    fontWeight: '500',
  },
  content: {
    flex: 1,
    paddingHorizontal: Spacing.lg,
  },
  statsBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: FontSizes.lg,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  notesContainer: {
    marginTop: Spacing.lg,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    padding: Spacing.md,
    minHeight: 400,
  },
  notesInput: {
    color: '#ffffff',
    fontSize: FontSizes.md,
    lineHeight: 24,
    minHeight: 380,
  },
  hint: {
    marginTop: Spacing.lg,
    marginBottom: Spacing.xl,
    padding: Spacing.md,
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    borderRadius: 8,
  },
  hintText: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1e293b',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
    paddingBottom: Spacing.xl,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  modalTitle: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  modalCloseButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  dateItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  dateItemSelected: {
    backgroundColor: 'rgba(99, 102, 241, 0.2)',
  },
  dateItemText: {
    fontSize: FontSizes.md,
    color: '#ffffff',
  },
  dateItemCheck: {
    fontSize: 18,
    color: Colors.primary,
    fontWeight: 'bold',
  },
  emptyDates: {
    padding: Spacing.xl,
    textAlign: 'center',
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: FontSizes.md,
  },
  newDateButton: {
    margin: Spacing.lg,
    padding: Spacing.md,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    alignItems: 'center',
  },
  newDateButtonText: {
    color: '#ffffff',
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
});

