import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing } from '../constants/config';
import Icon from '../components/Icon';

export default function ExploreScreen() {
  const navigation = useNavigation();

  const openBibleApp = () => {
    // Open Bible app (YouVersion or similar) or browser
    const bibleUrl = 'https://www.bible.com';
    Linking.openURL(bibleUrl).catch(() => {
      Alert.alert('Error', 'Unable to open Bible app. Please check your internet connection.');
    });
  };

  const openBibleSearch = () => {
    const searchUrl = 'https://www.bible.com/search';
    Linking.openURL(searchUrl).catch(() => {
      Alert.alert('Error', 'Unable to open Bible search.');
    });
  };

  // Featured/Trending content - Full width, spans 1 column
  const featuredContent = {
    title: 'Pulse TV',
    subtitle: 'Watch discipleship content and grow in your faith journey',
    onPress: () => navigation.navigate('TVHome'),
    gradientColors: ['#6366f1', '#8b5cf6'],
    icon: 'tv',
  };

  // Top Suggested - Full width cards
  const topSuggested = [
    {
      id: 'prayer',
      title: 'Prayer & Praise',
      subtitle: 'Submit prayer requests and share praises',
      icon: 'prayer',
      onPress: () => navigation.navigate('Prayer'),
      gradientColors: ['#ef4444', '#f87171'], // Red gradient
    },
    {
      id: 'groups',
      title: 'Connect in Groups',
      subtitle: 'Join a community and grow together',
      icon: 'groups',
      onPress: () => navigation.navigate('Groups'),
      gradientColors: ['#8b5cf6', '#a78bfa'], // Purple gradient
    },
  ];

  // Categories - Two column grid
  const categories = [
    {
      id: 'bible',
      title: 'Bible',
      icon: 'resources',
      description: 'Read Scripture',
      onPress: openBibleApp,
      cardColor: '#6366f1', // Indigo
    },
    {
      id: 'bible_search',
      title: 'Bible Search',
      icon: 'search',
      description: 'Find verses',
      onPress: openBibleSearch,
      cardColor: '#8b5cf6', // Purple
    },
    {
      id: 'worship',
      title: 'Worship',
      icon: 'music',
      description: 'Songs & playlists',
      onPress: () => Alert.alert('Coming Soon', 'Worship resources coming soon!'),
      cardColor: '#ec4899', // Pink
    },
    {
      id: 'devotionals',
      title: 'Devotionals',
      icon: 'meditation',
      description: 'Daily readings',
      onPress: () => navigation.navigate('Devotions'),
      cardColor: '#f59e0b', // Amber
    },
    {
      id: 'serving',
      title: 'Serving',
      icon: 'community',
      description: 'Get involved',
      onPress: () => Alert.alert('Coming Soon', 'Serving resources coming soon!'),
      cardColor: '#06b6d4', // Cyan
    },
    {
      id: 'events',
      title: 'Events',
      icon: 'events',
      description: 'Upcoming events',
      onPress: () => navigation.navigate('Events'),
      cardColor: '#10b981', // Green
    },
  ];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.gradient}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Explore</Text>
          <Text style={styles.headerSubtitle}>Tools and resources for your journey</Text>
        </View>

        {/* Featured/Trending Section - Full Width */}
        <TouchableOpacity
          style={styles.featuredCard}
          onPress={featuredContent.onPress}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={featuredContent.gradientColors}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.featuredGradient}
          >
            <View style={styles.featuredContent}>
              <View style={styles.trendingBadge}>
                <Icon name={featuredContent.icon} size={14} color="#ffffff" />
                <Text style={styles.trendingText}>TRENDING</Text>
              </View>
              <Text style={styles.featuredTitle}>{featuredContent.title}</Text>
              <Text style={styles.featuredSubtitle}>{featuredContent.subtitle}</Text>
              <View style={styles.discoverButton}>
                <Text style={styles.discoverButtonText}>Explore →</Text>
              </View>
            </View>
          </LinearGradient>
        </TouchableOpacity>

        {/* Top Suggested Section - Two Column Grid */}
        <View style={styles.topSuggestedSection}>
          <Text style={styles.sectionTitle}>Top Suggested</Text>
          <View style={styles.suggestedGrid}>
            {topSuggested.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={styles.suggestedCard}
                onPress={item.onPress}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={item.gradientColors}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.suggestedGradient}
                >
                  <View style={styles.suggestedContent}>
                    <View style={styles.suggestedIconContainer}>
                      <Icon name={item.icon} size={24} color="#ffffff" />
                    </View>
                    <Text style={styles.suggestedTitle}>{item.title}</Text>
                    <Text style={styles.suggestedSubtitle}>{item.subtitle}</Text>
                  </View>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Categories Section - Two Column Grid */}
        <View style={styles.categoriesSection}>
          <Text style={styles.sectionTitle}>Categories</Text>
          <Text style={styles.sectionSubtitle}>Explore resources by topic</Text>
          
          <View style={styles.categoriesGrid}>
            {categories.map((category) => (
              <TouchableOpacity
                key={category.id}
                style={[styles.categoryCard, { backgroundColor: category.cardColor }]}
                onPress={category.onPress}
                activeOpacity={0.8}
              >
                <Icon name={category.icon} size={32} color="#ffffff" />
                <Text style={styles.categoryTitle}>{category.title}</Text>
                <Text style={styles.categoryDescription}>{category.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={{ height: Spacing.xxl }} />
      </View>
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
    padding: Spacing.screenPadding,
    backgroundColor: Colors.background,
  },
  header: {
    marginBottom: Spacing.sectionSpacing,
    marginTop: Spacing.lg,
    paddingBottom: Spacing.sm,
  },
  headerTitle: {
    fontSize: FontSizes.xxxl,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  featuredCard: {
    marginBottom: Spacing.sectionSpacing,
    borderRadius: 20,
    overflow: 'hidden',
  },
  featuredGradient: {
    padding: Spacing.cardPadding,
    minHeight: 180,
    justifyContent: 'center',
    borderRadius: 20,
  },
  featuredContent: {
    flex: 1,
  },
  trendingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: Spacing.md,
  },
  trendingText: {
    fontSize: FontSizes.xs,
    fontWeight: '700',
    color: '#ffffff',
    marginLeft: 4,
    letterSpacing: 0.5,
  },
  featuredTitle: {
    fontSize: FontSizes.xxl,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  featuredSubtitle: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: Spacing.md,
    lineHeight: 22,
  },
  discoverButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.lg,
    borderRadius: 12,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    marginTop: Spacing.xs,
  },
  discoverButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
  },
  topSuggestedSection: {
    marginBottom: Spacing.sectionSpacing,
  },
  suggestedGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  suggestedCard: {
    width: '48%',
    marginBottom: Spacing.cardGap,
    borderRadius: 20,
    overflow: 'hidden',
  },
  suggestedGradient: {
    padding: Spacing.cardPadding,
    borderRadius: 20,
    minHeight: 140,
    justifyContent: 'center',
  },
  suggestedContent: {
    alignItems: 'center',
  },
  suggestedIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  suggestedTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs / 2,
    textAlign: 'center',
  },
  suggestedSubtitle: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.85)',
    lineHeight: 18,
    textAlign: 'center',
  },
  categoriesSection: {
    marginBottom: Spacing.sectionSpacing,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  sectionSubtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
    lineHeight: 20,
    paddingBottom: Spacing.xs,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryCard: {
    width: '48%',
    borderRadius: 20,
    padding: Spacing.cardPadding,
    alignItems: 'center',
    minHeight: 160,
    justifyContent: 'center',
    marginBottom: Spacing.cardGap,
  },
  categoryTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: Spacing.md,
    marginBottom: Spacing.xs / 2,
    textAlign: 'center',
  },
  categoryDescription: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.85)',
    lineHeight: 18,
    textAlign: 'center',
  },
});

