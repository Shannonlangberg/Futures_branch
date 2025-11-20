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

  const tools = [
    {
      id: 'bible',
      title: 'Bible',
      emoji: '📖',
      description: 'Read Scripture and find verses',
      onPress: openBibleApp,
      color: '#6366f1',
    },
    {
      id: 'bible_search',
      title: 'Bible Search',
      emoji: '🔍',
      description: 'Search for verses and topics',
      onPress: openBibleSearch,
      color: '#8b5cf6',
    },
    {
      id: 'worship',
      title: 'Worship Resources',
      emoji: '🎵',
      description: 'Songs, lyrics, and playlists',
      onPress: () => Alert.alert('Coming Soon', 'Worship resources coming soon!'),
      color: '#ec4899',
    },
    {
      id: 'devotionals',
      title: 'Daily Devotionals',
      emoji: '📿',
      description: 'Daily readings and reflections',
      onPress: () => Alert.alert('Coming Soon', 'Daily devotionals coming soon!'),
      color: '#f59e0b',
    },
    {
      id: 'prayer',
      title: 'Prayer Guide',
      emoji: '🙏',
      description: 'Prayer resources and guides',
      onPress: () => navigation.navigate('Prayer'),
      color: '#10b981',
    },
    {
      id: 'serving',
      title: 'Serving Resources',
      emoji: '🤝',
      description: 'Training and guidelines',
      onPress: () => Alert.alert('Coming Soon', 'Serving resources coming soon!'),
      color: '#06b6d4',
    },
  ];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <LinearGradient
        colors={['#0f172a', '#1e293b', '#0f172a']}
        style={styles.gradient}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Explore</Text>
          <Text style={styles.headerSubtitle}>Tools and resources for your journey</Text>
        </View>

        <View style={styles.toolsGrid}>
          {tools.map((tool) => (
            <TouchableOpacity
              key={tool.id}
              style={styles.toolCard}
              onPress={tool.onPress}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={[`${tool.color}20`, `${tool.color}10`]}
                style={styles.toolGradient}
              >
                <Text style={styles.toolEmoji}>{tool.emoji}</Text>
                <Text style={styles.toolTitle}>{tool.title}</Text>
                <Text style={styles.toolDescription}>{tool.description}</Text>
              </LinearGradient>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Links</Text>
          <TouchableOpacity
            style={styles.linkCard}
            onPress={() => navigation.navigate('TVHome')}
          >
            <Text style={styles.linkEmoji}>📺</Text>
            <View style={styles.linkContent}>
              <Text style={styles.linkTitle}>Pulse TV</Text>
              <Text style={styles.linkDescription}>Watch discipleship content</Text>
            </View>
            <Text style={styles.linkArrow}>→</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkCard}
            onPress={() => navigation.navigate('Groups')}
          >
            <Text style={styles.linkEmoji}>👥</Text>
            <View style={styles.linkContent}>
              <Text style={styles.linkTitle}>Connect Groups</Text>
              <Text style={styles.linkDescription}>Join a community group</Text>
            </View>
            <Text style={styles.linkArrow}>→</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkCard}
            onPress={() => navigation.navigate('Events')}
          >
            <Text style={styles.linkEmoji}>📅</Text>
            <View style={styles.linkContent}>
              <Text style={styles.linkTitle}>Events</Text>
              <Text style={styles.linkDescription}>Upcoming church events</Text>
            </View>
            <Text style={styles.linkArrow}>→</Text>
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
    padding: Spacing.md,
  },
  header: {
    marginBottom: Spacing.xl,
    marginTop: Spacing.md,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.xs,
  },
  headerSubtitle: {
    fontSize: FontSizes.md,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  toolsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.md,
    marginBottom: Spacing.xl,
  },
  toolCard: {
    width: '48%',
    aspectRatio: 1.1,
    borderRadius: 16,
    overflow: 'hidden',
  },
  toolGradient: {
    flex: 1,
    padding: Spacing.md,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
  },
  toolEmoji: {
    fontSize: 48,
    marginBottom: Spacing.sm,
  },
  toolTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs,
    textAlign: 'center',
  },
  toolDescription: {
    fontSize: FontSizes.xs,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    lineHeight: 16,
  },
  section: {
    marginTop: Spacing.lg,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.md,
  },
  linkCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  linkEmoji: {
    fontSize: 32,
    marginRight: Spacing.md,
  },
  linkContent: {
    flex: 1,
  },
  linkTitle: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs / 2,
  },
  linkDescription: {
    fontSize: FontSizes.sm,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  linkArrow: {
    fontSize: 24,
    color: 'rgba(255, 255, 255, 0.5)',
    marginLeft: Spacing.sm,
  },
});

