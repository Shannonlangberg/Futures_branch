import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Video } from 'expo-av';
import { WebView } from 'react-native-webview';
import { Linking } from 'react-native';
import { Colors, FontSizes, Spacing, API_BASE_URL } from '../constants/config';
import { ApiService } from '../services/ApiService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');
const VIDEO_HEIGHT = width * 0.5625; // 16:9 aspect ratio

export default function TVWatchScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { episodeId } = route.params || {};
  const videoRef = useRef(null);
  
  const [episode, setEpisode] = useState(null);
  const [series, setSeries] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [videoError, setVideoError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoType, setVideoType] = useState(null); // 'youtube', 'direct', or null
  const [youtubeId, setYoutubeId] = useState(null);

  useEffect(() => {
    if (episodeId) {
      loadEpisode();
    }
    
    // Load user for progress tracking
    AsyncStorage.getItem('userData').then(userData => {
      if (userData) {
        setUser(JSON.parse(userData));
      }
    });

    // Add hardware back button handler
    const unsubscribe = navigation.addListener('beforeRemove', (e) => {
      // Prevent default behavior of leaving the screen
      // Allow navigation if it's a programmatic navigation
      if (e.data.action.type === 'GO_BACK') {
        return;
      }
    });

    return unsubscribe;
  }, [episodeId, navigation]);

  useEffect(() => {
    // Save progress periodically (every 10 seconds) - only for direct videos
    if (videoType === 'direct' && episode && user && position > 0) {
      const progressInterval = setInterval(() => {
        saveProgress(position, false);
      }, 10000);
      return () => clearInterval(progressInterval);
    }
  }, [episode, user, position, videoType]);

  // Convert YouTube/Vimeo embed URLs to direct video URLs or detect YouTube
  const processVideoUrl = (url) => {
    if (!url) {
      console.log('[VIDEO] No URL provided');
      return { type: null, url: null, youtubeId: null };
    }

    console.log('[VIDEO] Processing URL:', url);

    // Normalize URL - remove extra whitespace
    url = url.trim();

    // If it's already a direct video URL (http/https), check what type
    if (url.startsWith('http://') || url.startsWith('https://')) {
      // Check for YouTube URLs - multiple formats
      // youtube.com/watch?v=VIDEO_ID
      // youtube.com/embed/VIDEO_ID
      // youtube.com/v/VIDEO_ID
      // youtu.be/VIDEO_ID
      // m.youtube.com/watch?v=VIDEO_ID
      const youtubePatterns = [
        /(?:youtube\.com\/watch\?v=|youtube\.com\/embed\/|youtube\.com\/v\/|youtu\.be\/|m\.youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})/,
        /youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})/,
      ];
      
      for (const pattern of youtubePatterns) {
        const youtubeMatch = url.match(pattern);
        if (youtubeMatch) {
          const videoId = youtubeMatch[1];
          console.log('[VIDEO] Detected YouTube video ID:', videoId);
          return { 
            type: 'youtube', 
            url: null, 
            youtubeId: videoId 
          };
        }
      }
      
      // Check if it's a Vimeo embed URL
      const vimeoMatch = url.match(/vimeo\.com\/(?:video\/|)(\d+)/);
      if (vimeoMatch) {
        console.log('[VIDEO] Detected Vimeo video');
        return { type: 'vimeo', url: null, youtubeId: null };
      }

      // Check if URL contains YouTube domain but we missed it
      if (url.includes('youtube.com') || url.includes('youtu.be')) {
        console.warn('[VIDEO] URL contains YouTube domain but pattern didn\'t match:', url);
        // Try to extract video ID manually
        const parts = url.split(/[?&]/);
        for (const part of parts) {
          if (part.startsWith('v=')) {
            const videoId = part.substring(2);
            if (videoId.length >= 11) {
              console.log('[VIDEO] Extracted YouTube video ID manually:', videoId);
              return {
                type: 'youtube',
                url: null,
                youtubeId: videoId.substring(0, 11)
              };
            }
          }
        }
      }

      // Check if it's a direct video file (mp4, m3u8, etc.)
      const directVideoExtensions = ['.mp4', '.m3u8', '.mov', '.avi', '.mkv', '.webm', '.m4v'];
      const hasDirectVideoExtension = directVideoExtensions.some(ext => 
        url.toLowerCase().includes(ext) || url.toLowerCase().match(/\.(mp4|m3u8|mov|avi|mkv|webm|m4v)(\?|$|#)/i)
      );
      
      if (hasDirectVideoExtension || (!url.includes('youtube') && !url.includes('vimeo'))) {
        console.log('[VIDEO] Detected direct video URL');
        return { type: 'direct', url: url, youtubeId: null };
      }

      // Default to direct if we can't determine
      console.log('[VIDEO] Defaulting to direct video URL');
      return { type: 'direct', url: url, youtubeId: null };
    }

    // If it's a relative path, prepend API base URL
    if (url.startsWith('/')) {
      const fullUrl = `${API_BASE_URL}${url}`;
      console.log('[VIDEO] Relative path, converted to:', fullUrl);
      return { type: 'direct', url: fullUrl, youtubeId: null };
    }

    console.log('[VIDEO] Unknown URL format, defaulting to direct');
    return { type: 'direct', url: url, youtubeId: null };
  };

  const loadEpisode = async () => {
    try {
      setLoading(true);
      setError(null);
      setVideoError(null);
      
      const data = await ApiService.getTVEpisode(episodeId);
      if (data.episode) {
        setEpisode(data.episode);
        
        // Process video URL
        const processed = processVideoUrl(data.episode.video_url);
        console.log('[VIDEO] Processed result:', processed);
        setVideoType(processed.type);
        
        if (processed.type === 'youtube') {
          console.log('[VIDEO] Setting up YouTube player with ID:', processed.youtubeId);
          setYoutubeId(processed.youtubeId);
          setVideoUrl(null); // Ensure videoUrl is null for YouTube
        } else if (processed.type === 'direct') {
          // Double-check it's not a YouTube URL that slipped through
          if (processed.url && (processed.url.includes('youtube.com') || processed.url.includes('youtu.be'))) {
            console.warn('[VIDEO] YouTube URL detected but marked as direct! Fixing...');
            // Try to extract YouTube ID
            const youtubeMatch = processed.url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
            if (youtubeMatch) {
              const videoId = youtubeMatch[1];
              console.log('[VIDEO] Fixed - using YouTube player with ID:', videoId);
              setVideoType('youtube');
              setYoutubeId(videoId);
              setVideoUrl(null);
            } else {
              setVideoError('Invalid YouTube URL format. Please check the video URL.');
            }
          } else {
            console.log('[VIDEO] Setting up direct video player with URL:', processed.url);
            setVideoUrl(processed.url);
            setYoutubeId(null); // Ensure youtubeId is null for direct videos
          }
        } else if (processed.type === 'vimeo') {
          setVideoError('Vimeo videos are not yet supported. Please use YouTube or direct video URLs.');
        } else {
          setVideoError('No video URL available for this episode');
        }
        
        // Set initial position from progress (only for direct videos)
        if (processed.type === 'direct' && data.episode.progress?.last_position_seconds) {
          setPosition(data.episode.progress.last_position_seconds);
        }
        
        // Load series if available
        if (data.episode.series_id) {
          try {
            const seriesData = await ApiService.getTVSeriesDetail(data.episode.series_id);
            if (seriesData.series) {
              setSeries(seriesData.series);
            }
          } catch (err) {
            console.warn('Could not load series:', err);
          }
        }
      } else {
        setError('Episode not found');
      }
    } catch (err) {
      console.error('Error loading episode:', err);
      setError('Failed to load episode. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const saveProgress = async (currentPosition, completed) => {
    if (!episode || !user) return;
    
    try {
      await ApiService.updateEpisodeProgress(episode.id, currentPosition, completed);
      
      if (completed) {
        Alert.alert(
          'Episode Completed! 🎉',
          'Your progress has been saved and added to your Heartbeat.',
          [{ text: 'OK' }]
        );
      }
    } catch (err) {
      console.error('Error saving progress:', err);
    }
  };

  const handlePlaybackStatusUpdate = (status) => {
    if (status.isLoaded) {
      setIsPlaying(status.isPlaying);
      setPosition(status.positionMillis / 1000); // Convert to seconds
      setDuration(status.durationMillis / 1000);
      
      // Calculate progress percentage
      if (status.durationMillis > 0) {
        const progressPercent = (status.positionMillis / status.durationMillis) * 100;
        setProgress(progressPercent);
      }
      
      // Auto-save when near completion (95%)
      if (status.durationMillis > 0 && status.positionMillis > 0) {
        const completionPercent = (status.positionMillis / status.durationMillis) * 100;
        if (completionPercent >= 95 && !episode.progress?.completed) {
          saveProgress(status.positionMillis / 1000, true);
        }
      }

      // Handle errors
      if (status.error) {
        console.error('Video playback error:', status.error);
        setVideoError(`Video playback error: ${status.error}`);
      }
    } else if (status.error) {
      console.error('Video loading error:', status.error);
      setVideoError(`Failed to load video: ${status.error}`);
    }
  };

  const handleVideoError = (error) => {
    console.error('[VIDEO] expo-av error:', error);
    const errorCode = error?.code || error?.errorCode;
    const errorMessage = error?.message || '';
    
    // Error 153 usually means configuration issue or unsupported format
    if (errorCode === 153 || errorMessage.includes('153')) {
      setVideoError('Video format not supported. This may be a YouTube URL that needs to be converted. Please check the video URL.');
    } else if (videoUrl && (videoUrl.includes('youtube') || videoUrl.includes('youtu.be'))) {
      setVideoError('This appears to be a YouTube URL. YouTube videos should be detected automatically. Please check the URL format.');
    } else {
      setVideoError(`Failed to load video (Error ${errorCode || 'unknown'}). The video URL may be invalid or the video may not be accessible.`);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0:00';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  };

  const handleBack = () => {
    navigation.goBack();
  };

  const openInYouTube = (videoId) => {
    const youtubeUrl = `https://www.youtube.com/watch?v=${videoId}`;
    Linking.openURL(youtubeUrl).catch(err => {
      console.error('Failed to open YouTube:', err);
      Alert.alert('Error', 'Unable to open YouTube app. Please check if YouTube is installed.');
    });
  };

  // Generate YouTube embed HTML with better error handling
  const getYouTubeEmbedHTML = (videoId) => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
          <style>
            * {
              margin: 0;
              padding: 0;
              box-sizing: border-box;
            }
            html, body {
              width: 100%;
              height: 100%;
              overflow: hidden;
              background: #000;
            }
            .video-container {
              width: 100%;
              height: 100%;
              position: relative;
              display: flex;
              justify-content: center;
              align-items: center;
            }
            iframe {
              width: 100%;
              height: 100%;
              border: none;
              position: absolute;
              top: 0;
              left: 0;
            }
            .error-message {
              color: #fff;
              text-align: center;
              padding: 20px;
              font-family: Arial, sans-serif;
            }
          </style>
        </head>
        <body>
          <div class="video-container">
            <iframe
              id="youtube-player"
              src="https://www.youtube.com/embed/${videoId}?playsinline=1&rel=0&modestbranding=1&controls=1&showinfo=0&fs=1&origin=${encodeURIComponent('https://www.youtube.com')}"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowfullscreen
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
            ></iframe>
            <div id="error" class="error-message" style="display: none;">
              <p>Unable to load YouTube video.</p>
              <p>This video may have embedding restrictions.</p>
              <p>Please try opening in the YouTube app.</p>
            </div>
          </div>
          <script>
            var iframe = document.getElementById('youtube-player');
            
            iframe.addEventListener('load', function() {
              console.log('YouTube iframe loaded');
            });
            
            iframe.addEventListener('error', function(e) {
              console.error('YouTube iframe error:', e);
              document.getElementById('error').style.display = 'block';
            });
            
            // Listen for YouTube API errors
            window.addEventListener('message', function(event) {
              if (event.data && event.data.error) {
                console.error('YouTube API error:', event.data.error);
                if (event.data.error === 153 || event.data.error === '150') {
                  document.getElementById('error').style.display = 'block';
                }
              }
            });
          </script>
        </body>
      </html>
    `;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#ffffff" />
        <Text style={styles.loadingText}>Loading episode...</Text>
      </View>
    );
  }

  if (error || !episode) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error || 'Episode not found'}</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={handleBack}
        >
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Back Button - Always visible */}
      <TouchableOpacity
        style={styles.backButtonHeader}
        onPress={handleBack}
      >
        <Text style={styles.backButtonIcon}>←</Text>
      </TouchableOpacity>

      {/* Video Player */}
      {videoType === 'youtube' && youtubeId ? (
        <View style={styles.videoContainer}>
          <WebView
            source={{ uri: `https://www.youtube.com/embed/${youtubeId}?playsinline=1&rel=0&modestbranding=1&controls=1&showinfo=0&fs=1` }}
            style={styles.video}
            allowsInlineMediaPlayback={true}
            mediaPlaybackRequiresUserAction={false}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            allowsFullscreenVideo={true}
            mixedContentMode="always"
            startInLoadingState={true}
            onError={(syntheticEvent) => {
              const { nativeEvent } = syntheticEvent;
              console.error('WebView error:', nativeEvent);
              // Try fallback to watch URL
              if (!nativeEvent.url?.includes('watch')) {
                setVideoError('Failed to load embedded video. Trying alternative method...');
                // Fallback: try opening in app
                setTimeout(() => {
                  openInYouTube(youtubeId);
                }, 2000);
              } else {
                setVideoError('Failed to load YouTube video. The video may have embedding restrictions.');
              }
            }}
            onHttpError={(syntheticEvent) => {
              const { nativeEvent } = syntheticEvent;
              console.error('WebView HTTP error:', nativeEvent);
              // Error 153 is a YouTube embed error - suggest opening in app
              if (nativeEvent.statusCode === 153 || nativeEvent.url?.includes('youtube.com/embed')) {
                Alert.alert(
                  'Embedding Restricted',
                  'This video cannot be embedded. Would you like to open it in the YouTube app instead?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Open in YouTube', onPress: () => openInYouTube(youtubeId) }
                  ]
                );
              } else {
                setVideoError(`HTTP error: ${nativeEvent.statusCode}`);
              }
            }}
            onShouldStartLoadWithRequest={(request) => {
              // Allow YouTube embeds and related domains
              const allowedDomains = ['youtube.com', 'youtu.be', 'google.com', 'gstatic.com', 'ggpht.com'];
              const isAllowed = allowedDomains.some(domain => request.url.includes(domain)) || 
                               request.url.startsWith('data:') || 
                               request.url.startsWith('about:blank');
              
              if (!isAllowed && request.url !== request.navigationType) {
                // If navigating away from YouTube, open in external browser
                Linking.openURL(request.url).catch(err => console.error('Failed to open URL:', err));
                return false;
              }
              
              return isAllowed;
            }}
            renderLoading={() => (
              <View style={styles.loadingOverlay}>
                <ActivityIndicator size="large" color="#e50914" />
                <Text style={styles.loadingText}>Loading YouTube video...</Text>
              </View>
            )}
          />
        </View>
      ) : videoType === 'direct' && videoUrl && !videoError ? (
        <View style={styles.videoContainer}>
          {(() => {
            // Final safety check - never pass YouTube URLs to expo-av
            if (videoUrl && (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be'))) {
              console.error('[VIDEO] SAFETY CHECK FAILED: YouTube URL passed to expo-av!');
              setVideoError('Video URL format error. Please contact support.');
              return null;
            }
            console.log('[VIDEO] Rendering expo-av player with URL:', videoUrl);
            return (
              <Video
                ref={videoRef}
                source={{ uri: videoUrl }}
                style={styles.video}
                resizeMode="contain"
                useNativeControls
                shouldPlay={false}
                positionMillis={position * 1000} // Set initial position
                onPlaybackStatusUpdate={handlePlaybackStatusUpdate}
                onError={handleVideoError}
                progressUpdateIntervalMillis={5000} // Update every 5 seconds
              />
            );
          })()}
        </View>
      ) : (
        <View style={[styles.video, styles.videoPlaceholder]}>
          <LinearGradient
            colors={['#1e293b', '#334155']}
            style={styles.placeholderGradient}
          >
            {videoError ? (
              <>
                <Text style={styles.errorIcon}>⚠️</Text>
                <Text style={styles.placeholderText}>{videoError}</Text>
                <Text style={styles.placeholderSubtext}>{episode.title}</Text>
                <View style={styles.buttonRow}>
                  {videoType === 'youtube' && youtubeId && (
                    <TouchableOpacity
                      style={[styles.retryButton, styles.youtubeButton]}
                      onPress={() => openInYouTube(youtubeId)}
                    >
                      <Text style={styles.retryButtonText}>Open in YouTube</Text>
                    </TouchableOpacity>
                  )}
                  <TouchableOpacity
                    style={styles.retryButton}
                    onPress={loadEpisode}
                  >
                    <Text style={styles.retryButtonText}>Retry</Text>
                  </TouchableOpacity>
                </View>
              </>
            ) : (
              <>
                <Text style={styles.placeholderText}>Video Coming Soon</Text>
                <Text style={styles.placeholderSubtext}>{episode.title}</Text>
              </>
            )}
          </LinearGradient>
        </View>
      )}

      {/* Episode Info */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <LinearGradient
          colors={['#000000', '#1a1a1a', '#000000']}
          style={styles.gradient}
        >
          <View style={styles.info}>
            <Text style={styles.title}>{episode.title}</Text>
            
            {series && (
              <TouchableOpacity
                onPress={() => navigation.navigate('TVSeries', { seriesId: series.id })}
                style={styles.seriesLink}
              >
                <Text style={styles.seriesLinkText}>{series.title} →</Text>
              </TouchableOpacity>
            )}
            
            {episode.description && (
              <Text style={styles.description}>{episode.description}</Text>
            )}

            {/* Progress Info - Only for direct videos */}
            {videoType === 'direct' && progress > 0 && (
              <View style={styles.progressInfo}>
                <Text style={styles.progressText}>
                  {formatTime(position)} / {formatTime(duration)}
                </Text>
                <View style={styles.progressBarContainer}>
                  <View style={[styles.progressBar, { width: `${progress}%` }]} />
                </View>
              </View>
            )}

            {/* Episode Meta */}
            <View style={styles.meta}>
              {episode.order_index && series && (
                <Text style={styles.metaText}>
                  Episode {episode.order_index} of {series.episodes?.length || '?'}
                </Text>
              )}
              {episode.duration_seconds > 0 && (
                <Text style={styles.metaText}>
                  Duration: {formatTime(episode.duration_seconds)}
                </Text>
              )}
              {videoType === 'youtube' && (
                <Text style={styles.metaText}>YouTube Video</Text>
              )}
            </View>
          </View>
        </LinearGradient>
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
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
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
  backButtonHeader: {
    position: 'absolute',
    top: 50,
    left: Spacing.md,
    zIndex: 1000,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonIcon: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  backButton: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: '#e50914',
    borderRadius: 8,
  },
  backButtonText: {
    color: '#ffffff',
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
  videoContainer: {
    width: width,
    height: VIDEO_HEIGHT,
    backgroundColor: '#000000',
  },
  video: {
    width: width,
    height: VIDEO_HEIGHT,
    backgroundColor: '#000000',
  },
  videoPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderGradient: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.md,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: Spacing.md,
  },
  placeholderText: {
    fontSize: FontSizes.xl,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  placeholderSubtext: {
    fontSize: FontSizes.md,
    color: '#b3b3b3',
    textAlign: 'center',
    paddingHorizontal: Spacing.md,
    marginBottom: Spacing.md,
  },
  retryButton: {
    marginTop: Spacing.md,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: '#e50914',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: FontSizes.md,
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: Spacing.md,
  },
  youtubeButton: {
    backgroundColor: '#FF0000',
  },
  content: {
    flex: 1,
  },
  gradient: {
    flex: 1,
    padding: Spacing.md,
  },
  info: {
    marginTop: Spacing.md,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: Spacing.sm,
    letterSpacing: -0.5,
  },
  seriesLink: {
    marginBottom: Spacing.md,
  },
  seriesLinkText: {
    fontSize: FontSizes.md,
    color: '#e50914',
    fontWeight: '600',
  },
  description: {
    fontSize: FontSizes.md,
    color: '#b3b3b3',
    lineHeight: 22,
    marginBottom: Spacing.md,
  },
  progressInfo: {
    marginBottom: Spacing.md,
  },
  progressText: {
    fontSize: FontSizes.sm,
    color: '#b3b3b3',
    marginBottom: Spacing.xs,
  },
  progressBarContainer: {
    height: 4,
    backgroundColor: '#2a2a2a',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#e50914',
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: '#2a2a2a',
  },
  metaText: {
    fontSize: FontSizes.sm,
    color: '#808080',
  },
});
