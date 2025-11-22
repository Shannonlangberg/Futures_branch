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

  // Featured Pulse TV content
  const featuredContent = {
    title: 'Pulse TV',
    subtitle: 'Watch discipleship content and grow in your faith',
    onPress: () => navigation.navigate('TVHome'),
    gradientColors: ['#6366f1', '#8b5cf6'],
  };

  const tools = [
    {
      id: 'bible',
      title: 'Bible',
      icon: 'resources',
      description: 'Read Scripture and find verses',
      onPress: openBibleApp,
      cardColor: '#6366f1', // Indigo
    },
    {
      id: 'bible_search',
      title: 'Bible Search',
      icon: 'search',
      description: 'Search for verses and topics',
      onPress: openBibleSearch,
      cardColor: '#8b5cf6', // Purple
    },
    {
      id: 'worship',
      title: 'Worship Resources',
      icon: 'music',
      description: 'Songs, lyrics, and playlists',
      onPress: () => Alert.alert('Coming Soon', 'Worship resources coming soon!'),
      cardColor: '#ec4899', // Pink
    },
    {
      id: 'devotionals',
      title: 'Daily Devotionals',
      icon: 'meditation',
      description: 'Daily readings and reflections',
      onPress: () => Alert.alert('Coming Soon', 'Daily devotionals coming soon!'),
      cardColor: '#f59e0b', // Amber
    },
    {
      id: 'prayer',
      title: 'Prayer Guide',
      icon: 'prayer',
      description: 'Prayer resources and guides',
      onPress: () => navigation.navigate('Prayer'),
      cardColor: '#ef4444', // Red
    },
    {
      id: 'serving',
      title: 'Serving Resources',
      icon: 'community',
      description: 'Training and guidelines',
      onPress: () => Alert.alert('Coming Soon', 'Serving resources coming soon!'),
      cardColor: '#06b6d4', // Cyan
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
            <View style={styles.featuredTextContainer}>
              <View style={styles.trendingBadge}>
                <Icon name="tv" size={14} color="#ffffff" />
                <Text style={styles.trendingText}>TRENDING</Text>
              </View>
              <Text style={styles.featuredTitle}>{featuredContent.title}</Text>
              <Text style={styles.featuredSubtitle}>{featuredContent.subtitle}</Text>
              <View style={styles.discoverButton}>
                <Text style={styles.discoverButtonText}>Let's discover</Text>
              </View>
            </View>
          </LinearGradient>
        </TouchableOpacity>

        {/* Resource Categories Section */}
        <View style={styles.categoriesSection}>
          <Text style={styles.sectionTitle}>Resource Categories</Text>
          <Text style={styles.sectionSubtitle}>Curated tools organized by ministry area</Text>
          
          <View style={styles.toolsGrid}>
            {tools.map((tool) => (
              <TouchableOpacity
                key={tool.id}
                style={[styles.toolCard, { backgroundColor: tool.cardColor }]}
                onPress={tool.onPress}
                activeOpacity={0.8}
              >
                <Icon name={tool.icon} size={36} color="#ffffff" />
                <Text style={styles.toolTitleWhite}>{tool.title}</Text>
                <Text style={styles.toolDescriptionWhite}>{tool.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={{ height: 100 }} />
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
    marginTop: Spacing.md,
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
    padding: Spacing.xl,
    minHeight: 180,
    justifyContent: 'center',
  },
  featuredTextContainer: {
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
  },
  discoverButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
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
    marginBottom: Spacing.lg,
    lineHeight: 20,
  },
  toolsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  toolCard: {
    width: '48%',
    borderRadius: 20,
    padding: Spacing.lg,
    marginBottom: Spacing.md,
    alignItems: 'center',
    minHeight: 180,
    justifyContent: 'center',
  },
  toolTitleWhite: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: Spacing.md,
    marginBottom: Spacing.xs,
    textAlign: 'center',
  },
  toolDescriptionWhite: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 18,
    textAlign: 'center',
  },
});

