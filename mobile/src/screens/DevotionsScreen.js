import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Image,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, FontSizes, Spacing } from '../constants/config';
import Icon from '../components/Icon';
import ApiService, { api } from '../services/ApiService';

export default function DevotionsScreen() {
  const navigation = useNavigation();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchDevotions();
  }, []);

  const fetchDevotions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/devotions/library');

      if (response && response.status === 200 && response.data) {
        const data = response.data;
        // Combine all plan types (assigned, in_progress, completed, personal)
        const allPlans = [
          ...(data.assigned || []),
          ...(data.in_progress || []),
          ...(data.completed || []),
          ...(data.personal || []),
        ];
        // Remove duplicates by ID
        const uniquePlans = allPlans.filter((plan, index, self) =>
          index === self.findIndex((p) => p.id === plan.id)
        );
        setPlans(uniquePlans);
      }
    } catch (error) {
      console.error('Error fetching devotions:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchDevotions();
  };

  const renderPlanCard = (plan) => (
    <TouchableOpacity
      key={plan.id}
      style={styles.planCard}
      activeOpacity={0.8}
      onPress={() => {
        // TODO: Navigate to plan detail screen
        console.log('Open plan:', plan.id);
      }}
    >
      {plan.cover_url ? (
        <Image
          source={{ uri: plan.cover_url }}
          style={styles.planImage}
          resizeMode="cover"
        />
      ) : (
        <LinearGradient
          colors={['#f59e0b', '#f97316']}
          style={styles.planImage}
        >
          <View style={styles.placeholderContent}>
            <Icon name="meditation" size={48} color="#ffffff" />
          </View>
        </LinearGradient>
      )}
      
      <View style={styles.planContent}>
        <Text style={styles.planTitle} numberOfLines={2}>
          {plan.title}
        </Text>
        {plan.description && (
          <Text style={styles.planDescription} numberOfLines={2}>
            {plan.description}
          </Text>
        )}
        <View style={styles.planMeta}>
          <View style={styles.metaItem}>
            <Icon name="calendar" size={14} color={Colors.textSecondary} />
            <Text style={styles.metaText}>
              {plan.total_days || plan.content_count || 30} days
            </Text>
          </View>
          {plan.campus && plan.campus !== 'All Campuses' && (
            <View style={styles.metaItem}>
              <Icon name="location" size={14} color={Colors.textSecondary} />
              <Text style={styles.metaText}>{plan.campus}</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Loading devotions...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Devotionals</Text>
          <Text style={styles.headerSubtitle}>
            Daily readings to grow in your faith
          </Text>
        </View>

        {plans.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="meditation" size={64} color={Colors.textSecondary} />
            <Text style={styles.emptyTitle}>No devotion plans available</Text>
            <Text style={styles.emptyText}>
              Check back soon for new devotional content!
            </Text>
          </View>
        ) : (
          <View style={styles.plansGrid}>
            {plans.map(renderPlanCard)}
          </View>
        )}

        <View style={{ height: Spacing.xxl }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  loadingText: {
    marginTop: Spacing.md,
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  header: {
    marginBottom: Spacing.sectionSpacing,
    marginTop: Spacing.lg,
  },
  headerTitle: {
    fontSize: FontSizes.xxxl,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  headerSubtitle: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  plansGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  planCard: {
    width: '48%',
    marginBottom: Spacing.cardGap,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: Colors.cardBackground,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  planImage: {
    width: '100%',
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  planContent: {
    padding: Spacing.cardPadding,
  },
  planTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs / 2,
  },
  planDescription: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    lineHeight: 18,
  },
  planMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.xxl * 2,
  },
  emptyTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginTop: Spacing.md,
    marginBottom: Spacing.xs,
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: Spacing.lg,
  },
});

