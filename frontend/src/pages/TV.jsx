import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import SeriesCard from '../components/tv/SeriesCard';

const TV = () => {
  const [series, setSeries] = useState([]);
  const [continueWatching, setContinueWatching] = useState([]);
  const [mostWatched, setMostWatched] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch most watched series (uses actual watch data)
      const mostWatchedResponse = await fetch('/api/tv/most-watched', {
        credentials: 'include'
      });
      
      if (mostWatchedResponse.ok) {
        const mostWatchedData = await mostWatchedResponse.json();
        setMostWatched(mostWatchedData.series || []);
      }
      
      // Fetch all series
      const seriesResponse = await fetch('/api/tv/series', {
        credentials: 'include'
      });
      
      if (seriesResponse.ok) {
        const seriesData = await seriesResponse.json();
        const allSeries = seriesData.series || [];
        setSeries(allSeries);
      }
      
      // Fetch continue watching
      const continueResponse = await fetch('/api/tv/continue-watching', {
        credentials: 'include'
      });
      
      if (continueResponse.ok) {
        const continueData = await continueResponse.json();
        setContinueWatching(continueData.episodes || []);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching TV data:', err);
      setError('Failed to load content');
      setLoading(false);
    }
  };

  // Get all unique categories dynamically
  const allCategories = [...new Set(series.map(s => s.category).filter(Boolean))];
  
  // Group series by category
  const seriesByCategory = {};
  allCategories.forEach(cat => {
    seriesByCategory[cat] = series.filter(s => s.category === cat);
  });

  // Create placeholder cards for demo
  const createPlaceholders = (count) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `placeholder-${i}`,
      isPlaceholder: true
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-white text-xl">Loading Pulse TV...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-20">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Top Navigation Bar - Netflix Style */}
      <div className="sticky top-0 z-50 bg-gradient-to-r from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-sm border-b border-purple-500/20 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left Side - Pulse TV Logo */}
            <Link to="/tv" className="flex items-center gap-3">
              <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-pink-400 bg-clip-text text-transparent drop-shadow-lg">
                Pulse TV
              </div>
            </Link>

            {/* Right Side - Navigation (can add later) */}
            <div className="flex items-center gap-6 text-sm">
              <span className="text-gray-300 hover:text-purple-400 transition-colors cursor-pointer">Home</span>
              <span className="text-gray-300 hover:text-blue-400 transition-colors cursor-pointer">Series</span>
              <span className="text-gray-300 hover:text-pink-400 transition-colors cursor-pointer">Categories</span>
            </div>
          </div>
        </div>
      </div>

      <div className="pb-12 relative z-10">
        {/* Most Watched Section */}
        {mostWatched.length > 0 && (
          <div className="mb-8 mt-6">
            <div className="max-w-7xl mx-auto px-6">
              <h2 className="text-2xl font-bold mb-4 text-white flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                Most Watched
              </h2>
              <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                {/* Add some placeholders to show layout */}
                {[...mostWatched, ...createPlaceholders(2)].map((item, index) => {
                  if (item.isPlaceholder) {
                    return (
                      <div key={item.id} className="flex-shrink-0 w-64 h-40 bg-gradient-to-br from-slate-800/60 to-slate-900/60 rounded-lg border border-purple-500/20 flex items-center justify-center">
                        <span className="text-slate-400 text-sm">Coming Soon</span>
                      </div>
                    );
                  }
                  return (
                    <SeriesCard key={item.id} series={item} isLarge={true} />
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Continue Watching Section */}
        {continueWatching.length > 0 && (
          <div className="mb-8">
            <div className="max-w-7xl mx-auto px-6">
              <h2 className="text-2xl font-bold mb-4 text-white flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                Continue Watching
              </h2>
              <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                {continueWatching.slice(0, 8).map((episode) => (
                  <Link
                    key={episode.id}
                    to={`/tv/watch/${episode.episode_id}`}
                    className="group flex-shrink-0 w-48 rounded-lg overflow-hidden hover:scale-105 transition-transform duration-200 relative"
                  >
                    <div className="relative aspect-video bg-gradient-to-br from-purple-900/40 via-blue-900/40 to-pink-900/40">
                      {episode.series?.thumbnail_url ? (
                        <img
                          src={episode.series.thumbnail_url}
                          alt={episode.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : null}
                      <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
                      {/* Progress bar */}
                      {episode.progress?.last_position_seconds > 0 && episode.episode?.duration_seconds > 0 && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-600">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 via-blue-500 to-pink-500"
                            style={{
                              width: `${(episode.progress.last_position_seconds / episode.episode.duration_seconds) * 100}%`
                            }}
                          />
                        </div>
                      )}
                    </div>
                    <div className="mt-2">
                      <h3 className="text-white font-medium text-sm line-clamp-1">{episode.title}</h3>
                      <p className="text-xs text-gray-400 mt-1">{episode.series?.title}</p>
                    </div>
                  </Link>
                ))}
                {/* Add placeholders */}
                {createPlaceholders(2).map((item) => (
                  <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-slate-800/60 to-slate-900/60 rounded-lg border border-purple-500/20 flex items-center justify-center">
                    <span className="text-slate-400 text-xs">Coming Soon</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Category Rows - Horizontal Scrolling */}
        {allCategories.map((category) => {
          const categorySeries = seriesByCategory[category] || [];
          if (categorySeries.length === 0) return null;

          return (
            <div key={category} className="mb-8">
              <div className="max-w-7xl mx-auto px-6">
                <h2 className="text-2xl font-bold mb-4 text-white capitalize flex items-center gap-2">
                  <span className="w-1 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                  {category.replace(/_/g, ' ')}
                </h2>
                <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                  {categorySeries.map((s) => (
                    <SeriesCard key={s.id} series={s} />
                  ))}
                  {/* Add placeholders to show more content is coming */}
                  {createPlaceholders(Math.min(3, 6 - categorySeries.length)).map((item) => (
                    <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-slate-800/60 to-slate-900/60 rounded-lg border border-purple-500/20 flex items-center justify-center">
                      <span className="text-slate-400 text-xs">Coming Soon</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}

        {/* Add a "New This Week" row with placeholders */}
        <div className="mb-8">
          <div className="max-w-7xl mx-auto px-6">
            <h2 className="text-2xl font-bold mb-4 text-white flex items-center gap-2">
              <span className="w-1 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
              New This Week
            </h2>
            <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
              {createPlaceholders(6).map((item) => (
                <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-purple-900/30 via-blue-900/30 to-pink-900/30 rounded-lg border border-purple-500/30 flex flex-col items-center justify-center">
                  <span className="text-slate-400 text-xs mb-2">📺</span>
                  <span className="text-slate-400 text-xs">Coming Soon</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Empty State */}
        {series.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg">No series available yet</p>
          </div>
        )}
      </div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
};

export default TV;
