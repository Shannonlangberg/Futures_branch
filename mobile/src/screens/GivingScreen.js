import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useStripe } from '@stripe/stripe-react-native';
import { Colors, FontSizes, Spacing, STRIPE_PUBLISHABLE_KEY } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function GivingScreen({ navigation }) {
  const { initPaymentSheet, presentPaymentSheet } = useStripe();
  const [user, setUser] = useState(null);
  const [amount, setAmount] = useState('');
  const [selectedType, setSelectedType] = useState('tithe');
  const [loading, setLoading] = useState(false);
  const [givingHistory, setGivingHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const givingTypes = [
    { id: 'tithe', label: 'Tithe', emoji: '💰' },
    { id: 'offering', label: 'Offering', emoji: '💵' },
    { id: 'missions', label: 'Missions', emoji: '✈️' },
    { id: 'event', label: 'Event', emoji: '🎫' },
  ];

  useEffect(() => {
    loadUser();
    loadGivingHistory();
  }, []);

  const loadUser = async () => {
    const userData = await AsyncStorage.getItem('userData');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  };

  const loadGivingHistory = async () => {
    try {
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        const userObj = JSON.parse(userData);
        const history = await ApiService.getGivingHistory(userObj.email);
        if (history.transactions) {
          setGivingHistory(history.transactions.slice(0, 10));
        }
      }
    } catch (error) {
      console.error('Error loading giving history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleGiving = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid amount.');
      return;
    }

    if (!user) {
      Alert.alert('Error', 'User not found. Please log in again.');
      return;
    }

    setLoading(true);

    try {
      // Create payment intent
      const intentResult = await ApiService.createPaymentIntent(
        parseFloat(amount) * 100, // Convert to cents
        selectedType,
        user.campus
      );

      if (!intentResult.client_secret) {
        throw new Error('Failed to create payment intent');
      }

      // Initialize payment sheet
      const { error: initError } = await initPaymentSheet({
        merchantDisplayName: 'Futures Church',
        paymentIntentClientSecret: intentResult.client_secret,
        defaultBillingDetails: {
          email: user.email,
        },
      });

      if (initError) {
        Alert.alert('Error', initError.message);
        setLoading(false);
        return;
      }

      // Present payment sheet
      const { error: presentError } = await presentPaymentSheet();

      if (presentError) {
        if (presentError.code !== 'Canceled') {
          Alert.alert('Error', presentError.message);
        }
      } else {
        // Payment successful
        Alert.alert(
          'Thank You! 🙏',
          `Your ${givingTypes.find(t => t.id === selectedType)?.label || 'gift'} of $${amount} has been received.`,
          [
            {
              text: 'OK',
              onPress: () => {
                setAmount('');
                loadGivingHistory();
                navigation.goBack();
              },
            },
          ]
        );
      }
    } catch (error) {
      console.error('Giving error:', error);
      Alert.alert('Error', error.message || 'Payment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={[Colors.background, Colors.surface, Colors.background]}
        style={styles.gradient}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Giving</Text>
          <Text style={styles.headerSubtitle}>Your generosity makes a difference</Text>
        </View>

        {/* Giving Type Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What would you like to give to?</Text>
          <View style={styles.typesGrid}>
            {givingTypes.map((type) => (
              <TouchableOpacity
                key={type.id}
                style={[
                  styles.typeCard,
                  selectedType === type.id && styles.typeCardActive,
                ]}
                onPress={() => setSelectedType(type.id)}
              >
                <Text style={styles.typeEmoji}>{type.emoji}</Text>
                <Text
                  style={[
                    styles.typeLabel,
                    selectedType === type.id && styles.typeLabelActive,
                  ]}
                >
                  {type.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Amount Input */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Amount</Text>
          <View style={styles.amountContainer}>
            <Text style={styles.currencySymbol}>$</Text>
            <TextInput
              style={styles.amountInput}
              placeholder="0.00"
              placeholderTextColor={Colors.textMuted}
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
            />
          </View>

          {/* Quick Amount Buttons */}
          <View style={styles.quickAmounts}>
            {[25, 50, 100, 200].map((quickAmount) => (
              <TouchableOpacity
                key={quickAmount}
                style={styles.quickAmountButton}
                onPress={() => setAmount(quickAmount.toString())}
              >
                <Text style={styles.quickAmountText}>${quickAmount}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Give Button */}
        <TouchableOpacity
          style={styles.giveButton}
          onPress={handleGiving}
          disabled={loading || !amount || parseFloat(amount) <= 0}
        >
          <LinearGradient
            colors={[Colors.primary, Colors.accent]}
            style={styles.giveButtonGradient}
          >
            {loading ? (
              <ActivityIndicator color={Colors.text} />
            ) : (
              <Text style={styles.giveButtonText}>Give ${amount || '0.00'}</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Giving History */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Giving History</Text>
          {loadingHistory ? (
            <ActivityIndicator color={Colors.primary} />
          ) : givingHistory.length > 0 ? (
            givingHistory.map((transaction, index) => (
              <View key={index} style={styles.historyCard}>
                <View style={styles.historyContent}>
                  <Text style={styles.historyType}>
                    {givingTypes.find(t => t.id === transaction.type)?.label || 'Gift'}
                  </Text>
                  <Text style={styles.historyDate}>
                    {formatDate(transaction.date)}
                  </Text>
                </View>
                <Text style={styles.historyAmount}>
                  ${(transaction.amount / 100).toFixed(2)}
                </Text>
              </View>
            ))
          ) : (
            <Text style={styles.noHistoryText}>No giving history yet</Text>
          )}
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
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  typesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  typeCard: {
    width: '48%',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    alignItems: 'center',
    marginBottom: Spacing.md,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  typeCardActive: {
    borderColor: Colors.primary,
  },
  typeEmoji: {
    fontSize: 32,
    marginBottom: Spacing.sm,
  },
  typeLabel: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  typeLabelActive: {
    color: Colors.primary,
    fontWeight: '600',
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  currencySymbol: {
    fontSize: FontSizes.xxl,
    fontWeight: '600',
    color: Colors.text,
    marginRight: Spacing.sm,
  },
  amountInput: {
    flex: 1,
    fontSize: FontSizes.xxl,
    fontWeight: '600',
    color: Colors.text,
  },
  quickAmounts: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: Spacing.md,
  },
  quickAmountButton: {
    backgroundColor: Colors.surface,
    borderRadius: 8,
    padding: Spacing.sm,
    minWidth: 70,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  quickAmountText: {
    color: Colors.text,
    fontSize: FontSizes.sm,
    fontWeight: '500',
  },
  giveButton: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: Spacing.xl,
  },
  giveButtonGradient: {
    padding: Spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  giveButtonText: {
    color: Colors.text,
    fontSize: FontSizes.lg,
    fontWeight: '600',
  },
  historyCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  historyContent: {
    flex: 1,
  },
  historyType: {
    fontSize: FontSizes.md,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  historyDate: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  historyAmount: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.primary,
  },
  noHistoryText: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
    textAlign: 'center',
    padding: Spacing.lg,
  },
});


