import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Image,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { Colors, FontSizes, Spacing, API_BASE_URL } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width * 0.38; // Smaller, tighter spacing
const LARGE_CARD_WIDTH = width * 0.92; // Almost full width for featured
const CARD_HEIGHT_LARGE = LARGE_CARD_WIDTH * 0.56; // Netflix-style featured card
const CARD_HEIGHT = CARD_WIDTH * 0.56; // 16:9 for regular cards

export default function TVHomeScreen() {
  const navigation = useNavigation();
  const [user, setUser] = useState(null);
  const [series, setSeries] = useState([]);
  const [mostWatched, setMostWatched] = useState([]);
  const [continueWatching, setContinueWatching] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const userData = await AsyncStorage.getItem('userData');
      if (userData) {
        setUser(JSON.parse(userData));
      }

      const seriesData = await ApiService.getTVSeries();
      if (seriesData.series) {
        setSeries(seriesData.series || []);
      }

      const mostWatchedData = await ApiService.getMostWatched();
      if (mostWatchedData.series) {
        setMostWatched(mostWatchedData.series || []);
      }

      const continueData = await ApiService.getContinueWatching();
      if (continueData.episodes) {
        setContinueWatching(continueData.episodes || []);
      }
    } catch (error) {
      console.error('Error loading TV data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  // Group series by category
  const seriesByCategory = {};
  series.forEach(s => {
    const category = s.category || 'Other';
    if (!seriesByCategory[category]) {
      seriesByCategory[category] = [];
    }
    seriesByCategory[category].push(s);
  });

  const categories = Object.keys(seriesByCategory);

  const renderSeriesCard = (seriesItem, isLarge = false) => {
    const imageUrl = seriesItem.thumbnail_url
      ? (seriesItem.thumbnail_url.startsWith('http')
          ? seriesItem.thumbnail_url
          : `${API_BASE_URL}${seriesItem.thumbnail_url}`)
      : null;

    return (
      <TouchableOpacity
        key={seriesItem.id}
        style={[
          styles.seriesCard,
          isLarge ? styles.seriesCardLarge : styles.seriesCardRegular
        ]}
        onPress={() => navigation.navigate('TVSeries', { seriesId: seriesItem.id })}
        activeOpacity={0.9}
      >
        <View style={[
          styles.seriesCardImage,
          isLarge ? styles.seriesCardImageLarge : styles.seriesCardImageRegular
        ]}>
          {imageUrl ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.seriesImage}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.placeholderContainer}>
              <LinearGradient
                colors={['#1e293b', '#334155']}
                style={styles.placeholderGradient}
              />
            </View>
          )}
          {/* Subtle overlay on hover/press */}
          <View style={styles.cardOverlay} />
        </View>
      </TouchableOpacity>
    );
  };

  const renderContinueWatchingCard = (episode) => {
    const progress = episode.progress?.last_position_seconds || 0;
    const duration = episode.episode?.duration_seconds || 1;
    const progressPercent = duration > 0 ? (progress / duration) * 100 : 0;
    
    const imageUrl = episode.series?.thumbnail_url
      ? (episode.series.thumbnail_url.startsWith('http')
          ? episode.series.thumbnail_url
          : `${API_BASE_URL}${episode.series.thumbnail_url}`)
      : null;

    return (
      <TouchableOpacity
        key={episode.id || episode.episode_id}
        style={styles.continueCard}
        onPress={() => navigation.navigate('TVWatch', { episodeId: episode.episode_id || episode.id })}
        activeOpacity={0.9}
      >
        <View style={styles.continueCardImage}>
          {imageUrl ? (
            <Image
              source={{ uri: imageUrl }}
              style={styles.continueImage}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.placeholderContainer}>
              <LinearGradient
                colors={['#1e293b', '#334155']}
                style={styles.placeholderGradient}
              />
            </View>
          )}
          {/* Progress bar - Netflix style */}
          {progressPercent > 0 && (
            <View style={styles.progressBarContainer}>
              <View style={[styles.progressBar, { width: `${progressPercent}%` }]} />
            </View>
          )}
          {/* Play icon overlay */}
          <View style={styles.playIconOverlay}>
            <View style={styles.playIcon}>
              <Text style={styles.playIconText}>▶</Text>
            </View>
          </View>
        </View>
        <View style={styles.continueTextContainer}>
          <Text style={styles.continueTitle} numberOfLines={1}>
            {episode.title || episode.episode?.title}
          </Text>
          <Text style={styles.continueSeries} numberOfLines={1}>
            {episode.series?.title || 'Series'}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#ffffff" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#ffffff" />}
        showsVerticalScrollIndicator={false}
      >
        {/* Header - Minimal, Netflix style */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>For You</Text>
        </View>

        {/* Continue Watching */}
        {continueWatching.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Continue Watching</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalScroll}
              snapToInterval={CARD_WIDTH + Spacing.sm}
              decelerationRate="fast"
            >
              {continueWatching.map(renderContinueWatchingCard)}
            </ScrollView>
          </View>
        )}

        {/* Most Watched - Large Featured Cards */}
        {mostWatched.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Most Watched</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalScroll}
              snapToInterval={LARGE_CARD_WIDTH + Spacing.md}
              decelerationRate="fast"
            >
              {mostWatched.map(item => renderSeriesCard(item, true))}
            </ScrollView>
          </View>
        )}

        {/* Categories */}
        {categories.map(category => (
          <View key={category} style={styles.section}>
            <Text style={styles.sectionTitle}>{category}</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalScroll}
              snapToInterval={CARD_WIDTH + Spacing.sm}
              decelerationRate="fast"
            >
              {seriesByCategory[category].map(item => renderSeriesCard(item))}
            </ScrollView>
          </View>
        ))}

        {series.length === 0 && !loading && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No content available</Text>
          </View>
        )}

        {/* Bottom spacing */}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: Spacing.md,
    color: '#ffffff',
    fontSize: FontSizes.md,
  },
  header: {
    paddingTop: Spacing.lg,
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.lg,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.5,
  },
  section: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.md,
    letterSpacing: -0.3,
  },
  horizontalScroll: {
    paddingLeft: Spacing.md,
    paddingRight: Spacing.sm,
  },
  // Regular Series Cards
  seriesCardRegular: {
    width: CARD_WIDTH,
    marginRight: Spacing.sm,
  },
  seriesCardImageRegular: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: 6,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
  },
  // Large Featured Cards
  seriesCardLarge: {
    width: LARGE_CARD_WIDTH,
    marginRight: Spacing.md,
  },
  seriesCardImageLarge: {
    width: LARGE_CARD_WIDTH,
    height: CARD_HEIGHT_LARGE,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
  },
  seriesCardImage: {
    position: 'relative',
  },
  seriesImage: {
    width: '100%',
    height: '100%',
  },
  placeholderContainer: {
    width: '100%',
    height: '100%',
  },
  placeholderGradient: {
    width: '100%',
    height: '100%',
  },
  cardOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'transparent',
  },
  // Continue Watching Cards
  continueCard: {
    width: CARD_WIDTH,
    marginRight: Spacing.sm,
  },
  continueCardImage: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: 6,
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    marginBottom: Spacing.xs,
  },
  continueImage: {
    width: '100%',
    height: '100%',
  },
  progressBarContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#e50914', // Netflix red
  },
  playIconOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  playIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  playIconText: {
    color: '#ffffff',
    fontSize: 18,
    marginLeft: 3, // Slight offset for play icon
  },
  continueTextContainer: {
    paddingHorizontal: 2,
  },
  continueTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
    letterSpacing: -0.2,
  },
  continueSeries: {
    fontSize: 11,
    color: '#b3b3b3',
    letterSpacing: -0.1,
  },
  emptyContainer: {
    padding: Spacing.xxl,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: '#b3b3b3',
  },
});
