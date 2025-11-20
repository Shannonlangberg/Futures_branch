import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Image,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Colors, FontSizes, Spacing, API_BASE_URL } from '../constants/config';
import { ApiService } from '../services/ApiService';

const { width } = Dimensions.get('window');
const EPISODE_CARD_WIDTH = width - Spacing.md * 2;

export default function TVSeriesScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { seriesId } = route.params || {};
  const [series, setSeries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (seriesId) {
      loadSeries();
    }
  }, [seriesId]);

  const loadSeries = async () => {
    try {
      setLoading(true);
      const data = await ApiService.getTVSeriesDetail(seriesId);
      if (data.series) {
        setSeries(data.series);
      } else {
        setError('Series not found');
      }
    } catch (err) {
      console.error('Error loading series:', err);
      setError('Failed to load series');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const renderEpisodeCard = (episode, index) => {
    const progress = episode.progress;
    const progressPercent = progress && episode.duration_seconds > 0
      ? (progress.last_position_seconds / episode.duration_seconds) * 100
      : 0;

    const episodeNumber = episode.order_index || index + 1;

    return (
      <TouchableOpacity
        key={episode.id}
        style={styles.episodeCard}
        onPress={() => navigation.navigate('TVWatch', { episodeId: episode.id })}
        activeOpacity={0.9}
      >
        <View style={styles.episodeLeft}>
          <Text style={styles.episodeNumber}>{episodeNumber}</Text>
        </View>
        <View style={styles.episodeRight}>
          <Text style={styles.episodeTitle} numberOfLines={2}>
            {episode.title}
          </Text>
          {episode.description && (
            <Text style={styles.episodeDescription} numberOfLines={2}>
              {episode.description}
            </Text>
          )}
          <View style={styles.episodeMeta}>
            {episode.duration_seconds > 0 && (
              <Text style={styles.episodeDuration}>
                {formatDuration(episode.duration_seconds)}
              </Text>
            )}
            {progress && progress.completed && (
              <View style={styles.completedBadge}>
                <Text style={styles.completedText}>✓</Text>
              </View>
            )}
          </View>
          {progressPercent > 0 && progressPercent < 100 && (
            <View style={styles.episodeProgressContainer}>
              <View style={[styles.episodeProgressBar, { width: `${progressPercent}%` }]} />
            </View>
          )}
        </View>
        <Text style={styles.playArrow}>▶</Text>
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

  if (error || !series) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error || 'Series not found'}</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const imageUrl = series.thumbnail_url
    ? (series.thumbnail_url.startsWith('http')
        ? series.thumbnail_url
        : `${API_BASE_URL}${series.thumbnail_url}`)
    : null;

  return (
    <View style={styles.container}>
      {/* Header Image */}
      <View style={styles.headerImageContainer}>
        {imageUrl ? (
          <Image
            source={{ uri: imageUrl }}
            style={styles.headerImage}
            resizeMode="cover"
          />
        ) : (
          <LinearGradient
            colors={['#1e293b', '#334155']}
            style={styles.headerImagePlaceholder}
          />
        )}
        <LinearGradient
          colors={['transparent', '#000000']}
          style={styles.headerGradient}
        />
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Series Info */}
        <View style={styles.info}>
          <Text style={styles.title}>{series.title}</Text>
          {series.description && (
            <Text style={styles.description}>{series.description}</Text>
          )}
        </View>

        {/* Episodes List */}
        <View style={styles.episodesSection}>
          <Text style={styles.episodesTitle}>
            Episodes {series.episodes?.length ? `(${series.episodes.length})` : ''}
          </Text>
          
          {series.episodes && series.episodes.length > 0 ? (
            <View style={styles.episodesList}>
              {series.episodes
                .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
                .map((episode, index) => renderEpisodeCard(episode, index))}
            </View>
          ) : (
            <View style={styles.emptyEpisodes}>
              <Text style={styles.emptyEpisodesText}>No episodes available</Text>
            </View>
          )}
        </View>

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
  errorContainer: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  errorText: {
    fontSize: FontSizes.lg,
    color: '#e50914',
    marginBottom: Spacing.lg,
    textAlign: 'center',
  },
  backButton: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: '#ffffff',
    borderRadius: 4,
  },
  backButtonText: {
    color: '#000000',
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
  headerImageContainer: {
    height: 280,
    position: 'relative',
  },
  headerImage: {
    width: '100%',
    height: '100%',
  },
  headerImagePlaceholder: {
    width: '100%',
    height: '100%',
  },
  headerGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 150,
  },
  scrollView: {
    flex: 1,
  },
  info: {
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.md,
    marginTop: -60,
    zIndex: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.sm,
    letterSpacing: -0.5,
  },
  description: {
    fontSize: 15,
    color: '#b3b3b3',
    lineHeight: 22,
    marginBottom: Spacing.lg,
    letterSpacing: -0.2,
  },
  episodesSection: {
    paddingHorizontal: Spacing.md,
  },
  episodesTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.md,
    letterSpacing: -0.3,
  },
  episodesList: {
    gap: Spacing.sm,
  },
  episodeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 6,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  episodeLeft: {
    width: 40,
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  episodeNumber: {
    fontSize: 20,
    fontWeight: '700',
    color: '#b3b3b3',
  },
  episodeRight: {
    flex: 1,
  },
  episodeTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.xs / 2,
    letterSpacing: -0.2,
  },
  episodeDescription: {
    fontSize: 13,
    color: '#b3b3b3',
    marginBottom: Spacing.xs,
    lineHeight: 18,
  },
  episodeMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  episodeDuration: {
    fontSize: 12,
    color: '#808080',
  },
  completedBadge: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#e50914',
    justifyContent: 'center',
    alignItems: 'center',
  },
  completedText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  episodeProgressContainer: {
    marginTop: Spacing.xs,
    height: 2,
    backgroundColor: '#2a2a2a',
    borderRadius: 1,
    overflow: 'hidden',
  },
  episodeProgressBar: {
    height: '100%',
    backgroundColor: '#e50914',
  },
  playArrow: {
    fontSize: 16,
    color: '#808080',
    marginLeft: Spacing.sm,
  },
  emptyEpisodes: {
    padding: Spacing.xl,
    alignItems: 'center',
  },
  emptyEpisodesText: {
    fontSize: FontSizes.md,
    color: '#b3b3b3',
  },
});
