import React, { useState, useEffect, useMemo } from 'react';
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
      setError(null);
      
      const [mostWatchedRes, seriesRes, continueRes] = await Promise.all([
        fetch('/api/tv/most-watched', { credentials: 'include' }),
        fetch('/api/tv/series', { credentials: 'include' }),
        fetch('/api/tv/continue-watching', { credentials: 'include' })
      ]);
      
      if (mostWatchedRes.ok) {
        const data = await mostWatchedRes.json();
        setMostWatched(data.series || []);
      }
      
      if (seriesRes.ok) {
        const data = await seriesRes.json();
        setSeries(data.series || []);
      }
      
      if (continueRes.ok) {
        const data = await continueRes.json();
        setContinueWatching(data.episodes || []);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching TV data:', err);
      setError('Failed to load content. Please try again.');
      setLoading(false);
    }
  };

  const allCategories = useMemo(() => {
    return [...new Set(series.map(s => s.category).filter(Boolean))];
  }, [series]);
  
  const seriesByCategory = useMemo(() => {
    const grouped = {};
    allCategories.forEach(cat => {
      grouped[cat] = series.filter(s => s.category === cat);
    });
    return grouped;
  }, [series, allCategories]);
  
  const filteredSeriesByCategory = useMemo(() => {
    if (selectedCategory) {
      return { [selectedCategory]: seriesByCategory[selectedCategory] || [] };
    }
    return seriesByCategory;
  }, [selectedCategory, seriesByCategory]);
  
  const displayCategories = useMemo(() => {
    return selectedCategory ? [selectedCategory] : allCategories;
  }, [selectedCategory, allCategories]);

  const hasContent = useMemo(() => {
    return Object.values(filteredSeriesByCategory).some(arr => arr.length > 0);
  }, [filteredSeriesByCategory]);

  // Helper Components
  const SectionHeader = ({ title }) => (
    <div className="max-w-7xl mx-auto px-6 mb-6">
      <h2 className="text-3xl font-bold text-white flex items-center gap-3">
        <span className="w-1 h-8 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
        {title}
      </h2>
    </div>
  );

  const PlaceholderCard = ({ count = 1, variant = 'default' }) => {
    const placeholders = Array.from({ length: count }, (_, i) => (
      <div 
        key={`placeholder-${i}`} 
        className={`flex-shrink-0 w-48 aspect-video rounded-lg border flex items-center justify-center ${
          variant === 'new' 
            ? 'bg-gradient-to-br from-purple-900/30 via-blue-900/30 to-pink-900/30 border-purple-500/30 flex-col'
            : 'bg-gradient-to-br from-slate-800/60 to-slate-900/60 border-purple-500/20'
        }`}
      >
        {variant === 'new' && <span className="text-slate-400 text-xs mb-2">📺</span>}
        <span className="text-slate-400 text-xs">Coming Soon</span>
      </div>
    ));
    return <>{placeholders}</>;
  };

  const HorizontalScrollSection = ({ children, className = '' }) => (
    <div className={`w-full overflow-x-auto pb-10 scrollbar-hide ${className}`} 
         style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
      <div className="flex gap-5" style={{ paddingLeft: '32px', paddingRight: '24px', minWidth: 'fit-content' }}>
        {children}
      </div>
    </div>
  );

  const CategoryRow = ({ category, series: categorySeries }) => {
    if (categorySeries.length === 0) return null;

    return (
      <div className="mb-16">
        <SectionHeader title={category.replace(/_/g, ' ')} />
        <HorizontalScrollSection>
          {categorySeries.map((s) => (
            <SeriesCard key={s.id} series={s} />
          ))}
          {!selectedCategory && (
            <PlaceholderCard count={Math.min(3, 6 - categorySeries.length)} />
          )}
        </HorizontalScrollSection>
      </div>
    );
  };

  const ContinueWatchingCard = ({ episode }) => {
    const thumbnailUrl = episode.episode?.thumbnail_url || episode.series?.thumbnail_url;
    const progressPercent = episode.progress?.last_position_seconds > 0 && episode.episode?.duration_seconds > 0
      ? (episode.progress.last_position_seconds / episode.episode.duration_seconds) * 100
      : 0;

    return (
      <Link
        to={`/tv/watch/${episode.episode_id}`}
        className="group flex-shrink-0 w-48 rounded-lg overflow-hidden hover:scale-105 transition-transform duration-200 relative"
      >
        <div className="relative aspect-video bg-gradient-to-br from-purple-900/40 via-blue-900/40 to-pink-900/40">
          {thumbnailUrl && (
            <img
              src={thumbnailUrl}
              alt={episode.title}
              className="w-full h-full object-cover"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          )}
          <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
          {progressPercent > 0 && (
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-600">
              <div
                className="h-full bg-gradient-to-r from-purple-500 via-blue-500 to-pink-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          )}
        </div>
        <div className="mt-2">
          <h3 className="text-white font-medium text-sm line-clamp-1">{episode.title}</h3>
          <p className="text-xs text-gray-400 mt-1">{episode.series?.title}</p>
        </div>
      </Link>
    );
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
        <div className="text-center">
          <p className="text-red-400 text-xl mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Animated Background Elements - More Subtle */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-10">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Top Navigation Bar - More Compact */}
      <div className="sticky top-0 z-50 bg-gradient-to-r from-slate-900/98 via-slate-800/98 to-slate-900/98 backdrop-blur-md border-b border-purple-500/10 shadow-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between py-3">
            {/* Left Side - Pulse TV Logo */}
            <Link to="/tv" onClick={() => setSelectedCategory(null)} className="flex items-center gap-2">
              <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-pink-400 bg-clip-text text-transparent">
                Pulse TV
              </div>
            </Link>

            {/* Right Side - Actions */}
            {selectedCategory && (
              <button
                onClick={() => setSelectedCategory(null)}
                className="px-3 py-1.5 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg transition-colors text-xs"
              >
                Clear Filter
              </button>
            )}
          </div>
          
          {/* Category Navigation - Compact Horizontal Scroll */}
          {allCategories.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
              <button
                onClick={() => setSelectedCategory(null)}
                className={`flex-shrink-0 px-3 py-1.5 rounded-lg font-medium transition-all text-xs ${
                  selectedCategory === null
                    ? 'bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white shadow-md'
                    : 'bg-slate-700/40 text-gray-300 hover:bg-slate-700/60 hover:text-white'
                }`}
              >
                All
              </button>
              {allCategories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`flex-shrink-0 px-3 py-1.5 rounded-lg font-medium transition-all text-xs capitalize ${
                    selectedCategory === category
                      ? 'bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white shadow-md'
                      : 'bg-slate-700/40 text-gray-300 hover:bg-slate-700/60 hover:text-white'
                  }`}
                >
                  {category.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="pb-12 relative pt-6" style={{ zIndex: 1 }}>
        {/* Most Watched Section */}
        {mostWatched.length > 0 && !selectedCategory && (
          <div className="mb-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span className="w-0.5 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                Most Watched
              </h2>
            </div>
            <div className="w-full overflow-x-auto pb-6 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
              <div className="flex gap-4" style={{ paddingLeft: '16px', paddingRight: '16px', minWidth: 'fit-content' }}>
                {mostWatched.map((s) => (
                  <SeriesCard key={s.id} series={s} />
                ))}
                {createPlaceholders(2).map((item) => (
                  <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-slate-800/40 to-slate-900/40 rounded-lg border border-purple-500/10 flex items-center justify-center">
                    <span className="text-slate-500 text-xs">Coming Soon</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Continue Watching Section */}
        {continueWatching.length > 0 && !selectedCategory && (
          <div className="mb-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span className="w-0.5 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                Continue Watching
              </h2>
            </div>
            <div className="w-full overflow-x-auto pb-6 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
              <div className="flex gap-4" style={{ paddingLeft: '16px', paddingRight: '16px', minWidth: 'fit-content' }}>
                {continueWatching.slice(0, 8).map((episode) => (
                  <Link
                    key={episode.id}
                    to={`/tv/watch/${episode.episode_id}`}
                    className="group flex-shrink-0 w-48 rounded-lg overflow-hidden hover:scale-105 transition-transform duration-200 relative"
                  >
                    <div className="relative aspect-video bg-gradient-to-br from-purple-900/40 via-blue-900/40 to-pink-900/40 rounded-lg overflow-hidden">
                      {(episode.episode?.thumbnail_url || episode.series?.thumbnail_url) ? (
                        <img
                          src={episode.episode?.thumbnail_url || episode.series.thumbnail_url}
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
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700/80">
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
                      <h3 className="text-white font-medium text-sm line-clamp-1 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-purple-400 group-hover:via-blue-400 group-hover:to-pink-400 group-hover:bg-clip-text transition-all">
                        {episode.title}
                      </h3>
                      <p className="text-xs text-gray-400 mt-1">{episode.series?.title}</p>
                    </div>
                  </Link>
                ))}
                {createPlaceholders(2).map((item) => (
                  <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-slate-800/40 to-slate-900/40 rounded-lg border border-purple-500/10 flex items-center justify-center">
                    <span className="text-slate-500 text-xs">Coming Soon</span>
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
            <div key={category} className="mb-10">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 mb-4">
                <h2 className="text-xl font-bold text-white capitalize flex items-center gap-2">
                  <span className="w-0.5 h-6 bg-gradient-to-b from-purple-500 via-blue-500 to-pink-500 rounded-full"></span>
                  {category.replace(/_/g, ' ')}
                </h2>
              </div>
              <div className="w-full overflow-x-auto pb-6 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', overflowY: 'visible' }}>
                <div className="flex gap-4" style={{ paddingLeft: '16px', paddingRight: '16px', minWidth: 'fit-content' }}>
                  {categorySeries.map((s) => (
                    <SeriesCard key={s.id} series={s} />
                  ))}
                  {!selectedCategory && createPlaceholders(Math.min(2, 5 - categorySeries.length)).map((item) => (
                    <div key={item.id} className="flex-shrink-0 w-48 aspect-video bg-gradient-to-br from-slate-800/40 to-slate-900/40 rounded-lg border border-purple-500/10 flex items-center justify-center">
                      <span className="text-slate-500 text-xs">Coming Soon</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}

        {/* Empty State */}
        {filteredSeries.length === 0 && !loading && (
          <div className="text-center py-16">
            {selectedCategory ? (
              <>
                <p className="text-gray-400 text-lg mb-4">No series found in this category</p>
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="px-5 py-2 bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-opacity text-sm"
                >
                  View All Categories
                </button>
              </>
            ) : (
              <p className="text-gray-400 text-lg">No series available yet</p>
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
