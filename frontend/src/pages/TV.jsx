import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import SeriesCard from '../components/tv/SeriesCard';

const TV = () => {
  const [series, setSeries] = useState([]);
  const [continueWatching, setContinueWatching] = useState([]);
  const [mostWatched, setMostWatched] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);

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
  
  // Filter series if category is selected
  const filteredSeries = selectedCategory 
    ? series.filter(s => s.category === selectedCategory)
    : series;
  
  // Filter categories for display
  const filteredSeriesByCategory = {};
  if (selectedCategory) {
    filteredSeriesByCategory[selectedCategory] = seriesByCategory[selectedCategory] || [];
  } else {
    Object.assign(filteredSeriesByCategory, seriesByCategory);
  }
  
  const displayCategories = selectedCategory ? [selectedCategory] : allCategories;

  // Create placeholder cards for demo
  const createPlaceholders = (count) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `placeholder-${i}`,
      isPlaceholder: true
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-white text-xl">Loading Pulse TV...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
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
          <div className="flex flex-col gap-4">
            {/* Top Row - Logo and Actions */}
            <div className="flex items-center justify-between">
              {/* Left Side - Pulse TV Logo */}
              <Link to="/tv" onClick={() => setSelectedCategory(null)} className="flex items-center gap-3">
                <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-pink-400 bg-clip-text text-transparent drop-shadow-lg">
                  Pulse TV
                </div>
              </Link>

              {/* Right Side - Actions */}
              <div className="flex items-center gap-4 text-sm">
                {selectedCategory && (
                  <button
                    onClick={() => setSelectedCategory(null)}
                    className="px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg transition-colors text-xs"
                  >
                    Clear Filter
                  </button>
                )}
              </div>
            </div>
            
            {/* Category Navigation - Scrollable */}
            {allCategories.length > 0 && (
              <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={`flex-shrink-0 px-4 py-2 rounded-lg font-medium transition-all text-sm ${
                    selectedCategory === null
                      ? 'bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white shadow-lg scale-105'
                      : 'bg-slate-700/50 text-gray-300 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  All
                </button>
                {allCategories.map((category) => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`flex-shrink-0 px-4 py-2 rounded-lg font-medium transition-all text-sm capitalize ${
                      selectedCategory === category
                        ? 'bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white shadow-lg scale-105'
                        : 'bg-slate-700/50 text-gray-300 hover:bg-slate-700 hover:text-white'
                    }`}
                  >
                    {category.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="pb-16 relative" style={{ zIndex: 1 }}>
        {/* Most Watched Section */}
        {mostWatched.length > 0 && !selectedCategory && (
          <div className="mb-16 mt-16">
            <div className="max-w-7xl mx-auto px-6 mb-6">
              <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                <span className="w-1 h-8 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                Most Watched
              </h2>
            </div>
            <div className="w-full overflow-x-auto pb-10 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
              <div className="flex gap-5" style={{ paddingLeft: '48px', paddingRight: '24px', minWidth: 'fit-content' }}>
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
        {continueWatching.length > 0 && !selectedCategory && (
          <div className="mb-16">
            <div className="max-w-7xl mx-auto px-6 mb-6">
              <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                <span className="w-1 h-8 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                Continue Watching
              </h2>
            </div>
            <div className="w-full overflow-x-auto pb-10 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
              <div className="flex gap-5" style={{ paddingLeft: '32px', paddingRight: '24px', minWidth: 'fit-content' }}>
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
        {displayCategories.map((category) => {
          const categorySeries = filteredSeriesByCategory[category] || [];
          if (categorySeries.length === 0) return null;

          return (
            <div key={category} className="mb-16">
              <div className="max-w-7xl mx-auto px-6 mb-6">
                <h2 className="text-3xl font-bold text-white capitalize flex items-center gap-3">
                  <span className="w-1 h-8 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                  {category.replace(/_/g, ' ')}
                </h2>
              </div>
              <div className="w-full overflow-x-auto pb-10 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
                <div className="flex gap-5" style={{ paddingLeft: '32px', paddingRight: '24px', minWidth: 'fit-content' }}>
                  {categorySeries.map((s) => (
                    <SeriesCard key={s.id} series={s} />
                  ))}
                  {/* Add placeholders to show more content is coming */}
                  {!selectedCategory && createPlaceholders(Math.min(3, 6 - categorySeries.length)).map((item) => (
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
        {!selectedCategory && (
          <div className="mb-16">
            <div className="max-w-7xl mx-auto px-6 mb-6">
              <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                <span className="w-1 h-8 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                New This Week
              </h2>
            </div>
            <div className="w-full overflow-x-auto pb-10 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
              <div className="flex gap-5" style={{ paddingLeft: '32px', paddingRight: '24px', minWidth: 'fit-content' }}>
                {createPlaceholders(6).map((item) => (
                  <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-purple-900/30 via-blue-900/30 to-pink-900/30 rounded-lg border border-purple-500/30 flex flex-col items-center justify-center">
                    <span className="text-slate-400 text-xs mb-2">📺</span>
                    <span className="text-slate-400 text-xs">Coming Soon</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {filteredSeries.length === 0 && !loading && (
          <div className="text-center py-20 mt-12">
            {selectedCategory ? (
              <>
                <p className="text-gray-400 text-xl mb-2">No series found in this category</p>
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="mt-4 px-6 py-2 bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                >
                  View All Categories
                </button>
              </>
            ) : (
              <p className="text-gray-400 text-xl">No series available yet</p>
            )}
          </div>
        )}
      </div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        /* Smooth scroll behavior */
        html {
          scroll-behavior: smooth;
        }
      `}</style>
    </div>
  );
};

export default TV;
